# 24 — Image Scanning — Trivy + Cosign + ECR

## Why this module exists

Your Dockerfile picked `python:3.13-slim` six months ago. Today that base image has 8 unpatched CVEs. Image scanning catches this before deployment. Image signing proves the artifact you deploy is the one you scanned.

## 1. The image-scanning matrix

| Tool | License | Scope |
|---|---|---|
| **Trivy** | Apache-2.0 | OS pkgs + lang deps + secrets + misconfigs + SBOM |
| **Grype** (Anchore) | Apache-2.0 | OS pkgs + lang deps |
| **Syft** (Anchore) | Apache-2.0 | SBOM generator (paired with Grype) |
| **Snyk Container** | Commercial | OS + lang + base-image recommendations |
| **Docker Scout** | Free + paid tiers | Docker Hub-integrated; Docker Inc. |
| **ECR Basic Scanning** | Free | Clair-based; on push |
| **ECR Enhanced Scanning** | Paid (Inspector) | Continuous; OS + OSS + Lambda |
| **GitHub Code Scanning** (Trivy/Container) | GHAS | Built into Actions; SARIF |
| **Anchore Engine / Sysdig Secure** | Commercial | Enterprise platform |

**Trivy is the OSS de-facto winner.** Installed in ~70% of K8s clusters per 2024 CNCF survey.

## 2. Trivy basics

```bash
# Install
brew install trivy

# Scan an image
trivy image python:3.13-slim
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:1.2.3

# Generate SBOM
trivy image --format cyclonedx -o sbom.json myapp:1.2.3
trivy image --format spdx-json -o sbom.spdx myapp:1.2.3

# Scan filesystem (pre-build)
trivy fs --severity HIGH,CRITICAL .

# Scan IaC
trivy config terraform/

# Scan a running K8s cluster
trivy k8s --report=summary cluster
```

### Output formats
- `table` — human-readable
- `json` — machine-readable
- `sarif` — for GitHub Code Scanning
- `cyclonedx` / `spdx-json` — SBOM formats
- `template` + custom templates — flexible

## 3. Trivy in CI

```yaml
# GitHub Actions
- name: Build image
  run: docker build -t app:${{ github.sha }} .

- name: Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: app:${{ github.sha }}
    severity: CRITICAL,HIGH
    exit-code: '1'
    format: sarif
    output: trivy.sarif

- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: trivy.sarif }
```

## 4. Cosign — image signing

```bash
# Install
brew install cosign

# Generate key pair (for traditional key-based; in 2026 prefer keyless)
cosign generate-key-pair
# cosign.pub + cosign.key produced

# Sign with key
cosign sign --key cosign.key 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Verify with public key
cosign verify --key cosign.pub 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Keyless (OIDC-based, the modern way)
cosign sign 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
# Opens browser; auth via OIDC (GitHub, Google, etc.)
# Signature + ephemeral cert from Fulcio + entry in Rekor transparency log

cosign verify \
  --certificate-identity-regexp 'https://github.com/myorg/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
```

### Keyless signing (the 2026 best practice)
- No key management — ephemeral keys per signing
- Identity bound to OIDC subject (GitHub repo, Google account)
- Verifiable in **Rekor** transparency log (immutable append-only)
- Signed by **Fulcio** (CA for short-lived certs)
- Part of the **Sigstore** project (Linux Foundation)

## 5. Attestations — SBOM, provenance, attestations as artifacts

Beyond signatures, Cosign can sign **attestations**:

```bash
# Generate SBOM
syft 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3 -o cyclonedx-json > sbom.json

# Attach SBOM as attestation
cosign attest --predicate sbom.json --type cyclonedx \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Verify
cosign verify-attestation --type cyclonedx \
  --certificate-identity-regexp 'https://github.com/myorg/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
```

Attestation types: `cyclonedx` (SBOM), `slsaprovenance` (build provenance per SLSA), `vuln` (scan results), `custom`.

## 6. SLSA — Supply chain Levels for Software Artifacts

SLSA v1.0 (2023) defines 4 levels of build-provenance hygiene:

| Level | What you prove |
|---|---|
| **L1** | Build is automated; provenance generated |
| **L2** | Provenance is signed; build runs on hosted service with audit |
| **L3** | Build runs in isolated env; provenance is non-falsifiable |
| **L4** | Two-party review of all changes; hermetic builds |

GitHub Actions can produce SLSA L3 provenance via the **slsa-github-generator** project.

Capital One internal policy: SLSA L3 minimum for production artifacts.

## 7. Admission control + signature verification at deploy

The deploy gate: K8s admission controller (Kyverno, OPA Gatekeeper, Sigstore Policy Controller) **verifies signatures before allowing pods**.

```yaml
# Kyverno policy: only signed images from your repo
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-signatures
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["1234.dkr.ecr.us-east-1.amazonaws.com/*"]
          attestors:
            - entries:
              - keyless:
                  subject: "https://github.com/myorg/*"
                  issuer: "https://token.actions.githubusercontent.com"
```

Pod fails admission if image isn't signed by your CI. This **closes the supply-chain loop** — verified at every stage from build to deploy.

## 8. ECR-specific image security

- **Basic scanning (free)** — Clair-based, runs on push only
- **Enhanced scanning** — uses **Amazon Inspector v2**; continuously rescans + alerts on new CVEs in already-pushed images
- **Pricing for Inspector**: ~$0.09 per image scan, ~$0.01 per image scan re-evaluation
- **Cross-account replication** for multi-team setups
- **Image tags immutable** option (toggle on repo) — once tagged, can't overwrite (prevents tag-takeover supply-chain attacks)

```bash
aws ecr put-image-scanning-configuration \
  --repository-name app --image-scanning-configuration scanOnPush=true

aws ecr put-image-tag-mutability \
  --repository-name app --image-tag-mutability IMMUTABLE
```

## 9. Distroless + minimal base images

Smaller base images = smaller attack surface = fewer CVEs to chase.

- **Distroless** (Google) — no shell, no package manager, just the runtime + your app
- **Chainguard Images** — distroless-style, daily-rebuilt, FIPS-validated options
- **Alpine** — small (~5MB) but has musl libc quirks
- **Wolfi** (Chainguard's distroless base) — glibc-based, designed for chainguard images

```dockerfile
# Build with full Python
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .

# Runtime distroless
FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /root/.local /home/nonroot/.local
COPY --from=builder /app /app
WORKDIR /app
ENV PATH=/home/nonroot/.local/bin:$PATH
CMD ["main.py"]
```

## 10. The end-to-end secure-image pipeline

```
Build (BuildKit, --no-cache-dir, non-root user, immutable tag)
  ↓
Scan with Trivy (HIGH+CRITICAL fail build)
  ↓
Generate SBOM with Syft
  ↓
Sign image with Cosign (keyless via OIDC)
  ↓
Attest SBOM with Cosign
  ↓
Generate SLSA provenance
  ↓
Push to ECR (immutable tags, enhanced scanning on)
  ↓
Deploy via ArgoCD/Flux
  ↓
Kyverno admission verifies signature + SBOM + provenance
  ↓
Falco runtime watches for drift / anomaly
```

This is the **SLSA L3 + verify-at-admission** pattern Capital One implements internally.

## 11. Quick self-check

1. What does Trivy scan beyond just OS package CVEs?
2. What's "keyless signing" with Cosign and what 3 components make it work?
3. What's the difference between an image signature and an attestation?
4. Why use immutable image tags?
5. What's SLSA L3 in one sentence?

(Answers: lang deps, secrets, IaC misconfigs, can also generate SBOM; OIDC-based ephemeral keys — Sigstore = Fulcio (CA) + Rekor (transparency log) + Cosign (CLI); signature proves who built it, attestation provides additional verified statements (SBOM, provenance, scan results); prevents tag-takeover supply-chain attacks where an attacker pushes a different image at the same tag; build runs in isolated env producing non-falsifiable provenance signed by the build platform.)
