# 23 — Admission control: OPA Gatekeeper, Kyverno, validating & mutating webhooks

## Why this module exists

PSA covers the security baseline. Everything else — "must have resource limits," "image from approved registries only," "no `latest` tag," "must have specific labels" — needs **admission control**. Kyverno and OPA Gatekeeper are the two heavyweights.

For Capital One–style postures: K8s policy enforcement at the admission layer is mandatory. Cloud Custodian (their open-source contribution) operates at the cloud-API layer; Kyverno/Gatekeeper at the K8s-API layer.

---

## 1. Admission flow recap

```
kubectl apply  →  API server
                     ↓
             authentication
                     ↓
             authorization (RBAC)
                     ↓
             mutating admission webhooks   ← inject defaults, sidecars, etc.
                     ↓
             schema validation
                     ↓
             validating admission webhooks  ← reject if non-compliant
                     ↓
             etcd write
```

**Mutating** webhooks can change the request (e.g., inject Istio sidecar). **Validating** webhooks can only accept/reject. PSA itself is a built-in validating admission plugin.

---

## 2. Kyverno — the cloud-native standard

[Kyverno](https://kyverno.io/) is **CNCF Incubating** (2022) → likely Graduated soon. Native K8s YAML policies (no Rego). Used by GitHub, Cloud Native Computing Foundation projects, and many regulated-finance shops.

### 2.1 Example policies

**Require resource limits:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: require-resource-limits }
spec:
  validationFailureAction: Enforce
  rules:
    - name: validate-limits
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Resource limits required for all containers"
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
```

**Disallow `latest` tag:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: disallow-latest-tag }
spec:
  validationFailureAction: Enforce
  rules:
    - name: validate-image-tag
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Tag 'latest' is not allowed in production"
        pattern:
          spec:
            containers:
              - image: "!*:latest"
```

**Mutate: add team label from namespace:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: inject-team-label }
spec:
  rules:
    - name: add-team-label
      match: { any: [{ resources: { kinds: [Deployment] } }] }
      mutate:
        patchStrategicMerge:
          metadata:
            labels:
              team: "{{ request.namespace }}"
```

**Verify image signatures (Cosign):**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: verify-images }
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-cosign
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["ghcr.io/myorg/*"]
          attestors:
            - entries:
                - keyless:
                    subject:  "https://github.com/myorg/*"
                    issuer:   "https://token.actions.githubusercontent.com"
                    rekor:    { url: "https://rekor.sigstore.dev" }
```

This last one is what makes Kyverno the supply-chain admission gate of choice — module 24 elaborates.

### 2.2 Why Kyverno (vs Gatekeeper) is the default in 2025+

- **YAML, not Rego** — no DSL to learn; team owns policy in `git`.
- **Built-in image verification** — first-class `verifyImages`, no plugins.
- **CLI** — `kyverno apply policy.yaml --resource manifest.yaml` for shift-left.
- **Background scan** — `Policy reports` (CRD `PolicyReport`) of existing non-compliant resources.

---

## 3. OPA Gatekeeper — the original

[OPA Gatekeeper](https://open-policy-agent.github.io/gatekeeper/) was the first K8s policy engine, based on **OPA (Open Policy Agent)** + the **Rego** language. Still widely deployed.

```yaml
# ConstraintTemplate — the policy logic
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata: { name: k8srequiredlabels }
spec:
  crd:
    spec:
      names: { kind: K8sRequiredLabels }
      validation:
        openAPIV3Schema:
          type: object
          properties: { labels: { type: array, items: { type: string } } }
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("missing labels: %v", [missing])
        }
---
# Constraint — the instance
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata: { name: must-have-team-label }
spec:
  match:
    kinds: [{ apiGroups: [""], kinds: ["Namespace"] }]
  parameters:
    labels: ["team", "cost-center"]
```

**When Gatekeeper wins**: orgs with existing OPA / Rego investment elsewhere (e.g., they use OPA for API gateway authz too); want the same language across.

**When Kyverno wins**: greenfield, want Cosign integration out of the box, want YAML rather than DSL.

---

## 4. Common policy library

A regulated-finance K8s platform usually enforces (via Kyverno/Gatekeeper):

| Category | Policies |
|---|---|
| **Security** | No privileged pods; no hostNetwork; no hostPID; capabilities dropped; non-root; readOnly root FS |
| **Identity** | Workload uses non-default SA; SA must have an `iam.gke.io/gcp-service-account` annotation (GKE); IRSA role annotation present (EKS) |
| **Supply chain** | Image from approved registry (ECR/GHCR/Harbor only); image signed; SBOM attestation present |
| **Resource** | Resource requests + limits set; QoS Guaranteed for prod; pidsLimit set |
| **Network** | NetworkPolicy must exist in namespace (otherwise reject pods); no `Service type=LoadBalancer` (only via Ingress + LB controller) |
| **Hygiene** | Every resource has `team`, `cost-center`, `environment` labels; no `latest` tags; `imagePullPolicy: IfNotPresent` (not `Always` — cost) |
| **Cost** | Storage class limited to approved (gp3 preferred over io2); no GPU on unapproved namespaces |
| **Operational** | PodDisruptionBudget required for Deployments with `replicas > 1`; HPA required for prod Deployments |

---

## 5. Background scanning + remediation

Both Kyverno and Gatekeeper periodically scan **existing** resources, not just admission-time. They write `PolicyReport` CRs listing non-compliant resources.

```bash
kubectl get policyreports -A
kubectl get clusterpolicyreports
```

Combined with **kyverno-cli generate** or **Gator** (Gatekeeper's CLI), you can run policies in CI before applying — shift-left.

For Capital One: the Cloud Custodian pattern (AWS-API) + Kyverno (K8s-API) gives belt-and-braces. Audit trails into Security Hub / SIEM.

---

## 6. Validating Admission Policies (CEL) — built-in alternative

K8s 1.30+ has **Validating Admission Policies** built-in, using CEL (Common Expression Language) — Kubernetes can do simple validations without an external webhook:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: require-team-label }
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: [v1]
        operations: [CREATE, UPDATE]
        resources: [namespaces]
  validations:
    - expression: "object.metadata.labels['team'] != ''"
      message: "Namespace must have a 'team' label"
```

For simple per-cluster rules with no external dependency, this is increasingly the cleanest path. For sophisticated logic (image verification, multi-resource correlation), Kyverno/Gatekeeper still win.

---

## 7. Failure modes

Admission webhooks are a **liveness risk**. If your Kyverno pods are down and `failurePolicy: Fail`, **no pods can start**. Recommended:

- `failurePolicy: Ignore` for non-security policies (informational, mutation-only).
- `failurePolicy: Fail` for security-critical (Cosign verification, PSA-equivalent).
- Exclude `kube-system` and the policy engine's own namespace from its rules.
- Run policy engine with HA (≥ 2 replicas).

---

## 8. The Cloud Custodian comparison

Cloud Custodian (C7N) operates at the **cloud-API layer**:

- "S3 bucket must have versioning enabled."
- "EBS volume must be encrypted."
- "EC2 instance must have IMDSv2."

It executes against AWS APIs (Lambda + CloudWatch Events, or scheduled). It does **not** enforce at admission time on K8s; it's after-the-fact for cloud resources.

Kyverno / Gatekeeper operate at the **K8s-API layer**:

- "Pod must have resource limits."
- "ServiceAccount must have IRSA annotation."
- "Image must be signed."

They enforce **before** the resource is created.

Together: Cloud Custodian guards the cloud account; Kyverno/Gatekeeper guard the K8s clusters in it. For Capital One the union is the answer.

---

## Sanity check

1. Mutating vs validating admission webhook — when is each used? Order in the request flow?
2. Kyverno vs OPA Gatekeeper — name two reasons greenfield shops pick Kyverno.
3. What does Kyverno's `verifyImages` block do, and what does it depend on?
4. `failurePolicy: Fail` on a Kyverno policy. What happens if the Kyverno pod is down?
5. Validating Admission Policies (CEL) covers what subset of cases Kyverno/Gatekeeper cover?
6. Cloud Custodian vs Kyverno — which layer of the stack does each operate on?

---

## Sources

- [Kyverno docs](https://kyverno.io/docs/)
- [OPA Gatekeeper docs](https://open-policy-agent.github.io/gatekeeper/website/)
- [Validating Admission Policies (CEL)](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)
- [Admission Controllers reference](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)
- [Cloud Custodian](https://cloudcustodian.io/)

→ Next: [24 — Supply chain on K8s — image signing admission, SBOM, BinAuth](24_k8s_supply_chain.md)
