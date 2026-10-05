# 34 — OPA Gatekeeper — Policy as Code

## Why this module exists

K8s admission control is your last gate. Pods get created via the API server; admission controllers validate (and mutate) every request. **OPA Gatekeeper** and **Kyverno** are the two policy engines. In 2026, **Kyverno is winning** for simpler use cases (YAML rules) but OPA/Rego still dominates for complex multi-cloud policy.

## 1. Why policy as code

Without policy enforcement: every team can deploy whatever they want — privileged containers, hostPath volumes, latest tags, no resource limits. Eventually one of them tanks the cluster.

With policy as code:
- Rules live in Git, reviewed like any other code
- Enforced at admission (request blocked before it reaches etcd)
- Auditable + dry-runnable (audit mode reports violations without blocking)
- Compliance-by-design

## 2. Admission controllers — how they work

```
kubectl apply → API server → authentication → authorization → mutating webhook(s)
                                                                  ↓
                                                       validating webhook(s) → etcd
```

Mutating webhooks can change the request (inject sidecars, add labels). Validating webhooks accept or reject.

OPA Gatekeeper + Kyverno register themselves as validating (and optionally mutating) webhooks.

## 3. Install OPA Gatekeeper

```bash
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace
```

Verify:
```bash
kubectl get pods -n gatekeeper-system
kubectl get crds | grep gatekeeper
```

## 4. Concepts

- **ConstraintTemplate** — Rego policy code + parameter schema
- **Constraint** — instance of a ConstraintTemplate with specific parameters and target kinds
- **Audit** — periodic re-evaluation against existing resources (not just admission)
- **Mutation** (since Gatekeeper 3.6) — modify requests; less mature than Kyverno mutations

## 5. ConstraintTemplate example

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names: { kind: K8sRequiredLabels }
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items: { type: string }
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

## 6. Apply a Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: ns-must-have-owner
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace"]
  enforcementAction: deny    # or "warn" or "dryrun"
  parameters:
    labels: ["owner", "cost-center"]
```

Now any Namespace creation/modification without `owner` AND `cost-center` labels gets denied.

## 7. The classic policies

### Reject NodePort Services
```rego
package k8snodeport
violation[{"msg": msg}] {
  input.review.object.kind == "Service"
  input.review.object.spec.type == "NodePort"
  msg := "NodePort Services are not allowed; use ClusterIP + Ingress"
}
```

### Reject privileged containers
```rego
package k8sprivileged
violation[{"msg": msg}] {
  some i
  container := input.review.object.spec.containers[i]
  container.securityContext.privileged == true
  msg := sprintf("Container %v is privileged", [container.name])
}
```

### Restrict image registries
```rego
package k8stregistry
violation[{"msg": msg}] {
  some i
  container := input.review.object.spec.containers[i]
  not startswith(container.image, "1234.dkr.ecr.us-east-1.amazonaws.com/")
  msg := sprintf("Image %v must be from approved registry", [container.image])
}
```

## 8. Kyverno alternative (simpler for most use cases)

Kyverno policies are YAML, not Rego — significantly simpler for the common 80% of policies.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-labels
      match:
        any:
          - resources: { kinds: [Namespace] }
      validate:
        message: "Namespace must have 'owner' and 'cost-center' labels"
        pattern:
          metadata:
            labels:
              owner: "?*"
              cost-center: "?*"
```

```yaml
# Reject privileged
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: no-privileged }
spec:
  validationFailureAction: Enforce
  rules:
    - name: privileged
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Privileged containers are not allowed"
        pattern:
          spec:
            containers:
              - =(securityContext):
                  =(privileged): "false"
```

Kyverno also does mutations (auto-inject sidecars, defaults) cleanly.

## 9. OPA Gatekeeper vs Kyverno (2026)

| | Gatekeeper | Kyverno |
|---|---|---|
| **Lang** | Rego | YAML |
| **Learning curve** | Steep | Mild |
| **Cross-platform** | Yes (Rego + OPA also used for Terraform, Envoy, etc.) | K8s-specific |
| **Mutation** | Mature-ish | Native, full-featured |
| **Generation** | Limited | Native (auto-create resources) |
| **Image signature verify** | Via plugins | Native (verifyImages) |
| **Performance** | OPA engine | Similar |
| **CNCF** | Graduated | Graduated 2024 |
| **Best for** | Multi-tool policy unification | K8s-focused shops |

Picking 2026: Kyverno for simpler policies; OPA when you need cross-tool policy (TF + K8s + Envoy in same Rego library).

## 10. Audit mode + dry-run

Before enforcing in prod, run in **audit** mode (Gatekeeper) / **Audit** action (Kyverno). Violations log without blocking. Then promote to Enforce when zero violations.

```yaml
enforcementAction: dryrun    # Gatekeeper
# or
enforcementAction: warn      # Gatekeeper
# or in Kyverno:
validationFailureAction: Audit
```

## 11. Common policy library

The **OPA Policy Library** (https://github.com/open-policy-agent/library) and **Kyverno Policy Library** (https://kyverno.io/policies/) have 100+ ready-to-use policies:
- Require resources/limits
- Require liveness/readiness probes
- Restrict node selectors
- Force runAsNonRoot
- Block deprecated APIs
- Image registry allowlist
- Pod Security Standards-equivalent

Start with the library; customize as needed.

## 12. Quick self-check

1. What's a Mutating vs Validating webhook?
2. What's a ConstraintTemplate vs Constraint in Gatekeeper?
3. Why is Kyverno winning over Gatekeeper for K8s-only shops in 2026?
4. What's the difference between audit mode and enforce mode?
5. What's the relationship between OPA and Gatekeeper?

(Answers: mutating modifies the request (inject sidecars), validating accepts/rejects; ConstraintTemplate is Rego policy + param schema (reusable), Constraint is an instance with specific params and target kinds; YAML simpler than Rego, native mutation + generation, image signature verify built-in; audit logs violations without blocking — used to roll out new policies safely; OPA is the policy engine, Gatekeeper is K8s admission controller using OPA + adds K8s-specific UX.)
