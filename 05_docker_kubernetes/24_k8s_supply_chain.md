# 24 — Supply chain on K8s: image signing admission, SBOM, Binary Authorization

## Why this module exists

Module 04 covered signing/SBOM at the registry level. This module covers **enforcement at the K8s admission gate** — making sure only verified images run.

---

## 1. The supply-chain admission stack

```
CI: build → SBOM (syft) → scan (Trivy) → sign (Cosign keyless via OIDC) → push
                                       ↓
                                  attestations stored as OCI referrers in registry
                                       ↓
       ─────────────────────────────────┼──────────────────────────────────
                                       ↓
       K8s admission webhook (Kyverno / Sigstore policy-controller / BinAuth)
                                       ↓
       Verify: signature valid, signer identity matches policy, attestation present
                                       ↓
       Pod created → kubelet pulls → containerd starts
```

---

## 2. Kyverno `verifyImages` — the cross-cloud answer

Already shown in module 23. Recap:

```yaml
verifyImages:
  - imageReferences: ["ghcr.io/myorg/*", "<acct>.dkr.ecr.us-east-1.amazonaws.com/myorg/*"]
    attestors:
      - count: 1
        entries:
          - keyless:
              subject: "https://github.com/myorg/*"
              issuer:  "https://token.actions.githubusercontent.com"
              rekor:   { url: "https://rekor.sigstore.dev" }
    verifyDigest: true          # also require @sha256 digest pinning
    mutateDigest: true           # auto-rewrite :tag → @sha256:... after verify
    required: true
```

The `mutateDigest: true` is a nice touch — Kyverno re-writes the image reference to include the digest at admission. The actually-running pod is pinned even if the manifest used `:1.2.3`.

---

## 3. Sigstore policy-controller — the focused alternative

`policy-controller` is a Sigstore project, narrower than Kyverno — only image verification. Suits teams who don't want the full Kyverno surface.

```yaml
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata: { name: require-cosign-keyless }
spec:
  images:
    - glob: "ghcr.io/myorg/**"
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuerRegExp: "https://token\\.actions\\.githubusercontent\\.com"
            subjectRegExp: "https://github\\.com/myorg/.*"
```

---

## 4. GCP Binary Authorization — cloud-native answer

For GKE, the cleanest path is native: **Binary Authorization** integrates with Cosign attestations stored as Grafeas notes.

```bash
# Create attestor
gcloud container binauthz attestors create prod-attestor \
  --attestation-authority-note=prod-note --pgp-public-key-file=key.pub

# Configure policy
gcloud container binauthz policy import policy.yaml
```

```yaml
# policy.yaml
defaultAdmissionRule:
  evaluationMode: ALWAYS_DENY
  enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
clusterAdmissionRules:
  us-central1-c.prod-cluster:
    evaluationMode: REQUIRE_ATTESTATION
    enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    requireAttestationsBy:
      - projects/my-proj/attestors/prod-attestor
```

Break-glass via labels with audit trail.

---

## 5. AWS Signer — the AWS path

AWS Signer + ECR + EKS:

1. AWS Signer signing profile (with KMS key).
2. ECR repo with `imageScanningConfiguration` and signing profile reference.
3. EKS admission via Kyverno verifying the signature.

AWS doesn't have a one-piece equivalent of BinAuth, but Cosign keyless via GitHub OIDC + Kyverno is what most AWS shops use today.

---

## 6. SBOM verification at admission

Not just "signed" — you can verify an SBOM attestation exists:

```yaml
# Kyverno
verifyImages:
  - imageReferences: ["ghcr.io/myorg/*"]
    attestations:
      - predicateType: https://spdx.dev/Document
        attestors: [...]
    required: true
```

Use this to reject images that have signatures but no SBOM — the security team's "we won't ship what we can't inventory" rule.

---

## 7. Vulnerability scan results at admission

Same pattern: an attestation of scan results (Trivy SARIF, e.g.) attached to the image.

```yaml
attestations:
  - predicateType: cosign.sigstore.dev/attestation/vuln/v1
    conditions:
      - all:
          - key: "{{ scan_result.scanner.result.severity }}"
            operator: NotEquals
            value: CRITICAL
```

The "scan must show no Criticals" gate, enforced at admission. Combined with allowlist for accepted exceptions.

---

## 8. The supply-chain checklist for a regulated K8s platform

- [ ] All images from approved registries (Kyverno `imageReferences` allowlist).
- [ ] All images pinned by digest at admission (Kyverno `mutateDigest`).
- [ ] All images signed (Kyverno `verifyImages` + Cosign keyless).
- [ ] SBOM attestation required.
- [ ] Scan-results attestation required, no CRITICAL.
- [ ] Build provenance attestation (SLSA L2+) required.
- [ ] Cosign verification log (Rekor) reachable + verified.
- [ ] Break-glass labeled + audited.
- [ ] Drift detected (existing pods rescanned periodically against new policy).

---

## 9. What about images that aren't yours? (3rd-party operators, Helm charts)

Reality: most clusters run dozens of community Helm charts (nginx-ingress, cert-manager, kube-prometheus-stack, ...). These are signed by their maintainers (Bitnami, Prometheus org, etc.) but not by *your* CI.

Two strategies:

1. **Re-sign** — pull, sign with your CI's identity, push to your registry. Tag with `myorg/cert-manager:1.14.0`.
2. **Allowlist their identities** — Kyverno policy that accepts `bitnami/*` signed by Bitnami's GitHub org, `prometheus/*` signed by Prometheus org, etc.

Re-signing is the safer pattern for air-gapped / strict shops. Allowlist is faster but trusts upstream identities you don't control.

---

## Sanity check

1. What does `mutateDigest: true` in Kyverno give you that just `verifyImages` doesn't?
2. GCP Binary Authorization vs Kyverno+Cosign — when to pick each?
3. Why does verifying an SBOM attestation matter beyond verifying a signature?
4. Third-party Helm charts: re-sign or allowlist? Trade-offs?
5. `failurePolicy: Fail` on a Cosign verification policy — what happens if Rekor is down?

---

## Sources

- [Kyverno verifyImages](https://kyverno.io/docs/writing-policies/verify-images/)
- [Sigstore policy-controller](https://docs.sigstore.dev/policy-controller/overview/)
- [GCP Binary Authorization](https://cloud.google.com/binary-authorization)
- [AWS Signer](https://docs.aws.amazon.com/signer/)
- [SLSA framework](https://slsa.dev/)
- [Sigstore](https://www.sigstore.dev/)

→ Next: [25 — Observability & runtime security — Prom, OTel, Falco, Hubble](25_observability_runtime.md)
