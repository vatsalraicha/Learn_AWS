# 02 — Docker architecture & runtime: dockerd → containerd → runc → OCI

> *"Docker is no longer one binary. It's four daemons in a trench coat."*

## Why this module exists

When you type `docker run nginx`, **four** distinct components participate. Knowing which one does what is what separates "Docker user" from "Docker engineer." More importantly, the trust and attack-surface boundaries you must protect in production all sit between these components. The `/var/run/docker.sock` mount is dangerous because of this architecture, not because Docker is broken.

This module also explains why Kubernetes removed `dockershim` in 1.24 — and why on most production clusters, **Docker doesn't actually run anywhere**. The CRI runtime is `containerd` or `CRI-O`, not Docker.

---

## 1. The runtime stack

```
┌─────────────────────────────────────────────────────────────┐
│  docker CLI                                                 │
│   └─→ REST over /var/run/docker.sock                        │
│                                                             │
│  dockerd  (Moby project; the Docker engine daemon)          │
│   ├─ image management, networking (libnetwork), volumes,    │
│   │  buildkit (since 23.0), swarm                           │
│   └─→ gRPC over /run/containerd/containerd.sock             │
│                                                             │
│  containerd  (CNCF Graduated; standalone)                   │
│   ├─ image pull/push, container lifecycle, snapshotter      │
│   └─→ exec containerd-shim-runc-v2                          │
│                                                             │
│  containerd-shim-runc-v2  (one per container)               │
│   └─→ exec runc                                             │
│                                                             │
│  runc  (OCI runtime reference impl, originally libcontainer)│
│   ├─ creates namespaces, cgroups, drops caps, applies LSM   │
│   └─→ exec /your/process                                    │
│                                                             │
│  Your container process                                     │
└─────────────────────────────────────────────────────────────┘
```

### Why so many layers?

History. Docker was originally one binary that did everything (build, push, pull, run, network, volume, swarm). The Linux Foundation pressured Docker to split out the runtime so other tools could use it without depending on the full Docker engine. The result:

- **OCI Image Spec + Runtime Spec** (June 2015 launch): standard format for images and a standard JSON config for starting them.
- **runc** (extracted from Docker): the OCI reference runtime.
- **containerd** (extracted from Docker): the lower-level container manager. Donated to CNCF, **Graduated 2019**.
- **dockerd** stays as the user-facing engine but talks to containerd underneath.

Kubernetes adopted **containerd directly** (skipping dockerd) via the CRI (Container Runtime Interface). The `dockershim` adapter was deprecated in K8s 1.20 and **removed in 1.24** (May 2022). If you `kubectl exec` into a pod on EKS / GKE / AKS today, the runtime underneath is almost certainly **containerd** or **CRI-O** — not Docker.

This matters because:

- Tooling that ships with Docker (BuildKit, Compose, docker-credential-helpers) does not work in `kubectl exec`-shells inside pods.
- A container running on K8s does NOT have Docker semantics; e.g., `entrypoint`/`cmd` precedence is OCI's, not Docker-compose's.
- Debugging "why does this image fail in prod but works locally?" often reduces to a containerd-vs-dockerd version-skew problem.

---

## 2. Alternative OCI runtimes

`runc` is the reference, but the runtime is pluggable. Production-relevant alternatives:

| Runtime | Language | Use case | Where |
|---|---|---|---|
| `runc` | Go | Default | Everywhere |
| `crun` | C | Lower memory footprint, faster startup | Default on RHEL/Fedora |
| `youki` | Rust | Memory-safe alternative; experimental | Research |
| `runsc` (gVisor) | Go | Userspace syscall reimplementation; smaller kernel attack surface | **Cloud Run, App Engine standard** |
| `kata-runtime` | Go | One lightweight VM per pod (QEMU/Cloud Hypervisor/Firecracker) | **AKS Confidential Containers, IBM Cloud, on-prem multi-tenant K8s** |
| `nvidia-container-runtime` | Go | runc wrapper that injects GPU devices/libraries | All GPU container hosts |

For ML on K8s (module 31), the runtime you actually care about is `nvidia-container-runtime` (a runc wrapper, not a replacement) plus the NVIDIA GPU Operator.

For **multi-tenant** ML platforms where you cannot trust workload code, **gVisor or Kata** is the production answer — they preserve the kernel boundary that vanilla runc does not.

---

## 3. The dangerous `/var/run/docker.sock`

The Docker daemon listens on a Unix socket at `/var/run/docker.sock`. **Anything that can talk to that socket has root on the host**, period. The mechanism: it can spawn a privileged container with `-v /:/host` and write to `/etc/sudoers` (or anywhere else).

This is why mounting docker.sock into a container — a pattern often seen for "Docker-in-Docker CI" or "let this container observe other containers" — is **the most dangerous bind mount you can make**. Anyone who compromises that container compromises the host.

**The `docker` Linux group is root-equivalent for the same reason** — adding a user to it lets them talk to the socket. CIS Docker Benchmark 1.x explicitly calls this out.

### Safer alternatives

- **Docker-in-Docker (DinD)** for CI: spawn a dedicated `docker:dind` *sibling* container with its own daemon, talk to *that* daemon. Still privileged, but at least the blast radius is the CI pod, not the host.
- **Rootless Docker / Podman**: the daemon runs as your user, the socket is in `~/.docker/run/docker.sock`. Mounting it into a container still grants your-user-level access, but not root.
- **Docker socket proxy** ([`tecnativa/docker-socket-proxy`](https://github.com/Tecnativa/docker-socket-proxy)): a sidecar that exposes only the API endpoints you whitelist (e.g., `GET /containers/json` for monitoring, no `POST`). Cattle-grade hygiene.
- **CRI / containerd directly**: K8s tooling like `crictl`, `nerdctl`, or kubelet itself. No Docker layer at all.

For any production environment: **never mount docker.sock**. For monitoring sidecars (Datadog agent, Falco), prefer the socket-proxy pattern with read-only API verbs.

---

## 4. TLS-protected Docker daemon (for remote control)

By default the Docker daemon listens *only* on a Unix socket. If you expose it on TCP (for remote management), it must be behind mTLS. The combination of `tcp://` + no-TLS is a complete RCE primitive — there are botnets that scan for it.

```bash
# /etc/docker/daemon.json
{
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/etc/docker/certs/ca.pem",
  "tlscert":   "/etc/docker/certs/server-cert.pem",
  "tlskey":    "/etc/docker/certs/server-key.pem",
  "hosts": ["tcp://0.0.0.0:2376", "unix:///var/run/docker.sock"]
}
```

In practice, **don't do this**. Use SSH for remote control (Docker context with `ssh://`), or use a higher-level orchestrator (K8s, Nomad, ECS, Swarm) so you never need to expose the daemon API.

---

## 5. BuildKit — the modern builder

Since Docker 23.0 (Feb 2023), **BuildKit is the default builder**. The legacy builder is gone from new installs. BuildKit brings:

- **Parallel layer execution** based on the DAG of `RUN` instructions.
- **Better caching** via content-addressed layer cache, registry-backed cache (`--cache-from`, `--cache-to`).
- **Mount types**:
  - `--mount=type=cache` — persistent build cache across runs (e.g., pip wheels, npm tarballs).
  - `--mount=type=secret` — *the only safe way* to use secrets at build time. Mounted into the build container as a file, **never written to a layer**.
  - `--mount=type=ssh` — forward your SSH agent for `git clone` of private repos at build time.
  - `--mount=type=bind` — bind from host without copying.
- **Frontends** — Dockerfile is just one frontend; you can write Buildpacks-style or HCL-style build definitions.

We will use BuildKit extensively in module 08 (secrets in Docker).

---

## 6. Where state lives

For the senior engineer, knowing the on-disk layout pays off when debugging:

| Path | Contents | Why you care |
|---|---|---|
| `/var/lib/docker/overlay2/` | Image and container layer data | Disk-full root cause; `docker system prune` cleans up |
| `/var/lib/docker/volumes/` | Named volumes | Backup target; volume drivers store metadata here |
| `/var/lib/containerd/` | containerd state (if running standalone) | K8s nodes |
| `/etc/docker/daemon.json` | dockerd config | Where you set `userns-remap`, default seccomp, log driver |
| `/etc/containerd/config.toml` | containerd config | CRI runtime selection, image registries, NVIDIA runtime |
| `~/.docker/config.json` | CLI config — credentials, BuildKit settings, contexts | Credentials anti-pattern: this file can hold registry passwords in plaintext if no credential-helper is configured |

On a K8s node, `~/.docker/config.json` is usually empty because credentials live in `imagePullSecrets`. But on developer laptops it routinely holds long-lived registry tokens — a frequent finding in laptop security audits.

---

## 7. Logging drivers

The path containers write to stdout/stderr does not just sit there — dockerd captures it via a **log driver**. The defaults differ across distros:

| Log driver | Where logs go | Notes |
|---|---|---|
| `json-file` | `/var/lib/docker/containers/<id>/<id>-json.log` | Default; truncate via `max-size` |
| `local` | Binary format, faster | Default on newer installs |
| `journald` | systemd journal | RHEL/Fedora default fit |
| `syslog` | rsyslog/syslog-ng | Centralized log shipping |
| `fluentd` | Fluentd | K8s logging pipelines |
| `awslogs` | CloudWatch Logs | ECS default |
| `gcplogs` | Cloud Logging | GKE |
| `splunk` / `gelf` | Splunk / Graylog | Enterprise |

**Production defaults you should set on every host:**

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3",
    "compress": "true"
  }
}
```

Without `max-size`, a chatty container can fill `/var/lib/docker` and crash the daemon.

---

## 8. The trust boundaries

For a Sr Lead / Architect, draw the boundaries clearly:

| Boundary | What crosses it | How it's protected |
|---|---|---|
| Container ↔ Host kernel | Syscalls | Capabilities, seccomp, AppArmor/SELinux |
| Container ↔ Container | Networking, IPC (if shared) | Network policies, NET namespace isolation |
| Container ↔ dockerd | Docker API (none normally) | NEVER mount docker.sock; if you must, use socket-proxy |
| dockerd ↔ containerd | Local gRPC over Unix socket | File perms |
| containerd ↔ runc | exec call | Process boundary |
| Registry ↔ dockerd | HTTPS, image pull | TLS, registry auth (module 5), image signing (module 4) |
| Image build ↔ secrets | BuildKit secret mounts | NEVER `ENV`/`ARG`; only `--mount=type=secret` (module 8) |

When you read a "container escape" CVE, locate it on this list. Leaky Vessels (CVE-2024-21626) was a `runc` working-directory leak across the `runc ↔ exec` boundary — knowing that immediately tells you the patch path is `runc ≥ 1.1.12`.

---

## 9. ECS-on-EC2 vs ECS-on-Fargate vs EKS — runtime delta

A Capital One–style senior engineer interview question: "describe the runtime stack of an ECS task on EC2 vs an ECS task on Fargate."

| | ECS-on-EC2 | ECS-on-Fargate | EKS |
|---|---|---|---|
| You manage | EC2 host OS, Docker daemon, agent | Nothing | EC2 host OS (unless Fargate) |
| Runtime | Docker (dockerd → containerd → runc) | **Firecracker MicroVM per task** | containerd → runc |
| Trust boundary | Linux kernel | Hypervisor (KVM via Firecracker) | Linux kernel |
| GPU support | Yes (nvidia-container-runtime) | No GPU on Fargate | Yes (nvidia-container-runtime + GPU Operator) |
| Cost model | EC2 hours + ECS free | Task vCPU·hour + GB·hour | EC2 hours + $0.10/hr cluster |
| Network model | awsvpc / bridge / host | awsvpc (ENI per task) | awsvpc (ENI per pod via VPC CNI) |

The **Fargate Firecracker boundary** is the reason Fargate is a defensible answer for "I need container isolation strong enough for untrusted multi-tenant code without managing K8s." It is also why Fargate tasks cost more than equivalent EC2 — you are paying for the hypervisor isolation per task.

---

## Sanity check

1. Why was `dockershim` removed from Kubernetes 1.24, and what runtime do EKS / GKE / AKS use instead?
2. List the four daemons that participate when you run `docker run nginx`. Which one applies seccomp/capabilities/namespaces?
3. Why is mounting `/var/run/docker.sock` into a container equivalent to giving that container root on the host?
4. What is the difference between `gVisor` and `Kata`, and which one does AWS Fargate actually use?
5. What does BuildKit's `--mount=type=secret` give you that `ARG SECRET_VAL` does not?
6. What is the trust boundary between an ECS-on-EC2 task and an ECS-on-Fargate task?

---

## Sources

- [OCI Image and Runtime Specs](https://opencontainers.org/)
- [containerd architecture](https://containerd.io/docs/getting-started/)
- [Moby / dockerd](https://github.com/moby/moby)
- [Kubernetes dockershim removal](https://kubernetes.io/blog/2022/02/17/dockershim-faq/)
- [gVisor](https://gvisor.dev/)
- [Kata Containers](https://katacontainers.io/)
- [AWS Fargate uses Firecracker](https://aws.amazon.com/blogs/aws/firecracker-lightweight-virtualization-for-serverless-computing/)
- [BuildKit](https://docs.docker.com/build/buildkit/)
- [CIS Docker Benchmark v1.7.0](https://www.cisecurity.org/benchmark/docker)

→ Next: [03 — Dockerfile & image layers — building production images](03_dockerfile_images.md)
