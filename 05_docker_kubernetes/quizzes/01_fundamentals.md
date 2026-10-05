# Quiz — Part A: Container fundamentals (modules 1-5)

Take cold. No peeking at modules.

---

## Section 1 — Linux primitives & runtime (modules 1-2)

1. The "container kernel == host kernel" claim — what does it imply for kernel CVEs that fire inside a container?

2. Name three Linux namespaces Docker creates by default and one it does NOT create unless rootless/userns-remap.

3. cgroup v1 vs v2 — what does v2 add architecturally?

4. `--cap-drop ALL --cap-add NET_BIND_SERVICE` — what defense does this implement?

5. `--security-opt no-new-privileges` — which kernel bit does it set, and what attack does it block?

6. `dockerd → containerd → runc → process` — which component applies namespaces and capabilities?

7. Why is mounting `/var/run/docker.sock` into a container equivalent to root on the host?

8. What runtime does Fargate use under the hood, and what trust boundary does that introduce?

9. Why was `dockershim` removed from Kubernetes 1.24, and what replaced it on EKS / GKE / AKS?

10. What's the practical difference between gVisor (`runsc`) and Kata Containers?

---

## Section 2 — Images and security (modules 3-5)

11. Why is multi-stage Dockerfile mandatory for production ML images?

12. Why does Alpine break Python ML wheels?

13. Distroless vs Chainguard — which is the safer default for regulated finance, and why?

14. What does `EXPOSE 8080` actually do at runtime?

15. Five things a missing `.dockerignore` can leak into your image.

16. What's the difference between an **attestation** and a **signature** in Sigstore terms?

17. SLSA Level 3 vs Level 2 — what does L3 require that L2 doesn't?

18. Why is keyless Cosign signing safer than long-lived KMS-key signing?

19. ECR requires an S3 VPC endpoint in addition to the ECR endpoints. Why?

20. Docker Hub rate limit — what is it, and name two mitigations.

---

## Answer key

1. The CVE compromises the host kernel. There is no hypervisor boundary. The only mitigation is runtime sandboxing (gVisor / Kata).
2. Default: PID, NET, MNT, UTS, IPC, CGROUP. Not by default: USER.
3. Unified hierarchy + PSI + cleaner controller model. Every process is in exactly one cgroup.
4. Drops all capabilities; adds back only the one needed to bind ports < 1024. Default Docker grants 14 capabilities; this principle-of-least-privilege.
5. Sets `PR_SET_NO_NEW_PRIVS`. Blocks privilege escalation via `execve` (setuid binaries can't gain privileges).
6. **runc** does the namespace creation and capability dropping — the OCI runtime is where the security primitives are applied.
7. The Docker API socket allows spawning privileged containers and mounting host paths; effective root.
8. Fargate uses Firecracker MicroVMs — each task gets its own hypervisor-isolated kernel.
9. dockershim was a maintenance burden bridging CRI to Docker. EKS/GKE/AKS use `containerd` directly.
10. gVisor reimplements the syscall surface in userspace (Go). Kata runs an actual lightweight VM (QEMU/Firecracker) per pod. gVisor: less overhead, more compat issues. Kata: stronger isolation, more overhead.
11. To exclude build-time deps (gcc, build-essential) from the runtime image. Cuts attack surface and image size.
12. musl libc (not glibc); manylinux wheels assume glibc; pip falls back to source build, very slow + risky.
13. Chainguard. Daily rebuilds with security patches + signed by default + SBOM ships with image. Distroless updates less frequently.
14. Documentation only. Does NOT publish the port. The runtime flag `-p` (or K8s `containerPort` + Service) is what actually opens it.
15. `.git/` (history with possibly committed secrets), `.env*`, `~/.aws`, `~/.kube`, `~/.ssh`, IDE files, `node_modules`, build artifacts.
16. A **signature** proves "this artifact was signed by this identity." An **attestation** is a typed JSON document (SBOM, vuln scan, provenance) that is itself signed. Signatures answer "who"; attestations answer "what."
17. L3 requires: source + build platform meet specific security requirements; hermetic isolated builds; provenance signed by the build platform. L2 only requires hosted build service + signed provenance.
18. No long-lived key to rotate / steal. Identity is OIDC-bound to your CI; verification checks the identity matches policy. Short-lived (10-min) signing certificate from Fulcio.
19. ECR stores image layers in S3 buckets owned by ECR. Without S3 endpoint, layer downloads silently fall back to public internet.
20. 100 anonymous pulls / 6h / IP; 200 authenticated free. Mitigations: ECR pull-through cache; replicate hot images to your own registry; use Chainguard/Distroless.
