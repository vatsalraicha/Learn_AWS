# 29 — Kubernetes Security Overview

> Cross-link: [Topic 05 Modules 21-25](../05_docker_kubernetes/21_rbac_serviceaccounts.md) cover K8s security in depth.

## 1. The K8s attack surface

A K8s cluster is a complex system. Attackers target:
- **API server** — anyone with cluster credentials
- **kubelet** — node-level component, can run anything
- **etcd** — has all secrets; full DB access = full cluster
- **Container runtime** — escape from container to host
- **Network** — east-west traffic between pods
- **Cloud control plane** — for managed clusters (EKS/GKE/AKS)
- **Container images** — vulnerable deps in your apps
- **CI/CD pipeline** — supplies the manifests + images
- **DNS** — service-name resolution can be hijacked

## 2. The K8s security layers (4C model)

Google's "4C":
1. **Cloud** — the underlying cloud account (IAM, network)
2. **Cluster** — control plane + nodes
3. **Container** — image + runtime
4. **Code** — your app

Compromise at lower layer cascades upward. Defense-in-depth across all four.

## 3. CIS Kubernetes Benchmark

The community-maintained checklist of K8s hardening. Versions per minor K8s release. **kube-bench** (Aqua Security, OSS) runs it locally:

```bash
docker run --rm --pid=host -v $(pwd):/host \
  aquasec/kube-bench:latest run --targets node,policies
```

Sample findings:
- Use --authorization-mode=Node,RBAC (not AlwaysAllow)
- Ensure kubelet only authorized
- Restrict use of privileged containers
- etcd peer + client TLS

For managed clusters: EKS/GKE/AKS handle the control plane CIS items; you handle node + workload items.

## 4. K8s Security Best Practices (the 20-point checklist)

**Control plane:**
1. K8s version current; auto-upgrade where possible
2. API server audit logs to CloudWatch/SIEM
3. etcd encrypted at rest (default in EKS; explicit on self-managed)
4. RBAC: least privilege; no system:masters bindings
5. ABAC + AlwaysAllow disabled

**Workload:**
6. Pod Security Standards `restricted` profile (PSA enforce on all namespaces)
7. NetworkPolicy default-deny per namespace (Cilium/Calico)
8. ResourceQuotas + LimitRanges per namespace
9. Non-root users in all containers
10. Read-only root filesystem where possible
11. No privileged containers (except specific DaemonSets like CNI)
12. Drop all Linux capabilities; add only needed
13. Pod-level SecurityContext: runAsNonRoot=true, allowPrivilegeEscalation=false

**Image:**
14. Trivy scan; fail Critical+High at build
15. Cosign signed images; verify at admission (Kyverno/OPA)
16. Distroless or minimal base images
17. No latest tags; pin to digest in production

**Secrets:**
18. External Secrets Operator → cloud secrets manager (Module 35)
19. Never base64 unencrypted Secrets committed to Git (use SOPS/Sealed Secrets if storing in Git)

**Network:**
20. mTLS via service mesh (Istio/Linkerd) or app-level TLS

## 5. Pod Security Standards (PSS / PSA)

K8s 1.25 (Aug 2022) removed PodSecurityPolicy and replaced with **Pod Security Admission** (PSA) which enforces **Pod Security Standards (PSS)**.

Three profiles:
- **Privileged** — anything goes (system DaemonSets)
- **Baseline** — minimally restrictive; blocks known dangerous (privileged, hostPID)
- **Restricted** — heavily restricted; required for non-system workloads in 2026

Enable per namespace:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Restricted profile requirements:**
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities: drop ["ALL"], add only "NET_BIND_SERVICE" if needed
- seccompProfile: RuntimeDefault
- volumes: limited to safe types
- no host* (hostPath, hostNetwork, hostPID, hostIPC)

## 6. The kubelet attack — and defense

kubelet listens on every node (port 10250). Defenses:
- `--authorization-mode=Webhook` (not AlwaysAllow)
- `--anonymous-auth=false`
- TLS certificates for kubelet (auto-rotated via CSR)
- NetworkPolicy or SG: kubelet port only accessible from control plane

## 7. etcd — the crown jewel

All cluster state including all Secrets lives in etcd. Hardening:
- Encryption at rest (`EncryptionConfiguration` in apiserver)
- TLS for peer + client
- Filesystem permissions: 0600, owned by root
- Backup regularly (etcdctl snapshot save) — see Module 74

EKS/GKE/AKS manage etcd; you don't have direct access (which is good).

## 8. Audit logging

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "clusterroles", "rolebindings", "clusterrolebindings"]
```

EKS: enable via Cluster logging in Console / TF; ships to CloudWatch.
Self-managed: `--audit-policy-file=` + `--audit-log-path=` on apiserver.

What to alert on:
- `kubectl exec` into pods in prod namespace
- Secret reads from unusual ServiceAccount
- ClusterRoleBinding changes
- Privileged pod creation

## 9. Runtime threat detection

After-the-deploy security. Tools:
- **Falco** (Sysdig, CNCF Graduated) — eBPF-based runtime security
- **Tetragon** (Cilium ecosystem) — eBPF-based
- **Sysdig Secure** (commercial)
- **Aqua Security**
- **CrowdStrike Falcon Cloud Workload Protection**

Sample Falco rule:
```yaml
- rule: Shell in Container
  desc: Detect shell exec inside container
  condition: container.id != host and proc.name in (sh, bash, zsh)
  output: "Shell launched in container (user=%user.name container_id=%container.id image=%container.image.repository)"
  priority: WARNING
```

## 10. Provisioning EKS securely (preview Module 32)

The hardening checklist for EKS:
- Latest K8s minor (auto-update)
- API server endpoint private OR strict CIDR allowlist
- Logs to CloudWatch (api, audit, authenticator, controllerManager, scheduler)
- Envelope encryption with KMS for Secrets
- Node groups in private subnets only
- IMDSv2 enforced on nodes (hop-limit=1)
- IRSA / Pod Identity for pod IAM
- Container Insights enabled
- Restrict aws-auth ConfigMap OR use Access Entries

## 11. The K8s security tool matrix

| Layer | Tool |
|---|---|
| **CIS scan** | kube-bench |
| **Image scan** | Trivy |
| **Image signing** | Cosign |
| **Admission control** | Kyverno (preferred), OPA Gatekeeper |
| **Network policy** | Cilium |
| **mTLS** | Istio, Linkerd, Cilium SM |
| **Runtime** | Falco, Tetragon |
| **Secrets** | External Secrets Operator + cloud SM |
| **Audit** | Native API server audit |
| **CSPM** | Wiz, Snyk, Sysdig — multi-cluster posture |

## 12. Quick self-check

1. What's the 4C model and what's at each layer?
2. What replaced PodSecurityPolicy and what are the three profiles?
3. Why is etcd the "crown jewel" of K8s security?
4. What's Falco and what does it use under the hood?
5. Why is `allowPrivilegeEscalation: false` important?

(Answers: Cloud/Cluster/Container/Code — defense in depth across; Pod Security Admission with PSS profiles privileged/baseline/restricted; contains all cluster state including Secrets — full DB access = full cluster compromise; runtime threat detector using eBPF kernel hooks to detect anomalous syscalls; prevents setuid binaries from escalating to root inside the container.)
