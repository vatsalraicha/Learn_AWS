# 04 — Image security: scanning, SBOM, signing, supply chain

> *"You don't run software — you run a supply chain. If you don't know what's in your image, neither do your auditors."*

## Why this module exists

The 2020 SolarWinds breach and the 2021 `node-ipc` sabotage by `RIAEvangelist` made supply-chain security a board-level concern. Containers are the unit of software delivery in modern infrastructure; the OCI image is your supply-chain artifact. This module covers the four pillars that every regulated-finance container platform implements:

1. **Vulnerability scanning** — what's known-bad in this image?
2. **SBOM (Software Bill of Materials)** — what's in this image?
3. **Signing & attestations** — who built it and from what?
4. **Admission policy** — only verified images allowed to run.

The CNCF supply-chain stack — **Sigstore (Cosign + Rekor + Fulcio)**, **SLSA**, **in-toto**, **syft + grype**, **Trivy** — is now the de facto standard.

---

## 1. Vulnerability scanning

A scanner reads an image's package manifests (apt/dpkg, pip, npm, gem, go.mod, ...) and cross-references them against vulnerability databases (NVD CVE, OSV.dev, GitHub Advisory Database, vendor advisories).

### 1.1 The major tools

| Tool | Pricing | What it scans | Notes |
|---|---|---|---|
| **Trivy** (Aqua Security) | OSS, free | OS pkgs, language libs, IaC, secrets, K8s manifests | Most popular OSS scanner; fast; comprehensive |
| **Grype** (Anchore) | OSS, free | Same; sister-project to syft (SBOM) | Pair of tools that produces SBOM-then-scan |
| **Snyk** | Free tier + paid | Same + license + reachability analysis | Best false-positive triage UI; expensive |
| **Docker Scout** | Free for Hub users, paid for advanced | Same; tight Docker Hub integration | Built into Docker Desktop |
| **Clair** | OSS, free | OS pkgs primarily | Used inside Quay/Harbor |
| **Aqua** | Commercial | Same + runtime + drift | Enterprise platform |
| **Sysdig Secure** | Commercial | Same + runtime + Falco-derived runtime threats | Enterprise platform |
| **Wiz** | Commercial (agentless) | Same + cloud config + workload identity | Hot 2024–2026 commercial play |

### 1.2 Trivy in practice

```bash
# Scan an image, fail CI on HIGH/CRITICAL
trivy image \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  --exit-code 1 \
  --format sarif --output trivy.sarif \
  myorg/myimage:1.2.3

# Generate SBOM in CycloneDX format
trivy image --format cyclonedx --output sbom.cyclonedx.json myorg/myimage:1.2.3

# Scan a Dockerfile / IaC + filesystem
trivy fs --scanners vuln,misconfig,secret .

# Scan a K8s cluster (rolebindings, exposed secrets, image vulns)
trivy k8s --report summary cluster
```

`--ignore-unfixed` is the production toggle: don't fail builds on a CVE that has no fix available — log it, but don't block. Otherwise CVE noise will cripple your release cadence.

### 1.3 The "vulnerability scanning is necessary but not sufficient" reality

Vuln scanners produce false positives (the CVE applies to a code path your app doesn't use) and false negatives (zero-days, supply-chain backdoors). They are **necessary** because they catch the known-bad with low effort. They are **not sufficient** because:

- Tools differ on what counts as "vulnerable" (NVD severity vs Red Hat severity vs vendor's own).
- A CVE in an unused dependency is theater unless you can prove unreachability.
- Image-scan policies that block every HIGH ship slowly; ones that block nothing add no value. **Tune to your risk appetite, then enforce.**

Capital One's posture (inferred from Cloud Custodian + cfn-guard + cdk-nag patterns): scan, gate on CRITICAL + KEV (CISA Known Exploited Vulnerabilities), report HIGH, ignore unfixed below.

---

## 2. SBOM (Software Bill of Materials)

An SBOM is a **machine-readable list of every component in a software artifact**. EO 14028 (US) and the EU CRA mandate SBOMs for software sold to governments — for regulated finance, your auditors will ask. The two major formats:

- **SPDX** (Linux Foundation, ISO/IEC 5962:2021)
- **CycloneDX** (OWASP)

Both express the same content: package name, version, purl (Package URL), license, optional supplier and hash.

### 2.1 Generating SBOMs

```bash
# syft from Anchore — the standard OSS SBOM tool
syft myorg/myimage:1.2.3 -o cyclonedx-json > sbom.cdx.json
syft myorg/myimage:1.2.3 -o spdx-json     > sbom.spdx.json

# Trivy can also produce SBOMs
trivy image --format cyclonedx -o sbom.cdx.json myorg/myimage:1.2.3
```

### 2.2 SBOMs and the OCI image

SBOMs can be **embedded in the image** (as a separate OCI artifact via OCI 1.1 referrers API) or **stored alongside** the image in the registry. Modern registries (GHCR, ECR, GAR, ACR, Harbor, JFrog) all support attaching SBOMs as referrers.

The Docker `buildx` builder generates an SBOM automatically when you pass `--sbom=true`:

```bash
docker buildx build --sbom=true --provenance=true -t myorg/myimage:1.2.3 --push .
```

This results in three artifacts in the registry: the image, the SBOM attestation, and the provenance attestation.

---

## 3. Signing & attestations — Sigstore / Cosign / SLSA

### 3.1 The Sigstore stack

| Component | What it does |
|---|---|
| **Cosign** | CLI that signs/verifies container images, blobs, attestations |
| **Fulcio** | Free CA that issues short-lived signing certificates tied to OIDC identities (`alice@anthropic.com`, `repo:myorg/myrepo`) |
| **Rekor** | Public, append-only, transparency log of all signatures (like Certificate Transparency for image signatures) |
| **Policy Controller** | K8s admission controller that verifies Sigstore signatures before allowing pods |

**Keyless signing** is the headline feature: no long-lived key to manage. The flow:

1. CI authenticates to Fulcio via OIDC (GitHub Actions, GitLab, GCP IDTOKEN, etc.).
2. Fulcio issues a 10-minute X.509 certificate identifying the CI workload.
3. Cosign signs the image with the cert, uploads the signature + cert + Rekor log entry.
4. At pull/admission time, verifiers check: signature valid, cert chains to Fulcio root, identity matches policy (e.g., "signature must come from `repo:myorg/myrepo`"), log entry exists in Rekor.

```bash
# Sign keylessly with the OIDC identity from this CI run
cosign sign --yes myorg/myimage@sha256:abc123...

# Verify with an identity-based policy
cosign verify \
  --certificate-identity-regexp 'https://github\.com/myorg/.*' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  myorg/myimage@sha256:abc123...
```

### 3.2 SLSA — Supply-chain Levels for Software Artifacts

SLSA ([slsa.dev](https://slsa.dev)) defines four levels of provenance assurance for build pipelines:

| Level | Requirement | Achievable how |
|---|---|---|
| **SLSA 1** | Build has documented process; provenance recorded | Any CI with a build log |
| **SLSA 2** | Hosted build service; signed provenance | GitHub Actions + Cosign attestation |
| **SLSA 3** | Source + build platform meet specific security requirements (hermetic, isolated builds) | GitHub Actions Reusable Workflows + Hermetic builders; GCB; AWS-CB with strict IAM |
| **SLSA 4** | Two-person review + hermetic + reproducible | Rare in industry |

A **SLSA provenance attestation** records: what source repo + commit, what builder, what build steps, what inputs, what outputs. Stored alongside the image as a signed OCI attestation. Admission controllers (cosign policy-controller, Kyverno, Sigstore policy) verify the attestation at pull time.

### 3.3 in-toto attestations

`in-toto` is the framework SLSA is built on. An **attestation** is a signed JSON document `{ "subject": [{"name": "myimage", "digest": "..."}], "predicateType": "https://slsa.dev/provenance/v1", "predicate": {...} }`. Cosign creates and verifies these.

Beyond provenance, common predicate types: **SPDX SBOM**, **CycloneDX SBOM**, **vuln scan results**, **policy decision logs**. The image becomes a hub for an entire signed-evidence graph.

---

## 4. Admission control — only verified images run

Signing without enforcement is theater. At admission time (the moment K8s tries to pull and run an image), a controller must verify:

- Signature exists and is valid.
- Signer identity matches policy (e.g., from your CI org).
- SBOM exists.
- No KEV-class CVEs (or whatever your policy demands).

### 4.1 The major admission controllers

| Tool | Origin | Notes |
|---|---|---|
| **Sigstore policy-controller** | Sigstore project | Lightweight; focused on signature verification |
| **Kyverno** | CNCF Incubating | General K8s policy engine; native signature verification (no Rego) |
| **OPA Gatekeeper** | Open Policy Agent | General; Rego-based; requires `image-verify` plugin or sidecar |
| **Connaisseur** | SAP open source | Signature-only |
| **AWS Signer + Signing Profiles** | AWS-native | ECR + EKS integration |
| **GCP Binary Authorization** | GCP-native | GKE-integrated; supports Cosign attestations natively |
| **Azure Defender for Containers** | Azure-native | Defender for Cloud feature |

For multi-cloud or vendor-neutral: **Kyverno is the leader for K8s admission policy in 2025–2026**. Native Cosign verification, no Rego, fast adoption curve. See module 23 for Kyverno deep-dive.

### 4.2 Example Kyverno policy — only signed images, only from your CI

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-cosign
      match:
        any:
          - resources: { kinds: [Pod] }
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestors:
            - count: 1
              entries:
                - keyless:
                    subject: "https://github.com/myorg/*"
                    issuer:   "https://token.actions.githubusercontent.com"
                    rekor:    { url: "https://rekor.sigstore.dev" }
```

This rejects any pod whose image (matching `ghcr.io/myorg/*`) is not signed by a workflow from the `myorg` GitHub org. No long-lived keys; no manual rotation.

---

## 5. The full supply-chain pipeline (template)

For a regulated shop, the production pipeline looks like:

```
1. Developer pushes to main
        │
        ▼
2. CI: build image with BuildKit, --sbom=true --provenance=true
        │
        ▼
3. CI: cosign sign (keyless via OIDC)
        │
        ▼
4. CI: cosign attest --predicate sbom.cdx.json --type cyclonedx
        │
        ▼
5. CI: trivy image --format sarif → upload to SecHub / DefectDojo
        │
        ▼
6. CI: cosign attest --predicate trivy-results.sarif --type vuln-results
        │
        ▼
7. CI: push to ECR / GHCR
        │
        ▼
8. ArgoCD / Flux deploys manifests referencing image@digest (not tag)
        │
        ▼
9. K8s admission (Kyverno) verifies signatures + SBOM + scan results
        │
        ▼
10. Workload runs.
        │
        ▼
11. Runtime (Falco) detects drift from declared behavior; emits to SIEM.
```

Capital One's Cloud Custodian operates one tier above this — at the AWS-API layer for things like "no public ECR repos," "no images older than 90 days in production." K8s-level enforcement (Kyverno/Gatekeeper) is the runtime gate.

---

## 6. Common supply-chain failures

| Failure | Example | Mitigation |
|---|---|---|
| Typosquatting | `requests-2.31.0` vs `requests-2.31.0.tar.gz` malicious | Verify by hash in lockfile; restrict registries |
| Dependency confusion | Internal package name resolves to public PyPI | Private PyPI mirror with strict precedence |
| Compromised build infra | Tooling tampered to inject backdoor | SLSA L3 hermetic builders |
| Compromised signing key | Key stolen | Keyless signing (Cosign + Fulcio) — no long-lived key |
| Compromised registry | Image swapped at rest | Pinned digests (not tags) + signature verification |
| Built-with-malicious-deps | Author publishes a clean version then a poisoned one | Lockfile + pin + monitor for diff in dep tree |
| Image layer poisoning | Old layer reused that contains a backdoor | Rebuild from base periodically; Chainguard rebuilds daily |

---

## 7. ECR / GAR / ACR — built-in scanning

Each cloud registry ships native scanning:

- **AWS ECR Image Scanning** — basic (free) on push; **Enhanced** (paid, via Amazon Inspector) for continuous + OS + language libs.
- **GCP Artifact Registry** — Container Analysis API, free for OS packages; paid for language libs.
- **Azure Container Registry** — Microsoft Defender for Cloud handles scanning; ACR itself doesn't scan natively (delegates to Defender).
- **Docker Hub / GHCR** — Docker Scout / GHCR dependency scanning.

For regulated finance, **use both**: cloud-native scanner + Trivy in CI. The cloud-native catches images that bypassed CI (e.g., from public registries), CI catches before push.

---

## 8. Image promotion model

A production policy distinguishes between:

- **dev/feature images** — scanned, NOT signed, NOT in prod registry, ephemeral
- **staging images** — scanned, signed, in staging registry
- **prod images** — scanned, signed, **promoted by digest** from staging, ECR/GHCR replicated, admission-verified

The key word is **promote, not rebuild**. Rebuilding "the same code" produces a different digest because of timestamps, package metadata, etc. Promotion preserves provenance: the prod image is byte-identical to the staging image that was scanned and signed.

```bash
# Promote by digest
crane copy \
  staging-registry.internal/myimage@sha256:abc... \
  prod-registry.internal/myimage:1.2.3
```

---

## Sanity check

1. What's the difference between SPDX and CycloneDX, and why might a regulated shop produce both?
2. Why is keyless Cosign signing safer than long-lived KMS-key signing?
3. What does SLSA L3 require that L2 does not?
4. Where is a Sigstore Rekor log entry actually stored, and why does that matter?
5. What's the difference between an **attestation** and a **signature**?
6. Why is "promote by digest" superior to "rebuild in CI" for production releases?

---

## Sources

- [Sigstore](https://www.sigstore.dev/)
- [Cosign repo](https://github.com/sigstore/cosign)
- [SLSA framework](https://slsa.dev/)
- [in-toto attestations](https://github.com/in-toto/attestation)
- [Trivy](https://trivy.dev/)
- [Syft & Grype](https://github.com/anchore)
- [CycloneDX spec](https://cyclonedx.org/specification/overview/)
- [SPDX spec](https://spdx.dev/)
- [Kyverno verifyImages](https://kyverno.io/docs/writing-policies/verify-images/)
- [GCP Binary Authorization](https://cloud.google.com/binary-authorization)
- [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

→ Next: [05 — Container registries: ECR, GAR, ACR, Harbor, JFrog](05_registries.md)
