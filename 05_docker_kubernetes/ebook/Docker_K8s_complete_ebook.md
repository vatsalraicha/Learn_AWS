---
title: "Docker & Kubernetes for AI/ML Engineers"
subtitle: "Multi-cloud data-exposure security lens (Career_upskill — Topic 05)"
author: "Compiled for Vatsal Raicha"
date: "2026"
lang: "en-US"
---

# How to read this ebook

This is the consolidated reading copy of **Topic 05 — Docker & Kubernetes for AI/ML Engineers**, from the **Career_upskill** project. Source markdown files live at `topics/05_docker_kubernetes/` and remain canonical.

**Audience:** A Senior/Lead AI/ML engineer preparing for the EKS+KServe stack at Capital One (and analogous regulated-finance environments). Linux primitives are taught from first principles so the security controls in later modules make sense at the system-call level. The unifying thread is **how to expose data to and from containers safely** across **on-premise, AWS, GCP, and Azure** — modules 12–15 and 26–29 carry the cloud-specific deep dives.

**Ordering:** natural numeric sequence — Modules 1 through 33, organized into 9 Parts (A–I).

**Included:** all 33 modules + FACTS.md as an appendix.

**Not included:** code artifacts (Dockerfiles, K8s manifests, Helm fragments, Terraform — they ship in `code/`); quizzes (in `quizzes/`); table-of-contents file (this ebook's auto-generated TOC supersedes it).

\newpage


\newpage

# 01 — Linux primitives: the substrate underneath every container

> *"A container is not a small VM. It is a Linux process where the kernel is lying to it about what exists."*

## Why this module exists

Senior engineers routinely mis-reason about container security because they treat "container" as a black box rather than as **kernel features composed together**. The single most important reframing: **the container kernel is the host kernel.** A kernel CVE that fires inside a container fires on the host. This sets the entire security agenda for the topic and is the foundation behind every CVE we will discuss (runc CVE-2019-5736, Leaky Vessels CVE-2024-21626, the Capital One 2019 SSRF→IMDSv1 pivot).

Everything you will learn about Docker, containerd, Kubernetes, ECS, GKE, AKS, Cloud Run, Fargate, MWAA, Composer, etc. is **scaffolding** over three classes of Linux kernel primitives:

1. **Namespaces** — restrict *what* a process can see.
2. **Cgroups** — restrict *how much* a process can consume.
3. **Capabilities + LSMs (seccomp, AppArmor, SELinux) + no-new-privileges** — restrict *which syscalls/APIs* a process can invoke even when DAC would allow it.

If you internalize the model in this module, every container escape becomes a story about one of those three classes failing or being misconfigured.

---

## 1. Namespaces — the visibility primitive

Linux namespaces ([`man 7 namespaces`](https://man7.org/linux/man-pages/man7/namespaces.7.html)) virtualize one global kernel resource at a time. A process belongs to exactly one of each kind. Namespaces are created or joined via `clone(2)`, `unshare(2)`, and `setns(2)` — these are the syscalls runc invokes to start a container.

| Namespace | What it isolates | When Docker creates it by default | If missing, what breaks |
|---|---|---|---|
| **PID** | Process ID tree (each ns has its own PID 1) | Always | Container can `kill` host PIDs |
| **NET** | Network devices, IPs, routes, ports, iptables, `/proc/net` | Always (unless `--network host`) | Container can sniff host traffic, bind host ports |
| **MNT** | Mount table — what the process sees in its filesystem view | Always | Container can read/write host paths |
| **UTS** | Hostname, NIS domain | Always | Trivial info leakage |
| **IPC** | System V IPC, POSIX message queues, shared memory | Always | Cross-container shared-memory abuse |
| **USER** | UID/GID mapping (root inside ≠ root outside) | **Only with rootless or `userns-remap`** | Root in container == root on host (subject to caps/seccomp) |
| **CGROUP** | View of the cgroup tree (4.6+) | Default since Docker 20.10 | Container sees host cgroup paths |
| **TIME** | `CLOCK_MONOTONIC` / `CLOCK_BOOTTIME` offsets (5.6+) | Not by default | Minor (testing clock-sensitive code) |

### PID namespace gotcha — PID 1 semantics

PID 1 in any PID namespace has special kernel semantics: it reaps zombie children and **ignores signals it has not explicitly registered handlers for** (including `SIGTERM`!). A naive `CMD ["python", "app.py"]` Dockerfile makes Python PID 1; Python doesn't reap, and many web servers don't install `SIGTERM` handlers — so `docker stop` waits the full 10-second grace period before sending `SIGKILL`. Fix: use `--init` (injects `tini`) or `dumb-init`, or run a proper supervisor.

### USER namespace is the only privilege-granting one

Every other namespace *takes away* visibility. The USER namespace is unique because it can map an unprivileged UID outside the namespace to UID 0 *inside* the namespace. This is the mechanism behind **rootless Docker** and **Podman rootless**: the process is uid=0 inside the container but uid=100000+ on the host, so a container escape lands you as a low-privileged user, not root. This is also why USER namespace bugs are particularly nasty — CVE-2022-0185 was a USER-namespace-enabled escape that earned CAP_SYS_ADMIN from inside a container.

> **Recommendation for production hosts:** run rootless Docker or enable `userns-remap` in `/etc/docker/daemon.json`. Capital One–style regulated shops typically prefer rootless on engineering laptops and `userns-remap` on shared CI runners.

---

## 2. Cgroups — the consumption primitive

Cgroups (`/sys/fs/cgroup/...`) account for and limit resource usage per process group. Two ABI versions exist:

- **cgroup v1** (legacy): per-controller hierarchies (`/sys/fs/cgroup/cpu/`, `/memory/`, `/blkio/`, etc.). Processes can be in different cgroups for different controllers — flexible but lets you construct nonsensical configurations.
- **cgroup v2** (unified hierarchy): one tree under `/sys/fs/cgroup/`. Every process is in exactly one cgroup; all enabled controllers apply together. Adds the `io` controller and Pressure Stall Information (PSI). Default on Fedora 31+, Ubuntu 21.10+, Debian 11+, RHEL 9+.

Docker CLI flags translate to cgroup files:

```bash
docker run \
  --memory=512m \                    # memory.max
  --cpus=2.0 \                       # cpu.max = "200000 100000"
  --pids-limit=200 \                 # pids.max
  --memory-swap=512m \               # memory.swap.max=0 (disables swap entirely)
  --blkio-weight=300 \               # io.weight (v2)
  --device-read-bps /dev/sda:10mb \  # io.max
  myimage
```

**Why this matters for ML containers:** A misconfigured cgroup is how a single rogue training job starves the entire node. The classic anti-pattern is `--memory` without `--memory-swap=512m` — the process can spill to swap and effectively bypass the limit by causing OOM at the *host* level instead of the container level. The recommendation: set `--memory-swap` equal to `--memory` to disable swap for the container.

**PSI (Pressure Stall Information)** is the modern mechanism for detecting "the system is under memory/CPU/IO pressure" — KEDA and Kubernetes Cluster Autoscaler can read PSI to decide when to scale. This is a v2-only feature; insist on cgroup v2 on any host you care about.

---

## 3. Capabilities — root, deconstructed

Traditional Unix has a binary privilege model: root (uid=0, bypass all DAC) or not. Linux **capabilities** (`man 7 capabilities`) decompose root's powers into ~40 named privileges. A process can hold any subset.

The big ones for container security:

| Capability | What it grants | Risk if a container has it |
|---|---|---|
| `CAP_SYS_ADMIN` | "Almost everything" — mount, swap, chroot, namespaces | Nearly always escapes |
| `CAP_NET_ADMIN` | Configure network interfaces, routing, firewall rules | Egress filter bypass, packet capture |
| `CAP_SYS_PTRACE` | `ptrace(2)` other processes | Read process memory of other containers |
| `CAP_SYS_MODULE` | Load/unload kernel modules | Persistent host backdoor |
| `CAP_NET_RAW` | Open raw sockets (ping, etc.) | ARP spoofing, packet crafting |
| `CAP_SETUID` / `CAP_SETGID` | Change user/group ID | Privilege escalation inside container |
| `CAP_DAC_OVERRIDE` | Bypass file permission checks | Read any file as any user |
| `CAP_AUDIT_WRITE` | Write to kernel audit log | Tamper with audit trail |

**Docker default capability set (14 capabilities, since 1.10)**: `CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FSETID, CAP_FOWNER, CAP_MKNOD, CAP_NET_RAW, CAP_SETGID, CAP_SETUID, CAP_SETFCAP, CAP_SETPCAP, CAP_NET_BIND_SERVICE, CAP_SYS_CHROOT, CAP_KILL, CAP_AUDIT_WRITE`.

**The production posture**: drop all and add back what you need.

```bash
docker run \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \   # only if binding port < 1024
  --user=10001:10001 \
  myimage
```

Modules 10 and 22 will revisit this in the K8s context (PSA `restricted` policy forces this).

---

## 4. LSMs — the syscall/api gate

**Capabilities** are coarse-grained per-syscall flags. Linux Security Modules go finer:

### 4.1 seccomp (Secure Computing Mode)

seccomp filters individual syscalls. Docker ships a **default seccomp profile** that blocks ~50 syscalls (mostly historical/dangerous: `clock_settime`, `kexec_load`, `mount`, `umount`, `keyctl`, `add_key`, etc.). Effective when you accept the default; disable only with `--security-opt seccomp=unconfined` (almost never).

You can supply a custom JSON profile:

```bash
docker run --security-opt seccomp=./custom-seccomp.json myimage
```

A practical pattern: use `strace -c -f` on a representative workload to get the syscall set actually used, then build a minimal allow-list. Tools like [`falco-driver-loader`](https://falco.org/) and [`oci-seccomp-bpf-hook`](https://github.com/containers/oci-seccomp-bpf-hook) automate this. Note that for general ML workloads the default profile is usually fine — only highly multi-tenant or adversarial environments justify the maintenance.

### 4.2 AppArmor vs SELinux

These are **path-based (AppArmor)** and **label-based (SELinux)** mandatory access control systems. Containers inherit a profile; Docker provides `docker-default` (AppArmor) and `container_t` (SELinux).

| Aspect | AppArmor | SELinux |
|---|---|---|
| Default on | Ubuntu, Debian | RHEL, Fedora, CentOS, Amazon Linux 2/2023 |
| Model | Path-based | Label-based |
| Granularity | File path patterns | Type/role/user labels on every inode |
| Audit trail | Yes (kern.log) | Yes (audit.log), richer |
| Container support | docker-default profile | container_t domain |
| Pain point | Profiles brittle when paths change | Steep learning curve, every volume mount needs the right label |

The `:z` and `:Z` suffixes on bind mounts (`-v /host:/container:Z`) tell Docker to relabel the host directory with the SELinux container label — without them, the container literally cannot read the volume on a SELinux-enforcing host. This is the #1 cause of "works on Ubuntu, fails on Amazon Linux" confusion.

### 4.3 `no-new-privileges`

The simplest, most underused security flag. Sets the kernel `PR_SET_NO_NEW_PRIVS` bit, which **disables setuid binaries** and prevents privilege escalation via `execve`. Should be on by default in production.

```bash
docker run --security-opt no-new-privileges myimage
```

In Kubernetes, this corresponds to `securityContext.allowPrivilegeEscalation: false` and is enforced by Pod Security Admission `restricted` policy (module 22).

---

## 5. Putting it together — a defensible container run

```bash
docker run \
  --read-only \                                   # read-only root FS
  --tmpfs /tmp:size=64m,mode=1777 \               # writable scratch in RAM
  --user 10001:10001 \                            # non-root UID
  --cap-drop=ALL \                                # drop all caps...
  --cap-add=NET_BIND_SERVICE \                    # ...add only what's needed
  --security-opt no-new-privileges \              # block setuid escalation
  --security-opt seccomp=/etc/docker/seccomp/default.json \
  --security-opt apparmor=docker-default \        # or SELinux on RHEL/AL2/AL2023
  --memory=2g --cpus=2.0 --pids-limit=200 \       # cgroups
  --memory-swap=2g \                              # disable swap
  --network mynet \                               # user-defined bridge, not host
  --init \                                        # tini as PID 1
  myimage:tag
```

If you can recite *why* each flag is there, you understand Linux container security at the depth Capital One Sr Lead AI/ML expects.

---

## 6. The "container is not a VM" gotcha — quantified

To make the equivalence concrete:

| Failure | Container effect | VM effect |
|---|---|---|
| Kernel use-after-free in a syscall | Host crashes, all containers die | VM crashes, host survives |
| Kernel UAF allowing arbitrary write | Container becomes root on host | VM becomes root inside VM only |
| `mount --bind` from inside | Visible to host kernel; can be exploited if perms wrong | Visible only inside VM |
| `iptables` rule | Goes into host's netfilter | Goes into VM's |

This is why **runtime sandboxing** (gVisor's `runsc`, Kata containers, Firecracker MicroVMs) exists. They re-introduce a hypervisor or syscall interposer between container and host kernel:

- **gVisor (runsc)** — reimplements the Linux syscall surface in Go, in userspace. Trades performance for a much smaller kernel-attack-surface. Google uses it for Cloud Run.
- **Kata Containers** — actually a lightweight VM (QEMU/Cloud Hypervisor/Firecracker) per pod. Used in Azure Confidential Containers, ACI.
- **AWS Fargate** — Firecracker MicroVMs, one VM per task.

For ML workloads with multi-tenancy or BYOC, runtime sandboxing is the right move. For trusted-tenant ML platforms (most enterprise teams), kernel-shared containers + the hardening above are sufficient.

---

## 7. CLI sanity check — what's running where

Commands every senior engineer should know cold:

```bash
# What namespaces is process 1234 in?
ls -la /proc/1234/ns/

# What capabilities does it have?
grep CapEff /proc/1234/status        # decode with: capsh --decode=<hex>

# What's the cgroup?
cat /proc/1234/cgroup

# What seccomp mode?
grep Seccomp /proc/1234/status        # 0=disabled, 1=strict, 2=filter

# AppArmor profile?
cat /proc/1234/attr/current

# SELinux label?
ls -lZ /proc/1234/exe
```

These commands work *inside* a container as well as on the host — that's how runtime tools like Falco (module 25) detect drift from the policy.

---

## 8. Data-exposure implications (the topic-wide theme)

The point of the topic is: **how does a container safely expose data?** Every primitive above has a data-exposure angle:

- **MNT namespace** — bind mounts are the primary way data crosses container/host. The MNT namespace decides whether the container can see `/etc/passwd`, `/var/run/docker.sock`, or arbitrary host paths.
- **NET namespace** — port publishing (`-p`), `host` networking, and overlay networks decide whether the container can talk to your S3 endpoint, Postgres, or the IMDS (the Capital One 2019 escalation path).
- **USER namespace** — without it, a container reading a mounted file does so as host root, bypassing UID-based file permissions.
- **Capabilities** — `CAP_NET_RAW` is what lets a container craft arbitrary packets. `CAP_DAC_OVERRIDE` lets it read files regardless of UID.
- **LSMs** — AppArmor/SELinux constrain *what files* a process can touch even when capabilities/UIDs would allow it. SELinux `container_t` blocks containers from reading `~/.ssh/id_rsa` even on bind-mount.

Hold the primitives in mind as we work through modules 6–15: every "how to expose data safely" question reduces to "which primitive enforces this boundary?"

---

## Sanity check (answer before moving on)

1. Why is "the container kernel == the host kernel" the most important phrase in container security?
2. What does `--cap-drop=ALL --cap-add=NET_BIND_SERVICE --user=10001` defend against that `--user=10001` alone does not?
3. Why does a Python web server in a container ignore `docker stop`, and what's the one-flag fix?
4. What does `--memory-swap=512m` paired with `--memory=512m` actually do, and why is it the right pairing?
5. When does `:Z` on a bind mount matter, and on which host distros?
6. What is the practical difference between gVisor and Kata containers, and which one Cloud Run uses?
7. Why is the USER namespace the *only* namespace that can grant a process privileges it didn't have?

---

## Sources

- [Linux namespaces — `man 7 namespaces`](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [cgroup v2 documentation — kernel.org](https://www.kernel.org/doc/Documentation/cgroup-v2.txt)
- [Linux capabilities — `man 7 capabilities`](https://man7.org/linux/man-pages/man7/capabilities.7.html)
- [seccomp BPF — kernel.org](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html)
- [Docker default seccomp profile](https://github.com/moby/moby/blob/master/profiles/seccomp/default.json)
- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
- [NIST SP 800-190 — Application Container Security Guide](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-190.pdf)
- [gVisor architecture overview](https://gvisor.dev/docs/architecture_guide/)
- [Kata Containers architecture](https://katacontainers.io/docs/)

→ Next: [02 — Docker architecture & runtime: dockerd → containerd → runc → OCI](02_docker_architecture.md)


\newpage

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


\newpage

# 03 — Dockerfile & image layers: building production images

> *"Your prod image is a one-line difference from a CVE-laden disaster. Make that difference deliberate."*

## Why this module exists

Most Dockerfiles in the wild are written by developers, not security engineers. They ship working software but leak attack surface: bloated base images, secrets baked into layers, dev tools left in `/usr/bin`, files owned by root. A senior AI/ML engineer interviewing for a regulated-finance Lead role is expected to spot every one of these in a code review and propose the fix from muscle memory.

This module is the **what-good-looks-like** guide. Module 04 covers scanning/signing/SBOM; module 08 covers runtime secrets; module 10 covers the runtime-side hardening.

---

## 1. Image layer mental model

An OCI image is a stack of **read-only layers** + a manifest + a config blob. Each `RUN`, `COPY`, `ADD` in a Dockerfile produces a layer. Layers are content-addressed (SHA256) and cached across builds. At container start time, the runtime mounts an **overlayfs** with the layers as lower-dir and a thin writable upper-dir for changes.

Three implications:

1. **Anything you write to a layer is permanent**, even if a later layer deletes it. `RUN curl secret.txt && rm secret.txt` leaves `secret.txt` in the lower layer; `docker history` reveals it; `docker save` ships it.
2. **Layer order affects cache.** Put the most-changing instructions last — `COPY . /app` before `pip install` is a cache-buster on every code change.
3. **Each layer adds metadata + a tarball.** Small bases (alpine, distroless, chainguard) → fewer layers → smaller attack surface and faster pulls.

---

## 2. Multi-stage builds — the single biggest hygiene win

The principle: **build environment** ≠ **runtime environment**. A multi-stage Dockerfile lets you compile/install in a fat stage, then `COPY --from=builder` only the artifacts you need into a minimal final stage.

```dockerfile
# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM python:3.12-slim AS builder
WORKDIR /build

# System build deps (drop in the final stage)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*

# Python wheels into a venv
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY pyproject.toml ./
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-deps -r requirements.txt

COPY . .
RUN pip install --no-deps .

# ---- runtime stage ----
FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/src /app/src
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["python", "-m", "src.app"]
```

Why this matters:

- The runtime image has **no shell, no package manager, no curl, no SSH**. An attacker who lands a webshell on it has nothing to pivot with.
- The builder layers contain `gcc`, `git`, `build-essential` — they never reach production.
- The `--mount=type=cache` keeps pip wheels across builds without baking them into the image.

---

## 3. Base image selection

| Base | Size | Has shell? | Pkg manager? | Default user | When to use |
|---|---:|---|---|---|---|
| `ubuntu:22.04` | ~75 MB | sh, bash | apt | root | Last resort; only when you need apt-installable system libs |
| `debian:12-slim` | ~75 MB | sh, bash | apt | root | Default for Python apps needing libc |
| `python:3.12-slim` | ~125 MB | sh, bash | apt + pip | root | Convenience; bloated |
| `alpine:3.19` | ~7 MB | sh (ash) | apk | root | Tiny but musl libc — breaks many ML wheels (NumPy/PyTorch) |
| `gcr.io/distroless/python3-debian12` | ~50 MB | **none** | none | root or `nonroot` | Production Python apps |
| `cgr.dev/chainguard/python:latest` | ~30 MB | **none** | none | `nonroot` | Production Python, daily-rebuilt, signed |
| `cgr.dev/chainguard/wolfi-base` | ~5 MB | sh | apk (apko) | root | Building custom Wolfi-based images |
| `scratch` | 0 B | none | none | root | Statically linked Go/Rust binaries |

### The Alpine / musl caveat for ML

Alpine uses **musl libc**, not glibc. PyTorch, TensorFlow, NumPy, and most data-science wheels on PyPI are **manylinux** wheels — glibc-only. On Alpine, pip falls back to **building from source**, which (a) takes 20+ minutes, (b) needs gcc/gfortran in the image, and (c) results in subtly different floating-point behavior in edge cases. **Don't use Alpine for ML images.** Use debian-slim, distroless, or Chainguard-Wolfi (which uses glibc).

### Distroless vs Chainguard — the production comparison

- **Distroless (Google)**: a small set of base images (`static`, `base`, `cc`, `python3`, `nodejs`, `java`) built from Debian packages. No shell, no package manager. Updated when Google decides to update. Free.
- **Chainguard Images**: similarly minimal, built from **Wolfi** (Chainguard's undistro). **Rebuilt daily** with security patches. **All images are signed with Cosign** and ship with SBOM. Free tier for many images; paid for hardened/FIPS variants.

For regulated finance, **Chainguard images are the safer default**: SBOM and signing are pre-done, vuln scan results are continuously low, and the FedRAMP/FIPS posture is documented.

---

## 4. Dockerfile production checklist

```dockerfile
# syntax=docker/dockerfile:1.7
ARG BASE_TAG=3.12-slim                          # Pin via build arg, not in FROM line directly

FROM debian:12-slim AS base
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Single RUN combines apt-get update + install + cleanup to fit one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Non-root user with explicit, deterministic UID/GID
RUN groupadd --gid 10001 app && \
    useradd  --uid 10001 --gid app --shell /sbin/nologin --create-home app

# Always WORKDIR before COPY
WORKDIR /app

# Copy minimal first for cache, then the rest
COPY --chown=app:app pyproject.toml uv.lock ./

# Reproducible install with lockfile; uv is faster than pip
RUN --mount=type=cache,target=/root/.cache/uv \
    pip install uv==0.4.* && uv pip sync --system uv.lock

# Application code
COPY --chown=app:app src/ ./src/

# Drop privileges before ENTRYPOINT
USER app:app

# Healthcheck — orchestrators (ECS, K8s probes) use this
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8080/healthz || exit 1

EXPOSE 8080
ENTRYPOINT ["python", "-m", "src.app"]
```

Checklist items (auditor-grade):

- [ ] **`USER` set to a non-root UID before `ENTRYPOINT`**
- [ ] **No `ADD` for remote URLs** (use `RUN curl ... && sha256sum -c`)
- [ ] **No `latest` tag in `FROM`** — pin to a digest (`FROM debian:12-slim@sha256:...`)
- [ ] **One `RUN apt-get update` paired with the install + cleanup in the same instruction**
- [ ] **No `COPY .` without `.dockerignore`** — see section 6
- [ ] **No secrets in `ENV` or `ARG`** (module 08)
- [ ] **`WORKDIR` set** (avoids `cd` in `RUN`)
- [ ] **`HEALTHCHECK` defined** (or explicitly delegated to K8s probes)
- [ ] **`ENTRYPOINT` as exec form `["..."]` not shell form** — avoids unintended shell parsing
- [ ] **Labels for traceability**: `org.opencontainers.image.{source,revision,version,licenses}`

---

## 5. Reproducible & deterministic builds

A defensible build is one that produces the **same image digest** from the same inputs. Three controls:

1. **Pin base image by digest, not tag.** Tags float; digests don't.
   ```dockerfile
   FROM debian:12-slim@sha256:f6c2fa53...
   ```
2. **Use a lockfile** for the language ecosystem. `uv.lock`, `poetry.lock`, `requirements.txt --hash=sha256:...`, `package-lock.json`, `Pipfile.lock`, `Cargo.lock`.
3. **Disable timestamps in layers**: set `SOURCE_DATE_EPOCH` for tools that honor it (apt, dpkg). BuildKit supports `--output type=docker,name=img,tar` with reproducible mode.

Capital One's policy-as-code (Cloud Custodian sibling on the AWS side, OPA/Kyverno on the K8s side) will reject images whose digest doesn't match the SBOM in the SLSA attestation (module 04). Reproducibility is what makes the attestation believable.

---

## 6. `.dockerignore` — the file every team forgets

`COPY . /app` is the most-deployed Dockerfile line in industry, and the most dangerous. Without a `.dockerignore`, it sweeps in:

- `.git/` (history, possibly committed secrets — `git filter-repo` cannot un-bake a docker layer)
- `.env`, `.env.local`, `.env.staging` (the secret bonanza)
- `node_modules/` (megabytes of bloat, half from the host platform)
- `__pycache__/`, `.pytest_cache/`, `.coverage`
- IDE files (`.vscode/`, `.idea/`, sometimes containing API tokens)
- Local SSH keys if `cwd=$HOME` (yes, this happens)

A minimal `.dockerignore`:

```
.git
.gitignore
.env*
**/.DS_Store
**/__pycache__
**/*.pyc
**/.pytest_cache
**/.coverage
**/htmlcov
**/.tox
**/.venv
**/venv
**/.mypy_cache
**/.ruff_cache
.vscode
.idea
*.md
LICENSE
Dockerfile
docker-compose*.yml
.dockerignore
node_modules
dist
build
*.log
```

Treat `.dockerignore` like a security control, not a convenience.

---

## 7. ML/AI–specific Dockerfile patterns

For an AI Architect, three image archetypes recur:

### 7.1 Training image

Heavy: CUDA, NCCL, PyTorch, Megatron, DeepSpeed, plus dataset prep code. Built on `nvcr.io/nvidia/pytorch:24.06-py3` (NGC) or `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`.

Pattern:
- Multi-stage: `FROM nvcr.io/nvidia/pytorch:... AS train` for the actual job; an earlier stage for repo checkout/code-only.
- Mount training data via volume at runtime (don't bake it in — see module 07).
- `WORKDIR /workspace` (NGC convention).
- Capture `nvidia-smi -L` at startup to fail fast on missing GPUs.

### 7.2 Inference / serving image

Slim: just the model + an HTTP/gRPC server. Built on distroless or Chainguard.

Pattern:
- Distroless Python or Triton Inference Server base.
- Model weights mounted via volume (or pulled from S3/GCS at startup) — **don't bake weights in if they are >1 GB or update independently of code.**
- `HEALTHCHECK` hits `/v2/health/ready` (Triton) or your own `/healthz`.
- `USER nonroot:nonroot`.
- Includes only the runtime dependencies (`torch` not `torch[dev]`, no `pytest`).

### 7.3 Data-pipeline / Spark image

Bulky: JVM, Spark, Hadoop, Iceberg, plus Python wheels. Built on `apache/spark:3.5.3-python3` or your platform's variant.

Pattern:
- Multi-stage with a Maven build for Spark plugins.
- `spark-submit` ENTRYPOINT.
- IRSA / Workload Identity for cloud auth (modules 13–15) — never bake AWS keys.

---

## 8. Common anti-patterns (you will see these in code review)

| Anti-pattern | Why it's bad | Fix |
|---|---|---|
| `FROM ubuntu:latest` | Tag floats; CVEs creep in invisibly | Pin to digest or specific tag |
| `RUN curl ... \| bash` | Untrusted execution, no integrity check | Download, verify checksum, then run |
| `ADD https://...` | Implicit unpack of remote tarballs | `RUN curl + sha256sum -c` |
| `RUN apt-get install $X` (no `--no-install-recommends`) | Installs unneeded packages | Add `--no-install-recommends` |
| `RUN apt-get update` in one layer, `RUN apt-get install` in next | Cache miss separation; stale package lists | Combine in one `RUN` |
| `RUN pip install -r req.txt` without lockfile | Non-reproducible | Use lockfile + `--no-deps` |
| `RUN cd /app && ...` | `cd` doesn't persist between RUN | Use `WORKDIR` |
| `COPY ./secrets/.env .env` | Secrets in layer | `--mount=type=secret` (module 08) |
| `EXPOSE 22` | SSH in a container; CVE magnet | Remove; use `kubectl exec` / debug sidecar |
| `CMD python app.py` (shell form) | Shell interpolation bugs, signal handling | Exec form: `CMD ["python", "app.py"]` |
| Image as root, container runs as root | No defense in depth | Add `USER 10001:10001` |

---

## 9. The `EXPOSE` clarification

`EXPOSE 8080` is **documentation only**. It does NOT publish the port; it only adds metadata to the image. The runtime flag that publishes is `-p` (Docker) or the `containerPort` + Service in K8s. This trips up newcomers who think `EXPOSE` is the firewall control. The real firewall is your network policy / security group (modules 06, 18).

---

## 10. Image labels & supply-chain metadata

Standard labels every image should carry (the OCI image annotations spec):

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/myorg/myrepo" \
      org.opencontainers.image.revision="$GIT_SHA" \
      org.opencontainers.image.version="1.4.2" \
      org.opencontainers.image.created="2026-05-21T10:00:00Z" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.title="my-model-server" \
      org.opencontainers.image.description="Real-time inference for X"
```

`org.opencontainers.image.source` is read by GHCR to wire the package to the source repo. Vulnerability scanners (Trivy, Grype, Scout) use these labels in their reports. This is the minimum for traceability in a regulated environment.

---

## Sanity check

1. Why is a multi-stage Dockerfile mandatory for production ML images, not just a nicety?
2. What's the practical reason to avoid Alpine for Python/ML images?
3. List five things a missing `.dockerignore` can leak into your image.
4. Why is `RUN curl ... | bash` an anti-pattern, and what replaces it?
5. What does `EXPOSE 8080` actually do at runtime?
6. Distroless vs Chainguard — which is the safer default for a regulated-finance shop and why?

---

## Sources

- [Dockerfile reference](https://docs.docker.com/engine/reference/builder/)
- [BuildKit Dockerfile frontend v1.7](https://docs.docker.com/build/buildkit/dockerfile-release-notes/)
- [Distroless images (Google)](https://github.com/GoogleContainerTools/distroless)
- [Chainguard Images](https://images.chainguard.dev/)
- [OCI Image Annotations](https://github.com/opencontainers/image-spec/blob/main/annotations.md)
- [NGC PyTorch image](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch)
- [`uv` package manager](https://docs.astral.sh/uv/)
- [Reproducible Docker builds — `SOURCE_DATE_EPOCH`](https://reproducible-builds.org/docs/source-date-epoch/)

→ Next: [04 — Image security: scanning, SBOM, signing, supply chain](04_image_security.md)


\newpage

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


\newpage

# 05 — Container registries: ECR, GAR, ACR, Harbor, JFrog

> *"Your registry is your single point of distribution. Treat it like production."*

## Why this module exists

The registry is the choke point between "code that built" and "container that runs." It's where signing/SBOM/scanning evidence lives, where pull credentials are validated, and where regulated audit trails are anchored. This module covers the four cloud registries you'll actually use (ECR, GAR, ACR, GHCR) plus the two heavyweight self-hosted options (Harbor, JFrog Artifactory). For each: auth mechanism, geo-replication, immutability/retention, scanning hooks, and the per-cloud IAM gotchas.

---

## 1. Amazon ECR (Elastic Container Registry)

ECR is the AWS-native registry. Two flavors:

- **ECR Private** — per-region, IAM-authenticated, the default.
- **ECR Public** (`public.ecr.aws/...`) — global CDN-fronted, anonymous read; used to publish public base images (think `public.ecr.aws/lambda/python:3.12`).

### 1.1 Auth model

Pull/push is **AWS IAM only**. The CLI flow:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

The token is **a 12-hour bearer token**, not a long-lived password. The Docker credential helper (`amazon-ecr-credential-helper`) refreshes it transparently — install it on developer laptops to avoid re-running `get-login-password` every shift.

For K8s on EKS, pulling works **automatically** when the node IAM role has `AmazonEC2ContainerRegistryReadOnly`. No `imagePullSecrets` needed. For cross-account pulls, configure ECR repository policy to allow the puller account, or use **ECR pull-through cache** (see below).

### 1.2 ECR features

| Feature | Notes |
|---|---|
| **Image scanning — Basic** | Free; scans on push; OS packages only |
| **Image scanning — Enhanced** | Paid (via Inspector); continuous + OS + language libs + KEV alerts |
| **Cross-region replication** | Configure per-repo; latency to replica is asynchronous |
| **Cross-account replication** | Same mechanism + destination account permission |
| **Pull-through cache** | Proxy through to upstream registry (Docker Hub, Quay, GCR, GHCR); caches in your ECR. Cuts Docker Hub rate limit risk. |
| **Image tag mutability** | `MUTABLE` (default) or `IMMUTABLE` — set IMMUTABLE for prod repos |
| **Lifecycle policies** | JSON rules: "expire images older than 30 days," "keep last 10 of tag prefix `v`" |
| **Repository encryption** | AES-256 default; CMK option for compliance |
| **VPC interface endpoint** | `com.amazonaws.<region>.ecr.api` + `.ecr.dkr` + `.s3` (the layers live in S3) |
| **Signing** | AWS Signer integration; also supports Cosign via the standard OCI referrers API |

### 1.3 The "ECR + S3" gotcha

Image layers are stored in **a regional S3 bucket managed by ECR**. For a private VPC endpoint to fully work, you need three endpoints: `ecr.api`, `ecr.dkr`, **and `s3`**. Skip the S3 endpoint and pulls will silently fall back to the public internet — a common audit finding.

### 1.4 ECR for Capital One–style regulated shops

- IMMUTABLE tags on prod repos.
- CMK encryption.
- VPC interface endpoints (all three).
- Lifecycle policy: expire `dev-*` and `pr-*` tags after 14 days.
- Replication to DR region.
- Enhanced scanning + Inspector findings → Security Hub.
- Cloud Custodian policy: `no-public-ecr-repos`, `ecr-without-lifecycle-policy`, `ecr-without-cmk`.

---

## 2. Google Artifact Registry (GAR)

**GAR** replaces the older **GCR** (Google Container Registry). All new projects should use GAR; GCR is deprecated and migrating to GAR for new pushes by default since 2024.

### 2.1 Differences vs GCR

- Multi-format: containers, Maven, npm, Python, apt, yum — not just OCI.
- Per-region, multi-region, or virtual repositories.
- VPC Service Controls compatible (GCR was not).
- IAM via Artifact Registry roles (`roles/artifactregistry.reader`, `roles/artifactregistry.writer`).
- Cost model is per-GB-stored + egress; GCR was free-storage.

### 2.2 Auth model

Auth flows:

- **Workload Identity Federation** (preferred for CI and workloads): no JSON keys. The workload trades an OIDC token for a GCP access token via STS.
- **gcloud SDK ADC** for developer laptops:
  ```bash
  gcloud auth configure-docker us-central1-docker.pkg.dev
  ```
  Sets the Docker credential helper to call gcloud.
- **Service account JSON keys** — explicitly discouraged by GCP since 2024; org policy can ban creation entirely.

For GKE, **Workload Identity Federation** on the pod's KSA binds to a GSA with the reader role on the repo. No `imagePullSecrets` needed when the GKE node service account has reader (the lazy/insecure pattern); for least-privilege, configure per-namespace pull credentials via WIF.

### 2.3 GAR features

| Feature | Notes |
|---|---|
| **Container Analysis API** | Vulnerability scanning, supports SBOM upload |
| **Binary Authorization integration** | First-class; attestations are stored as Grafeas notes |
| **CMEK** | Yes |
| **Virtual repositories** | Aggregate multiple upstreams behind one endpoint (useful for "Docker Hub via our proxy") |
| **Remote repositories** | Pull-through caching for Docker Hub, Quay, etc. |
| **Cleanup policies** | Per-repo TTL rules |
| **Region selection** | Single-region (cheap), multi-region (resilient), specific multi-region (US, EU, ASIA) |

---

## 3. Azure Container Registry (ACR)

### 3.1 Tiers

| Tier | Storage included | Geo-replication | Use case |
|---|---|---|---|
| **Basic** | 10 GB | No | Dev/test only |
| **Standard** | 100 GB | No | Default for most apps |
| **Premium** | 500 GB | **Yes** | Production, multi-region, regulated workloads |

Geo-replication, image signing, customer-managed keys, private endpoints, and content trust **require Premium**. For Capital One–style postures, you must run Premium.

### 3.2 Auth model

- **Microsoft Entra ID** (RBAC) — preferred. Roles: `AcrPull`, `AcrPush`, `AcrDelete`.
- **Admin user** — a username/password pair with full push/pull; **disable in production**.
- **Repository-scoped tokens** — narrower than the admin user; rotate them.
- **Managed Identity** (for AKS / VMs / ACI) — the production path. Assign `AcrPull` to the kubelet identity or pod-level managed identity.

For AKS, `az aks update --attach-acr <name>` is the one-liner that grants the kubelet's managed identity `AcrPull` on the registry. After that, image pulls "just work" — no `imagePullSecrets`.

### 3.3 ACR features

| Feature | Notes |
|---|---|
| **ACR Tasks** | Built-in image build/test/deploy automation (alternative to GitHub Actions / Azure DevOps) |
| **Content trust** | Docker Notary v1 (legacy). Use Cosign instead for new signing. |
| **Microsoft Defender for Cloud** | Vulnerability scanning (paid). Free baseline available. |
| **Quarantine pattern** | Push to a quarantined tag, scan, then promote |
| **Private endpoint** | Premium only |
| **Geo-replication** | Premium; per-region replicas |
| **Repository delete protection** | Lock policy + tag immutability |

---

## 4. GitHub Container Registry (GHCR)

`ghcr.io` is the GitHub-native registry. Tightly coupled to GitHub Actions: a push from a workflow auto-authenticates with `GITHUB_TOKEN`.

| Feature | Notes |
|---|---|
| **Auth** | PATs, `GITHUB_TOKEN` in Actions, OIDC tokens for Cosign keyless |
| **Visibility** | Public or private; private requires paid GitHub Org plan |
| **Scanning** | Dependabot for the source repo; no native image scanner |
| **SBOM/attestation storage** | Native via OCI referrers API |
| **Pricing** | Free unlimited storage for public; per-GB for private |
| **Geo-replication** | None (GitHub-managed regional) |

For a small org or a project that lives on GitHub, GHCR is the lowest-friction registry. For regulated finance, the lack of geo-replication and the GitHub-cloud dependency push you toward ECR/GAR/ACR.

---

## 5. Harbor — the OSS self-hosted standard

[**Harbor**](https://goharbor.io) is a **CNCF Graduated** OCI registry, originally from VMware/Project Pacific. The de facto choice when you need an on-prem or air-gapped registry.

### 5.1 Capabilities

- OCI registry (containers + Helm charts + OPA bundles + WASM via OCI artifact)
- RBAC with projects and roles
- Vulnerability scanning via Trivy (built-in)
- Image signing verification (Cosign)
- Image immutability and retention policies
- Replication to/from other registries (DockerHub, Harbor, ECR, GAR, ACR, GHCR, Quay)
- Proxy cache (pull-through)
- LDAP/AD, OIDC integration
- Audit logs to syslog or kafka

### 5.2 Deployment

Helm chart, runs on K8s. Backed by Postgres for metadata, Redis for cache, and S3-compatible (or filesystem) for blobs. Production deploys typically use **MinIO** or **Ceph S3** for the blob backend so the registry itself can be HA across AZs.

### 5.3 Why a regulated shop runs Harbor in addition to cloud registries

- Air-gapped environments require a self-hosted registry.
- Cross-cloud workloads pull from one canonical source.
- Strict policy enforcement (signed + scanned + retention) under your control.
- Replication: production-blessed images sync from Harbor to ECR/GAR/ACR in each region.

---

## 6. JFrog Artifactory

Commercial, omnivorous (any artifact type, including OCI). Two SKUs: **Artifactory Pro** (self-hosted) and **Artifactory Cloud** (SaaS).

- Manages OCI + Maven + npm + PyPI + Helm + Conan + Cargo + Debian + RPM + ... 30+ formats.
- Strong replication and cross-region HA.
- Tight integration with JFrog **Xray** (scanning) and **Distribution** (CDN).
- Common at enterprises that already standardized on JFrog for Maven/Python before containers — the "we already pay them" pattern.

For new shops without an existing Artifactory footprint, **Harbor + the cloud-native registry per cloud** is the lower-cost path. JFrog wins when the org has 10+ artifact types to manage.

---

## 7. Other registries you'll meet

| Registry | Who runs it | When you'll see it |
|---|---|---|
| **Docker Hub** | Docker Inc. | Default pull source; the rate-limit problem |
| **Quay.io** | Red Hat | OpenShift shops; Project Quay (OSS) for self-hosted |
| **nvcr.io** | NVIDIA | NGC catalog — PyTorch/TensorFlow/Triton optimized images |
| **registry.k8s.io** | Kubernetes | Official K8s system images (kube-apiserver, kube-proxy, etc.) |
| **mcr.microsoft.com** | Microsoft | .NET / SQL Server / Azure agent images |
| **public.ecr.aws** | AWS | Public ECR (e.g., AWS Lambda runtimes) |

### Docker Hub rate limits

Anonymous pulls: **100 per 6h per IP**. Authenticated free: **200/6h**. Paid: unlimited. This is the #1 cause of CI failures with cryptic "toomanyrequests" errors in 2020-2024. Mitigations:
- ECR/GAR/ACR pull-through cache for Docker Hub.
- Replicate hot base images to your own registry.
- Use Chainguard / Distroless images (different registries).

---

## 8. Pull credentials in Kubernetes

Three patterns:

### 8.1 Node-IAM pulls (the lazy default)

Pods inherit the node's cloud credentials. Works for EKS+ECR, GKE+GAR, AKS+ACR when the cluster is configured per the previous sections. **Pro**: no per-pod secret management. **Con**: all pods on the node can pull from the same set of repos.

### 8.2 `imagePullSecrets` (the granular fallback)

For pulling from registries the node doesn't have credentials for (Docker Hub, third-party, cross-account ECR):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dockerhub-creds
  namespace: ml-serving
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ml-server
  namespace: ml-serving
imagePullSecrets:
  - name: dockerhub-creds
```

Then pods using `serviceAccountName: ml-server` get the pull secret automatically.

### 8.3 IRSA / Workload Identity for cross-account pulls (the right way)

For cross-account ECR pulls without long-lived secrets, use IRSA: the pod's SA assumes a role in the target ECR account; the kubelet uses **EKS Pod Identity** (or IRSA) to broker the ECR auth token. Module 26 covers this in depth.

---

## 9. The registry mirror pattern for ML images

ML images often pull from **Docker Hub** (the default for `python:3.12`, `pytorch/pytorch:...`) and **nvcr.io** (NGC PyTorch/Triton). Both can become availability liabilities in regulated environments — what happens to your CI if Docker Hub has an outage?

Mirror pattern:

1. Run **Harbor** (or use ECR/GAR/ACR pull-through cache) in-cluster.
2. Cache `python`, `nvidia/cuda`, `nvcr.io/nvidia/pytorch` on first pull.
3. CI configured to pull through Harbor only — no direct Docker Hub / NGC pulls.
4. Replicate Harbor across regions for DR.

Cost: storage for cached images. Benefit: independent of upstream availability, full audit trail, no rate-limit surprises.

---

## 10. Capital One signal

Capital One is AWS-native, so the default is **ECR with Enhanced scanning, IMMUTABLE prod tags, CMK encryption, VPC endpoints**, replicated cross-region, with **Cloud Custodian policies** enforcing no-public-repos and no-non-CMK. K8s-level admission verifies signatures (Kyverno or Sigstore policy-controller).

For multi-tenant ML images, the pattern likely involves Harbor (or JFrog) as the canonical internal mirror, with ECR per region as the K8s-facing endpoint.

---

## Sanity check

1. Why does ECR require an S3 VPC endpoint in addition to the ECR endpoints?
2. What's the difference between ECR Image Scanning Basic and Enhanced, and what does Enhanced add that Basic doesn't?
3. What does `az aks update --attach-acr <name>` actually do under the hood?
4. Why is "Workload Identity Federation" preferred over service-account JSON keys for pulling from GAR?
5. What's the practical reason to use Harbor in front of cloud registries?
6. Docker Hub rate limit: what is it, and what are two mitigations?

---

## Sources

- [AWS ECR docs](https://docs.aws.amazon.com/AmazonECR/)
- [GCP Artifact Registry docs](https://cloud.google.com/artifact-registry/docs)
- [Azure Container Registry docs](https://learn.microsoft.com/azure/container-registry/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Harbor](https://goharbor.io/docs/)
- [JFrog Artifactory](https://jfrog.com/artifactory/)
- [Docker Hub rate limits](https://docs.docker.com/docker-hub/download-rate-limit/)
- [NGC Container Catalog](https://catalog.ngc.nvidia.com/)
- [`amazon-ecr-credential-helper`](https://github.com/awslabs/amazon-ecr-credential-helper)

→ Next: [06 — Docker networking — bridge, host, overlay, macvlan, port publishing](06_docker_networking.md)


\newpage

# 06 — Docker networking: bridge, host, overlay, macvlan, port publishing

> *"`-p 8080:8080` is iptables NAT. Understanding what that actually does explains 80% of 'works on my laptop, doesn't work in prod' bugs."*

## Why this module exists

Docker networking is **iptables and Linux network namespaces with helpful defaults**. When you understand the defaults, you understand the production failure modes. This module covers the five network drivers, the port-publishing model (and its surprising defaults), and the DNS resolver that makes service-by-name discovery work.

Cross-references: Linux NET namespaces (module 1), bridge/host trade-offs (module 10), K8s networking which is a different model entirely (module 18).

---

## 1. The five network drivers

Docker ships five built-in drivers. The first three handle 99% of cases.

| Driver | Scope | When to use |
|---|---|---|
| **bridge** | Single host | The default. Containers on a user-defined bridge see each other; isolated from host |
| **host** | Single host | Container shares host's network namespace — no isolation, full performance |
| **none** | Single host | No networking at all; for batch jobs that talk only to mounted volumes |
| **overlay** | Multi-host (Swarm) | Cross-host container-to-container via VXLAN; uses Swarm clustering |
| **macvlan** | Single host (with layer-2 connectivity to physical net) | Container gets its own MAC + IP on physical network; for legacy apps expecting "real" IPs |
| **ipvlan** | Single host | Layer-2 or layer-3 mode; lower overhead than macvlan |

### 1.1 Bridge networking

The Docker daemon creates `docker0`, a Linux bridge interface, on host startup. Each container gets a veth pair: one end inside the container's NET namespace (named `eth0`), the other end attached to `docker0`. Routes between `docker0` and the host's physical interface go through iptables NAT.

```
Host
├── eth0  (e.g. 192.0.2.10)
├── docker0 (172.17.0.1)  ← Linux bridge
│   ├── vethXXX ↔ container A eth0 (172.17.0.2)
│   └── vethYYY ↔ container B eth0 (172.17.0.3)
```

#### 1.1.1 Default bridge vs user-defined bridge

The `docker0` default bridge has historical baggage:
- **No built-in DNS resolution between containers** — you can only reach others by IP.
- **All containers on it can talk to each other** (no isolation).
- **Container names are not resolvable**.

User-defined bridges (created with `docker network create mynet`) fix all three:
- **Embedded DNS** resolves container names to IPs.
- **Per-network isolation**: containers only see others on the same user-defined network.
- **Can be deleted independently**.

**Rule: never use the default bridge in production.** Always `docker network create` or use Compose, which creates one per project automatically.

#### 1.1.2 Internal vs external bridges

```bash
docker network create --internal db-net
```

`--internal` networks have **no route to the outside**. Useful for databases or message queues that should only be reachable from siblings — even if a container on `db-net` had `CAP_NET_RAW`, it can't egress. Sibling containers can be on both `db-net` and a regular bridge if they need both intra-cluster + external access.

---

## 2. Port publishing (`-p`) — what really happens

`docker run -p 8080:80 nginx` is the canonical command. Under the hood:

1. Docker reserves host port 8080 (and fails with "port already allocated" if taken).
2. Docker adds an iptables NAT rule: `DNAT --to-destination 172.17.0.2:80` on incoming packets to `<host>:8080`.
3. The kernel rewrites destination addresses on inbound packets; the container responds; iptables SNATs the return traffic.

Three surprising defaults that bite everyone:

### 2.1 Default bind is ALL interfaces

`-p 8080:80` is shorthand for `-p 0.0.0.0:8080:80`. The container is reachable from any IP that can route to the host — including the public internet if the host has a public IP. This is why you find Mongo/Redis/etcd instances on Shodan: developers ran `-p 6379:6379` on a server with a public IP and a permissive firewall.

**The fix**: bind to a specific host IP.

```bash
docker run -p 127.0.0.1:8080:80 nginx       # localhost only
docker run -p 10.0.1.5:8080:80 nginx        # specific interface
```

For ML model servers in dev, **always** `127.0.0.1:`. For prod, the firewall/security-group is usually the last line — but binding to `127.0.0.1` (with a reverse proxy in front) is defense in depth.

### 2.2 iptables vs UFW conflict

Docker writes its own iptables rules in the `DOCKER` and `DOCKER-USER` chains, **bypassing UFW**. A `ufw deny 8080/tcp` rule does **nothing** to a port published by Docker — the packet matches DOCKER chain before INPUT. The fix:

```bash
# /etc/docker/daemon.json
{
  "iptables": true,
  "ip-forward": true
}

# DOCKER-USER chain (Docker adds DOCKER, you add DOCKER-USER, your rules win)
iptables -I DOCKER-USER -i eth0 ! -s 10.0.0.0/8 -j DROP
```

This is a frequent root cause of "my server is somehow accessible from the internet even though I have a firewall."

### 2.3 `EXPOSE` does NOT publish

`EXPOSE 8080` in the Dockerfile is documentation. The port is **not** reachable from outside the container unless you also pass `-p` (or use `--publish-all` which publishes all EXPOSEd ports to random host ports).

---

## 3. Host networking — when isolation isn't worth it

```bash
docker run --network host nginx
```

The container shares the host's NET namespace. **No port publishing**, no NAT, no overlay. The container can:

- Bind to any host port directly.
- See all host network interfaces.
- Sniff host traffic with `tcpdump` (if it has `CAP_NET_RAW`).
- See `/proc/net` of the host.

When to use:

- Maximum network performance (DPDK, high-frequency trading, large `tcp_window` workloads).
- Tools that need to inspect host network state (Falco, monitoring agents).
- Workloads that need raw socket access without iptables NAT overhead.

When **not** to use: any production multi-tenant context. Host networking is a privilege escalation. Capital One–style postures forbid `network_mode: host` outside of allow-listed monitoring DaemonSets.

In Kubernetes, the equivalent is `hostNetwork: true` — PSA `restricted` policy forbids it for the same reason.

---

## 4. Overlay networks (Swarm)

Docker Swarm's overlay driver lets containers on different hosts talk over an encrypted VXLAN tunnel. Swarm is mostly dead — Kubernetes won. But if you encounter a Swarm cluster:

- VXLAN encapsulates Ethernet frames in UDP (port 4789).
- Control plane uses TLS-mTLS via Swarm's built-in PKI.
- IPSec encryption available with `--opt encrypted=true`.

For multi-host container networking outside Swarm: use Kubernetes (module 18) or Nomad with its CNI.

---

## 5. Macvlan & ipvlan — when containers need "real" IPs

Some legacy apps expect to be on a Layer-2 network, with a unique MAC and an IP routable from the upstream switch. Macvlan creates a virtual NIC per container that the host's physical NIC presents to the switch.

```bash
docker network create -d macvlan \
  --subnet=192.0.2.0/24 \
  --gateway=192.0.2.1 \
  -o parent=eth0 \
  mvlan
docker run --network mvlan --ip 192.0.2.50 my-legacy-app
```

The container at `192.0.2.50` is **directly addressable from the upstream switch** — no NAT.

Gotchas:
- The host itself **cannot** reach its own macvlan containers via the macvlan interface (kernel limitation). You either reach them from another host or attach the host to its own macvlan network.
- Many cloud VMs disable promiscuous mode and break macvlan (AWS, GCP, Azure security groups assume one MAC per ENI).

**Macvlan is on-prem-only in practice.** Cloud networking forces NAT/overlay patterns.

---

## 6. Container DNS

User-defined bridge networks include an **embedded DNS resolver** at `127.0.0.11`. Inside the container, `/etc/resolv.conf` is set to `127.0.0.11`. The resolver:

1. Resolves other container names on the same network to their internal IPs.
2. Falls back to the host's resolvers for everything else (Google DNS / corporate DNS / cloud DNS).

This is how `db:5432` works inside Compose without any host-name configuration — the embedded resolver returns the db container's IP.

In K8s the equivalent is **CoreDNS** running as a deployment with a Service IP; pods get `/etc/resolv.conf` pointed at the cluster DNS service. The model is identical in spirit.

---

## 7. Container ↔ host: "host.docker.internal"

A container talking to the host (e.g., a process on the host's `localhost:5432`) is awkward. From inside the container, `127.0.0.1` is the container itself, not the host.

Docker Desktop (Mac/Win/WSL) provides the magic DNS name `host.docker.internal` that resolves to the host's gateway IP. On Linux, you must add `--add-host=host.docker.internal:host-gateway`:

```bash
docker run --add-host=host.docker.internal:host-gateway myapp
```

In K8s this pattern is uncommon — pods talk to services, not to the host. If you do need it, use `hostNetwork: true` (with caveats) or expose a host-port Service.

---

## 8. Network anti-patterns (you will see these)

| Anti-pattern | What's wrong | Fix |
|---|---|---|
| `docker run -p 6379:6379 redis` on a public-IP server | Public Redis on the internet | `127.0.0.1:6379:6379` + reverse proxy with auth |
| `network_mode: host` for everything | No isolation | Use a user-defined bridge |
| `EXPOSE` as a firewall | It's not a firewall, it's documentation | Real firewall + minimal `-p` |
| UFW rule that "blocks" a Docker port | Docker bypasses UFW INPUT chain | Use `DOCKER-USER` chain |
| Containers on default `bridge` | No DNS, no isolation | User-defined bridge |
| `--network host` to debug DNS issues | Hides the actual problem | Run a debug sidecar (`nicolaka/netshoot`) on the same user-defined network |
| `iptables -P FORWARD DROP` | Breaks all container egress | Use DOCKER-USER chain rules |

---

## 9. The egress side — outbound traffic from containers

A container's outbound traffic goes:

```
container eth0 → veth → docker0 → host iptables MASQUERADE → host eth0 → upstream
```

Three layers can block egress:

1. **Network policy at the container layer**: Docker doesn't have a built-in egress policy. Tools like **Cilium-on-Docker** (rare) or just iptables rules in DOCKER-USER do it.
2. **Host firewall**: `iptables -A DOCKER-USER -d 169.254.169.254 -j DROP` blocks the EC2/GCP/Azure IMDS endpoint from all containers — this is **the Capital One 2019 lesson encoded as one iptables rule**.
3. **Cloud security groups / NSG**: outside the host, the VPC firewall.

In K8s the layer-1 control is **NetworkPolicy** (module 18). The IMDS block is implemented at the **VPC CNI level** by setting hop-limit=1 on IMDSv2 (module 26).

---

## 10. The Capital One 2019 incident in network terms

Re-tell the breach with networking glasses on:

1. A misconfigured WAF in Capital One's web tier had an **SSRF vulnerability**: it accepted user-supplied URLs and fetched them server-side.
2. An attacker pointed the SSRF at `http://169.254.169.254/latest/meta-data/iam/security-credentials/` — the EC2 **IMDSv1** endpoint.
3. IMDSv1 returned a 200 with temporary AWS credentials of the IAM role attached to the WAF instance.
4. The IAM role had `s3:ListAllMyBuckets` and overly broad `s3:GetObject` — the attacker pulled 106M records.

The fix at multiple layers:

- **App layer**: prevent SSRF.
- **Network layer (the new lesson)**: block `169.254.169.254` from any process that doesn't need it. For containers, the standard pattern is `iptables -A DOCKER-USER -d 169.254.169.254/32 -j DROP` on the host, OR use **IMDSv2 only** (`MetadataHttpEndpoint=enabled,MetadataHttpTokens=required, MetadataHttpPutResponseHopLimit=1`). The hop-limit=1 means a container's request to IMDS — which has TTL decremented to 0 in the veth — fails. IMDSv2-only is the modern AWS default.
- **IAM layer**: tight role permissions + permission boundaries.

For containerized ML workloads on AWS, the canonical hardening is:

```hcl
# Terraform — IMDSv2 only, hop limit 1
resource "aws_instance" "worker" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"     # IMDSv2 token required
    http_put_response_hop_limit = 1              # blocks containers
  }
  # ...
}
```

This single block would have prevented the Capital One breach pattern from the container side. We will reinforce this in module 13 (Data exposure — AWS).

---

## Sanity check

1. What does `-p 8080:80` actually do at the iptables level, and why does that bypass UFW?
2. What does `docker0` resolve to, and why is the default bridge unsuitable for production?
3. Container A on user-defined network `app-net`, container B on `db-net`. Can A reach B by name? By IP?
4. Why does `--network host` make a container a security risk equivalent to running on the host directly?
5. From inside a Linux Docker container without Docker Desktop, how do you reach a service on the host's `localhost`?
6. What iptables rule (or AWS instance setting) would have prevented the Capital One 2019 IMDS pivot from a containerized workload?

---

## Sources

- [Docker network drivers](https://docs.docker.com/network/)
- [User-defined bridge networks](https://docs.docker.com/network/bridge/)
- [DOCKER-USER chain & iptables integration](https://docs.docker.com/network/iptables/)
- [Macvlan networks](https://docs.docker.com/network/macvlan/)
- [AWS IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [Capital One 2019 breach case study (OCC consent order)](https://www.occ.treas.gov/news-issuances/news-releases/2020/nr-occ-2020-101a.pdf)
- [`netshoot` debug image](https://github.com/nicolaka/netshoot)

→ Next: [07 — Docker storage — bind mounts, volumes, tmpfs, volume drivers](07_docker_storage.md)


\newpage

# 07 — Docker storage: bind mounts, volumes, tmpfs, volume drivers

> *"`-v /:/host` is RCE. `-v /var/run/docker.sock:/var/run/docker.sock` is RCE. `-v ~/.aws:/root/.aws` is credential theft. The volume flag is the most security-critical thing in `docker run`."*

## Why this module exists

Volumes are how data crosses the container/host boundary. They are also how the most common container escapes happen. This module covers the three volume types, the eight common patterns, and the four anti-patterns that will land you in a Capital One–style postmortem.

We focus on Docker semantics; module 19 covers Kubernetes' PV/PVC/StorageClass model which is a different abstraction with similar primitives underneath.

---

## 1. Three storage types

| Type | Where it lives | Lifecycle | Use case |
|---|---|---|---|
| **Bind mount** | Arbitrary host path | Host file's lifecycle | Dev (code reload), legacy apps expecting host paths |
| **Named volume** | `/var/lib/docker/volumes/<name>/_data` (or volume driver backend) | Independent of container; explicit delete | The default for any persistent state |
| **tmpfs mount** | RAM (host page cache, not host disk) | Lost on container stop | Secrets at runtime, scratch space, CI temp files |

### 1.1 Bind mount

```bash
docker run -v /home/vr/data:/data:ro,Z myapp
```

- `:ro` — read-only mount.
- `:Z` — relabel the source with the SELinux container label (RHEL/AL2/AL2023; lowercase `z` is shared, uppercase `Z` is private to this container).
- `:rshared` / `:rslave` — mount propagation; rarely needed; common in monitoring sidecars.

**Bind mounts are the most dangerous primitive in Docker.** They bypass image immutability — anything on the host is visible to the container, subject to UID/GID/SELinux. Three rules:

1. **Never** mount `/`, `/etc`, `/var`, `/home`, `~`, or any directory containing config or keys.
2. **Always** mount read-only if the container only needs to read.
3. **Always** use a dedicated, locked-down directory whose owner/perms match the container's UID.

### 1.2 Named volume

```bash
docker volume create mydata
docker run -v mydata:/data myapp
```

The volume is managed by Docker; its on-disk path is `/var/lib/docker/volumes/mydata/_data`. Named volumes:

- Persist beyond container deletion.
- Get backed up by `docker volume` commands or via volume drivers.
- Can be exposed by **volume drivers** to remote backends: NFS, EFS, Ceph, Portworx, AWS EBS via `rexray`, etc.
- Are the recommended default for any state.

**Volume drivers** are the cloud-data-exposure hook. We cover them in modules 12–15.

### 1.3 tmpfs mount

```bash
docker run --tmpfs /tmp:size=64m,mode=1777 myapp
```

The mount lives in RAM. Tmpfs is mandatory when running with `--read-only` (containers need *some* writable space for `/tmp`). It's also the right place for:

- Cached secrets (loaded once at startup, mounted in RAM, never hit disk).
- Temporary files that contain sensitive data (model intermediate outputs, query results).
- Scratch space that must not persist.

---

## 2. The anti-pattern hall of fame

| Anti-pattern | Why it's catastrophic | The fix |
|---|---|---|
| `-v /var/run/docker.sock:/var/run/docker.sock` | Root on host via Docker API | Use a socket proxy (Tecnativa, Datadog) with verb whitelist; or use rootless |
| `-v /:/host` | Trivial root escape — chroot + writes to /etc/sudoers | Never. If you must read host data, mount the specific path read-only |
| `-v ~/.aws:/root/.aws` or `-v ~/.kube:/root/.kube` | Steals user's cloud creds | Use IRSA / Workload Identity / Managed Identity instead (modules 13-15) |
| `-v ~/.ssh:/root/.ssh` | Steals SSH keys | Use BuildKit `--mount=type=ssh` at build, runtime needs no SSH |
| `-v /etc:/etc` | Container can read `/etc/shadow`, modify `/etc/passwd` | Never |
| Mount a Postgres data dir into a container with UID mismatch | Postgres refuses to start (correctly) | `--user $(id -u):$(id -g)` and `chown` the host dir |
| Host path used as both container data AND container runtime cache | Container can corrupt its own image artifacts | Separate paths |
| Bind mount over a Dockerfile-defined VOLUME | Image's seed data is hidden | Either bind-mount-only-the-subdirs or remove `VOLUME` from Dockerfile |

The `docker.sock` mount is so dangerous that any code review tool should flag it. The Cloud Custodian / Falco / Kyverno rule for "containers must not mount the Docker socket" is table stakes.

---

## 3. The Dockerfile `VOLUME` directive

`VOLUME /data` in a Dockerfile marks that path as a volume mount point. At runtime, if you don't supply `-v`, Docker creates an **anonymous volume** at that path. Anonymous volumes get a random ID; `docker volume ls --filter dangling=true` finds them.

Implications:

- Any state your image writes to that path **must** be in a volume — you can't bake initial state into the image after `VOLUME` is declared in the Dockerfile (it'd be shadowed by the volume mount).
- Anonymous volumes accumulate. Long-running production hosts gather hundreds of GB of "where did this come from?" volumes.
- Some images (Postgres, MySQL) declare `VOLUME /var/lib/postgresql/data`; this is why `-v pgdata:/var/lib/postgresql/data` is the standard pattern.

**Production rule**: always supply `-v` for any `VOLUME` directive. Use named volumes for clarity.

---

## 4. Volume drivers — the extension point

Docker volumes can be backed by remote storage via volume drivers. The driver ecosystem peaked around 2018 and has consolidated. Current healthy options:

| Driver | Backend | Notes |
|---|---|---|
| `local` (default) | Host filesystem | The default; also supports `tmpfs`, `nfs`, `cifs` options |
| `nfs` (via local + opts) | NFS server | `docker volume create -d local --opt type=nfs --opt o=addr=nfs.internal,rw --opt device=:/exports/data nfsvol` |
| `cifs` (Windows shares) | SMB/CIFS | Similar pattern, `type=cifs` |
| Portworx (`pxd`) | Portworx | Multi-node block storage, commercial |
| Longhorn | Rancher | OSS, K8s-first, has Docker plugin |
| REX-Ray | Multi-cloud (EBS, Azure Disk, GCE PD) | Mostly deprecated since 2020; use cloud CSI on K8s instead |

The Docker volume driver model is largely **deprecated for new development**. Kubernetes CSI replaced it; the volume primitives in Compose v2 still work but no new drivers are landing. For Docker-on-VM workloads, the local-NFS option is what you'll see most.

### 4.1 NFS volume — the on-prem default

```bash
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=10.0.0.50,rw,vers=4.1,nconnect=8 \
  --opt device=:/exports/mldata \
  mldata

docker run -v mldata:/data myimage
```

For ML workloads on-prem, this is how training data lives on a NetApp/Isilon/MinIO-NFS and is exposed to PyTorch containers.

---

## 5. Volume hygiene & lifecycle

### 5.1 Inspection

```bash
docker volume ls
docker volume ls --filter dangling=true        # not attached to any container
docker volume inspect mydata
docker system df -v                            # disk usage by volume
```

### 5.2 Cleanup

```bash
docker volume prune                            # remove dangling
docker volume prune --filter "label!=keep"     # respect a label
```

In production: tag volumes with `--label backup=daily` or similar; prune everything without the label periodically.

### 5.3 Backup

There is no built-in volume backup. The standard pattern:

```bash
docker run --rm \
  -v mydata:/data:ro \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/mydata-$(date +%F).tar.gz -C /data .
```

For cloud volume backends (EBS, EFS), use the native snapshot API. For NFS, use the storage appliance's snapshot (NetApp, Isilon, Ceph RBD). For self-hosted production volume backup, **Velero** is the K8s answer (module 29).

---

## 6. Read-only root + writable tmpfs — the production pattern

The hardest container is one whose root filesystem is read-only:

```bash
docker run \
  --read-only \                            # root FS is RO
  --tmpfs /tmp:size=64m,mode=1777 \        # writable /tmp
  --tmpfs /run:size=16m,mode=755 \         # writable /run for nginx, etc
  -v mydata:/data \                        # explicit named volume for state
  myimage
```

Benefits:

- Eliminates the "attacker writes a webshell into `/opt/`" class of attacks.
- Makes the container immutable at runtime — drift is impossible.
- Forces explicit declaration of every writable path.

Apps that don't tolerate read-only root usually need writable `/var/cache`, `/var/run`, or `/tmp`. Add a tmpfs for each. Some images (Postgres) need a writable data dir, which is your named volume.

---

## 7. UID/GID, ownership, and the "perm denied" mystery

The most-asked Docker question on Stack Overflow: "I mounted a volume but the container can't write to it." The cause is always UID mismatch.

```
Container UID = 10001 (your image's USER)
Host directory owner = 1000 (your dev user)

Container tries to write → kernel checks owner → not allowed.
```

Three fixes, in order of preference:

1. **Use a named volume** (`-v mydata:/data`). The volume directory is created with the container's UID; ownership is correct by definition.
2. **`chown` the host directory** to match the container's UID. Pre-create with `chown -R 10001:10001 /host/path` before mounting.
3. **Run the container as the host user** via `--user $(id -u):$(id -g)`. The container process runs with your UID; reads/writes succeed. Caveat: the container's `USER` directive is ignored.

SELinux adds a label dimension on top of UID. On RHEL/AL2/AL2023, even with UID alignment, the wrong type label denies access. `:Z` relabels for the container; ` :z` for shared use.

---

## 8. Volumes for ML containers

ML containers have three storage needs distinct from general apps:

1. **Training data** — large (TBs), read-mostly, often shared across many containers/jobs. → mount via NFS (on-prem), EFS (AWS), Filestore (GCP), Azure Files (Azure), or pull from S3/GCS/Blob to local SSD on job start.
2. **Model artifacts** — large (GBs), read-only at serve time, versioned. → either bake into image (only if <500 MB and updates rare) or mount from object store via Mountpoint/gcsfuse/blobfuse2.
3. **Checkpoints / intermediate state** — write-heavy during training, transient. → local SSD + periodic upload to object store. Mount as a named volume backed by host SSD with explicit cleanup.

We will go deep on each in modules 12–15.

---

## 9. The `dockerd` storage driver (the layer driver)

Distinct from volumes is the **storage driver** that manages the **image and container layer overlayfs**. Options:

| Driver | When |
|---|---|
| `overlay2` | Default on every modern Linux. Use this. |
| `aufs` | Old Ubuntu kernels. Replaced by overlay2. |
| `btrfs` / `zfs` | When host root FS is btrfs/zfs; copy-on-write snapshots are nice. |
| `devicemapper` | Removed; used to be default on RHEL. Don't. |
| `vfs` | No copy-on-write, used inside containers (e.g., DinD). Slow. |

You will only touch this if you're chasing a "container start is slow" problem on an old host. On EKS/GKE/AKS the answer is overlay2.

---

## 10. Compose volumes — the project model

Compose v2 (the modern `docker compose` not `docker-compose`) namespaces volumes per project:

```yaml
# compose.yml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
  app:
    image: myorg/myapp:1.0
    volumes:
      - ./src:/app/src:ro      # bind mount: dev source reload
      - cache:/app/.cache

volumes:
  pgdata:
  cache:
```

When you `docker compose up`, Docker creates volumes named `<project>_pgdata` and `<project>_cache`. Down → `docker compose down -v` to remove them.

For production (K8s), the equivalents are PV/PVC declarations. The Compose primitives are clean but the abstraction is host-local.

---

## Sanity check

1. Why is `-v /var/run/docker.sock:/var/run/docker.sock` equivalent to giving the container root on the host?
2. What's the production-grade pattern when a container needs a writable `/tmp` but you want `--read-only` on the root FS?
3. Why does `:Z` matter on RHEL/AL2 but not on Ubuntu?
4. You bind-mount a host directory and the container gets "permission denied." Name three fixes in order of preference.
5. The Dockerfile says `VOLUME /data` and you don't supply `-v`. What happens, and why is this a long-term problem?
6. For an ML training container that needs to read 10 TB of training data, what storage pattern do you reach for first on-prem? On AWS?

---

## Sources

- [Docker volumes](https://docs.docker.com/storage/volumes/)
- [Bind mounts](https://docs.docker.com/storage/bind-mounts/)
- [tmpfs mounts](https://docs.docker.com/storage/tmpfs/)
- [Volume drivers](https://docs.docker.com/storage/volumes/#use-a-volume-driver)
- [SELinux container labels](https://docs.docker.com/storage/bind-mounts/#configure-the-selinux-label)
- [Storage drivers](https://docs.docker.com/storage/storagedriver/)
- [Compose v2 volumes](https://docs.docker.com/compose/compose-file/07-volumes/)

→ Next: [08 — Secrets in Docker — BuildKit secrets, Swarm secrets, runtime patterns](08_docker_secrets.md)


\newpage

# 08 — Secrets in Docker: BuildKit secrets, Swarm secrets, runtime patterns

> *"`ENV SECRET_KEY=...` in a Dockerfile is a public commit. `docker history` reveals it. The image is the new git."*

## Why this module exists

Every container needs secrets — DB passwords, API tokens, signing keys, model artifacts that are themselves sensitive. There are exactly two ways to get a secret into a container safely:

1. **At build time** — only if the secret is needed *to build* and never to run (e.g., a private package registry token). Use **BuildKit `--mount=type=secret`**.
2. **At runtime** — for credentials the app uses. **Inject from a secret backend at container start**; never bake in.

The wrong ways are countless. This module enumerates them and the right replacements.

---

## 1. The cardinal sin: `ENV` / `ARG` for secrets

```dockerfile
# WRONG — both of these write the value into a layer that is visible forever
ENV DB_PASSWORD=hunter2
ARG NPM_TOKEN
RUN echo "${NPM_TOKEN}" > ~/.npmrc
```

`docker history <image>` reveals every `ENV`, every `RUN` command, and every `ARG` substitution. The image is, for all practical purposes, world-readable once pushed to a registry — anyone with pull access has the secret.

Even if the layer that "deletes" the secret is later, the secret persists in earlier layers:

```dockerfile
RUN curl -H "Authorization: $TOKEN" ... && rm /tmp/cache
# The token is in the RUN command string, captured in the layer's history.
```

---

## 2. BuildKit `--mount=type=secret` — the right way at build time

BuildKit (default builder since Docker 23.0) introduced typed mounts. Secret mounts are tmpfs-backed, exist only during one RUN, and never appear in the resulting layer.

### 2.1 Dockerfile syntax

```dockerfile
# syntax=docker/dockerfile:1.7
FROM debian:12-slim

RUN --mount=type=secret,id=npm_token,target=/root/.npmrc,mode=0400 \
    npm install --production

RUN --mount=type=secret,id=ca_bundle,target=/etc/ssl/certs/private-ca.pem \
    update-ca-certificates && \
    pip install --index-url https://private.pypi.internal/simple/ my-private-pkg
```

The `RUN` instruction can read the secret as a file at `target=`. After the RUN finishes, the mount disappears. Nothing about the secret is in the layer.

### 2.2 Build invocation

```bash
# Inline value (avoid in shell history)
docker build --secret id=npm_token,src=$HOME/.npmrc -t myimg .

# Or from an env var
docker build --secret id=db_pass,env=DB_PASS -t myimg .
```

Verify with `docker history myimg --no-trunc | grep secret` — you'll see the RUN with `--mount=type=secret,id=npm_token`, but **not the value**.

### 2.3 SSH mounts for private git

```dockerfile
RUN --mount=type=ssh \
    git clone git@github.com:myorg/private-repo.git
```

```bash
docker build --ssh default=$SSH_AUTH_SOCK -t myimg .
```

Lets your build container use your SSH agent without leaking keys.

---

## 3. Runtime secrets — the four patterns

For secrets the app needs *at runtime*, four patterns in increasing order of production maturity:

### 3.1 Env vars (the convenient but flawed pattern)

```bash
docker run -e DB_PASSWORD=$(vault read -field=password secret/db) myapp
```

Problems:

- Env vars leak via `/proc/<pid>/environ` to anyone who can read that file (often: anyone in the container).
- Crash reporters, error trackers, and Datadog/Sentry agents often **dump env vars in stack traces**. Real-world leakage source.
- `docker inspect` shows env vars to anyone with daemon access.
- Subprocesses inherit env vars (bash, python multiprocessing) — surprising leakage.

When env vars are OK: ephemeral CI jobs, dev environments, and the bootstrap step that *immediately* loads a secret-manager client and discards the env var. Even then, prefer files.

### 3.2 Mounted secret files (the default-safe pattern)

```bash
# Secret stored on host (perms 0400, owned by the container UID)
docker run \
  -v /etc/secrets/db_password:/run/secrets/db_password:ro \
  -e DB_PASSWORD_FILE=/run/secrets/db_password \
  myapp
```

The app reads the file at startup. Why this beats env vars:

- Filesystem perms enforce who can read.
- Crash dumps don't include file contents by default.
- `docker inspect` shows the mount source, not contents.
- Easy to rotate — replace the file, signal the app to reload.

The convention `*_FILE` env var (e.g., `DB_PASSWORD_FILE`) pointing to a path is the standard. Postgres, MySQL, MariaDB images all support it natively.

### 3.3 Docker Swarm secrets (declarative, encrypted at rest)

If you're on Swarm (rare in 2025+):

```bash
echo "hunter2" | docker secret create db_password -
docker service create \
  --name myapp \
  --secret db_password \
  myimg
```

Inside the container, the secret is mounted at `/run/secrets/db_password`, owned root, mode 0444. Encrypted in Swarm's Raft store. Distributed via mTLS to the right nodes.

For non-Swarm, the closest analogue is K8s Secret + Secret Store CSI Driver (module 20).

### 3.4 Sidecar / agent injection (the production pattern)

The dominant pattern in 2025–2026:

- **Vault Agent Injector / Sidecar** — Vault Agent runs alongside the app, fetches secrets, writes them as files into a shared volume. App reads from filesystem.
- **AWS Secrets Manager Agent (2024 GA)** — local agent that proxies AWS Secrets Manager calls with caching.
- **Google Secret Manager via SDK** — app SDK fetches at startup using Workload Identity.
- **Azure Key Vault SDK** — same, using Managed Identity.

For Docker (non-K8s), this looks like:

```yaml
# compose.yml
services:
  vault-agent:
    image: hashicorp/vault:1.16
    command: ["agent", "-config=/etc/vault/agent.hcl"]
    volumes:
      - secrets:/secrets
      - ./vault-agent.hcl:/etc/vault/agent.hcl:ro
  app:
    image: myorg/myapp:1.0
    volumes:
      - secrets:/secrets:ro
    environment:
      DB_PASSWORD_FILE: /secrets/db_password
    depends_on:
      - vault-agent
volumes:
  secrets:
```

Vault Agent authenticates to Vault (via AppRole / IAM / GCP / Azure), fetches the secret, writes to `/secrets/db_password`. App reads it. Rotates automatically.

In K8s, the same pattern is the **Vault Agent Sidecar Injector** or the **CSI driver** approach (module 20).

---

## 4. Secrets in Compose

Compose v2 supports secrets natively:

```yaml
services:
  app:
    image: myorg/myapp:1.0
    secrets:
      - db_password
secrets:
  db_password:
    file: ./db_password.txt        # source file on host
    # or: environment: DB_PASSWORD  (Compose v2 only)
    # or: external: true            (managed elsewhere, e.g. swarm)
```

The secret is mounted at `/run/secrets/db_password` inside the container — identical to Swarm semantics. Compose does NOT encrypt at rest the way Swarm does — it just bind-mounts. Treat the on-host file as the secret.

---

## 5. The "secrets at build time vs runtime" decision

| Need | Build-time | Runtime |
|---|---|---|
| Private package registry token | ✅ `--mount=type=secret` | ❌ |
| Private git clone | ✅ `--mount=type=ssh` | ❌ |
| Code signing key | ✅ in sealed CI environment only | ❌ |
| Database password | ❌ never | ✅ |
| API token (Stripe, OpenAI, ...) | ❌ never | ✅ |
| TLS cert + key | ⚠️ only if the same cert is shared across instances | ✅ preferred |
| Model weights (if treated as secret) | ❌ for any model that varies per-deploy | ✅ mount from object store |

The rule of thumb: **anything that changes between deploys MUST be runtime.** Build-time secrets are for things that are immutable for the lifetime of the image.

---

## 6. `.env` files and the `.env`-in-image trap

`.env` files are a developer convenience. They become production incidents two ways:

1. `COPY . /app` sweeps `.env` into the image. (Module 03 `.dockerignore` fix.)
2. `docker run --env-file .env myapp` works, but the `.env` lives in your git repo on the host and often gets committed.

Convention: `.env` is for local-dev defaults, never committed, replaced by Vault / Secrets Manager / Key Vault in higher environments.

---

## 7. Image layer history audit

To verify no secrets leaked:

```bash
docker history --no-trunc myorg/myimg:1.2.3
docker save myorg/myimg:1.2.3 -o myimg.tar
tar -xf myimg.tar
# Each layer is a .tar.gz; inspect manually or with `dive`
dive myorg/myimg:1.2.3        # https://github.com/wagoodman/dive
```

Run `trivy image --scanners secret myorg/myimg:1.2.3` — Trivy's secret scanner looks for AWS keys, GCP keys, GitHub tokens, etc. in layers and surface files. This is the table-stakes CI check.

---

## 8. The "secret in image but I deleted it" gotcha

Common belief: "I `RUN rm /tmp/secret` in a later layer, so the secret is gone."

Wrong. Layers are stacked; the deletion is a whiteout in the later layer. The earlier layer still has the file. Anyone who pulls the image and walks the layers (or just `docker save` + `tar -xf`) recovers the secret.

There is **no way to remove a secret from an existing image layer.** You must rebuild without it, push as a new digest, and rotate the secret.

---

## 9. Real-world breaches in this category

- **Uber 2016** — AWS keys committed in a private GitHub repo containing build scripts. Attacker accessed the repo, found the keys, exfil'd S3.
- **GitHub Actions 2024 disclosures** — multiple OSS projects had build images with embedded `GITHUB_TOKEN` artifacts because they `echo`'d them in CI logs.
- **CodeBuild misconfigurations** — common AWS finding: Docker images built in CodeBuild end up in ECR with `--build-arg AWS_KEY=...` baked in.

The pattern is always the same: secret used at build time, baked into a layer, image pushed to a registry someone unintended can read.

---

## 10. Production checklist

For every image:

- [ ] No `ENV` or `ARG` for secrets — `docker history` clean.
- [ ] BuildKit `--mount=type=secret` for any build-time credential.
- [ ] `.dockerignore` includes `.env*`, `.git`, `~/.aws`, `~/.kube`, `~/.ssh`.
- [ ] Runtime secrets injected from secret manager (Vault / AWS / GCP / Azure) at start.
- [ ] App reads secrets from files (`*_FILE` pattern), not env vars.
- [ ] Trivy CI step: `trivy image --scanners secret --severity HIGH,CRITICAL`.
- [ ] Cosign attestation of SBOM + provenance.
- [ ] Production image immutability (ECR/ACR set to IMMUTABLE).

---

## Sanity check

1. Why does `ENV DB_PASS=hunter2` followed by `RUN echo $DB_PASS` leave the secret in the image even if you `unset` it later?
2. What's the file location convention for a secret mounted at runtime, and why is the `*_FILE` env-var convention better than `DB_PASS=...`?
3. How does BuildKit `--mount=type=secret` differ from `ARG` for build-time credentials?
4. Why is Compose's `secrets:` directive **not** encrypted at rest while Swarm's is?
5. A teammate says "we'll just `rm` the secret in the next RUN." What's wrong with that reasoning?

---

## Sources

- [BuildKit secrets documentation](https://docs.docker.com/build/building/secrets/)
- [Docker Swarm secrets](https://docs.docker.com/engine/swarm/secrets/)
- [Compose secrets](https://docs.docker.com/compose/use-secrets/)
- [Vault Agent](https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent)
- [AWS Secrets Manager Agent](https://aws.amazon.com/blogs/security/use-the-aws-secrets-manager-agent/)
- [Trivy secret scanner](https://aquasecurity.github.io/trivy/latest/docs/scanner/secret/)
- [`dive` image-layer inspector](https://github.com/wagoodman/dive)

→ Next: [09 — Docker Compose & local development](09_docker_compose.md)


\newpage

# 09 — Docker Compose & local development

> *"Compose is for local dev. The day it becomes your production orchestrator is the day you owe yourself a Kubernetes migration."*

## Why this module exists

Compose is the de facto **local-dev** environment for any project with ≥2 services. It's also widely abused as a "lightweight orchestrator" — a fragile decision for anything beyond a single VM. This module covers Compose v2 (which replaced the legacy `docker-compose` Python tool), the production patterns, and the gotchas that turn dev compose files into incident reports.

---

## 1. Compose v2 vs `docker-compose` v1

`docker-compose` (Python, v1.x) is **deprecated**. Compose v2 is a Go plugin invoked as `docker compose` (note: no hyphen). It ships with Docker Desktop and is `apt install docker-compose-plugin` on Linux.

| | v1 (`docker-compose`) | v2 (`docker compose`) |
|---|---|---|
| Language | Python | Go |
| Bundled with | Separate install | Docker Engine plugin |
| Version | 1.29.2 (final) | 2.x ongoing |
| Performance | Slower | Faster, parallel |
| Compose Spec compliance | Partial | Full |
| Status | EOL July 2023 | Active |

Always use v2. Aliases for muscle memory: `alias dcom="docker compose"`.

---

## 2. The Compose Spec (file format)

The Compose Specification ([compose-spec.io](https://compose-spec.io/)) is the cross-tool standard. Compose v2 implements it. Kubernetes via **Kompose** can translate compose files to manifests (one-shot port, never bidirectional).

`compose.yml` (or `compose.yaml`; both work):

```yaml
name: ml-stack                         # project name, overrides directory name

services:
  api:
    image: myorg/api:1.2.3
    build:
      context: ./api
      dockerfile: Dockerfile
      args:
        BASE_TAG: 3.12-slim
    ports:
      - "127.0.0.1:8080:8080"          # bind to localhost only — see module 06
    environment:
      DATABASE_URL: postgres://app:password@db:5432/app
      REDIS_URL: redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/healthz"]
      interval: 15s
      timeout: 3s
      retries: 5
      start_period: 20s
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD_FILE: /run/secrets/db_pass
      POSTGRES_DB: app
    volumes:
      - pgdata:/var/lib/postgresql/data
    secrets:
      - db_pass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      retries: 10

  cache:
    image: redis:7-alpine
    command: ["redis-server", "--maxmemory", "256mb", "--maxmemory-policy", "allkeys-lru"]

volumes:
  pgdata:

secrets:
  db_pass:
    file: ./secrets/db_pass.txt
```

Everything that matters:

- `services.<name>` becomes a container. Service name is the DNS name on the project network.
- `depends_on.<service>.condition: service_healthy` waits for the dependency's HEALTHCHECK before starting the dependent. This is the single most-asked Compose feature.
- `secrets:` mounts files at `/run/secrets/<name>` — matches Swarm semantics.
- `volumes:` declares named volumes; project-scoped (`<project>_<name>`).
- `healthcheck:` is the dependency-readiness signal.
- `restart: unless-stopped` for prod-ish behavior locally.

---

## 3. Override files & profiles

### 3.1 Override files

Compose merges multiple files: `compose.yml` + `compose.override.yml` (auto), or explicit `-f compose.yml -f compose.prod.yml`.

```yaml
# compose.override.yml — auto-merged in dev
services:
  api:
    build:
      context: ./api
    volumes:
      - ./api/src:/app/src               # bind mount for live reload
    environment:
      DEBUG: "true"
```

```yaml
# compose.prod.yml — explicit, --file required
services:
  api:
    image: myorg/api:${VERSION}
    environment:
      DEBUG: "false"
    deploy:
      resources:
        limits:
          memory: 1g
          cpus: "1.0"
```

Run: `docker compose -f compose.yml -f compose.prod.yml up -d`.

### 3.2 Profiles

Selective service activation:

```yaml
services:
  api: {...}
  db: {...}
  jupyter:
    image: jupyter/minimal-notebook
    profiles: ["dev", "notebooks"]
  prometheus:
    image: prom/prometheus
    profiles: ["monitoring"]
```

`docker compose up` brings up only `api` and `db`. `docker compose --profile monitoring up` adds Prometheus. Cleaner than maintaining separate compose files for variations.

---

## 4. The "compose as production orchestrator" trap

Compose works "fine" for a single-VM deployment. Then:

- One host goes down → all services go down. No HA.
- You scale: `docker compose up --scale api=3` works, but there's no load balancer in front (you bolt on Traefik/HAProxy; now you own that too).
- You want zero-downtime deploy: Compose's `up` recreates a container with a brief downtime. No rolling update.
- You need secrets: Compose secrets are bind-mounted from the host filesystem — no encryption at rest, no rotation.
- You want monitoring: roll your own.

Each problem has a Compose workaround. Together they reinvent Kubernetes badly. The threshold to move:

- > 1 host
- > 5 services
- Compliance requires audit logs, encrypted secrets, RBAC
- You start writing `restart: always` + `sleep && healthcheck` retry loops

At that point: K8s on a managed offering (EKS / GKE / AKS) is cheaper than the operational debt of stretched Compose.

---

## 5. Compose-on-ECS — the deprecated bridge

AWS once supported `docker compose up --context ecs` to deploy compose files directly to ECS. This was deprecated in 2023. Use **Copilot** (`copilot deploy`) or write CloudFormation/CDK/Terraform if you need ECS.

There is no GCP/Azure equivalent. Compose remains local-dev–first.

---

## 6. Compose + GPUs for local ML

NVIDIA Container Toolkit + Compose v2:

```yaml
services:
  train:
    image: nvcr.io/nvidia/pytorch:24.06-py3
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all                 # or count: 1, or capabilities: [gpu]
              capabilities: [gpu]
    volumes:
      - ./data:/workspace/data:ro
      - ./checkpoints:/workspace/checkpoints
    command: ["python", "train.py"]
    ulimits:
      memlock: -1
      stack: 67108864
    shm_size: "8gb"                       # PyTorch DataLoader needs large /dev/shm
```

`shm_size: "8gb"` is the gotcha that costs people days. PyTorch's multiprocess DataLoader uses `/dev/shm`; the default 64MB starves it and causes weird OOMs labeled as "DataLoader worker (pid X) is killed by signal: Bus error."

---

## 7. Devcontainers — the modern superset

VS Code's Devcontainers (`.devcontainer/devcontainer.json`) build on the Compose model:

```json
{
  "name": "ml-stack",
  "dockerComposeFile": ["../compose.yml"],
  "service": "api",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/aws-cli:1": {},
    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {}
  },
  "remoteUser": "vscode",
  "postCreateCommand": "pip install -r requirements-dev.txt"
}
```

Replaces "set up your dev environment in 27 steps from the README" with a one-button "Reopen in Container." Devcontainers run on GitHub Codespaces too — the spec is portable.

For a regulated-finance shop, devcontainers fix the "developer laptop has 8 incompatible Python versions and a different OpenSSL" class of bugs and keep credentials off the host.

---

## 8. Compose in CI

Common pattern: bring up dependencies for integration tests.

```yaml
# .github/workflows/test.yml
jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose -f compose.ci.yml up -d --wait
      - run: pytest tests/integration/
      - run: docker compose -f compose.ci.yml down -v
        if: always()
```

`--wait` blocks until all services with healthchecks become healthy. Without it, tests race past slow startups.

Caveats:
- GitHub Actions runners have limited disk; `docker system prune -a -f` between jobs.
- Don't rely on Compose for parallel test isolation — use `--project-name` to namespace.

---

## 9. Networking in Compose

By default, Compose creates one user-defined bridge network per project. All services on the project share it. Service names resolve via embedded DNS (module 06).

Multi-network patterns:

```yaml
services:
  api:
    networks: [frontend, backend]
  db:
    networks: [backend]
  proxy:
    networks: [frontend]
    ports:
      - "127.0.0.1:80:80"

networks:
  frontend:
  backend:
    internal: true              # no external egress
```

`db` is on `backend` only. `proxy` is on `frontend` only. `api` bridges. `backend` is `internal: true` so even if `db` was compromised, it can't reach the internet.

For an ML server: `model_inference` is on a `data` network with `gpus`; the `api-gateway` is on `frontend`; only `api-gateway` is published.

---

## 10. Compose secret hygiene

```yaml
secrets:
  db_pass:
    file: ./secrets/db_pass.txt              # OK locally, ensure .gitignore
  jwt_signing_key:
    environment: JWT_KEY                     # from env var (v2)
  cloud_secret:
    external: true                           # already exists in Swarm/etc
```

For local dev: keep `./secrets/*.txt` in `.gitignore`. The file is plain text — treat it like a private key.

For staging/prod: move to Vault/AWS Secrets Manager/Key Vault — Compose secrets `file:` does NOT scale beyond a single host.

---

## 11. Compose — the senior-engineer checklist

- [ ] `compose.yml` + `compose.override.yml` separation (dev defaults vs prod overrides).
- [ ] `127.0.0.1:` prefix on every `ports:` entry locally.
- [ ] Every service has a `HEALTHCHECK` (image-level or compose-level).
- [ ] `depends_on.<svc>.condition: service_healthy` everywhere.
- [ ] Secrets via `secrets:`, never `environment:`.
- [ ] `.gitignore` excludes `secrets/`, `.env`, `.env.*`.
- [ ] Volumes named (not anonymous) for clarity.
- [ ] `restart: unless-stopped` only where you want auto-restart; otherwise `restart: no` to expose failures.
- [ ] Profiles for optional dev tools (Jupyter, monitoring).
- [ ] Memory and CPU limits via `deploy.resources` if you care about local fairness.

---

## Sanity check

1. Why is `docker-compose` (with hyphen) deprecated, and what replaced it?
2. What does `depends_on.<svc>.condition: service_healthy` actually wait for, and what supplies that signal?
3. PyTorch DataLoader in a Compose service crashes with "Bus error." What's the one-line fix?
4. Why is `127.0.0.1:8080:8080` better than `8080:8080` for local dev?
5. List three reasons to graduate from Compose to K8s.
6. How do Compose secrets differ from Swarm secrets in terms of at-rest protection?

---

## Sources

- [Compose Specification](https://compose-spec.io/)
- [Compose v2 docs](https://docs.docker.com/compose/)
- [Profiles](https://docs.docker.com/compose/profiles/)
- [Devcontainer spec](https://containers.dev/)
- [NVIDIA Container Toolkit + Compose](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [Kompose (Compose → K8s)](https://kompose.io/)

→ Next: [10 — Container hardening checklist](10_hardening_checklist.md)


\newpage

# 10 — Container hardening checklist

> *"Twenty lines in a `docker run` command separate 'works on my laptop' from 'passes a SOC2 audit.'"*

## Why this module exists

Modules 01–09 covered each primitive in isolation. This module assembles them into the **production-grade defensive `docker run`** that you should be able to recite cold in any senior-engineer interview. Module 22 will re-cast this as Kubernetes `securityContext` + Pod Security Admission `restricted`.

---

## 1. The reference hardened invocation

```bash
docker run \
  --name infer-server-1 \
  --restart unless-stopped \
  \
  # ─── filesystem ────────────────────────────────────────────────
  --read-only \                                       # root FS is RO
  --tmpfs /tmp:size=64m,mode=1777 \                   # writable scratch in RAM
  --tmpfs /var/run:size=16m,mode=755 \                # writable /var/run (some apps need)
  -v model-cache:/var/cache/model:ro \                # named volume, RO
  \
  # ─── identity ──────────────────────────────────────────────────
  --user 10001:10001 \                                # non-root UID:GID
  --group-add 10100 \                                 # supplementary group if needed
  \
  # ─── capabilities ──────────────────────────────────────────────
  --cap-drop ALL \                                    # drop every capability
  --cap-add NET_BIND_SERVICE \                        # only if binding port < 1024
  \
  # ─── syscall / LSM gates ───────────────────────────────────────
  --security-opt no-new-privileges \                  # no setuid escalation
  --security-opt seccomp=default \                    # default seccomp filter
  --security-opt apparmor=docker-default \            # or SELinux on RHEL/AL
  \
  # ─── resources ─────────────────────────────────────────────────
  --memory 2g \
  --memory-swap 2g \                                  # disables swap (== memory)
  --cpus 2.0 \
  --pids-limit 200 \
  --ulimit nofile=4096:8192 \
  \
  # ─── networking ────────────────────────────────────────────────
  --network app-net \                                 # user-defined bridge, not default
  -p 127.0.0.1:8080:8080 \                            # localhost-only port publish
  \
  # ─── lifecycle ─────────────────────────────────────────────────
  --init \                                            # tini as PID 1
  --label org.opencontainers.image.revision=$GIT_SHA \
  \
  myorg/infer:1.2.3@sha256:abc...
```

Every flag has a defensive purpose. If you can explain why each is there, you understand container security at the depth required for a Sr Lead / Architect role.

---

## 2. Annotated rationale

| Flag | Defense |
|---|---|
| `--read-only` | Attacker who lands code can't persist a backdoor in the image FS |
| `--tmpfs /tmp` | Required scratch when root is RO; lives in RAM, cleared on restart |
| `--user 10001:10001` | Process inside is non-root; UID matches volume ownership |
| `--cap-drop ALL` + selective `--cap-add` | Eliminates default 14-capability blanket; least privilege |
| `--security-opt no-new-privileges` | Disables setuid escalation paths |
| `--security-opt seccomp=default` | Blocks ~50 historical/dangerous syscalls |
| `--security-opt apparmor=docker-default` | Filesystem path restrictions |
| `--memory` + `--memory-swap=<same>` | Hard memory cap; no swap-spill bypass |
| `--cpus` | CPU share cap; fair scheduling |
| `--pids-limit` | Fork bomb mitigation |
| `--network <user-defined>` | DNS resolution + isolation from other projects |
| `-p 127.0.0.1:8080:8080` | Not exposed to LAN/internet; reverse proxy in front |
| `--init` | `tini` PID 1 handles signals + zombie reaping |
| Pinned image digest (`@sha256:...`) | Tag-floating attacks impossible; reproducible deploy |

---

## 3. Compose equivalent

```yaml
services:
  api:
    image: myorg/infer:1.2.3@sha256:abc...
    read_only: true
    tmpfs:
      - /tmp:size=64m,mode=1777
      - /var/run:size=16m,mode=755
    user: "10001:10001"
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    security_opt:
      - no-new-privileges:true
      - seccomp:default
      - apparmor:docker-default
    deploy:
      resources:
        limits:
          memory: 2g
          cpus: "2.0"
          pids: 200
    pids_limit: 200                # works without swarm/deploy mode
    ports:
      - "127.0.0.1:8080:8080"
    networks: [app-net]
    init: true
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/healthz"]
      interval: 15s
      retries: 5
    restart: unless-stopped
```

---

## 4. The 20-point production checklist

Print this and use it in PR reviews:

### Image
- [ ] Image pinned by digest, not floating tag
- [ ] Built from distroless or Chainguard base (no shell, no apt)
- [ ] Multi-stage build; no compilers in final stage
- [ ] `.dockerignore` excludes `.git`, `.env*`, secrets, `~/.aws`, `~/.ssh`
- [ ] No `ENV` or `ARG` for secrets; build secrets via BuildKit `--mount=type=secret`
- [ ] `USER` directive set to non-root before `ENTRYPOINT`
- [ ] Signed with Cosign; SBOM attached as attestation
- [ ] Trivy/Grype scan clean for HIGH/CRITICAL (or explicit allowlist with justification)

### Runtime
- [ ] `--user <non-root>` (or image's `USER` set)
- [ ] `--read-only` root filesystem with explicit `--tmpfs` for writable paths
- [ ] `--cap-drop=ALL` + minimal `--cap-add`
- [ ] `--security-opt no-new-privileges`
- [ ] Default seccomp profile (or stricter custom)
- [ ] Default AppArmor/SELinux profile applied
- [ ] `--memory`, `--memory-swap` (equal), `--cpus`, `--pids-limit` set
- [ ] No `--privileged` flag
- [ ] No `--network host` (unless dedicated infra DaemonSet)
- [ ] `127.0.0.1:` prefix on published ports (or proper firewall + LB)
- [ ] `--init` for proper PID 1 semantics

### Volumes
- [ ] No `docker.sock` mount
- [ ] No `/`, `/etc`, `/home`, `~`, host-config bind mounts
- [ ] Bind mounts read-only where possible
- [ ] Named volumes for state
- [ ] SELinux `:Z` suffix on RHEL/AL2 bind mounts
- [ ] Secrets via `--secret` (Swarm) / mounted file / Vault agent — never `-e PASSWORD=`

### Network
- [ ] User-defined bridge or overlay; not default bridge
- [ ] Egress filtered (DOCKER-USER chain or VPC SG)
- [ ] IMDS (`169.254.169.254`) blocked from non-AWS-aware containers OR IMDSv2-only with hop-limit=1
- [ ] No exposed Docker daemon TCP socket
- [ ] If reverse proxy in front, TLS terminated; container speaks plain to LB

### Logging & monitoring
- [ ] Logs captured by daemon log driver (`json-file` with `max-size` or shipped to centralized)
- [ ] Health endpoint defined
- [ ] Runtime security (Falco) installed on host

---

## 5. Privileged escape paths — what each defense actually prevents

A typical "container compromised → host compromised" path:

```
1. Code execution in container (RCE in app)
   ↓ blocked by: read-only FS limits persistence
2. Read sensitive files
   ↓ blocked by: --cap-drop ALL (no CAP_DAC_OVERRIDE), AppArmor/SELinux paths
3. Privilege escalation via setuid binary
   ↓ blocked by: --security-opt no-new-privileges
4. Spawn child processes / fork bomb
   ↓ blocked by: --pids-limit
5. Memory pressure host
   ↓ blocked by: --memory + --memory-swap
6. Network pivot to IMDS, internal services
   ↓ blocked by: DOCKER-USER chain, IMDSv2 hop-limit=1, NetworkPolicy
7. Mount host filesystem
   ↓ blocked by: --cap-drop ALL (no CAP_SYS_ADMIN), no /var/run/docker.sock
8. Container escape via kernel bug
   ↓ partially mitigated by: seccomp, default AppArmor — only runtime sandbox (gVisor/Kata) fully closes this
```

Each defense closes one layer. Stacked, they make escape uneconomical for opportunistic attackers and require nation-state-grade chains for targeted attackers.

---

## 6. What CIS Docker Benchmark actually wants

CIS Docker Benchmark v1.7.0 (July 2024) has 116 controls across 7 sections. The high-impact 20:

1. Audit log enabled on `/var/lib/docker`, `/etc/docker`, `/usr/bin/dockerd`.
2. Docker daemon runs as non-root user (rootless mode).
3. No insecure registries configured.
4. TLS auth enabled if daemon TCP socket exposed.
5. `userns-remap` enabled.
6. Live restore enabled (`--live-restore`).
7. Default network bridge not used.
8. Trusted base images (signed, scanned).
9. `HEALTHCHECK` in every image.
10. No `latest` tags in production.
11. `USER` directive in every Dockerfile.
12. No add of trusted CAs except via Dockerfile.
13. No `--privileged` containers.
14. No `--network host`.
15. AppArmor or SELinux profile applied.
16. Seccomp profile applied.
17. `no-new-privileges` set.
18. `--read-only` root filesystem.
19. Mount propagation set to `rslave` (not `shared`) where applicable.
20. Containers run with `--restart=on-failure:5` (not `--restart=always`).

Run `docker-bench-security` (a script that automates these checks) on any host before declaring it production-ready:

```bash
docker run --rm --net host --pid host --userns host --cap-add audit_control \
  -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
  -v /etc:/etc:ro \
  -v /var/lib:/var/lib:ro \
  -v /usr/bin/containerd:/usr/bin/containerd:ro \
  -v /usr/bin/runc:/usr/bin/runc:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  --label docker_bench_security \
  docker/docker-bench-security
```

---

## 7. The reality check

This checklist will fail on developer laptops. That's intentional — laptops are not production. But every divergence between dev and prod should be **explicit, justified, and minimized**. The closest you can keep them, the fewer "works on my machine" surprises and the smaller the compromise surface during local dev.

For Capital One–style postures, the K8s-level equivalent (PSA `restricted` + admission control) is what enforces the checklist at scale (modules 22, 23). Docker `run` hardening matters for ECS tasks, Cloud Run revisions, ACI containers, and any single-host deployment.

---

## Sanity check

1. Why is `--memory-swap` paired with `--memory` more secure than `--memory` alone?
2. Which combination of flags prevents a container from reading `/etc/shadow` even if its process is root?
3. Why is image-pinning by digest a security control, not just a hygiene thing?
4. List the three runtime sandboxes (Docker / OCI) that close the "kernel CVE → host compromise" gap that vanilla runc leaves open.
5. What does `--init` actually do, and why does the default Python container often need it?

---

## Sources

- [CIS Docker Benchmark v1.7.0](https://www.cisecurity.org/benchmark/docker)
- [`docker-bench-security`](https://github.com/docker/docker-bench-security)
- [NIST SP 800-190 — Application Container Security Guide](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-190.pdf)
- [OWASP Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html)
- [Docker daemon security](https://docs.docker.com/engine/security/)

→ Next: [11 — CIS Docker Benchmark + common CVEs](11_cis_cves.md)


\newpage

# 11 — CIS Docker Benchmark + the must-know container CVEs

> *"Every container CVE worth memorizing fails one of the three classes: namespaces, capabilities/syscalls, or the daemon trust boundary. Anchor the story to the class."*

## Why this module exists

A senior engineer must be able to:

1. Walk an interviewer through the **CIS Docker Benchmark** structure and the top controls.
2. Recall the **canonical container CVEs**, their root cause, the fix, and the lesson learned.
3. Map each CVE to a layer of defense from module 10.

This module is intentionally compact — a reference card you should know cold.

---

## 1. CIS Docker Benchmark structure

CIS Docker Benchmark v1.7.0 (July 2024) has **116 recommendations across 7 sections**. Each rec has:

- **Level 1**: should-have, low operational cost.
- **Level 2**: defense in depth, may impact functionality.
- Automated check status (yes/no).

| Section | Approx count | Focus |
|---|---:|---|
| 1. Host Configuration | 14 | Audit rules on Docker paths, separate partition for `/var/lib/docker`, kernel version |
| 2. Docker Daemon Configuration | 21 | TLS on TCP socket, `userns-remap`, no insecure registries, `--live-restore` |
| 3. Docker Daemon Configuration Files | 11 | Permissions on `/etc/docker/*`, `daemon.json` ownership |
| 4. Container Images and Build Files | 12 | `HEALTHCHECK`, `USER`, trusted base images, no secrets in env |
| 5. Container Runtime | 38 | All the `docker run` flags from module 10 |
| 6. Docker Security Operations | 4 | Image scanning, no orphan images |
| 7. Docker Swarm Configuration | 8 | Swarm-only; skip if you don't use Swarm |

`docker-bench-security` (a Docker-supplied script) automates ~90 of these. Run it on every prod host quarterly.

---

## 2. The CVE roll call — what you must know

### 2.1 CVE-2019-5736 — runc container escape via `/proc/self/exe`

**Year**: Feb 2019. **CVSS**: 8.6 High. **Layer**: runc binary integrity.

**The bug**: When a container executed `/proc/self/exe` (which points to the host's `runc` binary), it could overwrite the host's `runc` from inside the container. Next time runc was invoked (for any container), it ran the attacker's payload as root on the host.

**The fix**: runc copy-on-write of itself before exec (runc ≥ 1.0-rc6). All distros patched in days.

**The lesson**: runc binary integrity is part of the trust boundary. A read-only host `runc` + a non-shared `/proc` namespace would not have fully prevented this. The class of bug — **the runtime binary is reachable from inside the container** — is structural.

### 2.2 CVE-2022-0185 — Linux kernel `fs_context` heap overflow

**Year**: Jan 2022. **CVSS**: 8.4 High. **Layer**: kernel + USER namespace.

**The bug**: A heap overflow in the kernel's filesystem context parsing (`legacy_parse_param`) was reachable from inside a USER namespace. A container with USER namespace enabled (rootless) could trigger CAP_SYS_ADMIN inside the namespace, then chain to host root.

**The fix**: kernel patch + most distros backported.

**The lesson**: USER namespaces gave attackers **more** kernel surface (more code paths reachable as "uid 0"), not less. This is a tension: USER namespaces close one class of bug (UID-based container-root-on-host) while opening another (kernel code that assumes "root means sysadmin, not 'root in some namespace'").

### 2.3 CVE-2024-21626 — "Leaky Vessels" runc working-directory leak

**Year**: Jan 2024. **CVSS**: 8.6 High. **Layer**: runc fd inheritance.

**The bug**: runc could leak its own working directory file descriptor into the container process. The container could `cd` to `/proc/self/fd/<N>` and access paths outside its mount namespace, including the host root filesystem.

**The fix**: runc ≥ 1.1.12. Three companion CVEs in BuildKit (CVE-2024-23651, -23652, -23653) followed similar patterns.

**The lesson**: file descriptor inheritance across the runtime/container boundary is a structural risk. Modern runtimes (gVisor, Kata) close this by isolating syscall/fd handling entirely.

### 2.4 CVE-2018-15664 — Docker `cp` symlink TOCTOU

**Year**: 2018. **CVSS**: 7.5 High. **Layer**: dockerd file API.

**The bug**: `docker cp` was vulnerable to a time-of-check-to-time-of-use race. Container could replace the source path with a symlink during the copy, causing Docker to copy host files out.

**The fix**: dockerd patched to resolve paths atomically.

**The lesson**: any API that lets the container influence host file access is a TOCTOU candidate.

### 2.5 CVE-2017-1002101 / 1002102 — Kubernetes `subPath` symlinks

**Year**: 2018. **Layer**: kubelet volume handling.

**The bug**: `volumeMounts.subPath` was resolved relative to the container's view; symlinks in the container could redirect the mount to host paths.

**The lesson**: subPath is dangerous; PSA `restricted` and CIS K8s benchmark discourage it.

### 2.6 CVE-2022-23648 — containerd CVE-2022-23648 race

**Year**: Feb 2022. **Layer**: containerd image extraction.

**The bug**: containerd unpacked image layers with symlink races, allowing image layers to write outside the image rootfs at unpack time. An attacker who controlled the image (a public, popular image) could plant arbitrary files at host paths on every node that pulled it.

**The fix**: containerd ≥ 1.6.1.

**The lesson**: image pulls are not passive. The trust boundary includes the registry and image author.

---

## 3. Real incidents that taught the industry

### 3.1 Tesla cryptojacking, Feb 2018

**Root cause**: A Kubernetes dashboard was deployed without authentication on a Tesla AWS Kubernetes cluster. Attackers found it via Shodan, deployed cryptominer pods, used AWS credentials they discovered in pod env vars to access S3 telemetry data.

**Lessons**:
- Never expose K8s dashboard publicly without auth.
- Don't put AWS creds in pod env vars — use IRSA.
- Egress filtering would have prevented the cryptominer from reaching mining pools.
- Cluster discovery via Shodan is real.

This incident is **why** K8s Dashboard 2.x added mandatory auth and **why** IRSA / Workload Identity exist.

### 3.2 Capital One, July 2019

Already covered in module 06. Re-framing for this module:

- **App layer**: SSRF.
- **Network layer**: container/host had access to IMDSv1 at `169.254.169.254`.
- **Identity layer**: WAF instance had over-permissive IAM role.
- **Storage layer**: S3 buckets readable across accounts/services.

The lesson for container engineers: **the IMDS endpoint is part of every container's egress surface unless you explicitly cut it**. IMDSv2 hop-limit=1 is the standard answer; module 13 will revisit.

### 3.3 Codecov breach, Apr 2021

Codecov's Bash uploader image was compromised. Attackers modified the upload script to exfiltrate environment variables — full of CI secrets — to a server they controlled. Multiple downstream companies were breached via the harvested credentials.

**Lesson**: an image (even a CI helper) is a supply-chain artifact. Pin by digest, monitor for changes, prefer first-party-built images.

### 3.4 PyPI `colorama` / `crypto-tools` typosquats, 2023–2024

Hundreds of typosquatted packages on PyPI installed malicious code that ran at `pip install` time. ML containers that pulled "the latest" of common packages without lockfile-pinning shipped backdoors to production.

**Lesson**: lockfile + hash pinning + private PyPI mirror with strict precedence.

---

## 4. Falco rules — runtime detection of the lessons above

Falco rules (module 25 covers Falco in depth) detect *behavioral* signs of these CVE classes:

```yaml
# Detect a container writing to /proc/self/exe (CVE-2019-5736 family)
- rule: Write to /proc/self/exe
  desc: A container wrote to /proc/self/exe, suggestive of runc-overwrite escape
  condition: open_write and fd.name startswith "/proc/" and fd.name endswith "/exe"
  output: "Container wrote to /proc/self/exe (user=%user.name container=%container.name)"
  priority: CRITICAL

# Detect IMDS access from a container (Capital One pattern)
- rule: Container contacted IMDS
  desc: A container attempted to reach AWS/GCP/Azure IMDS
  condition: outbound and fd.sip in (169.254.169.254)
  output: "Container reached IMDS (container=%container.name proc=%proc.cmdline)"
  priority: WARNING
  exceptions:
    - name: imds_allowlisted_containers
      fields: [container.image.repository]
      values: ["aws-load-balancer-controller", "cloud-init-helper"]

# Detect docker.sock mount inside a container
- rule: docker socket mounted
  desc: A container has /var/run/docker.sock bound
  condition: container and fd.name = /var/run/docker.sock
  output: "docker.sock mounted in container (image=%container.image.repository)"
  priority: CRITICAL
```

---

## 5. The 2025–2026 container threat landscape

Three trends to know:

1. **AI-assisted typosquats**: LLM-generated typosquat package names that pass surface-level reviews. Lockfile + hash pinning is the only defense.
2. **Supply-chain attacks against base image maintainers**: e.g., a maintainer of a popular Docker Hub image has their account compromised, ships a poisoned `:latest`. Mitigation: pin by digest, monitor digest changes, use Chainguard or similarly attested images.
3. **GPU-driver CVEs**: CUDA / NVIDIA driver bugs reachable from a GPU container — `--gpus all` is the new privileged escalation primitive in ML environments. Mitigation: NVIDIA Container Toolkit ≥ 1.16, GPU Operator with patched DCGM, no `--privileged` on GPU pods.

---

## 6. Patch cadence and your obligation

For each CVE class above, the patch-cadence requirements (typical regulated-finance shop):

- **Critical (CVSS ≥ 9.0)**: 7 days to patch.
- **High (7.0–8.9)**: 30 days.
- **Medium (4.0–6.9)**: 90 days.
- **CISA KEV** (known exploited): 14 days regardless of CVSS.

For container runtimes (runc, containerd), the patch path is host-OS-level — your job as an architect is to ensure the platform team has the cadence. For images you build: rebuild on a schedule (Chainguard does this daily), re-scan, re-promote.

---

## Sanity check

1. Map each of these CVEs to the defense layer that would have prevented or contained it:
   - CVE-2019-5736
   - CVE-2024-21626
   - Capital One 2019
   - Tesla 2018
2. What's the practical difference between CIS Docker Benchmark Level 1 and Level 2?
3. Why is the `docker-bench-security` script invocation so complex (lots of `-v` mounts)? What does each mount give it visibility into?
4. Why is `--gpus all` a heightened risk in 2025–2026 vs 2020?
5. A regulated shop discovers a CISA KEV-listed High in a base image still on prod nodes. By when must they patch?

---

## Sources

- [CIS Docker Benchmark v1.7.0 (July 2024)](https://www.cisecurity.org/benchmark/docker)
- [`docker-bench-security`](https://github.com/docker/docker-bench-security)
- [Snyk Labs — Leaky Vessels disclosure](https://labs.snyk.io/resources/leaky-vessels-docker-runc-container-breakout-vulnerabilities/)
- [NVD entry for CVE-2019-5736](https://nvd.nist.gov/vuln/detail/CVE-2019-5736)
- [NVD entry for CVE-2024-21626](https://nvd.nist.gov/vuln/detail/CVE-2024-21626)
- [Tesla cryptojacking incident (RedLock report, Feb 2018)](https://www.cnbc.com/2018/02/21/hackers-hijack-teslas-cloud-system-to-mine-cryptocurrency-redlock.html)
- [Capital One OCC consent order, Aug 2020](https://www.occ.treas.gov/news-issuances/news-releases/2020/nr-occ-2020-101a.pdf)
- [Falco rules](https://falco.org/docs/concepts/rules/)
- [CISA KEV Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)

→ Next: [12 — **Data exposure — on-premise**](12_data_exposure_onprem.md)


\newpage

# 12 — Data exposure for containers — on-premise patterns

> *"On-prem doesn't mean 'less security' — it means **you** own every layer of the trust boundary, with no AWS / GCP / Azure to lean on. Get the storage right and the rest follows."*

## Why this module exists

This is the first of four cloud-targeted deep dives requested by the user: "Cover all possible scenarios on how people use and expose data within Docker containers safely and securely. Cover this for on-premise, AWS, GCP, Azure."

On-prem is where the storage ecosystem is most diverse — NFS, CIFS, iSCSI, Ceph, GlusterFS, MinIO, Portworx, Longhorn, NetApp, Dell EMC PowerScale (Isilon), Pure FlashBlade. Each is a different trust model and a different way to fail. This module walks the full landscape, plus the cross-cutting concerns: encryption at rest, encryption in transit, key management without KMS, backups, air-gap, registries, and the regulated-finance posture.

We cover **Docker-on-host** here; on-prem Kubernetes is covered in module 29.

---

## 1. The storage taxonomy on-prem

### 1.1 File vs Block vs Object

| Kind | Protocols | Example backends | Container exposure pattern |
|---|---|---|---|
| **File (shared)** | NFSv3/v4, SMB/CIFS | NetApp, Isilon, GlusterFS, CephFS | Mount via Docker `local` driver with NFS opts, or `volume-driver` (legacy) |
| **Block** | iSCSI, FC, FCoE, NVMe-oF | NetApp SAN, Pure FlashArray, Dell PowerStore, Ceph RBD | Map iSCSI LUN to host, mkfs, bind-mount or volume |
| **Object** | S3 API, Swift | MinIO, Ceph RGW, Cloudian, Hitachi HCP | Pull/push via SDK; or mount via FUSE (s3fs, goofys) — slow, lossy |

### 1.2 Why this matters for containers

Containers prefer **file** or **object** storage. Block storage requires host-level mkfs + mount before bind-mounting into a container, which couples container lifecycle to host state — fragile.

For ML, the dominant pattern on-prem is **NFS to all training nodes**, with object storage (MinIO/Ceph RGW) holding model artifacts and large dataset archives. Spark/Iceberg/Delta workloads talk **S3 protocol** to MinIO or Ceph RGW.

---

## 2. NFS — the universal on-prem default

### 2.1 NFS volume in Docker

```bash
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=10.0.10.50,rw,vers=4.1,sec=sys,nconnect=8 \
  --opt device=:/exports/ml-data \
  ml-data

docker run -v ml-data:/data -e DATA_DIR=/data myorg/train:1.0
```

Critical options:

| Option | Default | Production setting | Why |
|---|---|---|---|
| `vers=` | varies | `4.1` (or `4.2`) | Modern stateful ACL support, parallel I/O via pNFS |
| `sec=` | `sys` | `krb5p` for sensitive data | `sys` is UID-trust on the wire (easily spoofed); `krb5p` is Kerberos + integrity + privacy |
| `nconnect=` | 1 | 4–16 | Multiple TCP connections per mount; massive throughput win for large reads |
| `hard,intr` | hard | `hard,intr` | Hang waiting on server (not silent corruption) on outages |
| `noatime` | off | `noatime` | Avoid update-on-read metadata storms |
| `rsize/wsize` | 1MB | 1MB or 4MB depending on backend | Larger reads, fewer round trips |

### 2.2 NFS auth — the AUTH_SYS trap

Default `sec=sys` means the client tells the server "I'm UID 1000" and the server trusts that. Anyone with root on the client (which is the host running Docker) can claim any UID. **This is not authentication; it's a convention.**

For regulated data, three options:

1. **`sec=krb5p`** — Kerberos auth + on-wire encryption. Requires KDC infra (typically AD).
2. **Network isolation** — put the NFS storage VLAN behind firewalls reachable only from blessed hosts.
3. **NFSv4 ACLs + per-host export rules** — each host only mounts what it needs; per-export root-squash to nobody.

For a Capital One–style regulated shop on-prem, **`sec=krb5p` + per-export root-squash + network-isolated storage VLAN** is the minimum.

### 2.3 UID/GID alignment

NFS reads/writes succeed based on UID/GID match between the container process and the file on the NFS server. Three common patterns:

- **All-hosts-converge**: every container that needs to access `ml-data` runs as UID 10001:10001; the NFS export is chown'd 10001:10001. Simple, brittle to multiple teams.
- **Per-team namespaces**: each ML team has a dedicated UID range; NFS exports per-team-dir with that UID's ACL. Scales better.
- **idmapd + NFSv4 names**: Linux `idmapd` maps remote NFSv4 names (`alice@CORP.EXAMPLE`) to local UIDs. Requires Kerberos and aligned name service.

### 2.4 NFS performance for ML training

For multi-node training where 8–256 GPUs read the same dataset:

- **`nconnect=16`** is the single biggest knob.
- **NFS pNFS (Parallel NFS)** with backends like NetApp ONTAP, Dell PowerScale (formerly Isilon), or BeeGFS gives parallel-stripe reads — same multi-GB/s as Lustre, less operational pain.
- For *very* large training (1k+ GPU), **Lustre** beats NFS. AWS FSx for Lustre is the cloud sibling.

### 2.5 NFS encryption at rest

NFS protocol itself doesn't encrypt at rest — that's the backend's job. NetApp Volume Encryption (NVE), Dell PowerScale at-rest encryption, CephFS via LUKS-backed OSD disks, etc. Without backend at-rest encryption, a stolen disk is a data breach.

---

## 3. CIFS / SMB — the Windows-shop default

For shops running file servers on Windows or where users access the same shares from Windows + Linux + containers:

```bash
docker volume create \
  --driver local \
  --opt type=cifs \
  --opt o=username=svc-mlpipe,password=...,uid=10001,gid=10001,vers=3.1.1 \
  --opt device="//fileserver.corp.example/ml-shared" \
  ml-shared
```

- `vers=3.1.1` is the modern dialect — has end-to-end encryption.
- Avoid putting passwords in volume options; bind-mount a credentials file instead.
- For Active Directory shops, Kerberos with `sec=krb5` is preferred over user/password.

CIFS is generally slower than NFS for large-file reads. For ML training, prefer NFS or object storage even in mixed Win/Linux shops.

---

## 4. iSCSI / FC / NVMe-oF — block storage to the host

Block storage is **mounted to the host**, then bind-mounted (or volume-mounted) into the container. The container never sees iSCSI directly.

```bash
# On the host
iscsiadm -m discovery -t st -p 10.0.20.50
iscsiadm -m node -T iqn.2026-05.com.example:lun.5 -l
mkfs.xfs /dev/sda
mount -o noatime /dev/sda /mnt/ml-block

# Now bind-mount or named-volume bind that path
docker run -v /mnt/ml-block:/data myorg/train:1.0
```

For containers this is just a bind mount; the container has no awareness of the underlying iSCSI session. Implications:

- **Host outage** = the data is unmounted, but a different host can re-attach the LUN (with multipathing).
- **Multi-host concurrent write**: NOT supported on a normal block FS. Use a clustered FS (GFS2, OCFS2) or a clustered block storage (Ceph RBD with appropriate locking) if you need RWX. Or skip block — file is what you want.
- **Encryption at rest**: LUKS on the block device. The host has the key (or KMS-backed via Clevis + Tang). Containers see decrypted files.

Block storage suits **single-writer, high-IOPS** workloads — Postgres, MySQL data dirs, Vault's storage backend. Not the right primitive for shared training data.

---

## 5. Ceph — the OSS distributed-storage answer

Ceph provides three interfaces:

- **CephFS** — POSIX file (RWX); NFS-compatible.
- **Ceph RBD** — block (one writer).
- **Ceph RGW** — S3-compatible object storage.

For containers:

- **CephFS** via NFS gateway or via CephFS kernel client on the host. Works with Docker's NFS volume driver.
- **RBD** mapped to host, then mounted into container (same pattern as iSCSI).
- **RGW** accessed via S3 SDK from the container; or mounted via `goofys`/`s3fs` (FUSE).

Ceph is operationally heavy. For ML on-prem with budget, **Rook-Ceph on K8s** (module 29) is what you'll meet most. For Docker-on-VM, NFS appliances (NetApp/Isilon) usually win on operational sanity.

---

## 6. MinIO — S3 protocol on-prem

[MinIO](https://min.io/) is the dominant on-prem S3-compatible object store. Single binary, K8s-native operator, drop-in for S3 SDKs. Used by:

- **Spark / Iceberg / Delta** for the storage layer (`s3a://bucket/path` with MinIO endpoint override).
- **Model artifact stores** (MLflow's S3 backend).
- **Vault snapshots**, **Velero backup targets**, **Loki object backend**, **Tempo** — basically anywhere "S3" is the protocol.

Container access pattern:

```bash
# In the container's env (or via secrets file)
AWS_ACCESS_KEY_ID=minio-svc-mlpipe
AWS_SECRET_ACCESS_KEY=...
AWS_ENDPOINT_URL_S3=https://minio.corp.example:9000
S3_BUCKET=ml-artifacts
```

```python
import boto3
s3 = boto3.client("s3", endpoint_url=os.environ["AWS_ENDPOINT_URL_S3"])
s3.upload_file("model.pt", "ml-artifacts", "models/2026/v1/model.pt")
```

The app uses the **standard boto3 SDK** with the endpoint override. No FUSE, no kernel-side mounts. This is the cleanest container-data pattern on-prem and the one most regulated shops adopt.

### 6.1 MinIO security

- **TLS mandatory** in production. Self-signed CA OK for internal; install CA bundle in container at `/etc/ssl/certs/internal-ca.pem`.
- **MinIO Identity & Access Management (IAM)** — AWS-compatible JSON policies. Use STS for short-lived credentials.
- **Encryption at rest** — MinIO supports SSE-S3 (server-side, MinIO-managed key) and SSE-KMS (with HashiCorp Vault as KMS). Use SSE-KMS for compliance.
- **Object Lock + Retention** for WORM (write-once-read-many) compliance use cases — same API as S3.
- **Auditing** — MinIO audit logs to a webhook or to Kafka. Ship to SIEM.

### 6.2 MinIO + Vault for short-lived credentials

The production pattern: app authenticates to Vault (via AppRole / Kubernetes auth / TLS cert), Vault issues a 1-hour MinIO access key. App uses it via boto3. Vault rotates automatically.

```bash
vault read minio/creds/ml-pipeline-role
# Returns: access_key, secret_key, lease_duration=3600
```

No long-lived secrets in containers. This is the on-prem equivalent of IRSA / Workload Identity Federation.

---

## 7. The on-prem volume driver alternatives

Beyond NFS/CIFS/iSCSI, three plugin ecosystems matter on-prem:

### 7.1 Portworx (Pure Storage)

Commercial, K8s-first but has Docker plugin. Block storage atop your existing disks (DAS / SAN / SSDs). Features:

- Storage classes per workload (gold = SSD replicated, silver = HDD).
- Snapshots, clones, sync replication across DCs.
- Per-volume encryption with PX-Backup integration.
- BYOK with Vault KMS.

Adopt when: K8s-centric ML platform, need disaster-recovery-grade primitives.

### 7.2 Longhorn (Rancher / SUSE)

OSS, CNCF Incubating. K8s-first (DaemonSet on each node). Each volume is a striped replicated block device backed by the local disks of N nodes. Features:

- Snapshots + backups to S3 (or MinIO) compatible target.
- Volume encryption via LUKS.
- Multi-region replication via DR.

Adopt when: low budget, K8s on bare-metal, willing to operate the OSS.

### 7.3 OpenEBS (Mayastor / cStor / Jiva engines)

OSS, CNCF Sandbox. K8s-first. Multiple engines for different performance profiles (Mayastor = NVMe-fabric for performance, cStor = ZFS-based for snapshots, Jiva = simple per-node).

Adopt when: K8s on bare metal, need NVMe performance, OK with operating CNCF sandbox.

For pure Docker (no K8s) on-prem, **NFS + MinIO + iSCSI for stateful DBs** is the most-operated pattern. Portworx/Longhorn/OpenEBS shine in K8s (module 29).

---

## 8. Encrypting data at rest without a cloud KMS

The cloud's biggest hidden gift is KMS — managed key storage with hardware HSMs. On-prem, you have three paths:

### 8.1 Self-hosted Vault Transit / KMS

HashiCorp Vault's `transit` engine acts as a KMS: applications send plaintext for encryption, receive ciphertext, and the key never leaves Vault. Backed by an in-cluster HSM or by Vault's `auto-unseal` against an actual HSM (Thales, Entrust).

Pattern: container fetches the data encryption key (DEK) from Vault Transit, encrypts/decrypts data locally; the DEK is wrapped by a key encryption key (KEK) that never leaves Vault.

### 8.2 LUKS on storage volumes

For host-level disk encryption: LUKS (Linux Unified Key Setup) with key in Vault. `clevis` automates LUKS unlock against `tang` (a network presence service); a host can boot only when it can reach `tang`. This means a stolen disk is unreadable; a stolen host without network access is unreadable.

### 8.3 Storage appliance native encryption

NetApp NVE, Dell PowerStore native encryption, Pure FlashArray DARE. The storage controller handles encryption at rest; key management often integrates with Vault, Thales, or Entrust.

For a regulated-finance shop on-prem, **defense in depth**: storage-controller encryption + LUKS on dedicated volumes + Vault Transit for application-level field encryption (PII).

---

## 9. Backups

Container data backup on-prem:

- **For NFS/CephFS**: storage-controller snapshots (NetApp Snapshots, Ceph FS snapshots) + replicate snapshots to a backup site or to MinIO via `restic`.
- **For block volumes**: storage-controller snapshots + LVM thin snapshots; ship to backup with `borgbackup` / `restic`.
- **For MinIO**: bucket replication to a DR MinIO cluster.
- **For container state**: `restic` from inside a backup container — `docker run --rm -v mydata:/data:ro -v backup-cache:/cache restic/restic ...`

For K8s on-prem (module 29), **Velero** is the standard with CSI snapshots.

---

## 10. Air-gap and the private registry mirror

Many regulated shops are **air-gapped**: no internet from production. Two implications for containers:

1. **No Docker Hub / Quay / GHCR pulls in prod.** All images must come from a self-hosted registry (Harbor, JFrog Artifactory, ECR/GAR/ACR if running an on-prem-mirror service).
2. **PyPI / npm / Maven mirrors.** Sonatype Nexus or JFrog Artifactory or pypiserver mirrors that are sync'd from upstream via a controlled "diode."

Pattern:
- DMZ host with internet pulls upstream images, scans, signs.
- Promotes by digest into the air-gapped registry.
- Production hosts pull only from air-gapped registry.

CI/CD inside the air gap needs:
- Hermetic builders (no internet egress allowed).
- Pinned dependencies in lockfiles.
- All build tooling pre-pulled.

---

## 11. On-prem container egress controls — IMDS-equivalent risks

On-prem doesn't have IMDS, but it has analogues:

- **Service accounts on shared file systems**: if a container has access to a host path containing service-account JSON keys (`/etc/secrets/gcp-sa.json` left over from migration), it can pivot.
- **Internal-only services like config servers**: a Vault server reachable from one container is reachable from any compromised container on the same network. Egress filter to `vault.corp.example:8200` per container via `iptables` / `nftables` in the DOCKER-USER chain.
- **DNS resolvers** as a covert channel: lock down DNS to your internal resolver and monitor query patterns.

The principle: **egress is a security control, not an availability one.** Default-deny outbound; explicitly allow per workload.

---

## 12. Pulling it together — the on-prem ML data architecture

A defensible reference architecture for ML containers on-prem:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Production VLAN (containers)                                   │
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │ training pod │    │ inference pod│    │ pipeline pod │      │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│          │ NFS krb5p          │ S3                │ DB           │
│          │ /data              │ via boto3         │ via PgBouncer│
└──────────┼───────────────────┼───────────────────┼──────────────┘
           │                   │                   │
   ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
   │ NetApp ONTAP │    │ MinIO cluster│    │ PgBouncer +  │
   │ + NVE        │    │ + Vault KMS  │    │ Postgres HA  │
   │ + Snapshots  │    │ + bucket repl│    │ + LUKS       │
   └──────────────┘    └──────────────┘    └──────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │ Vault       │
                                            │ (Transit +  │
                                            │  K8s auth + │
                                            │  HSM-unseal)│
                                            └─────────────┘
```

Cross-cuts:

- **Image source**: Harbor on-prem, replicated from DMZ-Harbor (which pulls upstream).
- **Identity**: Vault K8s auth (for K8s) or AppRole (for VMs).
- **Secrets**: Vault Transit + dynamic credentials, not static.
- **Audit**: Falco + audit log shipped to SIEM.
- **Egress**: DOCKER-USER chain + per-VLAN firewall; default-deny outbound.
- **DR**: NFS snapshots replicated to DR site; MinIO bucket replication; Vault Raft replicated.

---

## Sanity check

1. What does `sec=sys` actually trust, and why isn't that authentication?
2. Why does `nconnect=8` materially change ML training throughput on NFS?
3. iSCSI is mounted to the host, then bind-mounted into the container. Why does that mean iSCSI is NOT suitable for multi-host RWX use cases?
4. What does MinIO's SSE-KMS need that SSE-S3 does not, and why does compliance often require SSE-KMS?
5. How does Vault Transit differ architecturally from Vault's regular KV engine for handling encryption?
6. In an air-gapped shop, name three categories of external dependency that must have on-prem mirrors.

---

## Sources

- [Linux NFS docs](https://www.kernel.org/doc/Documentation/filesystems/nfs/)
- [SMB/CIFS man page](https://linux.die.net/man/8/mount.cifs)
- [MinIO docs](https://min.io/docs/minio/)
- [HashiCorp Vault Transit](https://developer.hashicorp.com/vault/docs/secrets/transit)
- [Rook-Ceph](https://rook.io/)
- [Longhorn](https://longhorn.io/)
- [OpenEBS](https://openebs.io/)
- [Portworx](https://portworx.com/)
- [Tang & Clevis](https://github.com/latchset/tang)
- [Velero](https://velero.io/)

→ Next: [13 — **Data exposure — AWS**](13_data_exposure_aws.md)


\newpage

# 13 — Data exposure for containers — AWS

> *"Capital One 2019 was a single missing config: `MetadataHttpTokens=required` and `http_put_response_hop_limit=1`. Everything else amplified it."*

## Why this module exists

The user's explicit ask: how to use and expose data within Docker containers safely on AWS. This module covers Docker-on-EC2 + ECS (EC2 + Fargate). EKS gets its own deep dive in module 26.

The AWS data-exposure story has five mandatory disciplines:

1. **No long-lived AWS credentials in containers** — use IAM roles via IMDS or task roles.
2. **IMDSv2-only with hop limit = 1** — the Capital One lesson.
3. **VPC endpoints** for S3 and other services to keep traffic off the public internet.
4. **KMS** for encryption at rest, with CMKs for compliance.
5. **Bucket policies + S3 Block Public Access** as last-line defense.

---

## 1. Identity — how containers get AWS credentials

### 1.1 EC2 instance profile (the foundation)

An EC2 instance can have an **IAM instance profile** attached. The role's credentials are exposed via the **Instance Metadata Service (IMDS)** at `http://169.254.169.254/`. Any process on the instance — including any container — can fetch these credentials.

```bash
# Inside any container on the host
TOKEN=$(curl -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
        http://169.254.169.254/latest/api/token)
ROLE=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/iam/security-credentials/)
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE
```

This is **convenient and dangerous**. Every container shares the instance role.

### 1.2 ECS Task IAM Role (the right pattern for ECS)

ECS gives each *task* its own IAM role. Credentials are served on `169.254.170.2/v2/credentials/<token>` — different endpoint than IMDS. The AWS SDK detects this automatically via `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI` env var that ECS sets in the task.

```jsonc
// task-definition.json
{
  "family": "infer-server",
  "taskRoleArn": "arn:aws:iam::123456789012:role/InferServerTaskRole",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  // ...
}
```

Two distinct roles:

- **`executionRoleArn`** — used by the ECS agent to pull the image, push logs to CloudWatch, fetch secrets from Secrets Manager *for the task definition*. Permissions: `AmazonECSTaskExecutionRolePolicy` plus `secretsmanager:GetSecretValue` for any secrets referenced.
- **`taskRoleArn`** — used by the application itself for AWS API calls (read S3, query DynamoDB, etc.). This is where application IAM policies live.

This separation is essential: the executor doesn't need application data permissions; the application doesn't need image-pull permissions.

### 1.3 EC2-on-ECS vs Fargate

For tasks on **EC2 capacity providers**, the host's IMDS is still reachable from containers if you don't block it. For **Fargate**, the host is a Firecracker MicroVM, and IMDS is restricted by AWS to only the task role endpoint by default. Fargate is the **safer choice** if you don't otherwise need EC2.

### 1.4 IMDSv2 — the Capital One fix

IMDSv1 was a simple HTTP GET. IMDSv2 requires a **session token** obtained via PUT request first. The token is bound to the session and (crucially) has a **TTL hop-limit** for forwarding.

Hardening for EC2 instances running containers:

```hcl
resource "aws_instance" "container_host" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"     # IMDSv2 only — rejects IMDSv1
    http_put_response_hop_limit = 1              # token has 1 hop max
  }
}
```

The hop-limit=1 is the lever: when a containerized process makes the PUT to get a token, the response packet's TTL is set to 1. The packet has to traverse the veth interface to leave the container — and veth interfaces decrement TTL. The token never reaches the container. **No IMDS access from containers, period.**

The AWS-launched default for new EC2 since 2024 is IMDSv2-required, but you must set `http_put_response_hop_limit=1` explicitly to fully block containers.

For ECS-on-EC2, this means containers must use the **task role endpoint** (`169.254.170.2`), not IMDS — exactly the desired posture.

For EKS, same posture, plus IRSA / Pod Identity (module 26).

### 1.5 The Capital One incident re-told as one IaC fix

```hcl
# What Capital One missed (pre-2019):
resource "aws_instance" "waf" {
  # ... no metadata_options block ...
}

# What would have prevented it:
resource "aws_instance" "waf" {
  metadata_options {
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
}
```

That single block. Capital One's published response built **Cloud Custodian rules** (now CNCF Incubating) that detect missing `http_tokens=required` across the org and remediate automatically. Module 23 covers the policy-as-code angle.

---

## 2. Object storage — Amazon S3

### 2.1 Access patterns

For ML, S3 is the canonical object store. Three access patterns:

| Pattern | Use case | Trade-offs |
|---|---|---|
| **SDK calls (boto3, AWS Python SDK)** | App-level reads/writes, batch ETL | Cleanest; explicit; full IAM control |
| **Mountpoint for Amazon S3** | Training data, read-heavy mount | GA Apr 2024; POSIX-limited (no rename in same prefix); ML training is the headline use case |
| **s3fs / goofys (FUSE)** | Legacy apps that need a file path | NOT recommended; performance unpredictable; CAP_SYS_ADMIN required |

**Mountpoint for S3** is the safer modern choice when filesystem semantics are needed. For ECS-on-EC2 or EC2-Docker:

```bash
# Install mount-s3 on the host
yum install -y mount-s3                       # AL2023
mount-s3 mybucket /mnt/mybucket --read-only

# Bind-mount into container
docker run -v /mnt/mybucket:/data:ro myimage
```

For EKS, the **Mountpoint for S3 CSI driver** does this declaratively (module 26).

### 2.2 S3 IAM patterns

The IAM policy attached to the task role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::myorg-ml-data/training/2026/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::myorg-ml-data",
      "Condition": {
        "StringLike": {"s3:prefix": ["training/2026/*"]}
      }
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::myorg-ml-artifacts/models/${aws:PrincipalTag/Team}/*"
    }
  ]
}
```

Three discipline points:

- **No bucket-level wildcards in prod** — restrict to prefixes.
- **Separate read and write resources** — never `s3:*` on the same role.
- **Tag-conditional resources** — `${aws:PrincipalTag/Team}` enforces per-team isolation in shared buckets.

### 2.3 S3 encryption & VPC endpoints

- **Bucket encryption at rest**: SSE-S3 (free, AWS-managed key), SSE-KMS (CMK, billed per call), or SSE-C (you supply key). For regulated finance, **SSE-KMS with a CMK** is the floor. Bucket policy should `Deny` `s3:PutObject` without `s3:x-amz-server-side-encryption=aws:kms`.
- **In transit**: TLS to S3 is the default; bucket policy should `Deny` `aws:SecureTransport=false`.
- **VPC Gateway Endpoint for S3**: free, no public-internet egress. Configure your VPC route table; S3 traffic stays inside AWS backbone.
- **S3 Block Public Access**: account-level + bucket-level. Set at the account level via Service Control Policy for an org-wide guarantee.
- **S3 Object Ownership = Bucket Owner Enforced**: disables ACLs; everything is owned by the bucket account. Removes a class of misconfig (cross-account objects with broken ACLs).

### 2.4 The S3 read-only-from-container pattern

For ML serving containers that pull a model artifact at startup:

```dockerfile
# In the container's startup script
#!/bin/bash
set -euo pipefail
aws s3 sync s3://myorg-ml-artifacts/models/sentiment/v1.4/ /opt/model/
exec python -m server.app
```

The container's IAM role grants only `s3:GetObject` on `s3://myorg-ml-artifacts/models/sentiment/*`. No write permission, no other bucket, no other prefix. If the container is compromised, the blast radius is one model version.

---

## 3. EFS for shared file access

**Amazon EFS** is NFSv4 as a service. Multi-AZ replicated, scales to petabytes, mounts to many hosts/containers concurrently (RWX). Perfect for:

- Shared training data on ECS / EKS / EC2.
- Notebook home directories for SageMaker Studio (uses EFS underneath).
- Any "Linux filesystem we want many containers to share" pattern.

### 3.1 EFS mount on ECS (`efsVolumeConfiguration`)

```jsonc
// task-definition.json
{
  "volumes": [
    {
      "name": "training-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "fs-0123456789abcdef0",
        "rootDirectory": "/training",
        "transitEncryption": "ENABLED",
        "authorizationConfig": {
          "accessPointId": "fsap-0a1b2c3d4e5f67890",
          "iam": "ENABLED"
        }
      }
    }
  ],
  "containerDefinitions": [
    {
      "mountPoints": [
        {"sourceVolume": "training-data", "containerPath": "/data", "readOnly": true}
      ]
    }
  ]
}
```

Three security knobs:

- **`transitEncryption: ENABLED`** — TLS for the NFS connection (port 2049 via stunnel).
- **`accessPointId`** — restricts the mount to one POSIX-uid-owned subdirectory of the EFS.
- **`iam: ENABLED`** — IAM authorization on top of NFS — the task role must have `elasticfilesystem:ClientMount`.

### 3.2 EFS Access Points — the multi-tenant pattern

An EFS Access Point lets you carve a single EFS file system into per-tenant slices, each with its own:

- Root directory (the tenant's view)
- POSIX UID/GID enforced at mount time
- Creation permissions

```hcl
resource "aws_efs_access_point" "team_alpha" {
  file_system_id = aws_efs_file_system.shared.id
  root_directory {
    path = "/teams/alpha"
    creation_info { owner_uid = 10001, owner_gid = 10001, permissions = "0750" }
  }
  posix_user { uid = 10001, gid = 10001 }
}
```

Now a task with this access point sees only `/teams/alpha` as `/`. Even with `cd ..`, the kernel keeps it confined. This is **the** multi-tenant primitive for shared EFS.

### 3.3 EFS performance modes

- **Throughput**: Bursting (default, scales with size) or Provisioned (pay for guaranteed MB/s).
- **Performance**: General Purpose (default) or Max I/O (higher concurrent but higher per-op latency — usually NOT what you want).
- **`nconnect=`**: NFS option, set via mount options. Boosts throughput from a single client.

For ML training that fits the "many containers reading the same dataset" pattern, EFS is the closest cloud-native equivalent to on-prem NFS.

---

## 4. FSx variants

| FSx flavor | Use |
|---|---|
| **FSx for Lustre** | High-perf parallel FS for HPC + ML training (1k+ GPU). Native S3 integration ("data repository association"). |
| **FSx for OpenZFS** | NFS with ZFS features (snapshots, clones). |
| **FSx for NetApp ONTAP** | Lift-and-shift from on-prem NetApp; same protocols (NFS, SMB, iSCSI). |
| **FSx for Windows File Server** | SMB for Windows containers. |

**FSx for Lustre** is the ML-training high-perf primitive. Provision a 1.2 TB+ filesystem, link to an S3 bucket; reads from the FS pull lazily from S3; writes can be evicted back to S3. The container mounts Lustre via the Lustre kernel client on the host, then bind-mounts.

For ECS/EC2-Docker training: mount FSx on the host, bind-mount into the container. For EKS: FSx for Lustre CSI driver (module 26).

---

## 5. Secrets — Secrets Manager and Parameter Store

### 5.1 Secrets Manager pattern in ECS

```jsonc
// task-definition.json — container definition
{
  "secrets": [
    {
      "name": "DB_PASSWORD_FILE",
      "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:prod/db/postgres-xxxx"
    }
  ]
}
```

ECS fetches the secret using the **execution role** (not the task role!), and exposes it as an env var. Permission needed on the execution role:

```json
{"Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:...:secret:prod/db/*"}
```

**The env-var pattern is suboptimal** (env-var leak surface — module 08). For better hygiene, the application should fetch the secret directly from Secrets Manager using the task role at runtime, write to a tmpfs path, and reference that path. AWS Secrets Manager Agent (Sep 2024 GA) automates this — runs as a sidecar, exposes a local HTTP/Unix-socket cache.

### 5.2 SSM Parameter Store

The cheaper option (free tier exists). Same mechanism, different ARN format (`ssm:parameter/...`). Use SecureString type with KMS encryption.

```bash
aws ssm get-parameter --name /prod/myapp/db_url --with-decryption --query 'Parameter.Value' --output text
```

For high-frequency reads, Parameter Store has rate limits — use Secrets Manager + caching for high-traffic services.

### 5.3 KMS — the encryption backbone

All AWS data-at-rest options use **KMS**: S3 SSE-KMS, EBS volume encryption, RDS, Secrets Manager. Three key types:

- **AWS managed key** (`aws/s3`, `aws/secretsmanager`) — free, can't audit usage at key level, can't restrict who uses it across accounts.
- **Customer managed key (CMK)** — paid ($1/month/key + $0.03 per 10k API calls), full key policy control, KMS Grants for fine-grained.
- **AWS CloudHSM** — your own FIPS 140-2 Level 3 HSM. Required for some payment/healthcare contexts.

For regulated finance (Capital One pattern): **CMK per workload / data class**, with key policy restricting `kms:Decrypt` to the specific task role + S3 service + bucket condition.

---

## 6. ECR — covered in module 05, recap for containers

For ECS / EKS, pulling from ECR works automatically when the **execution role** has `AmazonEC2ContainerRegistryReadOnly` (or the IRSA / Pod Identity equivalent in EKS).

For cross-account pulls: ECR Repository Policy on the source allows the puller account; the puller's execution role gets `ecr:GetAuthorizationToken` + `ecr:BatchGetImage` + `ecr:GetDownloadUrlForLayer`.

For VPC isolation: ECR API endpoint + ECR DKR endpoint + **S3 Gateway Endpoint** (image layers live in S3 — module 05 reminder).

---

## 7. VPC endpoints — the data-plane firewall

Without VPC endpoints, every API call from a container to AWS services goes over the public internet (or via NAT gateway). With VPC endpoints, the API call stays in AWS's network. For containers:

| Service | Endpoint type | Why containers need it |
|---|---|---|
| S3 | Gateway (free) | Object reads/writes |
| DynamoDB | Gateway (free) | Key-value reads/writes |
| ECR API + DKR | Interface (paid) | Image pulls |
| Secrets Manager | Interface | Secret reads |
| SSM | Interface | Parameter reads |
| CloudWatch Logs | Interface | Log shipping |
| KMS | Interface | Encryption ops |
| STS | Interface | Cross-account assume-role |
| Bedrock | Interface | LLM API calls |
| SageMaker Runtime | Interface | Inference endpoint calls |

VPC endpoint **policies** scope what API calls can be made through them. E.g., the S3 endpoint policy can restrict to specific buckets: `"Resource": "arn:aws:s3:::myorg-*"`. This is a powerful belt-and-braces control over the per-task IAM role.

---

## 8. ECS network modes

| Mode | Container networking | Use case |
|---|---|---|
| `awsvpc` | Each task gets its own ENI in the VPC | The default; required for Fargate; lets per-task SG work |
| `bridge` | docker0 bridge | Legacy EC2-mode tasks |
| `host` | Host network namespace | Performance, but loses task isolation |
| `none` | No networking | Batch jobs talking only to volumes |

**Always use `awsvpc` in production.** Per-task ENI gives:

- Per-task security group (fine-grained ingress/egress control).
- IPv4 (and IPv6) address per task — clean for service discovery.
- VPC Flow Logs at task level.

---

## 9. Security groups — task-level egress controls

```hcl
resource "aws_security_group" "task_egress" {
  name = "ml-task-egress"
  vpc_id = var.vpc_id

  # Allow S3 via Gateway endpoint
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    prefix_list_ids = [data.aws_prefix_list.s3.id]
  }
  # Allow KMS via Interface endpoint
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = [data.aws_vpc.this.cidr_block]
  }
  # Allow logs
  egress {
    from_port = 443
    to_port   = 443
    protocol  = "tcp"
    cidr_blocks = [data.aws_vpc.this.cidr_block]
  }
  # Deny everything else — implicit
}
```

Default-deny outbound + explicit allows. Cloud Custodian rules detect "security group with `0.0.0.0/0` egress" and remediate.

---

## 10. Logs — to CloudWatch via `awslogs`

```jsonc
{
  "containerDefinitions": [
    {
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/infer-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "infer-server",
          "awslogs-create-group": "true"
        }
      }
    }
  ]
}
```

Permission on execution role: `logs:CreateLogStream`, `logs:PutLogEvents` (+ `logs:CreateLogGroup` if `awslogs-create-group` is true).

Encrypt log groups with KMS CMK if logs may contain sensitive data: `aws logs associate-kms-key`.

---

## 11. The reference architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ VPC (10.0.0.0/16)                                                │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │ ECS Fargate  │    │ ECS Fargate  │    │ ECS EC2      │        │
│  │ infer-server │    │ pipeline     │    │ training     │        │
│  │              │    │              │    │ (GPU)        │        │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘        │
│         │ awsvpc ENI         │ awsvpc ENI       │ awsvpc ENI     │
│         │ per-task SG        │ per-task SG      │ per-task SG    │
│         │                    │                  │                │
│  ┌──────▼────────────────────▼──────────────────▼─────────────┐  │
│  │ Private subnet                                             │  │
│  └──────┬─────────────────────┬───────────────────────────────┘  │
│         │ S3 Gateway Endpoint │ Interface Endpoints              │
│         │                     │ (ECR, KMS, SecretsMgr, Logs)     │
└─────────┼─────────────────────┼──────────────────────────────────┘
          │                     │
   ┌──────▼──────┐         ┌────▼──────┐
   │ S3 buckets  │         │ Secrets   │
   │ (SSE-KMS    │         │ Manager   │
   │  + Block    │         │ + KMS CMK │
   │  Public)    │         └───────────┘
   └─────────────┘
```

All flows stay inside the VPC + AWS backbone. No NAT gateway egress to the internet for AWS service calls. IMDS unreachable from containers (hop-limit=1). Per-task IAM roles enforce least privilege. KMS encrypts at rest. Cloud Custodian enforces all of this with policy.

---

## 12. Capital One signal

Capital One's published security posture on AWS includes:

- **Cloud Custodian** policies enforcing `MetadataHttpTokens=required`, `BlockPublicAcls=true`, no `0.0.0.0/0` SG egress, no untagged resources.
- **Databolt** for at-rest tokenization (PCI/PII protection).
- **cfn-guard / cdk-nag** as CI-side IaC linting.
- **SCPs** at the org level enforcing region restrictions, deny-by-default services.

For an interviewee, the muscle memory should be: when asked "how would you secure container data on AWS?", you walk through IMDSv2 + IRSA/Task-Role + VPC endpoints + KMS CMK + S3 Block Public Access + Cloud Custodian — in that order — and you reference the Capital One 2019 breach as the canonical lesson for the first one.

---

## Sanity check

1. What's the exact mechanism by which `http_put_response_hop_limit=1` prevents a container from reading IMDS?
2. ECS task role vs execution role — what does each cover, and why is the separation important?
3. Mountpoint for S3 vs s3fs — name two reasons Mountpoint is the safer choice.
4. What does an EFS Access Point give you that a vanilla EFS mount does not?
5. Why is `aws:SecureTransport=false` deny in a bucket policy a defense in depth even if all clients use HTTPS?
6. List the seven VPC endpoints a typical ECS task needs (S3 + six interface endpoints).
7. KMS CMK vs AWS-managed key — list two reasons regulated finance requires CMK.

---

## Sources

- [AWS IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [ECS Task IAM Role](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html)
- [Mountpoint for Amazon S3](https://aws.amazon.com/blogs/aws/mountpoint-for-amazon-s3-generally-available-and-ready-for-production-workloads/)
- [EFS Access Points](https://docs.aws.amazon.com/efs/latest/ug/efs-access-points.html)
- [FSx for Lustre](https://docs.aws.amazon.com/fsx/latest/LustreGuide/what-is.html)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html)
- [AWS KMS](https://docs.aws.amazon.com/kms/)
- [Capital One OCC consent order, Aug 2020](https://www.occ.treas.gov/news-issuances/news-releases/2020/nr-occ-2020-101a.pdf)
- [Cloud Custodian](https://cloudcustodian.io/)

→ Next: [14 — **Data exposure — GCP**](14_data_exposure_gcp.md)


\newpage

# 14 — Data exposure for containers — GCP

> *"Workload Identity Federation replaces every long-lived service-account JSON key in your stack. If you still have JSON keys, you're behind."*

## Why this module exists

GCP's container-data story is the cleanest of the three big clouds because:

1. **Workload Identity Federation** has been the default for K8s for years; no JSON keys.
2. **Service accounts** at the project level are first-class principals.
3. **GCS** is the storage spine; **gcsfuse** is now CSI-driver-grade.
4. **Secret Manager** + Workload Identity is one short hop.

This module covers Docker-on-GCE (Compute Engine), Cloud Run, and the GCP-specific identity model. GKE is in module 27.

---

## 1. Identity — service accounts everywhere

In GCP, a **service account** is an IAM principal with an email like `infer-server@my-proj.iam.gserviceaccount.com`. Roles are bound to it; resources reference it by email; workloads authenticate AS it.

Two ways to authenticate as a service account from a container:

### 1.1 Compute Engine instance default service account (the IMDS pattern)

A GCE VM has an associated service account, exposed via GCE Metadata Server at `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token`. Any process on the VM — including containers — can fetch tokens.

Inside any container on a GCE host:

```bash
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
# Returns: {"access_token":"...","expires_in":3599,"token_type":"Bearer"}
```

This is **the GCP equivalent of EC2 IMDS**, and it has the same risk surface. Mitigation:

- **Run with the minimal service account** the workload needs (use `--service-account=...` on `gcloud compute instances create`).
- **GCE metadata blocked from container** via `--metadata-from-file=block-project-ssh-keys=true` + iptables rule on the metadata IP `169.254.169.254`.
- **Prefer Workload Identity Federation** (see below) for per-workload identity.

### 1.2 Workload Identity Federation (WIF) — the modern default

WIF lets a non-GCP workload (or a GCP workload that you want to identity-bound) **trade an OIDC token for a GCP access token via STS**, without any long-lived JSON key.

The setup:

1. Create a **Workload Identity Pool** + Provider that trusts your IdP (GitHub OIDC, AWS, Azure, OIDC of your own).
2. Bind the pool to a GCP service account: "principals from this pool can `iam.serviceAccounts.getAccessToken` on this SA."
3. Workload presents an OIDC token; STS exchanges it for a 1-hour SA access token.

For containers on GCE that should not use the VM's default SA, this is the modern path. For GKE (module 27), Workload Identity *for GKE* is a tighter integration (KSA → GSA without WIF pool).

### 1.3 The JSON-key anti-pattern

```bash
# DO NOT DO THIS
docker run -v ~/.config/gcloud:/root/.config/gcloud myimage          # leaks YOUR identity
docker run -v /etc/gcp-sa.json:/etc/gcp-sa.json -e GOOGLE_APPLICATION_CREDENTIALS=/etc/gcp-sa.json myimage  # static key on disk
```

GCP org policies can **forbid creation of service-account JSON keys** entirely (`iam.disableServiceAccountKeyCreation`). For regulated workloads, this is the right org-policy setting. Replace every JSON key with WIF.

---

## 2. Object storage — Google Cloud Storage (GCS)

### 2.1 Access patterns

| Pattern | Use case | Notes |
|---|---|---|
| **SDK calls (google-cloud-storage)** | App-level reads/writes | The default; cleanest |
| **gcsfuse** | Mount GCS as a filesystem | ML training data; supported by Google |
| **`gsutil`** | CLI scripting | Fine for batch jobs |
| **Cloud Storage Transfer Service** | Bulk loads | One-time migrations |

`gcsfuse` is officially supported and stable. Mount on the host, bind-mount into the container:

```bash
gcsfuse --implicit-dirs my-bucket /mnt/my-bucket
docker run -v /mnt/my-bucket:/data:ro myimage
```

For GKE, the **GCS Fuse CSI driver** (GA late 2023) does this declaratively as a sidecar per pod (module 27).

Caveat: `gcsfuse` is not a real POSIX FS — no random writes, no rename atomicity. For ML training (sequential reads of large files), it's fine. For database storage, never.

### 2.2 GCS IAM

GCS supports both **fine-grained ACLs** (legacy) and **Bucket Policy Only / Uniform Bucket-Level Access** (modern). Always enable Uniform — disables ACLs, simplifies the model to IAM only.

Standard roles:

| Role | What it grants |
|---|---|
| `roles/storage.objectViewer` | Read objects |
| `roles/storage.objectCreator` | Create objects (no read of existing) |
| `roles/storage.objectAdmin` | Read/write/delete objects |
| `roles/storage.admin` | Full admin including bucket settings |

For containers, the principle of least privilege: grant `objectViewer` on the specific bucket (or prefix-conditional with IAM Conditions):

```bash
gcloud storage buckets add-iam-policy-binding gs://my-bucket \
  --member="serviceAccount:infer-server@my-proj.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \
  --condition='expression=resource.name.startsWith("projects/_/buckets/my-bucket/objects/models/sentiment/"),title=models-sentiment-only,description="Read only sentiment model"'
```

### 2.3 Encryption

- **Default at rest**: Google-managed keys, AES-256.
- **CMEK** (Customer-Managed Encryption Key): you supply a Cloud KMS key. Bucket-level + project-level options.
- **CSEK** (Customer-Supplied Encryption Key): you supply the raw key on every request. Rare; only for extreme cases where Google never sees the key material.
- **In transit**: TLS always. No setting needed.

For regulated finance, **CMEK with project-specific KMS keys** is the floor. Org policy can require CMEK on all buckets:

```yaml
# Organization Policy
constraint: constraints/gcp.restrictNonCmekServices
listPolicy:
  allowedValues:
    - "storage.googleapis.com"
```

### 2.4 VPC Service Controls (VPC-SC)

The GCP equivalent of "no exfiltration to external buckets" — VPC-SC creates a **service perimeter** that prevents API calls from inside the perimeter to resources outside, and vice versa.

For ML data, put your project (or specific buckets) in a perimeter; containers in the same perimeter can read; nothing outside can. Even if an IAM mistake grants read to a wrong principal, VPC-SC blocks the call if the principal is outside the perimeter.

This is one of GCP's best-loved features for regulated shops — there's no exact equivalent in AWS or Azure (AWS VPC endpoints are conceptually similar but per-service).

### 2.5 Private Google Access

For GCE / Cloud Run / Compute instances in subnets without public IPs, **Private Google Access** lets them reach `storage.googleapis.com`, `secretmanager.googleapis.com`, etc. via private IP. Enable on the subnet:

```bash
gcloud compute networks subnets update my-subnet --region=us-central1 \
  --enable-private-ip-google-access
```

Together with VPC-SC, this is how you keep ML container traffic off the internet entirely.

---

## 3. Filestore — managed NFS

**Filestore** is GCP's managed NFSv3 (and v4.1 for some tiers). Tiers:

- **Basic HDD** — cheap, low IOPS.
- **Basic SSD** — better.
- **Zonal SSD** — high-perf, single-zone.
- **Enterprise** — regional HA, ~100k IOPS.

Mount on a GCE host, bind-mount into container:

```bash
mount -t nfs -o vers=3,rsize=1048576,wsize=1048576 \
  10.0.10.5:/share /mnt/share
docker run -v /mnt/share:/data myimage
```

For GKE: **Filestore CSI driver** (module 27).

Filestore is the right pick for "Linux file share with many concurrent readers" patterns. For ML training at extreme scale, **Cloud Storage with gcsfuse** or **Lustre on Compute Engine** is cheaper.

---

## 4. Persistent Disks (PD) — block storage for containers

Persistent Disks are the GCP block storage primitive. Tiers:

- **pd-standard** — HDD, cheap.
- **pd-balanced** — gp3-equivalent.
- **pd-ssd** — high IOPS.
- **pd-extreme** — provisioned IOPS.
- **Hyperdisk** — newer family with tier-specific extremes (throughput, IOPS, balanced); cleaner separation than `pd-extreme`.

Pattern: attach PD to GCE host, mkfs, mount, bind-mount into container. Single-host writer; for multi-host RWX, use Filestore or GCS.

### 4.1 Disk encryption

- **Google-managed key** by default.
- **CMEK** via Cloud KMS — enforced via org policy.
- **CSEK** for the extreme cases.

For container hosts: enable CMEK on the disks at create time.

---

## 5. Secret Manager

Google Cloud's secret store. Versions, IAM-controlled, KMS-encrypted, optionally CMEK.

```python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
resp = client.access_secret_version(request={"name": "projects/123/secrets/db-pass/versions/latest"})
pw = resp.payload.data.decode("UTF-8")
```

Authentication is automatic via ADC (Application Default Credentials) — the container picks up the GCE metadata token or the WIF token transparently.

### 5.1 Best practices

- IAM roles per secret (`roles/secretmanager.secretAccessor` on a specific secret, not project-wide).
- Use **labels** to tag secrets by team / environment / data class.
- Enable **secret version pinning** in your code (avoid `:latest` in prod — version drift causes silent failures).
- Use **secret rotation** with Cloud Functions to rotate DB passwords periodically.
- **CMEK** for secret encryption.

### 5.2 Mounting secrets as files

A common pattern (and the safer one — module 08):

```python
# At container startup
secret_value = fetch_from_secret_manager("db-pass")
with open("/run/secrets/db_pass", "w") as f:
    f.write(secret_value)
os.chmod("/run/secrets/db_pass", 0o400)
# App reads from /run/secrets/db_pass
```

On GKE, the **Secret Manager CSI driver** does this declaratively (module 27).

---

## 6. Cloud Run — fully managed containers

Cloud Run is GCP's serverless containers product. It runs OCI images via **gVisor (runsc)** on a Google-managed infra; you provide an image, GCP scales it.

### 6.1 Identity for Cloud Run

A Cloud Run service has a service account. The container's processes can use ADC to get credentials. No JSON key, no metadata server fiddling — `gcloud auth application-default` works inside.

```bash
gcloud run deploy infer-server \
  --image=us-central1-docker.pkg.dev/my-proj/repo/infer:1.0.0 \
  --service-account=infer-server@my-proj.iam.gserviceaccount.com \
  --region=us-central1 \
  --vpc-connector=my-vpc-connector \
  --vpc-egress=all-traffic \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```

### 6.2 Data exposure from Cloud Run

Cloud Run containers can't bind-mount host paths (no host). Volume options:

- **Cloud Storage Fuse** (Cloud Run 2nd gen, GA 2024) — mount a GCS bucket as a volume.
- **Cloud SQL** via private IP + Cloud SQL Connector (Python `cloud-sql-python-connector`).
- **In-memory tmpfs** — automatic, container's writable layer is ephemeral.
- **Cloud Storage SDK** — the dominant pattern for data movement.

### 6.3 Cloud Run security defaults

- `--ingress=internal-and-cloud-load-balancing` — not reachable from public internet.
- `--no-allow-unauthenticated` — requires Google-issued JWT for invocation.
- `--vpc-connector` + `--vpc-egress=all-traffic` — egress through your VPC, subject to firewall rules + VPC-SC.
- gVisor runtime — kernel-attack-surface reduction comes free.

Cloud Run is the **simplest container compute on GCP** with the strongest defaults. For workloads that fit (HTTP/gRPC, stateless, ≤ 60 minutes), it's usually the right answer.

---

## 7. Binary Authorization for image verification

[Binary Authorization](https://cloud.google.com/binary-authorization) is GCP's image-attestation admission control — GKE-focused but also supports Cloud Run.

Pattern:

1. Build image in CI; sign with Cosign keyless via WIF.
2. CI generates an attestation (`gcloud container binauthz attestations create`).
3. Cloud Run / GKE deployment policy requires an attestation from the trusted attestor before allowing the image to run.

For regulated finance on GCP: enforce BinAuth on every prod cluster + Cloud Run service. Break-glass via labels with audit trail.

---

## 8. Firewall rules — the container egress

GCP firewall rules apply to VM network tags or service accounts. Containers inherit the VM's network identity (for GCE-Docker) or Cloud Run's egress identity.

Default-deny outbound pattern:

```bash
gcloud compute firewall-rules create deny-all-egress \
  --direction=EGRESS \
  --priority=65530 \
  --network=my-vpc \
  --action=DENY \
  --rules=all \
  --destination-ranges=0.0.0.0/0

gcloud compute firewall-rules create allow-gcp-private \
  --direction=EGRESS \
  --priority=1000 \
  --network=my-vpc \
  --action=ALLOW \
  --rules=tcp:443 \
  --destination-ranges=199.36.153.8/30   # private.googleapis.com
```

Combined with Private Google Access + VPC-SC, the container can talk to Google services only — no internet egress.

---

## 9. Logging — Cloud Logging

The default for containers on GCE / Cloud Run / GKE:

- **GCE-Docker**: install Ops Agent on the host; container stdout/stderr flows to Cloud Logging.
- **Cloud Run**: stdout/stderr → Cloud Logging automatically.
- **GKE**: GKE's logging agent (Fluent Bit) → Cloud Logging.

Logs are encrypted at rest by Google-managed keys by default; CMEK available.

Cloud Logging log buckets can be **regionally constrained** for data-residency requirements — set this at project create time.

---

## 10. The reference architecture for ML on GCP (Docker on GCE)

```
┌────────────────────────────────────────────────────────────────────┐
│ VPC (my-vpc) + VPC-SC perimeter                                    │
│                                                                    │
│  ┌──────────────────┐    ┌──────────────────┐                      │
│  │ GCE host (no     │    │ Cloud Run        │                      │
│  │ public IP)       │    │ infer-server     │                      │
│  │ + Docker         │    │ + per-SA identity│                      │
│  │ + SA (least priv)│    │ + VPC connector  │                      │
│  └──────┬───────────┘    └──────┬───────────┘                      │
│         │ private IP             │ VPC egress                      │
│         │                        │                                 │
│  ┌──────▼────────────────────────▼────────────────────────────┐    │
│  │ Private Google Access subnet                              │    │
│  └──────┬────────────────────────────────────────────────────┘    │
│         │ private.googleapis.com (199.36.153.8/30)                 │
└─────────┼──────────────────────────────────────────────────────────┘
          │
   ┌──────▼──────┐    ┌──────────────┐   ┌──────────────┐
   │ GCS buckets │    │ Filestore    │   │ Secret Mgr   │
   │ + CMEK      │    │ + CMEK       │   │ + CMEK       │
   │ + Uniform   │    │              │   │              │
   │   ACL       │    │              │   │              │
   └─────────────┘    └──────────────┘   └──────────────┘
```

Cross-cuts:

- **Image source**: Artifact Registry (GAR), signed with Cosign.
- **Identity**: per-workload service account (no JSON keys); WIF for off-GCP CI.
- **Egress**: VPC firewall default-deny; Private Google Access; VPC-SC perimeter.
- **Audit**: Cloud Audit Logs to centralized log sink.

---

## 11. Capital One angle for GCP

Capital One is AWS-first and AWS-only, so GCP isn't strictly in scope for the Sr Lead AI/ML role. But knowing the parallels is interview gold — "I would map this AWS X to GCP Y" is the kind of architect-level thinking that scores points.

| AWS | GCP |
|---|---|
| IAM Role + STS | Service Account + STS |
| IMDSv2 hop-limit=1 | GCE Metadata Server (block via FW) |
| IRSA / Pod Identity (EKS) | Workload Identity for GKE |
| Cross-account assume-role | Workload Identity Federation |
| S3 + SSE-KMS | GCS + CMEK |
| EFS | Filestore |
| FSx for Lustre | Lustre on GCE (3rd-party) / Parallelstore |
| Secrets Manager | Secret Manager |
| KMS | Cloud KMS |
| Cloud Custodian (AWS-API) | Organization Policy + Forseti (legacy) |
| VPC Endpoints | Private Google Access + VPC-SC |
| Service Control Policies | Org Policies + IAM Conditions |
| ECR | Artifact Registry |
| ECS Fargate (Firecracker per task) | Cloud Run (gVisor per request batch) |

---

## Sanity check

1. Why is Workload Identity Federation preferable to a service-account JSON key, even when the JSON key is "only in the build pipeline"?
2. What does VPC Service Controls give you that VPC firewall rules don't?
3. `gcsfuse` is fine for ML training but unsuitable for a Postgres data dir. Why?
4. Cloud Run uses gVisor by default. What attack class does that close that vanilla Docker on GCE doesn't?
5. Name three controls a regulated shop should enforce on every GCS bucket via Organization Policy.
6. How does "Private Google Access" interact with a subnet that has no public IPs?

---

## Sources

- [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [GCS overview](https://cloud.google.com/storage/docs)
- [Cloud Storage Fuse](https://cloud.google.com/storage/docs/cloud-storage-fuse/overview)
- [Filestore](https://cloud.google.com/filestore/docs)
- [Persistent Disks](https://cloud.google.com/compute/docs/disks)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Cloud Run](https://cloud.google.com/run/docs)
- [Binary Authorization](https://cloud.google.com/binary-authorization/docs)
- [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs)
- [Private Google Access](https://cloud.google.com/vpc/docs/private-google-access)

→ Next: [15 — **Data exposure — Azure**](15_data_exposure_azure.md)


\newpage

# 15 — Data exposure for containers — Azure

> *"In Azure, managed identity is the lever. Once a container has the right MI, every other primitive — Key Vault, Storage, ACR — slots in for free."*

## Why this module exists

Azure's container-data story is built around two primitives:

- **Microsoft Entra ID Managed Identities** (system-assigned or user-assigned). Identity binding to compute, no secrets in code.
- **Azure Resource Manager (ARM) role-based access control (RBAC)**. Roles assigned at resource, resource-group, subscription, or management-group scope.

This module covers Docker on Azure VMs, Azure Container Instances (ACI), and Azure Container Apps. AKS is in module 28.

This module also relates to Topic 02 (Azure Databricks), which uses Azure Files / ADLS Gen2 / Managed Identities heavily — same primitives in a different consumption model.

---

## 1. Identity — Managed Identities

A **Managed Identity** (MI) is a special service principal in Entra ID, automatically managed (rotated, lifecycle-bound to the resource).

### 1.1 System-assigned vs user-assigned

- **System-assigned MI** — bound 1:1 to a resource (VM, ACI, App Service). Deleted when the resource is. Simple.
- **User-assigned MI** — a standalone resource. Can be attached to multiple resources. Lives independently. The production choice for containers that may run on many VMs.

For VM hosts running Docker:

```bash
az identity create --name my-ml-mi --resource-group my-rg
az vm identity assign --name my-vm --resource-group my-rg \
  --identities /subscriptions/.../resourcegroups/my-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/my-ml-mi
```

Inside any container on the VM, the **Azure Instance Metadata Service (IMDS)** at `http://169.254.169.254/metadata/identity/oauth2/token` provides tokens:

```bash
curl -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://vault.azure.net/&mi_res_id=/subscriptions/.../my-ml-mi"
```

The Azure SDK does this automatically via **DefaultAzureCredential** in any supported language.

### 1.2 The same IMDS-trust problem as AWS

Azure's IMDS is also at `169.254.169.254` (different paths than AWS), and the same containerization-pivot risk applies. Mitigation:

- **Block IMDS from containers** via `iptables -A DOCKER-USER -d 169.254.169.254 -j DROP`.
- Use **Microsoft Entra Workload ID** for AKS workloads (module 28) instead of host IMDS.
- For VMs, **assign per-workload user-assigned MIs** so the blast radius of an IMDS leak is one MI, not the host's full identity.

### 1.3 Service principals — the legacy / explicit pattern

Before MI, you used a **service principal** (an Entra app registration with a client ID + client secret or cert). These are still used for cross-tenant scenarios, CI/CD systems outside Azure, and integrations.

Anti-pattern: bake SP client secret into image. Right pattern: store secret in Key Vault, fetch via MI at runtime.

For containers running outside Azure but needing Azure resources: **Federated Identity Credentials** (the Azure equivalent of WIF) — your CI's OIDC token → Azure user-assigned MI → access tokens. No client secret.

---

## 2. Object storage — Azure Blob Storage

Blob Storage has three "blob types":

| Blob type | Use |
|---|---|
| **Block blobs** | Most use cases — files, images, model artifacts |
| **Append blobs** | Log files |
| **Page blobs** | Random read/write, backing for VHDs |

Storage account tiers: Standard (HDD/SSD) and Premium (block blobs SSD-only). For ML data: Premium block blob.

### 2.1 Access patterns

| Pattern | Use case | Notes |
|---|---|---|
| **Azure SDK / boto3-equivalent (azure-storage-blob)** | App-level | Default |
| **blobfuse2** | Mount as filesystem | Microsoft-supported FUSE; better than s3fs's reliability |
| **AzCopy** | Bulk transfer | CLI; performance |
| **NFS 3.0 mount on Blob** | Container fs | Specific account configuration; Premium tier with NFS feature enabled |
| **HDFS protocol via ABFS driver** (ADLS Gen2) | Spark / Databricks | Topic 02 territory |

`blobfuse2` is the production-grade FUSE for Azure Blob:

```bash
blobfuse2 mount /mnt/blob --config-file=/etc/blobfuse2-config.yaml
docker run -v /mnt/blob:/data:ro myimage
```

Config file format auths via MI (no secrets in config):

```yaml
# /etc/blobfuse2-config.yaml
azstorage:
  type: block
  account-name: mystorageacct
  container: ml-data
  mode: msi
  msi:
    resource-id: /subscriptions/.../my-ml-mi
file_cache:
  path: /var/cache/blobfuse2
  timeout-sec: 240
```

For AKS, the **Blob CSI driver** does this declaratively (module 28).

### 2.2 Blob RBAC

Roles (modern, AAD-RBAC; ignore the legacy SAS-token model where possible):

| Role | Grants |
|---|---|
| `Storage Blob Data Reader` | Read blobs |
| `Storage Blob Data Contributor` | Read/write/delete blobs |
| `Storage Blob Data Owner` | Same + ACL management |
| `Storage Account Contributor` | Manage account (not data plane!) |

Assignment is scoped: management-group / subscription / resource-group / account / container / blob-prefix.

```bash
az role assignment create \
  --role "Storage Blob Data Reader" \
  --assignee-object-id $MI_PRINCIPAL_ID \
  --scope "/subscriptions/.../mystorageacct/blobServices/default/containers/ml-data"
```

### 2.3 Encryption

- **Default at rest**: AES-256, Microsoft-managed keys.
- **CMK** via Azure Key Vault — encryption scope per storage account or per blob container.
- **Double encryption** (Microsoft 256-bit AES + your CMK) for compliance.
- **In transit**: TLS 1.2+ required (storage account setting `minimumTlsVersion: TLS1_2`).
- **Storage account firewall**: deny by default; allowlist trusted Azure services + VNet subnets.

### 2.4 Storage account hardening

The defensive baseline (Azure Policy can enforce):

- `minimumTlsVersion: TLS1_2`.
- `supportsHttpsTrafficOnly: true`.
- `allowBlobPublicAccess: false` (anonymous read blocked).
- `allowSharedKeyAccess: false` (forces AAD auth — the strongest setting).
- `networkAcls.defaultAction: Deny` + explicit VNet rules.
- Private endpoint for the storage account; DNS overrides to point to the private IP.
- Diagnostic logs → Log Analytics workspace.

`allowSharedKeyAccess: false` is the **most important** — it disables the storage-account-key auth (the historic "key A and key B" model), forcing all access through AAD. Eliminates a huge class of leaked-key incidents.

### 2.5 ADLS Gen2 = Blob with hierarchical namespace

ADLS Gen2 is Blob with a hierarchical namespace (HNS) enabled. Adds:

- POSIX-style folder hierarchy (not just flat key/value).
- POSIX ACLs alongside RBAC (fine-grained per-folder permissions).
- ABFS driver for Hadoop/Spark/Databricks.

For ML/Spark workloads on Azure, **ADLS Gen2 with HNS is the default**. Topic 02's Databricks corpus goes deeper.

---

## 3. Azure Files — SMB and NFS as a service

Azure Files offers SMB (default) and NFS 4.1 (Premium tier required). Mount on a VM host and bind-mount into container:

```bash
# SMB mount (the common case)
mount -t cifs //mystorageacct.file.core.windows.net/share /mnt/share \
  -o vers=3.1.1,credentials=/etc/smbcreds,uid=10001,gid=10001,iocharset=utf8,nosharesock

# Or with AAD-Kerberos (no static creds)
mount -t cifs //mystorageacct.file.core.windows.net/share /mnt/share \
  -o vers=3.1.1,sec=krb5,iocharset=utf8

docker run -v /mnt/share:/data myimage
```

For NFS 4.1:

```bash
mount -t nfs -o vers=4,minorversion=1,sec=sys mystorageacct.file.core.windows.net:/share /mnt/share
```

Encryption in transit:
- SMB 3.1.1 has end-to-end encryption — enable on the share.
- NFS over Azure Files **does NOT support encryption in transit at the protocol layer** — requires the network to be inside a VNet with private endpoints. Configure storage account to require private endpoints.

For AKS, **Azure Files CSI driver** (module 28).

---

## 4. Azure Disks

Block storage. Tiers:

- **Standard HDD** — cheap.
- **Standard SSD** — better.
- **Premium SSD v2** — high IOPS.
- **Ultra Disk** — premium for high-IOPS DBs.

Attach to VM, format, mount. Same pattern as on-prem block / EBS / PD: not multi-host RWX.

Encryption: Server-Side Encryption (SSE) by default with Microsoft-managed keys. Customer-Managed Keys via Disk Encryption Set (DES) — a resource that pairs an Azure Key Vault key with the disk. **Required for regulated workloads.**

```bash
az disk-encryption-set create --name my-des --resource-group my-rg --source-vault my-kv --key-url $KEY_URL
az disk create --name my-disk --resource-group my-rg --size-gb 100 --disk-encryption-set my-des
```

---

## 5. Azure Key Vault

Azure's managed secret/key/cert store. Three modes:

- **Standard** — software-protected keys.
- **Premium** — HSM-protected keys (FIPS 140-2 Level 2).
- **Managed HSM** — dedicated HSM (FIPS 140-2 Level 3).

For regulated finance, Premium or Managed HSM.

### 5.1 Pattern: container fetches secret from KV via MI

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://my-kv.vault.azure.net/", credential=credential)
db_pass = client.get_secret("db-pass").value
```

`DefaultAzureCredential` walks the credential chain: env vars → managed identity → CLI auth → etc. In a container on a VM with MI attached, it picks up the MI token automatically. No client secret in code, no JSON key on disk.

The KV access policy (or RBAC role assignment) grants the MI `Get` permission on secrets. Least-privilege:

```bash
az keyvault set-policy --name my-kv --object-id $MI_PRINCIPAL_ID --secret-permissions get
# Or via RBAC: az role assignment create --role "Key Vault Secrets User" --assignee-object-id $MI_PRINCIPAL_ID --scope "/subscriptions/.../my-kv"
```

### 5.2 Key Vault references — Azure App Service / Container Apps pattern

For Azure App Service / Container Apps / Functions, you can put `@Microsoft.KeyVault(SecretUri=...)` in env-var definitions. The platform fetches and substitutes at start.

For raw Docker on a VM: write your own bootstrap that fetches and writes to a tmpfs file (module 08).

For AKS: **Key Vault Secrets Store CSI driver** (module 28).

### 5.3 KV networking

- **Private endpoint** for the vault — no public access.
- **Firewall** with allowed VNets if no PE.
- **Soft delete** + **purge protection** — once enabled, secrets can be recovered for 7-90 days even after delete. Regulated requirement.
- **Diagnostic logs** to Log Analytics.

---

## 6. Azure Container Instances (ACI)

ACI is "run a container, no infrastructure." Single-container or pod-of-containers. Used for batch jobs, CI/CD runners, and one-off compute.

### 6.1 Identity in ACI

ACI containers can have a **user-assigned managed identity**:

```bash
az container create \
  --name infer-job \
  --resource-group my-rg \
  --image myacr.azurecr.io/infer:1.0 \
  --assign-identity /subscriptions/.../my-ml-mi \
  --acr-identity   /subscriptions/.../my-acr-pull-mi
```

Two MIs:
- `--acr-identity` — used to pull the image from ACR.
- `--assign-identity` — used by the application code.

`DefaultAzureCredential` in the container picks up `--assign-identity` automatically.

### 6.2 ACI data exposure

- Volume mounts: Azure Files (SMB), GitRepo (deprecated), secret volumes, emptyDir.
- No bind mounts to host (no host concept).
- Outbound networking: through the assigned subnet if you use the `--vnet` flag, otherwise public.
- For private ACI: use the **VNet integration** + private endpoints for everything ACI touches.

### 6.3 Confidential containers on ACI

ACI supports **confidential containers** on AMD SEV-SNP / Intel TDX. The container runs in a hardware-encrypted memory region; even Microsoft operators can't read it. Attestation tokens prove the container runs in a confidential environment before secrets are released.

For PII / regulated workloads, this is a strong primitive — though it adds friction to debugging.

---

## 7. Azure Container Apps

Azure Container Apps (ACA) is a managed Kubernetes-on-the-side serverless container runtime. Used for:

- Microservices that need auto-scaling (KEDA built in).
- Background jobs (Jobs feature).
- Long-running workloads.

ACA's data exposure:

- **Volume mounts**: Azure Files, ephemeral, secrets.
- **Identity**: system or user-assigned MI.
- **Secrets**: native ACA secrets (encrypted, bound to revision) + Key Vault references.
- **Networking**: managed VNet (default) or your VNet; internal-only ingress option.
- **Ingress**: HTTPS endpoint with managed cert; can be internal-only.

ACA is the **Cloud Run analogue on Azure**. Same trade-offs: simple, opinionated, fits HTTP/gRPC/jobs.

---

## 8. ACR — Azure Container Registry

Covered in module 05. For data-exposure purposes:

- Use Premium tier for VNet integration via private endpoint.
- Disable admin user.
- Use AAD/RBAC.
- Attach to AKS via managed identity: `az aks update --attach-acr`.
- Enable image scanning via Microsoft Defender for Cloud.
- ACR Tasks for CI; consider Azure Pipelines or GitHub Actions for sophisticated workflows.

---

## 9. Azure networking primitives for containers

- **VNet** — your virtual network. Containers on VMs / ACI / ACA all live in subnets.
- **NSG (Network Security Group)** — the firewall, applied per-subnet or per-NIC. Default-deny outbound is the regulated baseline.
- **Private Endpoint** — a private IP in your VNet that connects to an Azure PaaS service (Storage, Key Vault, ACR, Cosmos DB, ...). Replaces public endpoints.
- **Service Endpoint** (older) — a route from a subnet to a PaaS service; the PaaS still has a public IP. Private Endpoint is the modern replacement.
- **Azure Firewall** — managed L7 firewall; good for egress filtering with FQDN rules.
- **Application Gateway / Front Door** — L7 load balancer for ingress (WAF included).

### 9.1 The private-everything pattern

For regulated finance:

- Storage account, Key Vault, ACR, Cosmos DB, SQL DB — **all have private endpoints**, all have `publicNetworkAccess: Disabled`.
- VNet subnet for containers has NSG with default-deny outbound + allowlist for the private endpoint subnet.
- DNS: Private DNS Zones override the public DNS for these resources.

---

## 10. Logging

Container logs (stdout/stderr) collected by:

- **Azure Monitor Container Insights** for AKS / ACA.
- **Diagnostic settings** on ACI → Log Analytics.
- **For raw Docker on VMs**: install the **Azure Monitor Agent** + Log Analytics workspace.

Log Analytics workspaces support CMK for encryption at rest. Data Export rules ship logs to Storage for retention.

---

## 11. Azure Policy — the equivalent of Cloud Custodian / Org Policy

Azure Policy enforces resource configuration at scope (subscription / RG / MG). Built-in policies include:

- "Storage accounts should restrict network access."
- "Storage accounts should require minimum TLS version 1.2."
- "Key Vault should have soft delete enabled."
- "Container registries should not allow unrestricted network access."
- "Disks should use customer-managed keys."

Plus you can write **custom policies** in the Azure Policy JSON definition language. Combined with **Deploy-If-Not-Exists** effects, policy auto-remediates.

For Sr Architect interviews: know that Azure Policy is the canonical answer for "how would you enforce X across the subscription," and `Microsoft Defender for Cloud` is the analogue of AWS Security Hub.

---

## 12. The reference architecture for ML containers on Azure (VM-based)

```
┌────────────────────────────────────────────────────────────────────┐
│ VNet (my-vnet)                                                     │
│                                                                    │
│  ┌──────────────────────────┐                                      │
│  │ VM Scale Set             │                                      │
│  │ user-assigned MI         │                                      │
│  │ + Docker rootless        │                                      │
│  │ + iptables: drop IMDS    │                                      │
│  │   from containers        │                                      │
│  │ + custom-script: bootstrap│                                     │
│  │   secret to tmpfs        │                                      │
│  └──────┬───────────────────┘                                      │
│         │ NSG (default-deny egress + allowlist via PE subnet)      │
│         │                                                          │
│  ┌──────▼───────────────────────────────────────────────────┐      │
│  │ Private Endpoint subnet                                  │      │
│  └──────┬────────────────────────────────────────────────────┘     │
│         │                                                          │
└─────────┼──────────────────────────────────────────────────────────┘
          │ Private endpoint links (per resource)
   ┌──────▼──────┐    ┌──────────────┐   ┌──────────────┐
   │ Storage Acct│    │ Key Vault    │   │ ACR (Premium)│
   │ + CMK       │    │ + HSM        │   │ + PE         │
   │ + shared-key│    │ + purge prot │   │ + admin off  │
   │   DISABLED  │    │ + PE         │   │              │
   │ + PE        │    │              │   │              │
   └─────────────┘    └──────────────┘   └──────────────┘
```

Cross-cuts:

- **Image source**: ACR with private endpoint.
- **Identity**: user-assigned MI per workload.
- **Secrets**: Key Vault references via MI.
- **Egress**: NSG default-deny + Azure Firewall for FQDN allowlist.
- **Audit**: diagnostic settings → Log Analytics with CMK.
- **Posture**: Microsoft Defender for Cloud + Azure Policy.

---

## 13. Capital One angle for Azure

Capital One is AWS, not Azure. But Optum (the user's current employer) is **Microsoft Azure heavy**. The user has authored extensive Azure-Databricks material already (Topic 02). For an architect interview, framing Azure-fluency as a **transferable skill** ("I designed the Azure-native ML platform at Optum and can apply the same principles to AWS") plays well.

The Azure→AWS translation:

| Azure | AWS |
|---|---|
| Managed Identity | IAM Role + STS / IRSA |
| Microsoft Entra Workload ID | EKS Pod Identity |
| Azure Key Vault | AWS Secrets Manager + KMS |
| Blob Storage / ADLS Gen2 | S3 |
| Azure Files | EFS |
| Azure Disks | EBS |
| ACR | ECR |
| ACI / Container Apps | ECS Fargate / App Runner |
| AKS | EKS |
| Azure Policy | Cloud Custodian + SCPs + Config |
| Private Endpoint | VPC Endpoint (Interface) |
| Microsoft Defender for Cloud | Security Hub + GuardDuty + Inspector |

---

## Sanity check

1. Why is `allowSharedKeyAccess: false` the most security-impactful Azure storage account setting?
2. System-assigned vs user-assigned managed identity — name two scenarios where user-assigned is the right call.
3. What does `DefaultAzureCredential` actually do under the hood, and why is it the recommended pattern?
4. NFS 4.1 over Azure Files doesn't encrypt in transit. How do regulated shops compensate?
5. What's a Disk Encryption Set (DES), and why is it needed for CMK on Azure Disks?
6. Name the Azure equivalent of: VPC endpoint, Org Policy, IAM Role, S3, EFS, Cloud Custodian.

---

## Sources

- [Managed Identities](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [Federated Identity Credentials](https://learn.microsoft.com/entra/workload-id/workload-identity-federation)
- [Azure Blob Storage](https://learn.microsoft.com/azure/storage/blobs/)
- [blobfuse2](https://github.com/Azure/azure-storage-fuse)
- [ADLS Gen2](https://learn.microsoft.com/azure/storage/blobs/data-lake-storage-introduction)
- [Azure Files](https://learn.microsoft.com/azure/storage/files/)
- [Azure Disks](https://learn.microsoft.com/azure/virtual-machines/managed-disks-overview)
- [Azure Key Vault](https://learn.microsoft.com/azure/key-vault/)
- [Azure Container Instances](https://learn.microsoft.com/azure/container-instances/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Confidential containers on ACI](https://learn.microsoft.com/azure/container-instances/container-instances-confidential-overview)
- [Azure Policy](https://learn.microsoft.com/azure/governance/policy/)
- [Microsoft Defender for Cloud](https://learn.microsoft.com/azure/defender-for-cloud/)

→ Next: [16 — K8s architecture — control plane, kubelet, kube-proxy, etcd, CRDs](16_k8s_architecture.md)


\newpage

# 16 — Kubernetes architecture: control plane, kubelet, kube-proxy, etcd, CRDs

> *"K8s is a desired-state controller loop on top of a distributed key-value store. Everything else is mechanism."*

## Why this module exists

You can use K8s for a year without knowing what etcd is. The day a CKA / CKS exam shows up — or the day prod breaks — you need the architecture in your head, not your bookmarks.

This module is the 90-minute "everything fits" map. Modules 17–25 zoom into each piece.

---

## 1. The 30-second mental model

Kubernetes is a **declarative system**:

1. You write a YAML manifest declaring desired state (e.g., "I want 3 replicas of nginx").
2. The API server stores it in etcd.
3. Controllers watch etcd, observe a divergence (zero pods vs three desired), and act to converge.
4. The kubelet on each node creates/destroys containers to match what's assigned to it.

That's the entire model. Every K8s feature is a controller watching a resource and converging.

---

## 2. Control plane components

A cluster has a **control plane** (the brain) and **worker nodes** (the muscle). On managed K8s (EKS/GKE/AKS), the control plane is hidden — you only see worker nodes. On self-managed (kubeadm, Talos), you see both.

### 2.1 The five control-plane components

| Component | Role |
|---|---|
| **kube-apiserver** | The REST/gRPC API. The ONLY thing that writes to etcd. Authenticates, validates, admission-controls. |
| **etcd** | Distributed key-value store (Raft consensus). Single source of truth for cluster state. |
| **kube-scheduler** | Decides which node a Pod runs on (based on resources, taints, affinity, topology). |
| **kube-controller-manager** | Hosts ~30 controllers (Deployment, ReplicaSet, Node, Endpoint, ...). Each is a loop. |
| **cloud-controller-manager** | Cloud-specific controllers (LoadBalancer creation, Node lifecycle on cloud VMs). |

### 2.2 etcd — the heart

- **Raft** consensus algorithm; cluster of 3 or 5 nodes for HA.
- Stores **every** K8s object — pods, secrets, configmaps, custom resources.
- **Snapshotting** for backup is critical (`etcdctl snapshot save`).
- **Encryption at rest** for K8s secrets — must be configured explicitly (module 20).
- **Compaction** — etcd's MVCC accumulates revisions; defrag periodically or it grows.

**Lose etcd = lose the cluster.** This is why etcd backup is the #1 cluster-admin task and why managed K8s services (EKS/GKE/AKS) hide etcd entirely.

### 2.3 The API server is the only path

Nothing writes directly to etcd except the API server. Every component (scheduler, controller-manager, kubelet, custom operators, even kube-proxy) **reads via the API server**. Implications:

- Auth/authorization is centralized at the API server.
- Audit logging is at the API server.
- Admission control (validating, mutating webhooks) is at the API server.
- API server reliability == cluster reliability.

---

## 3. Worker-node components

Each worker node runs three components:

### 3.1 kubelet

The node's agent. Watches the API server for pods assigned to its node, then asks the CRI runtime (containerd / CRI-O) to start/stop containers. Reports node + pod status back. Implements:

- Volume mounts (via CSI).
- Liveness, readiness, startup probes.
- Image pulls (via the container runtime).
- Pod cgroup management.
- Eviction (under resource pressure).

The kubelet is what makes a node "join" a cluster. Its config (`/var/lib/kubelet/config.yaml`) has many security knobs (CIS K8s benchmark hammers these).

### 3.2 Container runtime (CRI)

Almost always **containerd** in 2025–2026. CRI-O on OpenShift. Docker is gone (`dockershim` removed in K8s 1.24).

The kubelet talks to the runtime via the CRI gRPC interface. The runtime pulls images, manages snapshots, calls runc/runsc/kata, and reports status.

### 3.3 kube-proxy

Implements **Service** networking. Two modes:

- **iptables** (default) — installs DNAT rules per Service ClusterIP → backend pod IPs.
- **IPVS** — kernel-level virtual server; better at high service count + connection rate.
- **eBPF** (Cilium replaces kube-proxy entirely) — programmable kernel datapath; cleaner at scale.

On modern clusters with Cilium installed in "kube-proxy-replacement" mode, kube-proxy is **not running**.

---

## 4. Objects and the API hierarchy

### 4.1 The core API

Every object has: `apiVersion`, `kind`, `metadata`, `spec`, `status`.

- **`spec`** — desired state (you write this).
- **`status`** — observed state (controllers write this).

The kube-apiserver presents APIs grouped by **API group + version**:

- `/api/v1` — core group: Pod, Service, ConfigMap, Secret, Namespace, Node, PersistentVolume, ...
- `/apis/apps/v1` — Deployment, StatefulSet, DaemonSet, ReplicaSet.
- `/apis/batch/v1` — Job, CronJob.
- `/apis/networking.k8s.io/v1` — Ingress, NetworkPolicy.
- `/apis/rbac.authorization.k8s.io/v1` — Role, RoleBinding, ClusterRole, ClusterRoleBinding.
- `/apis/storage.k8s.io/v1` — StorageClass, CSIDriver, VolumeSnapshot.

Versions: `v1alpha1` → `v1beta1` → `v1`. Beta becomes default-on in 1.16+; alpha must be enabled per cluster.

### 4.2 Custom Resource Definitions (CRDs)

Anyone (you, vendors) can extend the API. A **CRD** registers a new kind. Examples in the wild:

- `Certificate` (cert-manager).
- `InferenceService` (KServe).
- `PrometheusRule` (kube-prometheus-stack).
- `KafkaTopic` (Strimzi).
- `Ingress` was once a CRD; now it's core.

The **operator pattern**: write a CRD + a controller. The controller watches the CR and reconciles to the desired state, just like built-in controllers. The vast majority of CNCF projects expose themselves this way.

---

## 5. Namespaces — the K8s multi-tenancy primitive

Namespaces partition the cluster's resources. Default namespaces:

| Namespace | Use |
|---|---|
| `default` | If you don't specify, this is where things land. Don't use in prod. |
| `kube-system` | Control-plane components and addons. Don't touch. |
| `kube-public` | Cluster-info, readable to all (auth + auth model). |
| `kube-node-lease` | Node heartbeats. |

You create namespaces per team / per environment / per workload tier:

```bash
kubectl create namespace ml-serving
kubectl create namespace ml-training
kubectl create namespace data-pipeline
```

**RBAC**, **NetworkPolicy**, **ResourceQuota**, **LimitRange**, **PodSecurity** are all namespace-scoped — they're the multi-tenancy levers.

### 5.1 Namespaces are NOT a security boundary by themselves

A `ServiceAccount` in one namespace can talk to a Service in another namespace by default. **NetworkPolicy** is what makes it a real boundary (module 18). A vanilla cluster has no NetworkPolicy enforcement — you get one (Calico, Cilium) at install.

---

## 6. The controller pattern (operator-grade understanding)

A controller is a **for-loop**:

```python
while True:
    desired = api.watch("CustomResource")  # blocks on changes
    actual  = read_world_state()
    if desired != actual:
        reconcile(desired, actual)
    sleep(0.1)
```

Every CNCF tool that "extends K8s" is this loop wearing a costume. Knowing this:

- Explains why deletes are eventually consistent.
- Explains why `kubectl get` shows stale state during reconciliation.
- Explains why operators need RBAC for the resources they reconcile.
- Explains why misconfigured admission webhooks can hard-fail the API server.

---

## 7. Networking primitives (preview of module 18)

K8s networking has three layers:

1. **Pod network** — every pod gets a routable IP. Implemented by a **CNI plugin** (Calico, Cilium, AWS VPC CNI, Azure CNI, GCP CNI).
2. **Service network** — virtual IPs (`ClusterIP`) abstracting groups of pods. Implemented by kube-proxy (or Cilium replacement).
3. **Ingress / Gateway** — external HTTP/HTTPS into the cluster. Implemented by an ingress controller (nginx, Traefik, Envoy/Contour, Cilium ingress, AWS ALB Controller, etc.).

For data exposure: the CNI choice **and** NetworkPolicy enforcement determine container-to-container blast radius.

---

## 8. Storage primitives (preview of module 19)

- **Volume** — anything mounted into a pod (emptyDir, ConfigMap, Secret, PVC, ephemeral CSI).
- **PersistentVolume (PV)** — a real storage resource (EBS volume, NFS share, Ceph RBD).
- **PersistentVolumeClaim (PVC)** — a request for storage by a workload.
- **StorageClass (SC)** — a parametrized recipe for creating PVs on demand (e.g., "gp3 in us-east-1a").
- **CSI driver** — the interface between K8s and a storage backend.

---

## 9. Identity primitives (preview of modules 20–21)

- **ServiceAccount** — pod identity. Default SA exists per namespace.
- **Role / ClusterRole** — verbs + resources.
- **RoleBinding / ClusterRoleBinding** — link a Role to a SA / User / Group.
- **TokenRequest API** — short-lived projected SA tokens (default since 1.22).

For cloud identity: **IRSA** (EKS) / **Workload Identity** (GKE) / **Entra Workload ID** (AKS) federate K8s SAs to cloud IAM. Modules 26-28.

---

## 10. The kubectl request flow

What happens on `kubectl apply -f deployment.yaml`:

```
1. kubectl reads ~/.kube/config; resolves current context.
2. kubectl POSTs to API server (HTTPS, mTLS via your client cert / OIDC token).
3. API server authenticates: cert chain / OIDC / webhook.
4. API server authorizes: RBAC (or webhook/OPA).
5. API server runs **mutating** admission webhooks (Kyverno, defaults).
6. API server runs **validating** admission webhooks (Kyverno, OPA, PSA).
7. API server writes to etcd.
8. Deployment controller wakes, creates ReplicaSet.
9. ReplicaSet controller wakes, creates Pods.
10. Scheduler watches unscheduled Pods, picks a node.
11. Kubelet on that node watches its pods, asks containerd to pull + run.
12. CNI plugin assigns pod IP.
13. CSI driver mounts requested volumes.
14. Container starts. Pod IP exposed via Service via kube-proxy / Cilium.
```

Every step is a control point you can break or harden. CKA/CKS exams test that you can trace this flow.

---

## 11. The managed-K8s delta (EKS, GKE, AKS)

| | EKS | GKE | AKS |
|---|---|---|---|
| Control plane managed by | AWS | Google | Microsoft |
| Control plane SLA | 99.95% | 99.95% (region), 99.99% (zonal) | 99.95% (paid uptime SLA) |
| etcd visible to user | No | No | No |
| Custom Admission Controllers? | Yes (webhooks) | Yes (webhooks) | Yes (webhooks) |
| Bring your own CNI? | Yes (VPC CNI default; also Cilium, Calico) | Yes (Dataplane V2 / GKE CNI / Cilium) | Yes (Azure CNI, Kubenet, Cilium) |
| Default node OS | Bottlerocket, Amazon Linux 2/2023 | Container-Optimized OS (COS), Ubuntu | Ubuntu, Mariner (Azure Linux) |
| Pod identity model | IRSA, EKS Pod Identity | Workload Identity for GKE | Entra Workload ID |
| Auto-upgrade | Optional | Optional, can be enforced | Optional |
| Cost | $0.10/hr per cluster + node costs | $0.10/hr (Standard); Autopilot priced per pod | Free (Standard) or paid SLA |

---

## 12. The single most-asked CKA question

"How would you investigate a Pod stuck in `ImagePullBackOff`?"

```bash
kubectl describe pod <name>            # Events at bottom
kubectl get events --sort-by='.lastTimestamp' -n <ns>
kubectl logs -p <name>                 # previous container logs
kubectl get nodes -o wide              # node status
kubectl describe node <node-name>      # taints, resources, kubelet status
```

Hits to investigate (the same answer repeated thousands of times):

- Image typo / tag missing.
- Registry auth (no `imagePullSecrets` or wrong one).
- Private registry without network reachability (no VPC endpoint, no NAT).
- Image bigger than node ephemeral storage.

This is **the** debugging question. Master the flow.

---

## Sanity check

1. Why is etcd backup the #1 cluster admin task?
2. What's the difference between a Pod and a Deployment, and why do you almost never `kubectl run` a Pod directly?
3. The kube-scheduler decides node placement based on what factors?
4. Why does the operator pattern work for nearly any "I want to manage X declaratively in K8s" use case?
5. In a managed K8s service, what becomes the customer's responsibility vs the cloud provider's?
6. What does `kubectl apply` actually do at the API server level (list the steps).

---

## Sources

- [Kubernetes Components](https://kubernetes.io/docs/concepts/overview/components/)
- [etcd docs](https://etcd.io/docs/)
- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [Custom Resources](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)

→ Next: [17 — Workload objects — Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob](17_workload_objects.md)


\newpage

# 17 — K8s workload objects: Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob

> *"Pick the right workload object. Half of K8s 'failures' are someone using a Deployment where they needed a StatefulSet."*

## Why this module exists

A Pod is the unit of execution. Five higher-level controllers wrap Pods for different lifecycles. Picking correctly is a senior-engineer judgment call.

---

## 1. Pod — the atom

A Pod is **one or more containers** that share network namespace, IPC, and (optionally) volumes. The containers are co-scheduled on one node and live/die together.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: default
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
      resources:
        requests: { cpu: "100m", memory: "128Mi" }
        limits:   { cpu: "500m", memory: "512Mi" }
```

You **rarely** create Pods directly in production. You create a higher-level controller (Deployment, etc.) that creates Pods for you. Reason: a bare Pod has no self-healing — if it dies, it's gone.

### 1.1 Multi-container patterns

| Pattern | Sidecar example | Lifecycle |
|---|---|---|
| **Init container** | DB migration before app starts | Runs to completion, then app starts |
| **Sidecar** (init-style, but stays running, since 1.28) | Log forwarder, mesh proxy, Vault Agent | Lifecycle bound to main container |
| **Ambassador** | Proxy for external service auth (e.g., Cloud SQL Proxy) | Same as sidecar |
| **Adapter** | Format-conversion proxy (e.g., Prom exporter for legacy app) | Same |

K8s 1.28 added **sidecar containers** as first-class init containers with `restartPolicy: Always` — they start before the main container and live as long as it does. This is the right primitive for Istio/Linkerd proxies, Vault Agent, fluent-bit. Before 1.28, sidecars were just regular containers with a startup-race risk.

### 1.2 Probes

- **livenessProbe** — restart the container if this fails (the "is it alive?" check).
- **readinessProbe** — remove from Service endpoints if this fails (the "ready for traffic?" check).
- **startupProbe** — give a slow-starting container time before liveness kicks in.

Probe types: `httpGet`, `tcpSocket`, `exec`, `grpc`.

The most common mistake: confusing liveness and readiness. Liveness = "kill and restart"; readiness = "stop sending traffic." A slow-loading model server needs **readiness** (don't send traffic until model loaded) and a generous **startup** probe (don't kill while loading).

---

## 2. Deployment — stateless replicas

The workhorse. Wraps a Pod template in a ReplicaSet, manages rolling updates.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: infer-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: { app: infer-server }
  template:
    metadata:
      labels: { app: infer-server }
    spec:
      containers:
        - name: infer
          image: myorg/infer:1.2.3
          ports: [{ containerPort: 8080 }]
```

`maxUnavailable: 0, maxSurge: 1` is the safe default for production: never go below desired replicas; add one extra during rollout. The default (`25%, 25%`) is fine for many workloads.

When to use Deployment: stateless web apps, model servers, API gateways, anything where Pod-1 and Pod-2 are interchangeable.

### 2.1 Rollback

```bash
kubectl rollout undo deployment/infer-server
kubectl rollout history deployment/infer-server
kubectl rollout status deployment/infer-server
```

The ReplicaSet history (10 revisions by default) is what enables rollback. Don't `kubectl delete rs` casually.

---

## 3. StatefulSet — stable identity per replica

When pod identity matters: Pod 0 is "the leader," Pod 1 is "follower 1," and pods need stable network names and persistent storage.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless   # required headless Service
  replicas: 3
  selector:
    matchLabels: { app: postgres }
  template: { ... }
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: gp3
        resources: { requests: { storage: 100Gi } }
```

Properties:

- Pods named `<sts>-0`, `<sts>-1`, ... (stable).
- DNS: `postgres-0.postgres-headless.ns.svc.cluster.local`.
- PVCs auto-created from `volumeClaimTemplates`, one per pod, **persistent across pod replace** (the volume sticks to ordinal).
- Ordered startup/teardown by default (Pod 0 ready before Pod 1 starts).
- Pod deletion does NOT delete PVCs (you must opt in to that).

When to use StatefulSet: databases (Postgres HA, Cassandra, MongoDB), distributed message queues (Kafka, NATS JetStream), distributed caches (Redis Cluster), distributed FS (CephFS), some Spark + Flink configs.

For ML: vLLM with tensor-parallelism may want StatefulSet (rank 0 vs rank N matters), but most serving workloads are stateless Deployments.

---

## 4. DaemonSet — one Pod per node

Used for node agents: log forwarders (Fluent Bit), monitoring agents (Prometheus node-exporter, Datadog agent), CNI dataplane (Cilium agent), CSI driver components, GPU operator's device plugin.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
spec:
  selector:
    matchLabels: { app: node-exporter }
  template:
    spec:
      hostNetwork: true                  # often needed for node-level metrics
      tolerations:
        - operator: Exists               # tolerate ALL taints (run on every node, period)
      containers: [...]
```

DaemonSet is **the** privileged workload type — its pods often need `hostNetwork`, `hostPID`, or privileged containers. PSA `restricted` policy disallows these; DaemonSets typically live in a `kube-system`-like namespace labeled with PSA `privileged` (module 22).

---

## 5. Job — one-shot task

Runs a Pod (or N Pods) to completion. Retries on failure up to `backoffLimit`.

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: db-migrate }
spec:
  backoffLimit: 3
  ttlSecondsAfterFinished: 600       # auto-delete 10 min after success
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: migrate
          image: myorg/migrate:1.0
          command: ["python", "manage.py", "migrate"]
```

For batch jobs:

- `completions: N` — total successful pod runs needed.
- `parallelism: M` — how many in parallel.
- `completionMode: Indexed` — gives each pod a `JOB_COMPLETION_INDEX` env var (since 1.21). Useful for distributed ML training where rank == index.

### 5.1 ML training as Job

```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: train-bert-2026-05-21 }
spec:
  completions: 8
  parallelism: 8
  completionMode: Indexed
  backoffLimit: 0                      # don't retry ML training; let observability re-launch
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: train
          image: nvcr.io/nvidia/pytorch:24.06-py3
          command: ["torchrun", "--nproc-per-node=8", "--nnodes=8",
                    "--node-rank=$(JOB_COMPLETION_INDEX)",
                    "--rdzv-backend=c10d", "train.py"]
          resources:
            limits: { nvidia.com/gpu: 8 }
```

For more sophisticated training, use **Kubeflow Training Operator's PyTorchJob** (module 31) which handles rendezvous, rank assignment, and failure modes.

---

## 6. CronJob — scheduled jobs

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: nightly-etl }
spec:
  schedule: "0 2 * * *"                # 02:00 UTC daily
  timeZone: "America/New_York"          # k8s 1.27+
  concurrencyPolicy: Forbid             # don't overlap
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate: { spec: { ... } }
```

Cron expression is standard POSIX. `timeZone` field is opt-in since 1.27.

When NOT to use CronJob: anything you need observability/retries/lineage on. Use Airflow (Topic 06) or Argo Workflows for ETL/ML pipelines. CronJob is for "run this script nightly" with no parents/dependencies.

---

## 7. ReplicaSet — almost never directly

ReplicaSet is what Deployment manages under the hood. Don't create directly.

---

## 8. Resource requests vs limits

Every container should declare:

```yaml
resources:
  requests:
    cpu: "100m"          # 0.1 CPU
    memory: "256Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
    nvidia.com/gpu: 1
```

- **Requests** affect scheduling (the scheduler reserves this much).
- **Limits** affect runtime (cgroups enforce; over-limit memory = OOM-kill; over-limit CPU = throttling).

For ML serving: tight memory limits (no over-allocation = no node OOM crash); cpu limits generous (CPU throttling causes p99 latency spikes).

For training: requests == limits == node capacity (you want exclusive use of the GPU).

### 8.1 QoS classes

K8s derives a QoS class from your requests/limits:

- **Guaranteed** — requests == limits for both cpu and memory. Last to be evicted under pressure.
- **Burstable** — requests set, limits set higher (or unset).
- **BestEffort** — nothing set. First to be evicted.

For prod, always set requests and limits (Guaranteed or close to it).

---

## 9. Pod scheduling primitives

- **nodeSelector** — simple label match (`disktype: ssd`).
- **nodeAffinity** — richer expression (`In`, `NotIn`, `Exists`, ...) with required vs preferred.
- **podAffinity / podAntiAffinity** — "schedule near / away from pods matching label."
- **taints + tolerations** — keep workloads off certain nodes unless they tolerate the taint.
- **topologySpreadConstraints** — spread pods across zones/nodes evenly.

For GPU nodes:
```yaml
nodeSelector:
  nvidia.com/gpu.product: H100
tolerations:
  - key: nvidia.com/gpu
    operator: Exists
    effect: NoSchedule
```

Karpenter (module 31) provisions GPU nodes with these taints automatically.

---

## 10. PodDisruptionBudget (PDB) — protecting availability

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: infer-server-pdb }
spec:
  minAvailable: 2
  selector: { matchLabels: { app: infer-server } }
```

PDB blocks **voluntary** disruptions (node drain, scaling down, upgrades) if they would violate the budget. **Involuntary** disruptions (node crash) still happen. PDB is what keeps a careless `kubectl drain` from taking the whole service down.

For prod services with > 1 replica, **always** define a PDB.

---

## Sanity check

1. When do you need a StatefulSet instead of a Deployment? Name two real workloads.
2. Why do K8s 1.28+ sidecars (init container with `restartPolicy: Always`) fix problems that the older sidecar pattern had?
3. What's the difference between a livenessProbe and a readinessProbe, and which one do you need for a model server that takes 90s to load?
4. CronJob is the wrong tool when you need what?
5. QoS class Guaranteed requires what exact configuration?
6. Why is a PDB needed even on a managed K8s service like EKS?

---

## Sources

- [Pod concept](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [DaemonSets](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/)
- [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Sidecar containers (1.28+)](https://kubernetes.io/blog/2023/08/25/native-sidecar-containers/)
- [PodDisruptionBudget](https://kubernetes.io/docs/concepts/workloads/pods/disruptions/)
- [QoS classes](https://kubernetes.io/docs/concepts/workloads/pods/pod-qos/)

→ Next: [18 — Services & networking — Ingress, Gateway API, NetworkPolicy, CNI](18_k8s_networking.md)


\newpage

# 18 — K8s services & networking: ClusterIP, Ingress, Gateway API, NetworkPolicy, CNI

## Why this module exists

K8s networking is layered: pod network, service abstraction, ingress/gateway for external traffic, and NetworkPolicy for segmentation. Each layer has its own primitives — and every CNI plugin implements them differently.

---

## 1. The flat-pod-network promise

K8s requires: **every pod can talk to every other pod without NAT**. The CNI plugin implements this. Three families:

| Family | Examples | Datapath |
|---|---|---|
| **Overlay** (tunneled) | Flannel VXLAN, Calico VXLAN | Encapsulated UDP between nodes |
| **Routed (no overlay)** | Calico BGP, Cilium native routing | Underlying network knows pod CIDRs |
| **Cloud-native** (per-pod ENI) | AWS VPC CNI, Azure CNI | Pod gets an actual VPC IP |

Cloud-native CNIs (VPC CNI, Azure CNI) give pods routable VPC IPs — clean for SG-per-pod, NSG-per-pod. Tradeoff: pods-per-node limited by ENI/NIC capacity.

---

## 2. Service types

A **Service** is a stable virtual endpoint in front of a set of pods (selected by label).

| Type | Reachable from | Mechanism |
|---|---|---|
| **ClusterIP** (default) | Inside cluster only | kube-proxy / Cilium installs iptables/eBPF rules |
| **NodePort** | Any node IP on a high port (30000-32767) | iptables redirects nodeport → ClusterIP |
| **LoadBalancer** | External | Cloud-provided LB (ELB/ALB/NLB, GCP LB, Azure LB) |
| **ExternalName** | DNS CNAME only (no proxying) | CoreDNS returns CNAME |

ClusterIP is the default and most-used. For external traffic prefer **Ingress** or **Gateway API** (a higher abstraction on top of LoadBalancer).

### 2.1 Service discovery

CoreDNS resolves:
- `<svc>` (within namespace).
- `<svc>.<ns>` (cross-namespace).
- `<svc>.<ns>.svc.cluster.local` (FQDN).

Headless Service (`clusterIP: None`) returns pod IPs directly, not a VIP — required for StatefulSet member-by-DNS access.

---

## 3. Ingress vs Gateway API

### 3.1 Ingress (legacy but still everywhere)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts: [api.example.com]
      secretName: api-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-server
                port: { number: 80 }
```

An **Ingress Controller** (nginx, Traefik, Envoy/Contour, AWS Load Balancer Controller, GCP GLB Controller, Azure Application Gateway Ingress Controller) watches Ingress resources and configures the actual data path.

Ingress is HTTP-only (mostly). For non-HTTP, you fell back to NLB or Service LoadBalancer with raw TCP.

### 3.2 Gateway API — the successor (v1.0 Oct 2023)

Gateway API is the next-gen replacement. Three layers:

- **GatewayClass** — vendor-specific config (e.g., AWS ALB, Cilium, Envoy Gateway).
- **Gateway** — an instance: listeners, ports, certs.
- **HTTPRoute / TCPRoute / TLSRoute / GRPCRoute / UDPRoute** — routing rules to backend services.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: prod-gateway }
spec:
  gatewayClassName: aws-alb
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls: { mode: Terminate, certificateRefs: [{ name: api-tls }] }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: api-route }
spec:
  parentRefs: [{ name: prod-gateway }]
  hostnames: ["api.example.com"]
  rules:
    - matches: [{ path: { type: PathPrefix, value: "/" } }]
      backendRefs: [{ name: api-server, port: 80 }]
```

Advantages over Ingress:
- Role-oriented (cluster operator owns GatewayClass+Gateway; app owns HTTPRoute).
- Native non-HTTP support (TCP/UDP/TLS/gRPC).
- Header-based / query-based routing, traffic-splitting (canary, A/B), and more — all standardized.

For new clusters: prefer Gateway API. The ingress controllers are migrating (Envoy Gateway, Contour, Cilium are early adopters; nginx-ingress is slower).

---

## 4. NetworkPolicy — the in-cluster firewall

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow
  namespace: ml-serving
spec:
  podSelector: { matchLabels: { app: api-server } }
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { name: ml-clients } }
          podSelector: { matchLabels: { tier: client } }
      ports: [{ port: 8080, protocol: TCP }]
  egress:
    - to: [{ podSelector: { matchLabels: { app: postgres } } }]
      ports: [{ port: 5432 }]
    - to: [{ namespaceSelector: { matchLabels: { name: kube-system } }
            ,podSelector: { matchLabels: { k8s-app: kube-dns } } }]
      ports: [{ port: 53, protocol: UDP }]
```

Properties:

- **Default-deny is not automatic** — a vanilla cluster has no NetworkPolicy enforcement.
- The first NetworkPolicy that selects a pod **switches that pod to default-deny** for the policy types listed. Pods not selected by any policy: still allow-all.
- Egress rules must explicitly allow DNS (UDP/53 to kube-system kube-dns pods) — or every outbound resolution breaks.

### 4.1 CNIs that enforce NetworkPolicy

- **Calico** — full support, in BGP / VXLAN / eBPF modes.
- **Cilium** — full + L7 (HTTP method/path-aware).
- **Antrea** — full.
- **Weave Net** — full but project is unmaintained.

The default CNIs on managed K8s:
- **AWS VPC CNI** — basic NetworkPolicy support added in 2023 (also supports SG-per-pod, an AWS-specific belt-and-braces).
- **Azure CNI** — supports via Calico or Cilium addon.
- **GKE Dataplane V2** — Cilium-based, full support.

### 4.2 Beyond NetworkPolicy

L7-aware policy (e.g., "only POST /v1/predict, not /admin") is **not** in the K8s NetworkPolicy spec. For that you need:

- **Cilium L7 policy** — `httpRules` in CiliumNetworkPolicy CRD.
- **Service mesh** (Istio, Linkerd) — AuthorizationPolicy CRD.

For regulated finance: NetworkPolicy default-deny at namespace level + service mesh AuthorizationPolicy for L7. Both. Belt and braces.

---

## 5. The Cilium / eBPF revolution

Cilium replaces kube-proxy and CNI with an eBPF-based dataplane. Key wins:

- **Kube-proxy-less mode** — services implemented in eBPF, no iptables chains.
- **Identity-based policy** — instead of IP-based (IPs change with pod restarts).
- **L7 visibility** — Hubble (Cilium's observability) shows HTTP method/path/status without sidecars.
- **Mesh** without sidecar — Cilium Service Mesh provides mTLS without a per-pod proxy.

On modern GKE (Dataplane V2), EKS (`vpc-cni` with Cilium chained for policy, or AWS Cilium support), AKS (Azure CNI Powered by Cilium), Cilium is the default network-policy + visibility plane.

For the architect interview: knowing "Cilium replaces kube-proxy" + "Hubble gives L7 flow logs" + "Cilium can act as the service mesh too" is the modern stack.

---

## 6. CoreDNS — the cluster's DNS

CoreDNS runs as a Deployment (usually 2 replicas) in `kube-system`. It resolves:

- `<svc>.<ns>.svc.cluster.local` → ClusterIP.
- `<pod>.<ns>.pod.cluster.local` → pod IP (less common).
- External names — forwarded to upstream (cloud DNS, your corp DNS).

Performance pitfall: pods do many DNS lookups per second. **NodeLocal DNS Cache** is a DaemonSet pattern that caches DNS on each node — install it on any cluster doing serious traffic.

---

## 7. East-west TLS / mTLS

By default, pod-to-pod traffic in the cluster is **plaintext**. Most regulated shops want mTLS everywhere east-west.

Options:

- **Service mesh** (Istio, Linkerd) — automatic sidecar mTLS.
- **Cilium ambient mesh / mTLS** — sidecarless.
- **Application-level TLS** — apps mint and rotate their own certs (e.g., via cert-manager) and talk HTTPS to each other.

For Capital One–style postures: service mesh (Istio or Linkerd) is the standard answer. Module 32 covers this.

---

## 8. Ingress security checklist

- TLS termination at the ingress (cert-manager + Let's Encrypt or ACM/GAR-certs/AKV).
- HTTP→HTTPS redirect.
- HSTS header.
- WAF in front (AWS WAF on ALB, GCP Cloud Armor, Azure App Gateway WAF, or in-cluster ModSecurity).
- Rate limiting per IP / per user.
- Auth at the ingress where possible (OIDC via oauth2-proxy, IAP on GCP).

---

## 9. Common ingress controllers

| Controller | License | Notable |
|---|---|---|
| **ingress-nginx** | Apache 2.0 | The community default; widely deployed |
| **NGINX Inc.** | Mixed | Commercial; not the same project as ingress-nginx |
| **Traefik** | MIT | Auto-discovery, friendly |
| **Envoy/Contour** | Apache 2.0 | Heritage in cloud-native; Gateway API leader |
| **Envoy Gateway** | Apache 2.0 | Pure Gateway API impl on Envoy |
| **HAProxy Ingress** | Apache 2.0 | High-perf |
| **AWS Load Balancer Controller** | Apache 2.0 | Provisions ALB/NLB |
| **GKE Ingress / GCP Gateway** | Closed | Provisions GCP LB |
| **AGIC (Application Gateway Ingress Controller)** | Closed | Provisions Azure App Gateway |
| **Cilium Ingress / Gateway** | Apache 2.0 | Native to Cilium dataplane |

---

## 10. The networking-data-exposure summary

For a regulated ML workload:

1. **CNI**: Cilium (or VPC CNI + Cilium overlay for policy).
2. **Pod IPs**: VPC-routable if cloud (EKS, AKS, GKE); pod-network-only on-prem (Calico).
3. **Service mesh**: Istio (sidecar or ambient) or Linkerd for mTLS east-west.
4. **NetworkPolicy**: namespace-default-deny, explicit allows.
5. **Egress**: allowed only to declared destinations (cloud APIs via VPC endpoints, internal services).
6. **Ingress**: TLS terminated, WAF in front, OIDC auth, rate-limited.
7. **DNS**: NodeLocal DNS Cache; controlled upstream resolver.
8. **Observability**: Hubble for flow logs, Falco for runtime, OpenTelemetry for traces.

---

## Sanity check

1. Why is "NetworkPolicy default-deny" not automatic on a fresh cluster?
2. What's the migration story from Ingress to Gateway API for a team using `ingress-nginx` today?
3. Cilium replaces kube-proxy. What does it gain by doing so?
4. Why does an Egress NetworkPolicy that doesn't allow UDP/53 break the pod completely?
5. How does a Service mesh provide mTLS that NetworkPolicy doesn't?
6. AWS VPC CNI gives pods VPC IPs. What's the per-node limit, and how does it bite?

---

## Sources

- [K8s Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Gateway API](https://gateway-api.sigs.k8s.io/)
- [NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Cilium docs](https://docs.cilium.io/)
- [Calico docs](https://docs.tigera.io/calico/latest/)
- [CoreDNS](https://coredns.io/)
- [NodeLocal DNS Cache](https://kubernetes.io/docs/tasks/administer-cluster/nodelocaldns/)

→ Next: [19 — Storage in K8s — PV, PVC, StorageClass, CSI, ephemeral, projected](19_k8s_storage.md)


\newpage

# 19 — Storage in K8s: PV, PVC, StorageClass, CSI, ephemeral, projected

## Why this module exists

K8s storage is layered. Apps request via **PVC**; a **PV** is the actual storage; a **StorageClass** is the parametrized recipe; a **CSI driver** is the cloud/storage integration. Knowing where each layer fits unblocks every "my pod can't mount X" debugging session.

---

## 1. The 4-tuple — PVC, PV, StorageClass, CSI

```
Pod        →  uses        →  PVC (a claim, namespaced)
PVC        →  binds to    →  PV  (cluster-scoped, real storage)
PV         →  created by  →  StorageClass + provisioner
Provisioner →  is part of →  CSI driver (in-tree drivers all migrated out by 2024-2025)
```

A user creates a PVC. The PVC binds to a PV. If `volumeBindingMode: WaitForFirstConsumer`, the PV isn't provisioned until a pod actually claims the PVC — important for topology (you want the PV in the AZ of the scheduled pod).

---

## 2. PVC example

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: model-cache, namespace: ml-serving }
spec:
  storageClassName: gp3
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 50Gi
```

`accessModes`:

- **ReadWriteOnce (RWO)** — single node mount. EBS, GCE PD, Azure Disk.
- **ReadWriteOncePod (RWOP, GA 1.29)** — single pod mount (stricter).
- **ReadWriteMany (RWX)** — multiple nodes. EFS, Azure Files, GCS Fuse, Filestore, NFS.
- **ReadOnlyMany (ROX)** — read-only mount on multiple nodes.

For ML training (8+ pods reading same data) → RWX. For DB data (StatefulSet) → RWO.

---

## 3. StorageClass — the recipe

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3 }
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789012:key/abc..."
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

`reclaimPolicy: Delete` — delete the underlying storage when PVC is deleted. **For prod data: use `Retain`** so an accidental PVC delete doesn't wipe the disk; you reclaim manually.

`allowVolumeExpansion: true` — lets you `kubectl edit pvc` to grow the volume online (most CSI drivers support).

`volumeBindingMode: WaitForFirstConsumer` — delays provisioning until a pod schedules to a specific AZ. **Always use this on cloud disks** (otherwise PV may land in wrong AZ).

---

## 4. CSI — the plug-in spec

Container Storage Interface. Every storage backend ships a driver. Two pods per driver:

- **Controller** (one or two replicas, often as a Deployment): handles provisioning (CreateVolume API call), attach/detach orchestration, snapshot.
- **Node** (DaemonSet): runs on every node, handles mounting on demand.

Common drivers:

| Cloud | Driver | Notes |
|---|---|---|
| AWS | ebs.csi.aws.com | EBS (RWO) |
| AWS | efs.csi.aws.com | EFS (RWX) |
| AWS | fsx.csi.aws.com | FSx for Lustre |
| AWS | s3.csi.aws.com | Mountpoint for S3 |
| GCP | pd.csi.storage.gke.io | PD (RWO) |
| GCP | filestore.csi.storage.gke.io | Filestore (RWX) |
| GCP | gcs.csi.storage.gke.io | GCS Fuse |
| Azure | disk.csi.azure.com | Azure Disk (RWO) |
| Azure | file.csi.azure.com | Azure Files (RWX) |
| Azure | blob.csi.azure.com | Azure Blob |
| On-prem | rook-ceph.rbd.csi.ceph.com | Ceph RBD |
| On-prem | longhorn.io | Longhorn |
| On-prem | mayastor.openebs.io | OpenEBS Mayastor |
| On-prem | portworx.io | Portworx |

`kubectl get csidrivers` lists what's installed.

---

## 5. Ephemeral volumes — the underused category

Not everything needs to persist. Three ephemeral types:

### 5.1 `emptyDir`

Allocated on the node, gone when pod is gone. Default backed by node disk:

```yaml
volumes:
  - name: scratch
    emptyDir: { sizeLimit: 50Gi }
```

For RAM-backed (tmpfs):

```yaml
volumes:
  - name: tmpfs-scratch
    emptyDir: { medium: Memory, sizeLimit: 8Gi }
```

For ML: `emptyDir: { medium: Memory }` is essential for PyTorch DataLoader `/dev/shm` problem — without it, you get those "Bus error" crashes from module 09.

### 5.2 Generic ephemeral volumes

PVC-backed but lifetime is bound to the pod:

```yaml
volumes:
  - name: temp-pvc
    ephemeral:
      volumeClaimTemplate:
        spec:
          accessModes: [ReadWriteOnce]
          storageClassName: gp3
          resources: { requests: { storage: 100Gi } }
```

Used for: per-pod scratch on a real PV (e.g., 500Gi NVMe for training intermediate data).

### 5.3 CSI ephemeral volumes

CSI drivers can expose ephemeral inline (no PVC). The Secret Store CSI driver (modules 20, 26-28) is the canonical example.

---

## 6. Projected volumes — secrets, configmaps, SA tokens

Project multiple sources into one volume:

```yaml
volumes:
  - name: app-config
    projected:
      sources:
        - configMap:
            name: app-cm
            items: [{ key: app.yaml, path: config/app.yaml }]
        - secret:
            name: app-secret
            items: [{ key: token, path: secrets/token }]
        - serviceAccountToken:
            audience: api.internal.example.com
            expirationSeconds: 3600
            path: token/sa-token
        - downwardAPI:
            items:
              - path: meta/podname
                fieldRef: { fieldPath: metadata.name }
```

The `serviceAccountToken` projection (GA 1.20) is the modern pattern: short-lived (1-hour default), audience-scoped tokens — exactly what cloud IAM federation needs (IRSA, Workload Identity).

---

## 7. CSI snapshots & restore

Most production CSI drivers support snapshots:

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata: { name: training-data-2026-05-21 }
spec:
  volumeSnapshotClassName: ebs-snap
  source:
    persistentVolumeClaimName: training-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data-restore }
spec:
  storageClassName: gp3
  accessModes: [ReadWriteOnce]
  dataSource:
    name: training-data-2026-05-21
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  resources: { requests: { storage: 100Gi } }
```

Velero builds on this for cluster-wide backup (module 29).

---

## 8. Local PVs

A `local` PV is a node-local disk, statically provisioned. Used for:

- High-perf NVMe attached to a node (databases, ClickHouse, vector indices).
- Distributed-storage systems (Cassandra, ScyllaDB, OpenSearch).

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: nvme-1 }
spec:
  capacity: { storage: 1Ti }
  volumeMode: Filesystem
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-nvme
  local: { path: /mnt/disks/nvme-1 }
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - { key: kubernetes.io/hostname, operator: In, values: [node-1] }
```

Pods using this PV will only schedule to `node-1` — local storage doesn't move with pods.

---

## 9. Common gotchas

- **`volumeBindingMode: Immediate`** (the default in old StorageClasses) creates a PV before pod is scheduled — often in the wrong AZ. **Always use `WaitForFirstConsumer`**.
- **Pod can't write to a mounted volume** — UID mismatch. Set `fsGroup` in pod security context to chown.
- **`fsGroup` on a 10TB EFS** — chown'ing 10M files takes forever. Use `fsGroupChangePolicy: OnRootMismatch` (GA 1.23+) to only fix the root.
- **Stuck terminating PVC** — finalizer not removed. `kubectl patch pvc <name> -p '{"metadata":{"finalizers":null}}'`.
- **CSI driver pod evicted** — your storage operations grind to a halt. Pin CSI drivers as `priorityClassName: system-node-critical`.

---

## 10. The Capital One signal

For regulated finance ML on EKS:
- EBS CSI with CMK encryption + `reclaimPolicy: Retain`.
- EFS CSI for shared training data + Access Points for multi-tenancy.
- FSx for Lustre CSI for high-perf training (1k+ GPU).
- Mountpoint-for-S3 CSI for cold training data read.
- Velero for backup.
- Cloud Custodian / Kyverno policy: "no PVC without `storageClassName`" / "no PVC without `Retain` policy in prod."

Module 26 has the full EKS deep dive.

---

## Sanity check

1. Why is `volumeBindingMode: WaitForFirstConsumer` mandatory on cloud disks?
2. RWO vs RWOP — when do you actually need RWOP?
3. The PyTorch DataLoader bug is fixed by which exact `emptyDir` setting?
4. Why does `fsGroup` need `fsGroupChangePolicy: OnRootMismatch` on large EFS volumes?
5. A `local` PV is rigidly bound to one node — what does that mean for pod scheduling?
6. CSI driver controller vs node — which is a Deployment, which is a DaemonSet, and what does each do?

---

## Sources

- [PV / PVC concepts](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- [CSI](https://kubernetes-csi.github.io/docs/)
- [VolumeSnapshot](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)
- [Projected Volumes](https://kubernetes.io/docs/concepts/storage/projected-volumes/)
- [Ephemeral Volumes](https://kubernetes.io/docs/concepts/storage/ephemeral-volumes/)

→ Next: [20 — ConfigMaps & Secrets — etcd encryption-at-rest, sealed-secrets, external-secrets](20_configmap_secrets.md)


\newpage

# 20 — ConfigMaps & Secrets: etcd encryption, sealed-secrets, external-secrets

## Why this module exists

K8s Secrets are **base64-encoded plaintext in etcd by default**. That sentence shocks new operators. This module covers the four production patterns that fix it: etcd encryption-at-rest, Sealed Secrets, External Secrets Operator, and SOPS.

---

## 1. ConfigMap vs Secret

Both store key/value config. The differences:

- **Secret** values are auto-base64-decoded when mounted; ConfigMap values are mounted as-is.
- **Secret** has a `type` field (`Opaque`, `kubernetes.io/dockerconfigjson`, `kubernetes.io/tls`, ...).
- **Secret** is opt-in for etcd encryption-at-rest.
- **Audit log** treats them differently (Secret reads can be redacted/audited more aggressively).
- **`kubectl get secret`** redacts values by default (but `-o yaml` shows base64; `-o jsonpath` decodes).

ConfigMap: app config (feature flags, paths, log levels). Secret: passwords, tokens, certs.

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:
  password: aHVudGVyMg==          # base64("hunter2") — NOT encryption
```

base64 is **not encryption**. Anyone with the YAML has the plaintext. Stop pretending otherwise.

---

## 2. Mounting

```yaml
spec:
  containers:
    - name: app
      image: myapp
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef: { name: db-creds, key: password }
      volumeMounts:
        - name: cfg
          mountPath: /etc/cfg
          readOnly: true
        - name: tls
          mountPath: /etc/tls
          readOnly: true
  volumes:
    - name: cfg
      configMap: { name: app-config }
    - name: tls
      secret:
        secretName: tls-cert
        defaultMode: 0400
```

**Prefer mounted files** over env vars (module 08). The `defaultMode: 0400` makes the file readable only by the container's UID.

---

## 3. etcd encryption-at-rest

By default etcd stores Secrets as plaintext (well, base64-encoded). An attacker with read access to etcd (stolen backup, control plane compromise) gets every secret. **Enable encryption-at-rest** via EncryptionConfiguration on the API server:

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources: [secrets]
    providers:
      - kms:                              # KMS v2 — GA in K8s 1.29
          apiVersion: v2
          name: kms-provider
          endpoint: unix:///var/run/kmsplugin/socket.sock
          timeout: 3s
      - aescbc:                           # fallback: file-key
          keys:
            - { name: key1, secret: <base64-32-byte-key> }
      - identity: {}                      # last: no encryption (read existing)
```

**On managed K8s**: encryption is provider-side.

- **EKS** — enable KMS envelope encryption at cluster create; uses your KMS CMK to wrap a DEK.
- **GKE** — Application-layer Secrets Encryption with a Cloud KMS key.
- **AKS** — KMS etcd encryption with Azure Key Vault key.

For regulated finance: **always** enable. Use a CMK / customer key. Audit usage.

---

## 4. The "Secrets in Git" problem

K8s manifests are GitOps. Plain Secret YAMLs in git = secrets in git = SOC2 finding. Three solutions:

### 4.1 Sealed Secrets (Bitnami)

A controller (`sealed-secrets-controller`) holds a private key in-cluster. You encrypt secrets with the public key:

```bash
echo -n hunter2 | kubectl create secret generic db-creds \
  --dry-run=client --from-file=password=/dev/stdin -o yaml | \
  kubeseal --controller-namespace=sealed-secrets \
           --controller-name=sealed-secrets-controller \
           -o yaml > db-creds.sealed.yaml
```

Commit `db-creds.sealed.yaml`. Only the controller can decrypt. Pros: stupid simple, no external system. Cons: cluster-bound (can't reuse SealedSecret across clusters easily); key rotation requires re-sealing all.

### 4.2 SOPS + age (or KMS)

[SOPS](https://github.com/getsops/sops) (Mozilla) encrypts YAML/JSON values with AWS KMS / GCP KMS / Azure Key Vault / age / PGP. Decryption requires the matching key. Combine with **helm-secrets** or **kustomize-sops** for GitOps.

```bash
sops --age age1abc... -e secret.yaml > secret.enc.yaml
git add secret.enc.yaml
```

At deploy time: `sops -d secret.enc.yaml | kubectl apply -f -`. Pros: cloud-native KMS integration, file-level encryption (not field-level for SealedSecrets). Cons: still produces a K8s Secret object at the end — only the storage-in-git is fixed.

### 4.3 External Secrets Operator (ESO)

The cleanest production pattern: don't put secrets in git or in etcd at all. ESO is a controller that **pulls** from your real secret store and creates K8s Secret objects on the fly.

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata: { name: aws-secrets }
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef: { name: eso-sa }     # IRSA
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata: { name: db-creds }
spec:
  refreshInterval: 1h
  secretStoreRef: { name: aws-secrets, kind: SecretStore }
  target: { name: db-creds }
  data:
    - secretKey: password
      remoteRef: { key: prod/db/postgres, property: password }
```

ESO supports: AWS Secrets Manager + Parameter Store, GCP Secret Manager, Azure Key Vault, HashiCorp Vault, 1Password, Akeyless, Doppler, IBM, Oracle, Pulumi ESC. The current de facto standard for K8s secret integration.

### 4.4 Secrets Store CSI Driver

Alternative: **don't create a K8s Secret at all.** Mount directly from the secret store at pod start:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds }
spec:
  provider: aws                                   # or gcp, azure, vault
  parameters:
    objects: |
      - objectName: "prod/db/postgres"
        objectType: "secretsmanager"
        jmesPath:
          - path: "password"
            objectAlias: "password"
---
# In the pod spec:
volumes:
  - name: db-creds
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes: { secretProviderClass: "db-creds" }
```

Secret mounted at a file path; no K8s Secret object in etcd at all. Optional `syncSecret: true` mode also creates a K8s Secret for compatibility.

ESO vs CSI Driver: ESO produces native K8s Secrets (more compatible, env-var works); CSI Driver doesn't (no etcd exposure, but env-var injection requires a small bootstrap).

For regulated finance: **ESO is the typical default** because most apps need env vars, and the K8s Secret is encrypted-at-rest in etcd via KMS. CSI Driver is for apps that can read from files (the cleaner pattern).

---

## 5. Vault on K8s — three integration patterns

### 5.1 Vault Agent Injector

A mutating webhook that injects a `vault-agent` sidecar into pods (based on annotations). The sidecar authenticates to Vault using the pod's SA token, fetches secrets, writes them as files into a shared volume.

```yaml
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/agent-inject-secret-db: "database/creds/myapp-role"
    vault.hashicorp.com/role: "myapp"
```

### 5.2 Vault Secrets Store CSI Provider

Same CSI pattern as above, with Vault as the backend.

### 5.3 External Secrets Operator with Vault backend

ESO talks to Vault. Same UX as AWS/GCP/Azure.

For new shops standardizing on Vault: ESO is the unified pattern. For shops with existing Vault Agent investment: keep it.

---

## 6. SPIFFE/SPIRE — workload identity for the heterogeneous world

Beyond cloud-IAM federation, **SPIFFE** is a standard for cross-cluster workload identity. **SPIRE** is the reference implementation. A workload running in any environment can prove its identity (a SPIFFE ID like `spiffe://example.org/ns/ml-serving/sa/infer-server`) and get a short-lived X.509 SVID.

Use SPIFFE/SPIRE when:
- Multi-cluster / multi-cloud / hybrid identity federation.
- Service mesh (Istio uses SPIRE under the hood).
- Workload-to-workload mTLS without a service mesh.

For most K8s shops, cloud-IAM federation (IRSA/WIF/Entra Workload ID) is enough. SPIFFE/SPIRE adopt when you outgrow it.

---

## 7. Secret rotation — the production lever

Rotation strategies:

- **App-driven**: app fetches latest secret on every connection (clean but DB-pool unfriendly).
- **Sidecar-driven**: Vault Agent / Secrets Manager Agent rotates the mounted file; app re-reads (with signal handler `SIGHUP` to reload).
- **Operator-driven**: ESO re-reconciles every `refreshInterval`; updates the K8s Secret; you must restart the pods to pick it up (or use a sidecar reloader).
- **Database-side rotation**: rotate at the DB (cred-rotator Lambda / Cloud Function); app fetches fresh on next connection.

For regulated finance: **all DB credentials are short-lived (1-hour TTL) via Vault dynamic secrets or AWS Secrets Manager rotation**. No static credentials.

---

## 8. Pull-secrets — image pull credentials

A specific Secret type for image-pull auth:

```yaml
apiVersion: v1
kind: Secret
metadata: { name: ghcr-pull }
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-of-docker-config>
```

Reference via `imagePullSecrets` on the pod or ServiceAccount. Module 05 covers cloud-registry alternatives (node IAM, IRSA-based ECR auth) which eliminate the need.

---

## 9. TLS Secrets

```yaml
apiVersion: v1
kind: Secret
metadata: { name: api-tls }
type: kubernetes.io/tls
data:
  tls.crt: ...
  tls.key: ...
```

Used by Ingress, Gateway, services that need server certs. Generate via **cert-manager** which:
- Watches Ingress/Gateway resources.
- Requests certs from Let's Encrypt (ACME) / AWS ACM / GCP Cert Manager / Vault PKI.
- Renews automatically.

cert-manager is the standard K8s cert lifecycle solution. Module 32 (service mesh) builds on it.

---

## 10. Auditing secret access

The K8s **audit log** records every API call. Filter for Secret access:

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
```

Set on the kube-apiserver via `--audit-policy-file`. Logs go to file or webhook (typically forwarded to your SIEM).

For "who read which secret when" — this is the audit primitive.

---

## Sanity check

1. K8s Secrets are base64. Why is base64 not encryption?
2. What does etcd encryption-at-rest protect against, and what does it NOT protect against?
3. Sealed Secrets vs External Secrets Operator — which is better for multi-cluster GitOps and why?
4. The Secrets Store CSI Driver bypasses etcd entirely. What's the trade-off vs ESO?
5. Name three short-lived-credential patterns that eliminate static DB passwords.
6. Why is `defaultMode: 0400` on a mounted Secret a defensive control?

---

## Sources

- [K8s Secret docs](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)
- [External Secrets Operator](https://external-secrets.io/)
- [Secrets Store CSI Driver](https://secrets-store-csi-driver.sigs.k8s.io/)
- [HashiCorp Vault on K8s](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [SOPS](https://github.com/getsops/sops)
- [SPIFFE/SPIRE](https://spiffe.io/)
- [cert-manager](https://cert-manager.io/)

→ Next: [21 — RBAC & ServiceAccounts](21_rbac_serviceaccounts.md)


\newpage

# 21 — RBAC & ServiceAccounts: roles, cluster-roles, audit, least-privilege

## Why this module exists

90% of K8s "how did this get hacked" stories trace to a too-broad ServiceAccount or ClusterRoleBinding. RBAC is binary: either you understand it and grant least privilege, or you don't and grant `cluster-admin`.

---

## 1. The four RBAC primitives

| Object | Scope | Defines |
|---|---|---|
| `Role` | Namespaced | Verbs (get, list, ...) on resources (pods, secrets, ...) within one namespace |
| `ClusterRole` | Cluster | Same, but cluster-wide; can also reference cluster-scoped resources (Nodes, PVs, ...) |
| `RoleBinding` | Namespaced | Binds a Role (or ClusterRole) to subjects (User, Group, ServiceAccount) in one namespace |
| `ClusterRoleBinding` | Cluster | Binds a ClusterRole to subjects across the cluster |

Subjects:
- **User** — comes from auth (cert CN, OIDC sub, etc.).
- **Group** — also from auth (cert O, OIDC groups claim).
- **ServiceAccount** — a Pod's identity inside the cluster.

---

## 2. A least-privilege example

```yaml
# Namespace-scoped: this SA can read configmaps in ns ml-serving
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: cm-reader, namespace: ml-serving }
rules:
  - apiGroups: [""]
    resources: [configmaps]
    verbs: [get, list, watch]
---
apiVersion: v1
kind: ServiceAccount
metadata: { name: infer-server, namespace: ml-serving }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: infer-cm-reader, namespace: ml-serving }
subjects:
  - kind: ServiceAccount
    name: infer-server
    namespace: ml-serving
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: cm-reader
```

Pod uses `serviceAccountName: infer-server`. Its in-pod kubeconfig (via projected SA token) lets it `get configmaps` in `ml-serving` only.

---

## 3. The default-everything anti-pattern

A fresh pod gets the **default** SA of its namespace, which has **no permissions** by default. But the legacy pre-1.6 behavior was to give it broad rights. Two related anti-patterns persist:

- **`automountServiceAccountToken: true`** (the default for pods) — the SA token is mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`, and any process can talk to the API server. Set to `false` for pods that don't need API access (most app pods).
- **Binding `cluster-admin` to `system:serviceaccounts`** — gives every SA full power. Found in many "let's just get it working" sandboxes; never in prod.

### 3.1 The hardening default

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: infer-server, namespace: ml-serving }
automountServiceAccountToken: false
---
spec:
  serviceAccountName: infer-server
  automountServiceAccountToken: false             # also at pod level (overrides SA)
```

For pods that don't talk to the K8s API at all (most ML serving pods), disable the token mount entirely. Reduces blast radius if compromised.

---

## 4. Aggregating ClusterRoles

K8s ships several **system-** ClusterRoles. The default "viewer / editor / admin" three:

| ClusterRole | Verbs | Notes |
|---|---|---|
| `view` | get, list, watch on most resources except Secrets and Roles | Read-only |
| `edit` | get, list, watch, create, update, delete on most resources except RBAC and Namespaces | Most-used for developers |
| `admin` | edit + RBAC within namespace | Per-namespace "team admin" |
| `cluster-admin` | * on * | The big red button |

Custom roles can **aggregate**:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-viewer
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
  - apiGroups: [monitoring.coreos.com]
    resources: [prometheuses, servicemonitors]
    verbs: [get, list, watch]
```

This auto-aggregates into `view` — anyone with `view` now also has read access to PrometheusRules. Operators like kube-prometheus-stack use this pattern.

---

## 5. Audit the actual permissions

```bash
# What can this SA do in this namespace?
kubectl auth can-i --list --as=system:serviceaccount:ml-serving:infer-server -n ml-serving

# What can this user do?
kubectl auth can-i create pods --as=alice
kubectl auth can-i '*' '*' --as=alice -n ml-serving

# Who/what has cluster-admin?
kubectl get clusterrolebinding -o yaml | yq '.items[] | select(.roleRef.name == "cluster-admin")'
```

Tools to find over-permissive bindings:

- **[rbac-lookup](https://github.com/FairwindsOps/rbac-lookup)** — list all subjects and their permissions.
- **[rbac-tool](https://github.com/alcideio/rbac-tool)** — visualize and audit.
- **[KubiScan](https://github.com/cyberark/KubiScan)** — find risky pods/SAs.
- **[kubectl-who-can](https://github.com/aquasecurity/kubectl-who-can)** — answer "who can X on Y?"

For an architect interview: knowing these by name is enough to credibly say "I'd run an RBAC audit with rbac-lookup, find the broad bindings, and tighten."

---

## 6. The principal-of-least-privilege ladder

For a typical app pod, the SA needs:

- **Most pods: NOTHING.** They serve traffic and write logs; no K8s API call. `automountServiceAccountToken: false`.
- **Pods that read ConfigMaps/Secrets** — already do that via projected volumes; no API call needed.
- **Pods that need to discover services** — DNS works without API; no SA needed.
- **Pods that read other pods' state** (rare — usually only an operator does this) — explicit Role.
- **Pods that need cloud API access** — that's IRSA / Workload Identity, not K8s API.

If you're tempted to give a pod `list pods` permission: ask why. The answer is usually "I'm building an operator," and operators belong in their own namespace with explicit RBAC.

---

## 7. ServiceAccount projected tokens — the audience scoping

Modern (1.22+) ServiceAccount tokens are **projected volumes** with TokenRequest API. Crucially, they can have **audiences**:

```yaml
volumes:
  - name: api-token
    projected:
      sources:
        - serviceAccountToken:
            audience: api.internal.example.com
            expirationSeconds: 3600
            path: token
```

The token is valid only for the specified audience — so even if it leaks, you can't replay it against the K8s API. This is the mechanism IRSA / Workload Identity Federation use under the hood to federate K8s-issued tokens into cloud IAM tokens (modules 26-28).

---

## 8. RBAC for cluster admins — the human side

K8s authenticates users via:

- **Client certificates** (the kubeadm default; cert CN = user, cert O = group).
- **Static tokens** (rarely; only for testing).
- **OIDC** (the production default — Google, Okta, Azure AD, Auth0).
- **Authentication webhooks** (custom backends).

Most managed services have their own glue: EKS uses **AWS IAM mapped to RBAC via the `aws-auth` ConfigMap** (or the newer Access Entries API GA 2024); GKE uses **Google IAM mapped to K8s groups**; AKS uses **Microsoft Entra ID with K8s groups**.

For regulated finance: **OIDC + SCIM-managed groups + audit log to SIEM** is the minimum. No long-lived kubeconfig files; users authenticate per-session.

---

## 9. The aws-auth / Access Entries gotcha (EKS-specific)

For years, EKS clusters managed user/role to K8s identity via the `aws-auth` ConfigMap. This was infamous for being a single point of failure ("Bob edited the ConfigMap, locked everyone out, now we have to delete the cluster").

In 2024 AWS released **EKS Access Entries** — a proper API for "this IAM principal has this access policy." Migrate to it; deprecate the ConfigMap.

```bash
aws eks create-access-entry --cluster-name my-cluster --principal-arn arn:aws:iam::123:role/dev
aws eks associate-access-policy --cluster-name my-cluster --principal-arn arn:aws:iam::123:role/dev \
  --access-scope type=namespace,namespaces=ml-serving \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSEditPolicy
```

---

## 10. The audit log — what RBAC events look like

Sample audit policy:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    omitStages: [RequestReceived]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: [roles, rolebindings, clusterroles, clusterrolebindings]
  - level: RequestResponse
    verbs: [create, update, patch, delete]
    resources: [{group: "", resources: ["secrets"]}]
```

Every RBAC change is logged. Every Secret create/update/delete is logged with the request body. Ship to SIEM, alert on `system:masters` (= cluster-admin) bindings being created.

---

## 11. Hands-on detection lab

Find suspicious bindings (run on any cluster you administer):

```bash
# Bindings of cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name == "cluster-admin") | .subjects'

# SAs that can list secrets cluster-wide
kubectl get clusterroles -o json | \
  jq '.items[] | select(.rules[]? | select(.resources[]? == "secrets" and .verbs[]? == "list")) | .metadata.name'

# Default SAs that have non-default bindings
for ns in $(kubectl get ns -o name); do
  ns=${ns#namespace/}
  kubectl get rolebindings -n $ns -o json | \
    jq --arg ns "$ns" '.items[] | select(.subjects[]? | select(.kind=="ServiceAccount" and .name=="default")) | {ns:$ns, name:.metadata.name, role:.roleRef.name}'
done
```

Combine with rbac-lookup output for the architect-grade audit.

---

## Sanity check

1. Why is `automountServiceAccountToken: false` a recommended default for app pods?
2. RoleBinding vs ClusterRoleBinding — when do you use each?
3. The `view` ClusterRole excludes Secrets by design. Why?
4. EKS Access Entries replaced the `aws-auth` ConfigMap. What problem did the ConfigMap have?
5. How does the `audience` field on a projected SA token reduce credential-replay risk?
6. Name three tools to audit "who can do what" on a cluster.

---

## Sources

- [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [ServiceAccounts](https://kubernetes.io/docs/concepts/security/service-accounts/)
- [TokenRequest API](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)
- [Audit logging](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/)
- [EKS Access Entries](https://docs.aws.amazon.com/eks/latest/userguide/access-entries.html)
- [rbac-lookup](https://github.com/FairwindsOps/rbac-lookup)
- [KubiScan](https://github.com/cyberark/KubiScan)

→ Next: [22 — Pod Security — PSA, SecurityContext, runtime classes](22_pod_security.md)


\newpage

# 22 — Pod Security: PSA, SecurityContext, runtime classes (gVisor, Kata)

## Why this module exists

The Docker `run` hardening from module 10 has a K8s analogue: **Pod Security Admission (PSA)** + **SecurityContext** + (optionally) **RuntimeClass** for sandbox isolation. This module covers all three.

PodSecurityPolicy (PSP) was removed in 1.25. PSA is its replacement.

---

## 1. Pod Security Admission (PSA) — the namespace label gate

PSA is a built-in admission controller (since 1.23 beta, 1.25 GA) that classifies pods against three profiles:

| Profile | Allows |
|---|---|
| **privileged** | Unrestricted (current legacy). For DaemonSets, monitoring, CNI agents. |
| **baseline** | No privileged, no hostNetwork/hostPID/hostIPC, capabilities limited, no /proc mount tricks. |
| **restricted** | Baseline + non-root user, drop all capabilities, no privilege escalation, seccomp `RuntimeDefault`, no host volumes. |

Apply per namespace via labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ml-serving
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

Three modes per profile:

- **enforce** — reject the pod at admission.
- **audit** — allow, but emit audit event.
- **warn** — allow, but `kubectl apply` shows a warning.

Typical pattern: `audit: restricted` and `warn: restricted` on every namespace (visibility); promote to `enforce: restricted` once warnings clear. DaemonSets typically run in `kube-system` with `privileged`.

---

## 2. SecurityContext — the per-pod and per-container knobs

```yaml
spec:
  securityContext:                   # pod-level
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    fsGroupChangePolicy: OnRootMismatch
    seccompProfile: { type: RuntimeDefault }
    supplementalGroups: [10100]
  containers:
    - name: app
      securityContext:               # container-level (overrides pod where set)
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: [ALL]
          add: [NET_BIND_SERVICE]
        runAsUser: 10001
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir: { sizeLimit: 64Mi }
```

This is the K8s equivalent of the module-10 `docker run` line:

- `runAsNonRoot: true` + `runAsUser: 10001` — non-root identity.
- `readOnlyRootFilesystem: true` + tmpfs `emptyDir` for writable paths — immutable runtime.
- `allowPrivilegeEscalation: false` — `no-new-privileges` equivalent.
- `capabilities.drop: [ALL]` + selective add — minimal capability set.
- `seccompProfile.type: RuntimeDefault` — default seccomp filter.

PSA `restricted` enforces all of these. The PSA → SecurityContext mapping is the "what is restricted actually checking" question.

---

## 3. AppArmor / SELinux annotations

K8s 1.30 GA'd `appArmorProfile` in SecurityContext:

```yaml
securityContext:
  appArmorProfile:
    type: RuntimeDefault             # or Localhost with localhostProfile
```

Before 1.30: an annotation `container.apparmor.security.beta.kubernetes.io/<container>: runtime/default`.

For SELinux:

```yaml
securityContext:
  seLinuxOptions:
    level: "s0:c123,c456"
```

In practice: stick with defaults (`RuntimeDefault` profile, default container_t label) unless you have a specific reason. Custom profiles are a maintenance hot mess.

---

## 4. RuntimeClass — picking the runtime per pod

A pod can specify a non-default runtime:

```yaml
spec:
  runtimeClassName: gvisor
```

Available `RuntimeClass` objects depend on the cluster:

| RuntimeClass | Runtime | Use |
|---|---|---|
| (none) | runc | Default; what 99% of pods use |
| `gvisor` | runsc | Sandboxed kernel; multi-tenant untrusted workloads |
| `kata` | Kata Containers | VM-isolated; strongest boundary |
| `nvidia` | nvidia-container-runtime | GPU pods (wrapper around runc) |

The cluster admin installs the runtime + creates the `RuntimeClass`:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata: { name: gvisor }
handler: runsc
scheduling:
  nodeSelector:
    sandboxed: "true"
```

For ML platforms running untrusted user notebooks (think internal "ML workspace as a service"): mandate `runtimeClassName: gvisor` or `kata` at admission (Kyverno / Gatekeeper rule). The performance hit is real (10-30% on CPU-bound workloads, more on syscall-heavy) but the boundary is qualitatively stronger.

For Capital One–style first-party ML: regular runc is fine — the workload is trusted; defense in depth comes from the surrounding controls (RBAC, NetworkPolicy, Falco).

---

## 5. seccomp profile customization

The default seccomp profile (`RuntimeDefault`) blocks ~50 historical syscalls. To go stricter:

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: my-app-seccomp.json
```

The file lives on each node at `/var/lib/kubelet/seccomp/my-app-seccomp.json`. Cluster admin distributes via DaemonSet that copies the file.

Generating custom profiles: tools like **[security-profiles-operator](https://github.com/kubernetes-sigs/security-profiles-operator)** record syscalls during a recording phase and emit a profile. Useful for high-value workloads.

---

## 6. Pod-level resource limits — additional security

Beyond requests/limits (module 17), `LimitRange` per namespace + `ResourceQuota` enforce caps:

```yaml
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: ml-serving }
spec:
  limits:
    - type: Container
      default: { memory: 512Mi, cpu: 500m }
      defaultRequest: { memory: 128Mi, cpu: 100m }
      max: { memory: 8Gi, cpu: 4 }
---
apiVersion: v1
kind: ResourceQuota
metadata: { name: quota, namespace: ml-serving }
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    requests.nvidia.com/gpu: "4"
    persistentvolumeclaims: "10"
```

For multi-tenant clusters, these are how you prevent one team from starving others.

---

## 7. PodSecurity exemptions

PSA has an exemptions mechanism (via admission config) — but **avoid exempting namespaces from `restricted`** unless absolutely necessary. The right pattern: keep all app namespaces `restricted`, put DaemonSets / monitoring / CNI agents in `kube-system` (PSA-privileged).

---

## 8. Beyond PSA — Kyverno / Gatekeeper

PSA covers ~80% of security baselines. For the rest (require resource limits, require labels, require image-pull policy, require non-default ServiceAccount, etc.), use **Kyverno** or **OPA Gatekeeper**. Module 23.

---

## 9. The "restricted" PSA template every team can copy

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: infer-server, namespace: ml-serving }
spec:
  replicas: 3
  selector: { matchLabels: { app: infer-server } }
  template:
    metadata:
      labels: { app: infer-server }
    spec:
      serviceAccountName: infer-server
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
        seccompProfile: { type: RuntimeDefault }
      containers:
        - name: app
          image: myorg/infer:1.2.3@sha256:abc...
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: [ALL] }
          resources:
            requests: { cpu: 500m, memory: 1Gi }
            limits:   { cpu: 2,    memory: 2Gi }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
          ports: [{ containerPort: 8080 }]
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
            initialDelaySeconds: 30
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
      volumes:
        - { name: tmp, emptyDir: { sizeLimit: 64Mi } }
```

This passes PSA `restricted` enforcement. Use it as a template.

---

## Sanity check

1. PSA has three profiles. Map each to the kind of workload that fits.
2. Why was `PodSecurityPolicy` removed, and why is PSA easier to operate?
3. When does it make sense to use `runtimeClassName: gvisor`? `kata`?
4. Why is `readOnlyRootFilesystem: true` paired with an emptyDir for `/tmp`?
5. What does `fsGroupChangePolicy: OnRootMismatch` solve, and on what kind of volume?
6. Name two cluster-level enforcement objects (besides PSA) that multi-tenant clusters need.

---

## Sources

- [Pod Security Admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [SecurityContext](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)
- [Seccomp in K8s](https://kubernetes.io/docs/tutorials/security/seccomp/)
- [AppArmor in K8s](https://kubernetes.io/docs/tutorials/security/apparmor/)
- [RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/)
- [gVisor on K8s](https://gvisor.dev/docs/user_guide/quick_start/kubernetes/)
- [Kata Containers on K8s](https://github.com/kata-containers/kata-containers/blob/main/docs/Developer-Guide.md)
- [security-profiles-operator](https://github.com/kubernetes-sigs/security-profiles-operator)

→ Next: [23 — Admission control — OPA Gatekeeper, Kyverno](23_admission_control.md)


\newpage

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


\newpage

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


\newpage

# 25 — Observability & runtime security: Prometheus, OpenTelemetry, Falco, Hubble

## Why this module exists

You can't secure or operate what you can't observe. K8s ships nothing for observability — you bring the stack. The de facto: Prometheus + Grafana for metrics, OpenTelemetry for traces, Loki/Elasticsearch for logs, Falco for runtime security, Hubble for network flows, DCGM for GPUs.

---

## 1. The CNCF observability triad

| Signal | Open standard | K8s stack default |
|---|---|---|
| Metrics | OpenMetrics | Prometheus + Grafana |
| Traces | OpenTelemetry | OTel + Jaeger or Tempo |
| Logs | OpenTelemetry Logs | Loki, Elasticsearch, or Cloud-native |

OpenTelemetry is the unifying protocol. Auto-instrumentation for Python/Java/Go/.NET is mature.

---

## 2. kube-prometheus-stack (the standard install)

```bash
helm install kube-prom prometheus-community/kube-prometheus-stack -n monitoring
```

Bundles:
- Prometheus Operator + Prometheus (HA pair).
- Alertmanager.
- Grafana with prebuilt K8s dashboards.
- Node Exporter (per-node metrics).
- kube-state-metrics (object metrics).
- ServiceMonitor / PodMonitor CRDs (declarative scrape config).

Custom metrics: any app exposing `/metrics` in OpenMetrics format. Add a `ServiceMonitor`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: { name: infer-server, namespace: monitoring }
spec:
  namespaceSelector: { matchNames: [ml-serving] }
  selector: { matchLabels: { app: infer-server } }
  endpoints: [{ port: http, path: /metrics, interval: 15s }]
```

---

## 3. AI/ML-specific metrics

Beyond the generic K8s metrics:

| Metric | Source | Why |
|---|---|---|
| GPU utilization / memory / temp | DCGM Exporter (NVIDIA) | Cost control, capacity planning |
| Inference latency p50/p95/p99 | App | SLO basis |
| Tokens-per-second / requests/sec | App | Throughput |
| Cost per token (compound metric) | Recording rule combining cost + token metrics | Capital One–style FinOps |
| Cache hit rate (LLM KV-cache, RAG retrieval) | App | Cost optimization |
| GPU OOM count / Cgroup throttle events | DCGM, cAdvisor | Reliability |

DCGM Exporter as DaemonSet on GPU nodes:

```yaml
helm install dcgm-exporter nvidia/dcgm-exporter -n monitoring \
  --set serviceMonitor.enabled=true
```

---

## 4. OpenTelemetry — the unification

OTel SDKs auto-instrument web servers, DB clients, HTTP/gRPC. Collector receives signals, exports to backend (Tempo, Jaeger, X-Ray, Datadog, Honeycomb, etc).

```yaml
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata: { name: otel-collector, namespace: monitoring }
spec:
  mode: deployment
  config: |
    receivers:
      otlp: { protocols: { grpc: {}, http: {} } }
    processors:
      batch: {}
      memory_limiter: { check_interval: 5s, limit_mib: 512 }
    exporters:
      otlp/tempo:    { endpoint: tempo:4317, tls: { insecure: true } }
      prometheus:    { endpoint: 0.0.0.0:8889 }
    service:
      pipelines:
        traces:  { receivers: [otlp], processors: [memory_limiter, batch], exporters: [otlp/tempo] }
        metrics: { receivers: [otlp], processors: [memory_limiter, batch], exporters: [prometheus] }
```

The OpenTelemetry **Operator** can auto-inject SDKs into pods via annotation — `instrumentation.opentelemetry.io/inject-python: "true"` and the operator mutates the pod to include the SDK + collector endpoint. Zero-code instrumentation.

---

## 5. Loki — logs as a time series

[Loki](https://grafana.com/oss/loki/) treats logs like Prometheus treats metrics: label-indexed, content not indexed. Cheap at scale; query language (LogQL) similar to PromQL.

```bash
helm install loki grafana/loki-distributed -n monitoring
helm install promtail grafana/promtail -n monitoring \
  --set "loki.serviceName=loki"
```

Promtail (or Vector, or Fluent Bit) tails pod logs and ships to Loki. Storage: S3 / GCS / Azure Blob / on-prem MinIO.

---

## 6. Runtime security — Falco

[Falco](https://falco.org/) is **CNCF Graduated**. eBPF-based runtime security agent. Watches syscalls + K8s audit log + container events; matches against rules.

Detection examples:

- Shell spawned in a container (suspicious for prod ML inference).
- Outbound connection to crypto-mining pool (Tesla 2018 pattern).
- Write to `/etc/shadow` or `/proc/self/exe`.
- ServiceAccount token accessed from unusual process.
- IMDS access from container (Capital One pattern).

```yaml
- rule: Container shell spawned
  desc: A shell was opened inside a container
  condition: spawned_process and container and shell_procs
  output: "Shell in container (user=%user.name container=%container.name cmdline=%proc.cmdline)"
  priority: WARNING
```

Falco emits to **Falcosidekick** which forwards to: Slack, PagerDuty, SIEM (Splunk, Sumo), AWS Security Hub, GCP Security Command Center, Webhook.

For regulated finance: Falco DaemonSet + custom rules + falcosidekick → Security Hub. Standard.

---

## 7. Hubble — Cilium's flow log

If you've installed Cilium (module 18), Hubble gives you L7 network flow visibility:

```bash
hubble observe --namespace ml-serving --since 1m
hubble observe -n ml-serving --to-fqdn s3.amazonaws.com
hubble observe -n ml-serving --verdict DROPPED   # what's getting NetworkPolicy-blocked
```

Hubble UI gives a service-map visualization (which service talks to which, what verbs).

For "what is my pod actually connecting to" debugging: Hubble beats anything else by an order of magnitude.

---

## 8. Tracee — the Aqua eBPF tool

[Tracee](https://github.com/aquasecurity/tracee) is similar to Falco but with a slightly different lineage. eBPF-based, runtime threat detection. Choose one — running both is overkill.

---

## 9. Kubescape / Trivy K8s — scanning for misconfig

- [Kubescape](https://kubescape.io/) (CNCF Sandbox) — scans clusters for NSA + CIS + MITRE ATT&CK violations.
- `trivy k8s` — same idea, plus image vuln + secret scanning across the cluster.

CI integration: scan manifests before they're applied.

---

## 10. The cost-observability angle

Container cost is dominated by **GPU hours** for ML and **request volume** for serving. Tools:

- **OpenCost** (CNCF Sandbox) — cost-allocation per namespace / pod / label using cloud-provider billing data + K8s metrics.
- **Kubecost** (commercial) — same plus richer UI.
- **AWS Cost Anomaly Detection** + **AWS Cost Explorer** with cost-allocation tags from K8s labels.
- **Custom Prom recording rules** that multiply GPU-hours × $/hour.

For Capital One–style FinOps: OpenCost / Kubecost dashboards per business unit, monthly true-up.

---

## 11. The observability checklist for ML on K8s

- [ ] kube-prometheus-stack installed; ServiceMonitor for every prod app.
- [ ] DCGM Exporter on GPU nodes; Grafana dashboard for GPU SM utilization, memory.
- [ ] OpenTelemetry instrumentation for inference services (Python SDK auto-instrumentation).
- [ ] Logs to Loki / OpenSearch / CloudWatch Logs.
- [ ] Falco DaemonSet + custom rules → SIEM.
- [ ] Hubble enabled (or Cilium in cluster).
- [ ] Kubescape in CI + scheduled scans.
- [ ] OpenCost/Kubecost dashboards.
- [ ] SLOs defined per service (latency, error rate) with multi-window alerts.
- [ ] Runbooks linked from every alert.

---

## Sanity check

1. Why is Loki cheaper than Elasticsearch for K8s logs at scale?
2. DCGM Exporter — what does it expose, and on which pods does it need to run?
3. OpenTelemetry Operator's auto-injection — how does it work mechanically?
4. Falco vs Hubble — different purposes. Describe each.
5. OpenCost computes cost per namespace from what inputs?
6. What's the ML-specific recording rule for "cost per million tokens" combining what metrics?

---

## Sources

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)
- [OpenTelemetry Operator](https://github.com/open-telemetry/opentelemetry-operator)
- [Grafana Loki](https://grafana.com/oss/loki/)
- [Falco](https://falco.org/)
- [Cilium Hubble](https://docs.cilium.io/en/stable/observability/hubble/)
- [Kubescape](https://kubescape.io/)
- [OpenCost](https://www.opencost.io/)

→ Next: [26 — **EKS deep — IRSA, Pod Identity, EFS/FSx/S3 CSI, ASCP, KMS**](26_eks_data_exposure.md)


\newpage

# 26 — EKS deep: IRSA, EKS Pod Identity, EFS/FSx/S3 CSI, ASCP, KMS, VPC CNI

> *"This is THE module for the Capital One Sr Lead AI/ML role. EKS + KServe + IRSA + KMS is the stack."*

## Why this module exists

EKS is Capital One's K8s. The published Lead MLE job posting names KServe + EKS + PyTorch + TensorFlow explicitly. This module is the depth on the EKS-specific data-exposure primitives: IRSA, Pod Identity, the four CSI drivers (EBS, EFS, FSx-Lustre, S3-Mountpoint), ASCP for secrets, KMS for at-rest, and the VPC CNI's identity-per-pod model.

---

## 1. Identity — IRSA vs EKS Pod Identity

### 1.1 IRSA (2019, the established standard)

**IRSA (IAM Roles for Service Accounts)** uses an OIDC provider per cluster. A KSA (Kubernetes ServiceAccount) annotated with `eks.amazonaws.com/role-arn` becomes a holder of that IAM role's credentials.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/ml-serving-infer
```

Under the hood:

1. EKS issues SA tokens with the OIDC issuer as audience.
2. AWS SDK in the pod sees env vars `AWS_ROLE_ARN` + `AWS_WEB_IDENTITY_TOKEN_FILE` (injected by a mutating admission webhook).
3. SDK calls `sts:AssumeRoleWithWebIdentity` — STS validates the JWT against the cluster's OIDC provider and returns 1-hour role credentials.

Trust policy on the IAM role:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED:sub": "system:serviceaccount:ml-serving:infer-server",
        "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED:aud": "sts.amazonaws.com"
      }
    }
  }]
}
```

The `sub` condition pins the role to exactly one ns/sa pair. The `aud` condition ensures the token was minted for STS.

### 1.2 EKS Pod Identity (Nov 2023, the modern alternative)

EKS Pod Identity ditches the OIDC chain. The cluster runs an `eks-pod-identity-agent` DaemonSet that intercepts AWS SDK metadata-service-lookups and returns role credentials directly.

```bash
aws eks create-pod-identity-association \
  --cluster-name prod \
  --namespace ml-serving \
  --service-account infer-server \
  --role-arn arn:aws:iam::123456789012:role/ml-serving-infer
```

Trust policy:

```json
{ "Effect": "Allow", "Principal": { "Service": "pods.eks.amazonaws.com" }, "Action": ["sts:AssumeRole","sts:TagSession"] }
```

### 1.3 Choosing

| Aspect | IRSA | EKS Pod Identity |
|---|---|---|
| Setup overhead | Per-role OIDC trust policy | Per-association call (simpler) |
| Cross-cluster reuse of role | Hard (OIDC issuer per cluster) | Easy |
| Cross-account | Possible | Easier |
| AWS SDK support | Old + Universal | Newer SDKs (v3 for JS, recent boto3) |
| Capital One stack? | Pre-2024 standard | New deploys, post-2024 |

**Use Pod Identity for new clusters.** Migrate IRSA where convenient. Both work.

### 1.4 The IMDS hop-limit reminder

Independent of IRSA/Pod-Identity, set `httpPutResponseHopLimit=1` on EKS nodes. Capital One 2019 lesson. The EKS launch template should include:

```hcl
resource "aws_launch_template" "eks_node" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }
}
```

Pods talking to IMDS = bad. Pods talking to IRSA / Pod Identity endpoint = good (separate endpoint, `169.254.170.23` for Pod Identity).

---

## 2. EBS CSI — block storage for stateful pods

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3-encrypted }
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: arn:aws:kms:us-east-1:123456789012:key/<cmk-id>
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Retain                # prod: never auto-delete data
allowVolumeExpansion: true
```

The CSI controller is a Deployment + Node DaemonSet. Install via EKS add-on:

```bash
aws eks create-addon --cluster-name prod --addon-name aws-ebs-csi-driver \
  --service-account-role-arn arn:aws:iam::123:role/AmazonEKS_EBS_CSI_DriverRole
```

The controller's SA gets EC2 permissions to create/attach/delete volumes via IRSA.

For ML training checkpoints / vector indices / databases: gp3 is the default; io2 Block Express for high-IOPS DBs.

---

## 3. EFS CSI — RWX shared file storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: efs-sc }
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap                # use Access Points (recommended)
  fileSystemId: fs-0123456789abcdef0
  directoryPerms: "0750"
  gidRangeStart: "10000"
  gidRangeEnd: "20000"
```

The driver creates EFS Access Points (module 13) dynamically per PVC, with random GIDs in the range — multi-tenant safe.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data, namespace: ml-serving }
spec:
  storageClassName: efs-sc
  accessModes: [ReadWriteMany]
  resources: { requests: { storage: 1Ti } }       # EFS is elastic; this is just a label
```

Pod mounts EFS via NFSv4.1 with `tls`. The EFS file system has:
- Encryption at rest with CMK.
- Encryption in transit (stunnel-wrapped NFS).
- IAM-based access (`iam: ENABLED` on the access point + IRSA-rolled task permissions).

For ML training where 8-256 GPU pods read the same dataset: EFS is the cleanest cloud-native answer.

---

## 4. FSx for Lustre CSI — high-perf parallel training

For 1000+ GPU training where EFS bandwidth saturates: FSx for Lustre.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: fsx-lustre-1200-ssd }
provisioner: fsx.csi.aws.com
parameters:
  subnetId: subnet-abc...
  securityGroupIds: sg-abc...
  s3ImportPath: s3://myorg-training-data/2026-q2/
  s3ExportPath: s3://myorg-training-checkpoints/
  deploymentType: PERSISTENT_2
  perUnitStorageThroughput: "1000"
  storageType: SSD
```

Lustre provisioned with `s3ImportPath` lazy-loads data from S3 on first read (Data Repository Association). After training, dirty data evicts back to `s3ExportPath`. This is the **canonical large-scale training pattern**: S3 as cold storage + FSx Lustre as hot cache.

Pod mounts the Lustre FS at startup; reads stream from S3 transparently on first touch.

---

## 5. Mountpoint for Amazon S3 CSI — read-mostly S3 as filesystem

GA April 2024. For ML training where you want POSIX read but the dataset is S3:

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: s3-mountpoint }
spec:
  capacity: { storage: 1Ti }
  accessModes: [ReadOnlyMany]
  mountOptions:
    - allow-delete
    - region=us-east-1
    - prefix=2026-q2/
  csi:
    driver: s3.csi.aws.com
    volumeHandle: training-bucket-mount
    volumeAttributes: { bucketName: myorg-training-data }
```

POSIX limitations: no random writes, no in-place modifications, no rename in same prefix (which is fine for read-mostly). Significantly cheaper than provisioning Lustre, especially for occasional-read workloads.

---

## 6. ASCP — AWS Secrets and Configuration Provider for CSI

The K8s **Secrets Store CSI Driver** (vendor-neutral) + AWS provider (ASCP) lets pods mount Secrets Manager / SSM Parameter Store entries as files.

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/db/postgres"
        objectType: "secretsmanager"
        jmesPath:
          - { path: "password", objectAlias: "db_password" }
          - { path: "username", objectAlias: "db_username" }
```

```yaml
# Pod spec
spec:
  serviceAccountName: infer-server            # IRSA-rolled to allow SM access
  containers:
    - name: app
      volumeMounts:
        - { name: db-creds, mountPath: /run/secrets, readOnly: true }
  volumes:
    - name: db-creds
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes: { secretProviderClass: db-creds }
```

The Secrets Manager IAM permission on the IRSA role:

```json
{ "Effect": "Allow", "Action": "secretsmanager:GetSecretValue", "Resource": "arn:aws:secretsmanager:us-east-1:123:secret:prod/db/*" }
```

Alternative: **External Secrets Operator with AWS provider**. Picks the same secret, but creates a K8s Secret object (which then goes through KMS-encrypted etcd). Pick ESO if your app needs an env var; pick ASCP if it can read a file.

---

## 7. KMS envelope encryption for etcd

When creating an EKS cluster:

```hcl
resource "aws_eks_cluster" "prod" {
  encryption_config {
    provider { key_arn = aws_kms_key.eks_secrets.arn }
    resources = ["secrets"]
  }
}
```

K8s Secrets in etcd are now KMS-encrypted. EKS uses KMS v2 (since K8s 1.29). Required for any regulated-finance cluster.

---

## 8. VPC CNI — pod = ENI = VPC IP

The AWS VPC CNI gives each pod a routable VPC IP via a secondary IP on the node's ENI. Effects:

- Pods are **directly addressable from the VPC** — same network as anything else in your VPC. No overlay; no NAT.
- **Security groups per pod** — supported on Nitro instances. Attach SGs to KSA via `SecurityGroupPolicy` CRD.
- **Pod limits per node** — based on ENI count × IPs-per-ENI. A `m5.large` can hold 29 pods; an `m5.4xlarge` 234; a GPU `p4d.24xlarge` ~ 600. Beyond that, you need a larger instance or **prefix delegation** (an ENI can carry an IP prefix instead of individual IPs).

### 8.1 Security Group per Pod

```yaml
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata: { name: pg-client-sg, namespace: ml-serving }
spec:
  podSelector:
    matchLabels: { app: pg-client }
  securityGroups:
    groupIds: [sg-abc...]
```

Now pods labeled `app: pg-client` get an additional SG attached, useful for granting access to RDS without opening the whole node CIDR.

### 8.2 The VPC CNI alternative — Cilium

Some teams replace VPC CNI with **Cilium** for richer NetworkPolicy, L7 visibility, kube-proxy replacement, and service-mesh-without-sidecar. AWS now has a **first-class Cilium support** (Cilium Distribution for EKS) since 2024.

For Capital One's KServe stack: **Cilium for L7 + Istio for mesh** is plausible; **VPC CNI + Calico-policy + Istio** is the historical pattern. Either is defensible.

---

## 9. EKS Auto Mode (Dec 2024)

EKS Auto Mode bundles:
- Karpenter for node autoscaling.
- ALB controller for ingress.
- EBS CSI + EFS CSI.
- Pod Identity preconfigured.
- KMS encryption.

A "managed everything" tier. For non-regulated workloads, accelerates time-to-cluster. For Capital One: typically you want explicit control of these so Auto Mode may be over-managed.

---

## 10. Karpenter for GPU autoscaling

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: gpu-h100 }
spec:
  template:
    metadata:
      labels: { workload: ml-training }
    spec:
      taints:
        - { key: nvidia.com/gpu, value: "true", effect: NoSchedule }
      requirements:
        - { key: kubernetes.io/arch,           operator: In, values: [amd64] }
        - { key: node.kubernetes.io/instance-type, operator: In, values: [p5.48xlarge, p5e.48xlarge] }
        - { key: karpenter.sh/capacity-type,   operator: In, values: [on-demand] }
      nodeClassRef: { name: gpu-default }
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 5m              # don't churn GPU nodes
    expireAfter: 720h
  limits:
    cpu: "1000"
    memory: 4000Gi
    nvidia.com/gpu: "32"
```

Karpenter provisions nodes on demand based on pending pods. Critical for GPU economics — you only pay for active training capacity.

`consolidateAfter: 5m` avoids the "kill the GPU node we just spun up because a pod went away for a second" thrash. Capital One's KServe deployments would tune this to match their training churn.

---

## 11. The reference EKS+KServe architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ EKS cluster (with KMS envelope for etcd)                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ml-serving namespace                                       │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ InferenceService (KServe)                            │  │  │
│  │  │  ServiceAccount with IRSA → S3 model bucket          │  │  │
│  │  │  PSA: restricted                                     │  │  │
│  │  │  Pod: read-only FS + tmpfs + cap-drop ALL            │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ kube-system (PSA: privileged)                              │  │
│  │  VPC CNI, Karpenter, EBS/EFS/FSx/S3 CSI, ASCP, OTel        │  │
│  │  Falco, Cilium (if installed), Kyverno                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Node Launch Template: IMDSv2 + hop-limit 1                      │
└──────────────────┬──────────────────┬──────────────────┬─────────┘
                   │                  │                  │
            ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
            │ ECR (CMK,   │    │ S3 (SSE-KMS,│    │ Secrets Mgr │
            │ IMMUTABLE)  │    │ Block Pub,  │    │ + CMK       │
            │             │    │ VPC GW EP)  │    │             │
            └─────────────┘    └─────────────┘    └─────────────┘
```

Cross-cuts:
- **Identity**: IRSA / Pod Identity per workload.
- **Egress**: VPC endpoints; no NAT GW reachable from pods (Cloud Custodian rule).
- **Admission**: Kyverno enforcing PSA-restricted + image signing.
- **Audit**: K8s audit log → CloudWatch → Security Hub.
- **Observability**: kube-prometheus-stack + DCGM + Falco + Hubble.

---

## Sanity check

1. IRSA vs EKS Pod Identity — name two reasons to choose Pod Identity for a new cluster.
2. What's the practical difference between EFS CSI and FSx-for-Lustre CSI for ML training data?
3. Mountpoint-for-S3 vs s3fs — name two reasons Mountpoint is the safer choice for K8s.
4. What does Security Group per Pod give you that node-level SG does not?
5. Why does Karpenter need `consolidateAfter: 5m` for GPU node pools but not for CPU?
6. EKS KMS envelope encryption protects what specifically?

---

## Sources

- [IRSA](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [EFS CSI driver](https://github.com/kubernetes-sigs/aws-efs-csi-driver)
- [FSx for Lustre CSI](https://github.com/kubernetes-sigs/aws-fsx-csi-driver)
- [Mountpoint S3 CSI](https://github.com/awslabs/mountpoint-s3-csi-driver)
- [Secrets Store CSI ASCP](https://github.com/aws/secrets-store-csi-driver-provider-aws)
- [VPC CNI](https://github.com/aws/amazon-vpc-cni-k8s)
- [Karpenter](https://karpenter.sh/)
- [EKS Auto Mode](https://aws.amazon.com/eks/auto-mode/)

→ Next: [27 — **GKE deep — Workload Identity Federation, GCS Fuse CSI, BinAuth**](27_gke_data_exposure.md)


\newpage

# 27 — GKE deep: Workload Identity Federation, GCS Fuse CSI, Filestore CSI, Secret Manager CSI, BinAuth, Autopilot

## Why this module exists

GKE is the K8s with the cleanest identity story (Workload Identity Federation by default) and the most opinionated managed flavor (Autopilot). For a Sr Lead candidate, understanding GKE's primitives sharpens the EKS view by contrast.

---

## 1. Identity — Workload Identity Federation for GKE

Each pod's KSA maps to a GCP service account via annotation:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    iam.gke.io/gcp-service-account: infer-server@my-proj.iam.gserviceaccount.com
```

Then bind:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  infer-server@my-proj.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-proj.svc.id.goog[ml-serving/infer-server]"
```

Pod's `DefaultCredentials` uses the GKE metadata server (`metadata.google.internal`); the GKE-side workload identity component intercepts and trades the K8s token for a GCP access token via the GSA. No JSON keys. Period.

For new clusters (mid-2024+), enable **Workload Identity Federation for GKE in its new mode** (the "GKE Identity Federation"), which is cleaner under the hood. Old "Workload Identity for GKE" is the same model architecturally.

### 1.1 Org policy: ban JSON keys

```yaml
constraint: constraints/iam.disableServiceAccountKeyCreation
booleanPolicy: { enforced: true }
```

Apply at the organization level. Eliminates a whole class of credential leaks.

---

## 2. PD CSI — block storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: ssd-cmek }
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  disk-encryption-kms-key: projects/my-proj/locations/us-central1/keyRings/my-kr/cryptoKeys/my-key
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

Hyperdisk variants (Balanced, Throughput, Extreme) for tier separation. CMEK via Cloud KMS key reference.

For training checkpoints / vector indices / databases: `pd-ssd` is the default; Hyperdisk Balanced for cost.

---

## 3. GCS Fuse CSI driver — S3-equivalent mounted into pods

GA late 2023. Sidecar architecture: the driver injects a `gcs-fuse-sidecar` per pod that runs `gcsfuse` and presents the GCS bucket as a volume to the main container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: train
  namespace: ml-training
  annotations:
    gke-gcsfuse/volumes: "true"
    gke-gcsfuse/cpu-limit: "500m"
    gke-gcsfuse/memory-limit: 1Gi
spec:
  serviceAccountName: train-sa
  containers:
    - name: train
      image: nvcr.io/nvidia/pytorch:24.06-py3
      volumeMounts:
        - { name: training-data, mountPath: /data, readOnly: true }
  volumes:
    - name: training-data
      csi:
        driver: gcsfuse.csi.storage.gke.io
        readOnly: true
        volumeAttributes:
          bucketName: myorg-training-2026q2
          mountOptions: "implicit-dirs,file-cache-max-size-mb=10000"
```

The KSA `train-sa` is WIF-bound to a GSA with `roles/storage.objectViewer` on the bucket. Pods now have a read-only S3-equivalent at `/data`.

For ML training: this is the cleanest "read training data from object storage" pattern. Better than s3fs on AWS by quite a margin.

---

## 4. Filestore CSI — managed NFS

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: filestore-enterprise }
provisioner: filestore.csi.storage.gke.io
parameters:
  tier: enterprise
  network: my-vpc
  reserved-ipv4-cidr: 10.10.0.0/29
allowVolumeExpansion: true
```

RWX NFS for "many pods read the same data" patterns. Enterprise tier for HA. Comparable to AWS EFS or Azure Files.

---

## 5. Parallelstore — GCP's Lustre answer (2024)

For 1000+ GPU training, Parallelstore (GA mid-2024) is GCP's high-perf parallel FS. Mounts via CSI. Comparable to FSx for Lustre on AWS.

---

## 6. Secret Manager CSI provider

[secrets-store-csi-driver-provider-gcp](https://github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp):

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: gcp
  parameters:
    secrets: |
      - resourceName: "projects/my-proj/secrets/db-password/versions/latest"
        fileName: "db_password"
```

Pod's KSA (WIF-bound) needs `roles/secretmanager.secretAccessor` on the secret. Mount appears at the volume path.

ESO with GCP backend is the alternative if you want a K8s Secret object.

---

## 7. Binary Authorization — image attestations enforced

Already covered in module 24. GKE has the deepest cloud-native integration:

- Attestation notes stored in Grafeas (Container Analysis).
- Policy applied per cluster.
- Break-glass via deploy-time label, audited.

For regulated GKE clusters: BinAuth + signed images + CMEK. Standard.

---

## 8. GKE Autopilot — opinionated managed mode

GA Feb 2021. Differences from Standard:

- Node pools managed entirely by Google.
- You pay per pod resources (vCPU·hr, GB·hr) rather than per node-hour — predictable.
- Restrictions: no privileged pods, no hostPath, no hostNetwork, no `nodeSelector` for arbitrary labels, no DaemonSets except whitelisted, limited preempt.
- Default security: PSA-restricted, Workload Identity required.

For ML serving: Autopilot is fine and removes node ops. For ML training with GPUs and fine-grained tuning: Standard.

---

## 9. Confidential GKE Nodes

Confidential GKE runs nodes on **AMD SEV** (and **Intel TDX**, depending on region) — VM memory encrypted with a per-VM key. Useful for processing PII in containers where you don't want even Google operators to read memory.

```bash
gcloud container clusters create prod --enable-confidential-nodes
```

Same model as Azure Confidential containers. For regulated finance, this is the strongest hardware boundary.

---

## 10. Dataplane V2 — Cilium under the hood

GKE Dataplane V2 (default for new clusters since 2021) replaces kube-proxy + the legacy CNI with **Cilium**. Implications:

- L7 visibility (Hubble equivalent via gcloud CLI / Cloud Console).
- NetworkPolicy enforcement is built-in.
- BPF-based, low overhead at scale.

If you've been on Dataplane V2 for years, you're getting Cilium without knowing it.

---

## 11. The reference GKE+KServe architecture (for the curious)

Same idea as the EKS reference, with substitutions:

| Layer | EKS | GKE |
|---|---|---|
| Identity per pod | IRSA / Pod Identity | Workload Identity Federation |
| Block CSI | EBS CSI | PD CSI |
| File RWX CSI | EFS CSI | Filestore CSI |
| HPC | FSx for Lustre CSI | Parallelstore CSI |
| Object | Mountpoint-S3 CSI | GCS Fuse CSI |
| Secrets | ASCP / ESO | Secret Manager CSI / ESO |
| Image signing admission | Kyverno + Cosign | Binary Authorization |
| Dataplane | VPC CNI / Cilium | Dataplane V2 (Cilium) |
| Autoscaling | Karpenter | Cluster Autoscaler / Autopilot |

---

## Sanity check

1. Why does GCP's `iam.disableServiceAccountKeyCreation` org policy eliminate a whole class of credential leaks?
2. GCS Fuse CSI runs as a sidecar per pod, not as a node-level mount. What's the trade-off?
3. GKE Autopilot disallows hostPath. Why does that block some workloads, and which ones?
4. Confidential GKE Nodes — what specifically do they protect against?
5. GKE Dataplane V2 — what does it replace, and what does that give you?
6. Map: AWS EFS → GCP ?, AWS FSx-Lustre → GCP ?, AWS Secrets Manager → GCP ?

---

## Sources

- [Workload Identity Federation for GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [GCS Fuse CSI Driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver)
- [Filestore CSI](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver)
- [Parallelstore](https://cloud.google.com/parallelstore/docs)
- [Secret Manager CSI Provider for GCP](https://github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp)
- [Binary Authorization](https://cloud.google.com/binary-authorization)
- [GKE Autopilot](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Confidential GKE Nodes](https://cloud.google.com/confidential-computing/confidential-gke-nodes)
- [GKE Dataplane V2](https://cloud.google.com/kubernetes-engine/docs/concepts/dataplane-v2)

→ Next: [28 — **AKS deep — Entra Workload ID, Azure Files/Disk/Blob CSI, Key Vault CSI**](28_aks_data_exposure.md)


\newpage

# 28 — AKS deep: Entra Workload ID, Azure Files / Disk / Blob CSI, Key Vault CSI, private clusters

## Why this module exists

AKS is Optum's K8s and the K8s flavor the user has the strongest existing exposure to (Topic 02). This module covers the AKS-specific data primitives — what the user already knows in production, with explicit framing as the AKS counterpart of the EKS module.

---

## 1. Identity — Microsoft Entra Workload ID

GA July 2023. Replaces the deprecated AAD Pod Identity v1.

### 1.1 The model

1. AKS cluster has an OIDC issuer URL.
2. You create a **user-assigned managed identity** in Entra.
3. You add a **federated identity credential** on the MI that trusts the cluster's OIDC issuer + a specific KSA.
4. KSA annotated with the MI's client ID.
5. Pod uses the KSA; `DefaultAzureCredential` picks up the federated token via the projected SA token.

```bash
# Create a managed identity
az identity create --name ml-infer-mi --resource-group my-rg

# Configure federated credential
az identity federated-credential create \
  --name ml-infer-fc \
  --identity-name ml-infer-mi \
  --resource-group my-rg \
  --issuer $(az aks show -n prod -g my-rg --query oidcIssuerProfile.issuerUrl -o tsv) \
  --subject system:serviceaccount:ml-serving:infer-server
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    azure.workload.identity/client-id: <MI client ID>
  labels:
    azure.workload.identity/use: "true"
```

Pod gets env vars `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_FEDERATED_TOKEN_FILE`. The Azure SDK exchanges the federated token for an MI access token. No client secret.

---

## 2. Azure Disk CSI — block storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: managed-premium-cmk }
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  diskEncryptionSetID: /subscriptions/.../diskEncryptionSets/my-des
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

Disk Encryption Set (DES) pairs an Azure Key Vault key with disks for CMK encryption at rest.

For ML serving / databases / vector indices: Premium SSD v2 or Ultra Disk.

---

## 3. Azure Files CSI — RWX

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: azurefile-csi-premium }
provisioner: file.csi.azure.com
parameters:
  skuName: Premium_LRS
  protocol: nfs                # or "smb"
allowVolumeExpansion: true
```

SMB 3.1.1 by default; NFSv4.1 with Premium tier + the `nfs` protocol parameter.

For ML training where many pods read the same data: Azure Files Premium NFS. Less performant than Lustre but managed.

---

## 4. Azure Blob CSI — object storage as a volume

[Azure Blob CSI](https://learn.microsoft.com/azure/aks/azure-blob-csi):

- **blobfuse2** mount mode — FUSE; POSIX-friendly.
- **NFS 3.0** mount mode — kernel-level mount; faster but limited semantics.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: training-data }
spec:
  storageClassName: azureblob-fuse-premium
  accessModes: [ReadWriteMany]
  resources: { requests: { storage: 100Gi } }
```

For ML training data: blobfuse2 mode is what you want. Modeled on the same pattern as GCS Fuse / Mountpoint-S3.

---

## 5. Azure Key Vault Provider for Secrets Store CSI

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: <workload-identity-client-id>
    keyvaultName: my-kv
    cloudName: AzurePublicCloud
    objects: |
      array:
        - |
          objectName: db-password
          objectType: secret
          objectVersion: ""
    tenantId: <tenant-id>
  secretObjects:                               # optional: sync to native K8s Secret
    - secretName: db-creds-k8s
      type: Opaque
      data: [{ key: db_password, objectName: db-password }]
```

The `secretObjects` block creates a native K8s Secret for env-var-style consumption while also mounting the file.

---

## 6. Private clusters

```bash
az aks create --name prod --resource-group my-rg \
  --enable-private-cluster \
  --enable-managed-identity \
  --network-plugin azure \
  --network-plugin-mode overlay \
  --network-policy cilium \
  --enable-oidc-issuer \
  --enable-workload-identity
```

Private cluster = API server has no public IP. Reached via:
- VNet peering from a jumpbox.
- VPN / ExpressRoute.
- AKS Private Link.

For regulated workloads, this is mandatory. Pair with Azure Bastion for human admin access.

---

## 7. Azure CNI flavors

- **Kubenet** — deprecated path; overlay-style.
- **Azure CNI Overlay** — overlay model with VNet-routable pod IPs via NAT.
- **Azure CNI Pod Subnet** — each pod gets a real VNet IP (analogous to AWS VPC CNI). Limited pod density per node.
- **Azure CNI Powered by Cilium** — Cilium eBPF dataplane. The modern default.

For modern AKS: pick **Azure CNI Powered by Cilium**. Gets you NetworkPolicy + L7 visibility + kube-proxy replacement.

---

## 8. Confidential containers on AKS

Confidential Containers on AKS uses **Kata Containers** + **AMD SEV-SNP** to give per-pod VM isolation with memory encryption. For PII / regulated processing:

```yaml
spec:
  runtimeClassName: kata-cc-isolation
```

Comparable to GCP Confidential GKE Nodes and AWS Nitro Enclaves (in spirit, though Nitro is different in execution).

---

## 9. ACR integration

```bash
az aks update --name prod --resource-group my-rg --attach-acr myacr
```

Adds `AcrPull` role to the kubelet identity. Image pulls "just work."

For private network setups: ACR Premium with Private Endpoint + Private DNS Zone.

---

## 10. The reference AKS+KServe architecture (the parallel of EKS)

```
┌──────────────────────────────────────────────────────────────────┐
│ AKS (private cluster, KMS etcd, OIDC issuer enabled)             │
│                                                                  │
│  ml-serving namespace                                            │
│   ServiceAccount (workload-identity/client-id annotated)         │
│   InferenceService (KServe)                                      │
│   PSA: restricted                                                │
└────────┬────────────────┬──────────────────┬────────────────────┘
         │                │                  │
   ┌─────▼─────┐    ┌─────▼─────┐      ┌─────▼─────┐
   │ ACR       │    │ Blob/Files│      │ Key Vault │
   │ Premium   │    │ + CMK     │      │ + HSM     │
   │ + PE      │    │ + PE      │      │ + PE      │
   └───────────┘    └───────────┘      └───────────┘
```

Cross-cuts:
- **Identity**: Entra Workload ID per workload.
- **Egress**: NSG default-deny + Azure Firewall.
- **Admission**: Kyverno + Defender for Cloud signals.
- **Audit**: K8s audit → Log Analytics + Microsoft Sentinel.

---

## Sanity check

1. AKS Workload ID uses what kind of federated credential under the hood?
2. Azure Files SMB vs NFSv4.1 — when does each fit?
3. Why does Azure Blob CSI offer two modes (blobfuse2 vs NFS 3.0), and when do you pick each?
4. What does a **private AKS cluster** mean exactly, and how do humans reach the API server?
5. Confidential Containers on AKS — what hardware feature underpins them?
6. Map: AWS EFS → Azure ?, AWS Secrets Manager → Azure ?, IRSA → Azure ?

---

## Sources

- [Microsoft Entra Workload ID for AKS](https://learn.microsoft.com/azure/aks/workload-identity-overview)
- [Azure Disk CSI](https://learn.microsoft.com/azure/aks/azure-disk-csi)
- [Azure Files CSI](https://learn.microsoft.com/azure/aks/azure-files-csi)
- [Azure Blob CSI](https://learn.microsoft.com/azure/aks/azure-blob-csi)
- [Azure Key Vault Provider for Secrets Store CSI](https://learn.microsoft.com/azure/aks/csi-secrets-store-driver)
- [Private clusters](https://learn.microsoft.com/azure/aks/private-clusters)
- [Azure CNI Powered by Cilium](https://learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium)
- [Confidential Containers on AKS](https://learn.microsoft.com/azure/aks/confidential-containers-overview)

→ Next: [29 — **On-prem K8s — Rook-Ceph, Longhorn, Velero, Vault, MetalLB, air-gap**](29_onprem_k8s_data.md)


\newpage

# 29 — On-prem K8s: Rook-Ceph, Longhorn, OpenEBS, Portworx, Velero, Vault, MetalLB, air-gap

## Why this module exists

On-prem K8s requires you to bring everything yourself. Storage, load balancing, identity, secrets, registry, networking — all you. This module covers the dominant CNCF + commercial choices.

---

## 1. Distro selection

| Distro | License | Notes |
|---|---|---|
| **kubeadm** | Apache 2.0 | The canonical bootstrap; bring everything yourself |
| **Kubespray** | Apache 2.0 | Ansible-based; deploys kubeadm cluster with addons |
| **Rancher RKE2** | Apache 2.0 | Hardened; CIS-K8s compliant by default; FIPS option |
| **K3s** (SUSE) | Apache 2.0 | Lightweight; single binary; edge/IoT |
| **Talos** | MPL | Immutable OS; declarative; minimal attack surface |
| **OpenShift** (Red Hat) | Commercial | Most opinionated; tightly integrated; Operators-first |
| **Tanzu Kubernetes Grid** (VMware/Broadcom) | Commercial | VMware-aligned |
| **Mirantis Kubernetes Engine** | Commercial | (was Docker EE) |

For ML on-prem: **OpenShift** at regulated enterprises that already pay for it; **RKE2** for self-managed regulated finance; **Talos** for the security-pure shop.

---

## 2. Storage — the heart of on-prem K8s

The CSI ecosystem on-prem:

| Driver | Backend | Notes |
|---|---|---|
| **Rook-Ceph** | Ceph | CNCF Graduated; runs Ceph as K8s CRs (CephCluster, CephBlockPool, CephObjectStore, CephFilesystem). Heavy ops; powerful. |
| **Longhorn** | Per-node disks | CNCF Incubating (Rancher origin). Cluster-internal block storage; replicates across nodes. Simpler than Ceph. |
| **OpenEBS Mayastor** | NVMe over fabrics | CNCF Sandbox. Best perf for NVMe SSDs. |
| **OpenEBS cStor / Jiva** | Local disks | Mature OSS engines; cStor uses ZFS underneath. |
| **Portworx** | Per-node + commercial | Pure Storage product. Storage classes, replication, snapshots, DR. |
| **NetApp Trident** | NetApp appliances | If you have NetApp, use this. |
| **Pure Service Orchestrator** | Pure Storage FlashArray | Pure's CSI. |
| **Dell PowerStore / Dell EMC PowerScale CSI** | Dell appliances | If you have Dell. |

For ML on-prem: existing storage appliances (NetApp / Dell / Pure) → use their CSI. Greenfield with budget → Portworx. Greenfield with OSS → Rook-Ceph if you have ops staff; Longhorn if you don't.

### 2.1 Rook-Ceph example

```yaml
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata: { name: rook-ceph, namespace: rook-ceph }
spec:
  cephVersion: { image: quay.io/ceph/ceph:v18.2.4 }
  dataDirHostPath: /var/lib/rook
  mon: { count: 3, allowMultiplePerNode: false }
  mgr: { count: 2 }
  storage:
    useAllNodes: true
    useAllDevices: false
    deviceFilter: nvme[0-9]+n1
  network:
    provider: host                    # for performance
  resources:
    osd: { requests: { cpu: 2, memory: 4Gi }, limits: { memory: 8Gi } }
---
apiVersion: ceph.rook.io/v1
kind: CephBlockPool
metadata: { name: replicapool, namespace: rook-ceph }
spec:
  failureDomain: host
  replicated: { size: 3 }
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: ceph-block }
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  pool: replicapool
  clusterID: rook-ceph
  imageFormat: "2"
  imageFeatures: layering
  csi.storage.k8s.io/provisioner-secret-name: rook-csi-rbd-provisioner
  # ...
reclaimPolicy: Retain
```

Yields a `ceph-block` StorageClass that backs PVCs with replicated Ceph RBD volumes. CephFS pools for RWX file. CephObjectStore for S3-compatible (RGW).

---

## 3. Local PV — for high-IOPS workloads

```yaml
apiVersion: v1
kind: PersistentVolume
metadata: { name: nvme-node-1 }
spec:
  capacity: { storage: 2Ti }
  volumeMode: Filesystem
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: local-nvme
  local: { path: /mnt/nvme-1 }
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - { key: kubernetes.io/hostname, operator: In, values: [node-1] }
```

Local PVs are essential for ML training intermediate state, where 10–100 GB of fast NVMe per node beats any networked option. Combine with the **local-path-provisioner** (Rancher) or `sig-storage-local-static-provisioner` for declarative use.

---

## 4. Backups — Velero

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata: { name: nightly, namespace: velero }
spec:
  schedule: "0 2 * * *"
  template:
    includedNamespaces: ["ml-serving", "ml-training", "data-pipeline"]
    snapshotVolumes: true
    ttl: 720h
    storageLocation: minio-default
    volumeSnapshotLocations: [csi-default]
```

Velero backs up:
- K8s manifests (resources).
- PV data via **CSI snapshots** + restic for non-snapshot-capable volumes.

Target: S3-compatible (MinIO on-prem, AWS S3, Azure Blob, GCS).

Restore tested quarterly. If your cluster nukes itself, Velero is the difference between "8-hour fire drill" and "8-week reconstruction."

---

## 5. Vault on K8s

Vault HA on K8s:

```bash
helm install vault hashicorp/vault \
  --set server.ha.enabled=true \
  --set server.ha.raft.enabled=true \
  --set server.ha.replicas=5
```

5 replicas with Raft = quorum 3. Auto-unseal via cloud KMS or transit auto-unseal from another Vault.

Auth methods relevant for K8s:
- **Kubernetes auth** — pod's projected SA token authenticates to Vault.
- **AppRole** — for non-K8s callers.
- **TLS cert** — for the most security-sensitive cases.

Apps consume via:
- **Vault Agent Injector** (annotation-driven sidecar).
- **Vault CSI Provider**.
- **External Secrets Operator with Vault backend**.

For on-prem regulated finance: Vault is the standard. Topic 04 covered Cloud Custodian; on-prem the secret-management spine is Vault.

---

## 6. MetalLB — bare-metal LoadBalancer

K8s `Service type=LoadBalancer` calls a cloud-provider integration to provision an ELB/GCP-LB/Azure-LB. On-prem there's no such thing. **MetalLB** is the answer.

Two modes:

- **Layer 2** — MetalLB pods on each node ARP-respond for the assigned IPs. Simple; one node is "active" per IP.
- **BGP** — MetalLB advertises routes via BGP to upstream switches. Multi-active; load-balanced across nodes.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata: { name: default, namespace: metallb-system }
spec:
  addresses: ["10.0.100.50-10.0.100.100"]
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata: { name: default, namespace: metallb-system }
spec:
  ipAddressPools: [default]
```

Alternative: **kube-vip** (similar) or **Cilium L2 announcements** (Cilium 1.14+; cleanest if you're already running Cilium).

---

## 7. Air-gapped K8s

The full air-gap setup:

- **Registry mirror**: Harbor with the upstream-mirroring config. Allowlist of upstream registries; sync via secure DMZ "diode."
- **Container runtime config**: containerd mirror rules in `/etc/containerd/config.toml` to redirect all pulls to your Harbor.
- **Helm chart repo**: Harbor's Helm OCI artifact storage.
- **PyPI mirror**: Sonatype Nexus / JFrog Artifactory / pypiserver.
- **OS package mirror**: apt/yum proxy.
- **Cert authority**: internal PKI; CA bundle baked into base images.
- **DNS**: internal resolver; no public DNS.
- **Time sync**: internal NTP.
- **Validation**: CI runs in a network-isolated namespace before pulling new artifacts.

The Cosign verification gets harder air-gapped: Rekor is public. Either:
- Mirror Rekor (advanced); or
- Use Cosign keyed signing with a key from internal KMS / HSM and skip Rekor.
- Or trust attestations within a known-pinned set without verifying Sigstore log.

---

## 8. Identity on-prem

Without cloud IAM, the K8s identity-binding for "talk to Vault / talk to MinIO / talk to internal services" is:

- **K8s ServiceAccount with projected tokens** + **SPIFFE/SPIRE** for federation.
- **Vault as the broker**: SA → Vault K8s auth → Vault returns dynamic creds for MinIO / DB / API.
- **mTLS via cert-manager** with an internal CA — every workload has a cert; mTLS is the identity.

SPIFFE/SPIRE is the gold standard but op-heavy. For most on-prem K8s shops: Vault-as-broker + service mesh mTLS (Istio with SPIRE under the hood, or Linkerd's built-in identity) is the practical answer.

---

## 9. The reference on-prem K8s ML architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ K8s cluster (RKE2, Talos, or OpenShift)                          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ml-serving (PSA restricted, NetworkPolicy default-deny)    │  │
│  │   KSA → Vault K8s auth → dynamic creds                     │  │
│  │   KServe InferenceService                                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ kube-system  (privileged)                                  │  │
│  │   Cilium, MetalLB/cilium-L2, Rook-Ceph operator, Velero    │  │
│  │   cert-manager, Vault Agent Injector, Falco                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────┬──────────────┬─────────────────┬─────────────────┘
               │              │                 │
        ┌──────▼──────┐ ┌─────▼─────┐    ┌──────▼──────┐
        │ Rook-Ceph   │ │ Vault HA  │    │ Harbor      │
        │ Block/FS/RGW│ │ + HSM     │    │ + Trivy     │
        │ + LUKS OSDs │ │ + KV+Tran │    │ + Cosign    │
        └─────────────┘ └───────────┘    └─────────────┘
```

Cross-cuts:
- **Identity**: K8s SA + Vault K8s auth + (optional) SPIFFE/SPIRE.
- **Storage**: Rook-Ceph (or NetApp Trident / Portworx if the appliance is there).
- **Secrets**: Vault Agent / CSI / ESO.
- **Registry**: Harbor with image signing.
- **Backup**: Velero with MinIO/Ceph RGW.
- **Audit**: K8s audit log + Falco → on-prem SIEM (Splunk, Elastic).

---

## 10. The "do we even need on-prem K8s?" question

For Capital One: no — they're 100% AWS. For Optum / regulated healthcare / sovereign-data shops: yes. For the user's career: knowing on-prem deeply is a multiplier on cloud knowledge.

The architect-grade summary: **on-prem K8s is K8s where you pay for the abstractions cloud gave you for free.** The patterns are identical; the operators do the heavy lifting.

---

## Sanity check

1. Rook-Ceph vs Longhorn — name two reasons to pick each.
2. Why is **Local PV** the right primitive for ML training intermediate state and the wrong primitive for application persistence?
3. Velero's role — what does it actually back up, and where does it store backups?
4. MetalLB Layer 2 vs BGP — when to use each?
5. Air-gapped K8s breaks Cosign keyless signing. What are the two workaround patterns?
6. Without cloud IAM, what's the on-prem "identity broker" pattern?

---

## Sources

- [Rook-Ceph](https://rook.io/docs/rook/)
- [Longhorn](https://longhorn.io/docs/)
- [OpenEBS](https://openebs.io/docs/)
- [Portworx](https://docs.portworx.com/)
- [NetApp Trident](https://docs.netapp.com/us-en/trident/)
- [Velero](https://velero.io/docs/)
- [HashiCorp Vault on K8s](https://developer.hashicorp.com/vault/docs/platform/k8s)
- [MetalLB](https://metallb.io/)
- [cilium L2 announcements](https://docs.cilium.io/en/stable/network/l2-announcements/)
- [Talos Linux](https://www.talos.dev/)
- [Rancher RKE2](https://docs.rke2.io/)

→ Next: [30 — Model serving on K8s — KServe, Seldon, BentoML, Triton, vLLM, Ray Serve](30_model_serving_k8s.md)


\newpage

# 30 — Model serving on K8s: KServe, Seldon, BentoML, Triton, vLLM, Ray Serve

> *"KServe + KEDA + Karpenter on EKS is the Capital One stack. Master the `InferenceService` CRD and you've made yourself credible for the Lead role."*

## Why this module exists

Model serving on K8s is the area Capital One's Lead MLE job posting explicitly names. This module compares the leading frameworks, focuses on KServe (the C1 choice), and shows the `InferenceService` patterns for classical ML, transformer, and LLM serving.

---

## 1. The framework landscape

| Framework | License | What it adds over a plain Deployment |
|---|---|---|
| **KServe** | Apache 2.0 (CNCF Incubating) | `InferenceService` CRD; pre/post-processor + predictor + explainer chain; ModelMesh for many small models; autoscaling (Knative or RawDeployment); standard `/v1/models/X:predict` API |
| **Seldon Core v2** | Source-available (Seldon Inc.) | Multi-model serving, experiments (canary, A/B), Seldon Inference Graph |
| **BentoML + Yatai** | Apache 2.0 | Python-first framework; bundles deps + model into a "Bento"; Yatai for K8s deploy |
| **NVIDIA Triton** | Apache 2.0 | High-perf C++ inference server; backends for ONNX, TensorRT, PyTorch, TensorFlow, Python, FIL (forest); concurrent model exec |
| **vLLM** | Apache 2.0 | LLM-specialized; continuous batching, PagedAttention; the de facto for LLM inference 2024-2026 |
| **Text Generation Inference (TGI)** | Apache 2.0 | HuggingFace; similar to vLLM; quantization-friendly |
| **Ray Serve** | Apache 2.0 | Ray-based; flexible Python deployment graphs; HPC parallelism |

For Capital One context: **KServe + RawDeployment mode + a Triton or vLLM predictor underneath**. KServe is the orchestration layer; Triton/vLLM is the actual model runtime.

---

## 2. KServe — the `InferenceService` CRD

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: sentiment, namespace: ml-serving }
spec:
  predictor:
    serviceAccountName: sentiment-sa            # IRSA / Pod Identity / WIF role
    minReplicas: 1
    maxReplicas: 5
    containerConcurrency: 4
    timeout: 60
    pytorch:
      storageUri: s3://myorg-ml-models/sentiment/v1.4/
      resources:
        requests: { cpu: 1, memory: 4Gi, nvidia.com/gpu: 1 }
        limits:   { cpu: 2, memory: 8Gi, nvidia.com/gpu: 1 }
```

What's happening:
- KServe controller creates a Deployment (or Knative service in default mode), Service, and (if Knative) revision.
- The `pytorch` predictor pulls weights from `s3://...` via the SA (IRSA permissions).
- Endpoint: `http://sentiment.ml-serving.svc.cluster.local/v1/models/sentiment:predict` (the OpenAI-style API).

### 2.1 Deployment modes

- **Serverless** (Knative-backed, default before v0.11) — scale to zero, request-based autoscaling.
- **RawDeployment** — vanilla Deployment + HPA. No Knative dependency. **Capital One's likely mode** for predictable workloads.

```yaml
metadata:
  annotations:
    serving.kserve.io/deploymentMode: RawDeployment
```

### 2.2 ModelMesh — many small models on one pod

For RAG retrievers, embedding services, traditional ML with thousands of models: ModelMesh loads models on-demand into pre-warmed serving pods. One pod serves many models; LRU eviction.

### 2.3 The transformer + predictor chain

```yaml
spec:
  transformer:
    containers:
      - name: tokenize
        image: myorg/tokenizer:1.0
        env: [{ name: MODEL_NAME, value: sentiment }]
  predictor:
    triton:
      storageUri: s3://myorg-models/sentiment-onnx/
```

Request flows: client → KServe transformer → predictor → response. Useful for tokenization, image preprocessing, etc.

---

## 3. KServe + Triton

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: bert-base }
spec:
  predictor:
    triton:
      runtimeVersion: 24.06-py3
      storageUri: s3://myorg-models/bert-base/
      resources: { requests: { nvidia.com/gpu: 1 } }
```

Triton's model repository format (`models/<name>/<version>/model.plan` for TensorRT, etc.) defined in `s3://...`. KServe pulls and starts Triton.

For multi-model serving with hot model swapping: this is the canonical pattern.

---

## 4. KServe + vLLM for LLM serving

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata: { name: llama3-8b }
spec:
  predictor:
    containers:
      - name: vllm
        image: vllm/vllm-openai:v0.6.2
        args:
          - --model=meta-llama/Llama-3.1-8B-Instruct
          - --dtype=bfloat16
          - --max-num-seqs=64
          - --gpu-memory-utilization=0.92
          - --enable-prefix-caching
        env:
          - { name: HF_TOKEN, valueFrom: { secretKeyRef: { name: hf-token, key: token } } }
        resources:
          requests: { nvidia.com/gpu: 1, memory: 32Gi }
          limits:   { nvidia.com/gpu: 1, memory: 32Gi }
        ports: [{ containerPort: 8000 }]
```

vLLM exposes the OpenAI-compatible API at `/v1/chat/completions`. Drop-in for LangChain / OpenAI SDK clients. PagedAttention + continuous batching extracts ~2-5x throughput over naïve serving.

For LLM-scale serving (Llama 70B, Mixtral 8x7B): tensor-parallel across multiple GPUs:

```yaml
args:
  - --tensor-parallel-size=4
  - --pipeline-parallel-size=2
resources:
  limits: { nvidia.com/gpu: 4 }
```

The pod gets 4 GPUs; vLLM shards the model.

---

## 5. Autoscaling

### 5.1 HPA (CPU/memory + custom metrics)

Standard HPA works for serving:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: sentiment-hpa }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sentiment-predictor-default
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Pods
      pods:
        metric: { name: requests_per_second }
        target: { type: AverageValue, averageValue: "50" }
```

For ML serving, latency or queue depth metrics work better than CPU. Expose them via Prometheus + `prometheus-adapter`.

### 5.2 KEDA — event-driven autoscaling

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: { name: vllm-scaler, namespace: ml-serving }
spec:
  scaleTargetRef: { name: llama3-8b-predictor-default }
  minReplicaCount: 1
  maxReplicaCount: 8
  triggers:
    - type: prometheus
      metadata:
        serverAddress: http://prometheus.monitoring.svc:9090
        metricName: vllm_pending_requests
        threshold: '10'
        query: sum(rate(vllm_pending_requests[1m])) by (model)
```

KEDA scales based on prom metrics. Works with any queue (Kafka, SQS, Redis lists, RabbitMQ).

### 5.3 Knative scale-to-zero

Default KServe mode. Pod scales to 0 when no requests; cold start on first request (~10s for small models, 30-90s for large).

For LLM serving: **NEVER use scale-to-zero** — cold start of a 70B model is minutes. Use `minReplicas: 1+`.

---

## 6. GPU sharing

Three patterns:

- **NVIDIA MIG** (A100, H100, H200, H200 NVL) — hardware partition. e.g., A100-80GB split into 7×10GB MIG slices. Each pod gets a slice as a "fractional GPU."
- **NVIDIA time-slicing** — software multiplexing; multiple pods share one GPU. No isolation; throughput share.
- **MPS** (Multi-Process Service) — multiple processes share GPU concurrently. CUDA-native.

For ML serving with small models: MIG is the right call. For training: full GPU per pod.

The **NVIDIA GPU Operator** installs and manages the device plugin, MIG, DCGM, GPU Feature Discovery, MIG-parted config.

---

## 7. Karpenter for GPU pools

Already covered in module 26. The GPU NodePool with `consolidateAfter: 5m` prevents thrash on expensive instances.

For multi-tier serving: separate NodePools for inference (low-latency, smaller GPUs like L4/L40S) vs training (multi-GPU nodes).

---

## 8. Capital One signal — putting it together

The job posting language: "Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)". Decode:

- **KServe** — the orchestration layer.
- **Building Kubernetes Clusters** — the candidate is expected to operate the cluster, not just consume a managed one. Karpenter, VPC CNI, IRSA, etc.
- **PyTorch + TensorFlow** — frameworks, both. Triton supports both as backends; KServe predictor handles both.
- **on AWS** — EKS specifically.

What this implies for talking-points in an interview:

- "I'd use KServe RawDeployment mode with KEDA for autoscaling on Prometheus metrics — Knative-Serverless adds latency that hurts at p99."
- "For LLM serving I'd reach for vLLM with PagedAttention; for traditional models, Triton."
- "GPU pools managed by Karpenter with `consolidateAfter: 5m` to prevent expensive node thrash."
- "IRSA-rolled model S3 bucket; model artifacts versioned by `storageUri` with digest in the InferenceService."
- "Falco runtime rules for shell-spawn / IMDS / SA-token-theft signals."

This is the credibility multiplier vs candidates who only know SageMaker endpoints.

---

## 9. Observability for serving

Per-model metrics:

- **request_count, request_latency** (histograms).
- **gpu_utilization** (DCGM).
- **vllm_pending_requests, vllm_running_requests, vllm_tokens_generated_per_second** (LLM-specific).
- **model_load_seconds** (cold start).

Combined with OpenTelemetry traces for per-request latency breakdown.

---

## 10. Security hardening for serving

Inherits modules 22 + 23:

- PSA `restricted` namespace label.
- ServiceAccount with IRSA / Pod Identity → S3 read-only on the model bucket only.
- NetworkPolicy: ingress only from API gateway; egress to S3 + KMS + Secrets Manager + DCGM + logging.
- Cosign-verified image at admission (Kyverno).
- Read-only root FS + tmpfs for `/tmp` + `/dev/shm` of appropriate size.
- Resource requests = limits for GPU pods (Guaranteed QoS).

---

## Sanity check

1. Why does Capital One likely use KServe RawDeployment instead of Knative Serverless?
2. vLLM vs Triton — when does each fit?
3. NVIDIA MIG vs time-slicing — which gives isolation, which gives more density?
4. Why is scale-to-zero a bad idea for LLM serving?
5. KEDA scales based on what kinds of metrics, and what does it give over HPA-with-CPU?
6. Name three security controls a KServe `InferenceService` pod should have.

---

## Sources

- [KServe docs](https://kserve.github.io/website/)
- [KServe InferenceService API](https://kserve.github.io/website/latest/reference/api/)
- [NVIDIA Triton Inference Server](https://github.com/triton-inference-server/server)
- [vLLM](https://docs.vllm.ai/)
- [HuggingFace TGI](https://huggingface.co/docs/text-generation-inference/)
- [Ray Serve](https://docs.ray.io/en/latest/serve/index.html)
- [KEDA](https://keda.sh/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [Karpenter](https://karpenter.sh/)

→ Next: [31 — Training on K8s — Training Operator, Volcano, GPU Operator, Karpenter](31_training_k8s.md)


\newpage

# 31 — Training on K8s: Kubeflow Training Operator, Volcano, NVIDIA GPU Operator, Karpenter

## Why this module exists

Distributed training has different K8s semantics than serving: gang scheduling (all pods or none), rendezvous (rank assignment), GPU topology, and aggressive autoscale-down post-completion. This module covers the four primitives.

---

## 1. Kubeflow Training Operator

CRDs for distributed training: `PyTorchJob`, `TFJob`, `MPIJob`, `PaddleJob`, `XGBoostJob`, `JAXJob`. Each handles framework-specific rendezvous and lifecycle.

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata: { name: train-bert-2026q2, namespace: ml-training }
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      restartPolicy: OnFailure
      template:
        spec:
          serviceAccountName: train-sa
          containers:
            - name: pytorch
              image: nvcr.io/nvidia/pytorch:24.06-py3
              command: ["torchrun", "--standalone", "--nnodes=1", "--nproc-per-node=8", "train.py"]
              resources: { limits: { nvidia.com/gpu: 8 } }
    Worker:
      replicas: 7
      restartPolicy: OnFailure
      template: { ... }
```

The operator sets `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK` env vars per pod. `torchrun` consumes them; PyTorch initializes the process group automatically.

For 64 GPUs across 8 nodes: 1 Master + 7 Workers, each with `nvidia.com/gpu: 8`.

---

## 2. Volcano — gang scheduling

Default K8s scheduler picks pods one at a time. For training with 64 GPUs, you don't want 7 pods running while pod 8 waits for capacity — that wastes GPU hours. **Gang scheduling** says: schedule all-or-nothing.

[Volcano](https://volcano.sh/) is the CNCF Incubating batch scheduler:

```yaml
apiVersion: scheduling.volcano.sh/v1beta1
kind: PodGroup
metadata: { name: train-bert, namespace: ml-training }
spec:
  minMember: 8                        # 8 pods minimum to start
  queue: ml-default
---
# Pod template includes:
metadata:
  annotations:
    scheduling.k8s.io/group-name: train-bert
spec:
  schedulerName: volcano
```

Volcano + Training Operator is the standard production combo for large training.

---

## 3. NVIDIA GPU Operator

Helm-installable. Manages:

- **NVIDIA driver** (matching kernel).
- **Container Toolkit** (for nvidia-container-runtime).
- **Device Plugin** (advertises `nvidia.com/gpu` resource to K8s).
- **GPU Feature Discovery** (labels nodes with `nvidia.com/gpu.product=H100` etc).
- **DCGM Exporter** (Prometheus metrics).
- **MIG Manager** (for MIG-capable GPUs).
- **PSA-restricted** compatibility.

```bash
helm install gpu-operator nvidia/gpu-operator -n gpu-operator --create-namespace \
  --set toolkit.version=v1.16.0 \
  --set driver.version=550.90.07 \
  --set migManager.enabled=true
```

For Capital One–style stack: GPU Operator is non-negotiable on any GPU node pool.

---

## 4. MIG, time-slicing, MPS — capacity strategies

| Strategy | Hardware | Use case |
|---|---|---|
| **MIG** | A100/H100/H200 | Multi-model serving with isolation; up to 7 instances per A100-80GB |
| **Time-slicing** | Any | Multi-tenant training without isolation (don't recommend) |
| **MPS** | Any | Multiple processes share one GPU; CUDA-native; co-located inference |

For training: full GPU per pod. For serving small models: MIG.

---

## 5. Distributed-comm primitives

NCCL is the GPU-to-GPU comm library. Optimal NCCL needs:

- **NVLink** between GPUs in same node (P5/P5e instances on AWS).
- **InfiniBand** or **EFA** (AWS) between nodes for multi-node.
- **NCCL_TOPO_FILE** for topology hints.

For multi-node on EKS:

```yaml
# Pod annotations for EFA
metadata:
  annotations:
    k8s.amazonaws.com/efa-resource: "true"
spec:
  containers:
    - resources:
        limits:
          nvidia.com/gpu: 8
          vpc.amazonaws.com/efa: 4                   # 4 EFA interfaces
```

EFA gives ~3.2 Tbps inter-node on `p5.48xlarge`. Without it, multi-node training is bottlenecked at GPU 1's pace.

---

## 6. Karpenter for GPU autoscaling

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata: { name: gpu-h100-training }
spec:
  template:
    metadata:
      labels: { workload: training }
    spec:
      taints:
        - { key: nvidia.com/gpu, value: "h100", effect: NoSchedule }
      requirements:
        - { key: kubernetes.io/arch, operator: In, values: [amd64] }
        - { key: node.kubernetes.io/instance-type, operator: In,
            values: [p5.48xlarge, p5e.48xlarge, p5en.48xlarge] }
        - { key: karpenter.sh/capacity-type, operator: In, values: [on-demand, spot] }
      nodeClassRef: { name: gpu-default-ec2 }
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 30s              # training is fail-fast; can churn nodes
    expireAfter: 168h
```

For training: `consolidateAfter: 30s` is OK (jobs are batched). For serving: 5m+ as in module 26.

For multi-node training: **EC2 Capacity Blocks for ML** is the AWS primitive to reserve capacity for fixed time windows (1-8 weeks). Karpenter can target capacity blocks. Required when chasing scarce P5 capacity.

---

## 7. Spot instances for training — checkpointing

Spot is 70-80% cheaper but interruptible. For training:

- Checkpoint every 30 min or per-epoch.
- Use **Karpenter Spot** capacity type.
- On interruption (2-min warning), kubelet evicts; PyTorchJob's `OnFailure` policy reschedules.
- **The job resumes from last checkpoint** — write a resume-from-checkpoint code path in training scripts.

This is the cost lever that turns $1M training into $200K. Capital One's published FinOps culture would care.

---

## 8. Topology-aware scheduling

For 64-GPU training where same-rack matters: **Topology Aware Scheduling** (TAS) hints to scheduler "place these 8 pods on nodes in the same rack."

The K8s primitive: `topologySpreadConstraints` + node labels for rack/AZ:

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector: { matchLabels: { job-name: train-bert } }
```

For training: prefer same-AZ (minimize inter-AZ cost + latency).

---

## 9. The Training Operator alternatives

- **Ray on K8s** (KubeRay) — Ray cluster as RayCluster CRD; flexible Python parallelism.
- **DeepSpeed / FSDP / Megatron** — frameworks for >7B-param training; called from PyTorchJob.
- **NVIDIA NeMo Curator + NeMo Megatron** — LLM-specific.
- **Argo Workflows** — for DAGs of training steps (compose with PyTorchJob inside).

For ML platforms: Training Operator is the standard; Ray is the alternative for HPC-flexible workloads.

---

## 10. The training pipeline on K8s

```
S3 bucket (raw data) → Glue/EMR transform → S3 bucket (features) → KubeFlow PyTorchJob → S3 (checkpoints) → KServe InferenceService
                                                       ↑
                                                  Argo / Step Functions orchestration
                                                       ↑
                                                  Triggered by data freshness / schedule
```

For Capital One: Step Functions orchestrates (not Airflow); PyTorchJob runs on EKS; checkpoints go to S3 with KMS; model artifact promoted to KServe via GitOps.

---

## Sanity check

1. PyTorchJob auto-sets which four env vars per pod, and what do they mean?
2. Why does multi-node distributed training need gang scheduling?
3. EFA on EKS — what does it accelerate, and on which instance types?
4. Spot for training: what's the one code change you need to make in training scripts?
5. MIG vs time-slicing — pick one for "model serving with strict isolation."
6. Step Functions vs Argo Workflows for training orchestration — what's the Capital One choice?

---

## Sources

- [Kubeflow Training Operator](https://www.kubeflow.org/docs/components/training/overview/)
- [Volcano](https://volcano.sh/en/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/)
- [NVIDIA MIG](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/)
- [AWS EFA on EKS](https://docs.aws.amazon.com/eks/latest/userguide/node-efa.html)
- [Karpenter](https://karpenter.sh/)
- [EC2 Capacity Blocks for ML](https://aws.amazon.com/ec2/capacityblocks/)
- [KubeRay](https://docs.ray.io/en/latest/cluster/kubernetes/index.html)

→ Next: [32 — Service mesh & zero-trust — Istio, Linkerd, Cilium, SPIFFE/SPIRE](32_service_mesh.md)


\newpage

# 32 — Service mesh & zero-trust: Istio, Linkerd, Cilium, SPIFFE/SPIRE

## Why this module exists

East-west traffic (pod-to-pod) is plaintext by default. Service mesh adds mTLS, traffic management, and L7 policy. For regulated finance, mesh is the standard answer for "zero-trust between services."

---

## 1. The three meshes

### 1.1 Istio

- The most-deployed. CNCF Graduated 2024.
- Two architectures: **sidecar mode** (Envoy proxy per pod) and **ambient mode** (sidecarless: `ztunnel` per node + optional `waypoint proxy` per identity).
- Strong L7 policy via **AuthorizationPolicy** CRD.
- Built on Envoy.

### 1.2 Linkerd

- CNCF Graduated. Light-weight; written in Rust.
- Sidecar only.
- Simpler config; faster; smaller resource footprint.
- mTLS automatic.

### 1.3 Cilium Service Mesh

- Sidecarless; mesh functions implemented in the eBPF dataplane.
- Identity-based (Cilium identities).
- For shops already running Cilium as CNI: it's free.

For Capital One–style: **Istio** is the most-deployed; **Linkerd** is the easier-to-operate alternative. Cilium SM is gaining ground in 2025-2026.

---

## 2. mTLS — what the mesh actually does

Service mesh automates:

1. Each pod gets a SPIFFE-style X.509 identity (`spiffe://cluster.local/ns/ml-serving/sa/infer-server`).
2. Sidecar (or eBPF datapath) terminates outbound TLS and establishes mTLS to the peer.
3. Inbound: validates peer cert against trust domain; enforces AuthorizationPolicy.
4. App code is unchanged — sidecar transparently proxies plain HTTP/gRPC to the app.

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata: { name: default, namespace: ml-serving }
spec:
  mtls: { mode: STRICT }                  # require mTLS for all pods in this ns
```

---

## 3. AuthorizationPolicy

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata: { name: allow-clients, namespace: ml-serving }
spec:
  selector: { matchLabels: { app: infer-server } }
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/ml-clients/sa/client-app"]
      to:
        - operation:
            methods: [POST]
            paths: ["/v1/models/*:predict"]
```

This is **L7 zero-trust**: only client-app SA can POST to /v1/models/*:predict. NetworkPolicy can't do this (L3/L4 only); the mesh can.

---

## 4. Istio sidecar vs ambient

### 4.1 Sidecar mode

Every pod gets an injected Envoy proxy (~50-100 MB RAM, ~50ms latency penalty). The classic; battle-tested.

### 4.2 Ambient mode (Istio 1.19 GA Sep 2023)

- **ztunnel** DaemonSet per node — does L4 mTLS for all pods.
- **Waypoint proxy** per service-account (deployed only when L7 policy is needed) — Envoy-based.
- No sidecar. Pods are unchanged.

Pros: lower overhead, no app pod resource budget for proxy, simpler upgrades.
Cons: newer; some features still being added.

For new Istio installs in 2025-2026: prefer **ambient**.

---

## 5. SPIFFE / SPIRE

[**SPIFFE**](https://spiffe.io/) is the spec for workload identity. **SPIRE** is the reference implementation.

- Issues short-lived X.509 SVIDs (SPIFFE Verifiable Identity Documents).
- Cross-cluster, cross-cloud, cross-on-prem identity federation.
- Used by Istio under the hood for trust domain management.

When to adopt explicitly: multi-cluster (active-active across regions/clouds) where you want unified identity. For single-cluster, the mesh's built-in identity is enough.

---

## 6. Service mesh + IRSA / Workload Identity

These are **complementary**:

- **IRSA / WIF / Entra Workload ID** — pod's identity to **cloud APIs** (S3, GCS, Blob).
- **Service mesh** — pod's identity to **other pods** (mTLS, AuthorizationPolicy).

A KServe inference pod has both: IRSA for reading S3 model artifacts, mesh identity for serving mTLS to API gateway.

---

## 7. cert-manager — the cert lifecycle layer

The mesh handles east-west mTLS certs. For ingress + app-level TLS, **cert-manager** issues from:

- Let's Encrypt (ACME) for public-facing.
- AWS PCA, GCP Private CA, Azure Key Vault — for internal.
- Vault PKI — for fully self-hosted.

Every Ingress / Gateway / VirtualService refers to a cert by Secret reference; cert-manager renews automatically.

---

## 8. Ambient + Cilium combo

A current 2025-2026 stack: **Cilium CNI + Cilium Service Mesh**. Single project, single dataplane, no sidecar. For new clusters this is increasingly the default.

---

## 9. Capital One signal

Service mesh isn't named in the C1 job posting, but for any K8s+KServe deployment in regulated finance, **mesh is implied**. mTLS + AuthorizationPolicy is the modern answer to "how do you secure pod-to-pod?" — the alternative (app-level TLS everywhere) is operational pain.

Likely C1 stack: **Istio ambient** (for the cleanest serverless-style + L7) OR **Cilium SM** (if Cilium is the CNI).

---

## Sanity check

1. mTLS — what does the mesh actually do that NetworkPolicy can't?
2. Istio sidecar vs ambient — name two reasons ambient is the 2025-2026 default.
3. AuthorizationPolicy at L7 — what verbs/paths can you constrain?
4. SPIFFE/SPIRE — when do you adopt it explicitly vs let the mesh use it implicitly?
5. IRSA and mesh identity — how do they complement each other?
6. cert-manager — what does it solve that the mesh's mTLS doesn't?

---

## Sources

- [Istio docs](https://istio.io/latest/docs/)
- [Istio ambient mesh](https://istio.io/latest/docs/ambient/)
- [Linkerd docs](https://linkerd.io/2/overview/)
- [Cilium Service Mesh](https://docs.cilium.io/en/stable/network/servicemesh/)
- [SPIFFE / SPIRE](https://spiffe.io/)
- [cert-manager](https://cert-manager.io/)

→ Next: [33 — Certification roadmap — KCNA, KCSA, CKAD, CKA, CKS](33_cert_roadmap.md)


\newpage

# 33 — Certification roadmap: KCNA, KCSA, CKAD, CKA, CKS — plus AWS/GCP/Azure K8s certs

> *"For a Sr Lead AI/ML interview at Capital One: CKA + CKS is the credibility multiplier. KCNA is noise."*

## Why this module exists

The user has explicitly asked to add K8s certs to the resume. This module gives a buy/skip verdict per cert tailored to "Sr AI/ML Engineer targeting Sr Lead AI/ML at Capital One" — a regulated-finance, AWS-only, EKS+KServe shop.

---

## 1. The CNCF / Linux Foundation cert ladder

| Cert | Level | Cost | Format | Time | Validity |
|---|---|---:|---|---|---|
| **KCNA** (Kubernetes & Cloud Native Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **KCSA** (Kubernetes Security Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **CKAD** (Certified Kubernetes App Developer) | Associate | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **CKA** (Certified Kubernetes Administrator) | Associate | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **CKS** (Certified Kubernetes Security Specialist) | Specialty (requires active CKA) | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **PCA** (Prometheus Certified Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **ICA** (Istio Certified Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |

[Source: training.linuxfoundation.org] — all hands-on exams allow `kubectl` autocomplete and access to kubernetes.io docs in a sandboxed browser.

### 1.1 Bundle discounts

- CKA + CKAD + CKS bundle commonly available at $1,135 (vs $1,335 separate).
- KubeCon weeks: extra 30-40% off.
- Linux Foundation Black Friday: ~50% off all certs.

**Buy during a discount window.** No certs are urgent enough to pay full price.

---

## 2. Verdict per cert for "Sr AI/ML Engineer → Sr Lead AI/ML at Capital One"

| Cert | Verdict | Why |
|---|---|---|
| **KCNA** | **Skip** | Too elementary for a Sr engineer; no ROI on resume |
| **KCSA** | **Skip-or-bundle** | Useful for someone explicitly targeting security roles; otherwise covered by CKS |
| **CKAD** | **Buy** | Validates "you can build K8s-native apps"; required muscle memory; ~2 weeks of prep |
| **CKA** | **Buy** | The credibility-pillar K8s cert; required for CKS; ~4 weeks of prep |
| **CKS** | **Buy** | Security-spec; the Capital One-aligned cert; ~6 weeks of prep after CKA |
| **PCA** | **Maybe** | Useful if you'll own production observability; otherwise low-priority |
| **ICA** | **Skip-or-later** | Service mesh is niche; only buy if you become the mesh owner |
| **AWS DOP-C02** (DevOps Engineer Pro) | **Maybe** | Covers EKS extensively; complements CKA on AWS. Buy after CKS. |
| **AWS Specialty: Adv. Networking ANS-C01** | **Skip for this role** | Network depth more than the AI role demands |

---

## 3. Recommended sequence + 18-month plan (at 3 hr/week)

| Month | Cert | Hours | Notes |
|---|---|---|---|
| 1-2 | **CKAD** | ~30 | Get the muscle memory for `kubectl`; YAML reflexes |
| 3-5 | **CKA** | ~50 | Operator-level depth; etcd backup; cluster troubleshooting |
| 6-9 | **CKS** | ~60 | Security focus; CIS K8s benchmark; Falco; admission; supply chain |
| 10-12 | Break / production work / Topic 06 study | | |
| 13-15 | **AWS DOP-C02** | ~50 | EKS + CI/CD on AWS; complements CKS |
| 16-18 | **AWS MLA-C01** (covered Topic 04) or **AWS AIP-C01** | ~50 | Top off the AI specialization |

Cap at 3 certs per year. Sustainability over speed.

---

## 4. CKA / CKAD / CKS exam mechanics

- **Hands-on only.** No MCQ. You SSH into K8s clusters and `kubectl` your way through tasks.
- **Allowed tools in exam environment**: terminal, `kubectl` (with autocomplete), `kubernetes.io/docs` in a sandboxed browser, `kubectl` cheat sheet bookmark.
- **Time pressure is real.** ~120 minutes for 15-20 questions; budget ~6-8 min each.
- **Cluster context switching**: every task gives you `kubectl config use-context <name>` — execute it immediately. Wrong cluster = 0 points.
- **Saved snippets**: practice alias setups (`alias k=kubectl; export do='--dry-run=client -o yaml'`).

---

## 5. CKAD curriculum highlights

- Define + apply pods, deployments, services.
- Multi-container pods (sidecar, init).
- ConfigMaps + Secrets injection.
- Probes (liveness, readiness, startup).
- Jobs + CronJobs.
- Resource limits + QoS.
- Updating workloads (rolling update + rollback).
- Helm charts.
- NetworkPolicy basics.

Approx 30 hours of focused practice. Killer.sh has the official practice exam.

---

## 6. CKA curriculum highlights (2025+)

- Cluster architecture, installation, configuration (25%).
- Workloads + scheduling (15%).
- Services + networking (20%).
- Storage (10%).
- Troubleshooting (30%) — the big one; cluster + node + pod + log debugging.

Approx 50 hours.

---

## 7. CKS curriculum highlights

- Cluster setup (10%): network policies, CIS benchmarks, ingress TLS, NSG hardening.
- Cluster hardening (15%): RBAC, ServiceAccounts, K8s upgrades.
- System hardening (15%): kernel, IAM, network restrictions.
- Microservice vulnerabilities (20%): managing K8s Secrets, container runtime sandboxes (gVisor, Kata), mTLS.
- Supply chain security (20%): image scanning, signing, admission control.
- Monitoring, logging, runtime security (20%): Falco, syscall tracing, audit logs.

Approx 60 hours. Heavy on hands-on **Falco** rule writing and **AppArmor/seccomp** profile authoring — practice on a local cluster.

---

## 8. Study resources

| Resource | Cost | Notes |
|---|---|---|
| **Killer.sh practice exam** | $25 (often included with cert purchase) | The closest simulator |
| **KodeKloud CKA/CKS courses** | $30/mo | Best video course; hands-on labs |
| **Linux Academy / A Cloud Guru** | $40/mo | Decent but less hands-on |
| **Pluralsight** | $30/mo | More breadth, less depth |
| **Free official curriculum** | Free | training.linuxfoundation.org |
| **Sander van Vugt CKA/CKS books** | $50 | Solid textbooks |
| **CNCF KCNA/KCSA free path** | Free | If you want to do those |
| **YouTube: Tech World with Nana, KubeCraft, TechWorld with Vatsal Kohli** | Free | Concept reinforcement |

For the user's context: **KodeKloud + Killer.sh** is the standard combo.

---

## 9. The role-relevance argument

For a Capital One interview, the order of impressiveness on a resume:

1. **CKS** — "I know K8s security at the depth of regulated finance."
2. **CKA** — "I know cluster operations."
3. **AWS DOP-C02** — "I know EKS + CI/CD on AWS."
4. **AWS MLA-C01** — "I know the ML platform on AWS."
5. **CKAD** — "I can build K8s apps."
6. KCNA / KCSA — barely registers.

For interviewing, certs are the foot in the door. **The "Lead Machine Learning Engineer (MLOps, KServe)" job posting language signals that hands-on K8s + KServe wins over alphabet soup.** Pair cert prep with real KServe deployment in a personal lab.

---

## 10. The personal-lab build that pairs with certs

Spin up a Kind / Minikube cluster on your laptop, or a small EKS cluster in your own AWS account ($50-100/month budget). Practice:

- Install Cilium, Karpenter, GPU Operator (if GPU laptop), KServe, Prometheus, Falco, Kyverno, ESO.
- Deploy a sentiment model via KServe with IRSA.
- Sign images with Cosign keyless via GitHub Actions OIDC; verify with Kyverno.
- Configure Falco rules; trigger one yourself and watch the alert flow.
- Velero backup; restore drill.

This personal lab is the **single most useful** interview-prep asset. Talks about it score more points than any cert.

---

## Sanity check

1. Which 3 certs are the "buy" list for the Capital One target?
2. CKS requires what prerequisite?
3. Why is KCNA likely noise for a Sr engineer's resume?
4. What's allowed in the CKA/CKS exam environment that catches new test-takers off guard?
5. The 18-month plan caps at how many certs per year, and why?

---

## Sources

- [Linux Foundation Training](https://training.linuxfoundation.org/)
- [CNCF Certifications](https://www.cncf.io/training/certification/)
- [Killer.sh](https://killer.sh/)
- [KodeKloud](https://kodekloud.com/)
- [CKA Curriculum PDF](https://github.com/cncf/curriculum)
- [AWS DOP-C02](https://aws.amazon.com/certification/certified-devops-engineer-professional/)

→ End of Topic 05.


\newpage

# Appendix A — FACTS.md

_Atomic, citable facts. Single source of truth for CVE numbers, CSI driver GA dates, K8s version cutoffs, certification metadata, cloud-specific identity-binding mechanisms._

# Topic 05 — FACTS.md (Docker & Kubernetes)

> Atomic, citable facts. Single source of truth for CVE numbers, CSI driver GA dates, K8s version cutoffs, certification metadata, cloud-specific identity-binding mechanisms.
>
> **Format:** one fact per line, citation in square brackets, last-verified date. If older than 90 days at quote-time, re-verify.
>
> **Last updated:** 2026-05-21 (seed)

---

## Docker / OCI

- **Docker Engine** is now a CLI + REST API on top of **containerd**; `containerd` calls **runc** (the OCI runtime). Other runtimes: `crun` (C), `youki` (Rust), `runsc` (gVisor user-space kernel), `kata-runtime` (VM-isolated). [Source: docs.docker.com architecture; containerd.io] [Verified 2026-05-21]
- **OCI Image Spec v1.1** (Feb 2024) added artifacts and reference types (Sigstore attestations land here). [Source: github.com/opencontainers/image-spec] [Verified 2026-05-21]
- **BuildKit** is the default builder since Docker 23.0 (Feb 2023). `--mount=type=secret` requires BuildKit. [Source: docs.docker.com/build/buildkit] [Verified 2026-05-21]
- **Docker Desktop license**: free for personal, small businesses (<250 employees AND <$10M revenue); paid otherwise. [Source: docker.com/pricing] [Verified 2026-05-21]
- **The `docker` group is root-equivalent** — adding a user to it gives them a path to root via mounting `/`. CIS Docker Benchmark calls this out. [Source: CIS Docker Benchmark v1.6.0] [Verified 2026-05-21]

## Docker security CVEs (must-know)

- **CVE-2019-5736** — runc container escape via overwriting the runc binary; CVSS 8.6. Patched Feb 2019. [Source: nvd.nist.gov] [Verified 2026-05-21]
- **CVE-2022-0185** — Linux kernel filesystem context heap-overflow exploitable from inside containers with CAP_SYS_ADMIN. [Source: nvd.nist.gov] [Verified 2026-05-21]
- **CVE-2024-21626 "Leaky Vessels"** — runc working-dir leak allowing container escape; CVSS 8.6. Patched Jan 2024. [Source: snyk.io/blog/leaky-vessels; runc release notes] [Verified 2026-05-21]
- **CVE-2024-23651, CVE-2024-23652, CVE-2024-23653** — BuildKit Leaky Vessels companions. Patched Jan 2024. [Source: github.com/moby/buildkit advisories] [Verified 2026-05-21]
- **Tesla cryptojacking 2018** — unauthenticated Kubernetes dashboard exposed; cryptominers deployed; root cause: dashboard service exposed without auth. [Source: RedLock CSI report Feb 2018] [Verified 2026-05-21]

## Kubernetes versions & support

- **Kubernetes 1.32** released Dec 2024 ("Penelope"). **1.33** released early 2025. **1.34** GA mid-2025 — confirm at quote time. [Source: kubernetes.io/releases] [Verified 2026-05-21]
- **Support window**: K8s maintains the last 3 minor versions with patches; ~14 months from release. [Source: kubernetes.io/releases/version-skew-policy] [Verified 2026-05-21]
- **etcd KMS v2** GA in K8s 1.29 (Dec 2023); v1 deprecated. [Source: kubernetes.io/docs/tasks/administer-cluster/kms-provider] [Verified 2026-05-21]
- **PodSecurityPolicy (PSP)** removed in K8s 1.25 (Aug 2022). Replaced by **Pod Security Admission (PSA)** namespace labels. [Source: kubernetes.io/blog Aug 2022] [Verified 2026-05-21]
- **Gateway API** v1.0 GA Oct 2023 (ingress successor); v1.1 added GRPCRoute GA, v1.2+ added more. [Source: gateway-api.sigs.k8s.io] [Verified 2026-05-21]
- **dockershim** removed in K8s 1.24 (May 2022); containerd/CRI-O are the runtimes. [Source: kubernetes.io/blog Dec 2020 + 1.24 release] [Verified 2026-05-21]
- **K8s ReadWriteOncePod** access mode GA in 1.29. [Source: kubernetes.io] [Verified 2026-05-21]

## AWS — EKS data exposure primitives

- **IRSA** (IAM Roles for Service Accounts) launched Sep 2019. OIDC-provider based; pod gets `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` env vars; SDK calls AssumeRoleWithWebIdentity. [Source: aws.amazon.com/blogs Sep 2019; docs.aws.amazon.com/eks] [Verified 2026-05-21]
- **EKS Pod Identity** GA Nov 2023 (re:Invent). Alternative to IRSA; uses `eks-pod-identity-agent` daemonset, no OIDC chain. Trust policy on the role allows `pods.eks.amazonaws.com`. [Source: aws.amazon.com/blogs Nov 2023] [Verified 2026-05-21]
- **Mountpoint for Amazon S3 CSI driver** GA Apr 2024. Provides PV-backed S3 with limited POSIX (no random writes, no rename in same prefix). [Source: aws.amazon.com/blogs Apr 2024] [Verified 2026-05-21]
- **EFS CSI driver** supports dynamic provisioning via Access Points; encryption-in-transit via TLS (port 2049 with stunnel). [Source: github.com/kubernetes-sigs/aws-efs-csi-driver] [Verified 2026-05-21]
- **AWS Secrets Manager + SSM Parameter Store via the Secrets Store CSI Driver (ASCP)**. [Source: github.com/aws/secrets-store-csi-driver-provider-aws] [Verified 2026-05-21]
- **EKS Auto Mode** GA Dec 2024 (re:Invent 2024). Bundles Karpenter + ALB controller + EBS CSI + EFS CSI + storage class defaults. [Source: aws.amazon.com/eks/auto-mode] [Verified 2026-05-21]
- **VPC CNI**: each pod gets a primary VPC ENI IP; security group per pod is supported on Nitro instances. [Source: github.com/aws/amazon-vpc-cni-k8s] [Verified 2026-05-21]
- **IMDSv2 enforcement** for pods via `httpPutResponseHopLimit=1` at the instance level OR via `eks.amazonaws.com/role-arn` IMDS hop-limit settings. Capital One 2019 root cause was IMDSv1 SSRF. [Source: aws.amazon.com/blogs IMDSv2; OCC consent order] [Verified 2026-05-21]

## GCP — GKE data exposure primitives

- **Workload Identity Federation for GKE** launched 2019; now the default identity binding. KSA annotated with `iam.gke.io/gcp-service-account` maps to a GSA. JSON service-account keys are explicitly discouraged and can be org-policy-blocked. [Source: cloud.google.com/kubernetes-engine/docs/how-to/workload-identity] [Verified 2026-05-21]
- **GCS Fuse CSI driver** GA late 2023; sidecar architecture, runs as a sidecar in each pod. ML training data use case. [Source: cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver] [Verified 2026-05-21]
- **Secret Manager CSI provider** (secrets-store-csi-driver-provider-gcp). [Source: github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp] [Verified 2026-05-21]
- **Binary Authorization** for GKE — image attestations checked at admission; breakglass via annotation. [Source: cloud.google.com/binary-authorization] [Verified 2026-05-21]
- **GKE Autopilot** GA Feb 2021; node management entirely managed; restricts privileged pods, hostPath, hostNetwork. [Source: cloud.google.com/blog Feb 2021] [Verified 2026-05-21]
- **Confidential GKE Nodes** GA Sep 2020 on AMD SEV; Intel TDX preview/GA expanding. [Source: cloud.google.com/confidential-computing] [Verified 2026-05-21]

## Azure — AKS data exposure primitives

- **Microsoft Entra Workload ID for AKS** GA July 2023; uses federated identity credentials on user-assigned managed identities; OIDC issuer URL per cluster. Replaces deprecated AAD Pod Identity v1. [Source: learn.microsoft.com/azure/aks/workload-identity-overview] [Verified 2026-05-21]
- **Azure Files CSI** supports SMB and NFSv4.1 (Premium tier required for NFS). [Source: learn.microsoft.com/azure/aks/azure-files-csi] [Verified 2026-05-21]
- **Azure Blob CSI** supports blobfuse2 mount mode and NFS 3.0 mount mode. [Source: learn.microsoft.com/azure/aks/azure-blob-csi] [Verified 2026-05-21]
- **Azure Key Vault Provider for Secrets Store CSI Driver**: `SecretProviderClass` CRD; optional `syncSecret` to native K8s Secret. [Source: learn.microsoft.com/azure/aks/csi-secrets-store-driver] [Verified 2026-05-21]
- **Azure CNI Powered by Cilium** (Azure's eBPF dataplane) GA 2023+; Azure CNI Overlay GA. Kubenet deprecation in progress. [Source: learn.microsoft.com/azure/aks/azure-cni-powered-by-cilium] [Verified 2026-05-21]
- **AKS private cluster** — API server has no public IP; access via Private Link, peered VNet, or VPN/ExpressRoute. [Source: learn.microsoft.com/azure/aks/private-clusters] [Verified 2026-05-21]
- **Confidential containers on AKS** preview/GA on AMD SEV-SNP via Kata. [Source: learn.microsoft.com/azure/aks/confidential-containers-overview] [Verified 2026-05-21]

## On-prem K8s storage / projects

- **Rook-Ceph**: CNCF Graduated (Oct 2020). Manages Ceph clusters as K8s resources. [Source: cncf.io project status] [Verified 2026-05-21]
- **Longhorn**: CNCF Incubating; from Rancher Labs. Block-storage CSI for K8s. [Source: longhorn.io] [Verified 2026-05-21]
- **OpenEBS** (Mayastor / cStor / Jiva engines): CNCF Sandbox. [Source: openebs.io] [Verified 2026-05-21]
- **Portworx** (commercial; acquired by Pure Storage 2020). [Source: portworx.com] [Verified 2026-05-21]
- **Velero** for backup/DR: CNCF Sandbox. Originally Heptio. [Source: velero.io] [Verified 2026-05-21]
- **MetalLB** for bare-metal LoadBalancer service type. CNCF Sandbox. [Source: metallb.io] [Verified 2026-05-21]
- **Cilium L2 announcements** as MetalLB alternative — GA in Cilium 1.14 (Aug 2023). [Source: cilium.io] [Verified 2026-05-21]

## AI/ML on K8s

- **KServe** v0.13 added LLM-serving primitives; v0.14 added vLLM-friendly templates. (Confirm latest at quote time.) [Source: kserve.io releases] [Verified 2026-05-21]
- **Karpenter** v1.0 GA Aug 2024 (Kubernetes-native node autoscaler, AWS-originated, now multi-cloud). [Source: karpenter.sh] [Verified 2026-05-21]
- **NVIDIA GPU Operator** version supports MIG (A100/H100/H200), time-slicing, GPU Feature Discovery, DCGM exporter. [Source: docs.nvidia.com/datacenter/cloud-native/gpu-operator] [Verified 2026-05-21]
- **Kubeflow 1.9** released 2024; Kubeflow Training Operator handles PyTorchJob/TFJob/MPIJob. [Source: kubeflow.org] [Verified 2026-05-21]
- **Cilium** v1.14+ ships native service mesh (sidecarless); v1.16 hardened L7 features. [Source: cilium.io blog] [Verified 2026-05-21]

## Certifications — Kubernetes / cloud-native (CNCF / Linux Foundation)

| Cert | Code | Level | Cost USD | Duration | Format | Validity |
|---|---|---|---:|---|---|---|
| Kubernetes & Cloud Native Associate | KCNA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Kubernetes & Cloud Native Security Associate | KCSA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Prometheus Certified Associate | PCA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Istio Certified Associate | ICA | Foundational | $250 | 90 min / 60 MCQ | Online proctored | 2 years |
| Certified Kubernetes Application Developer | CKAD | Associate | $445 | 120 min / hands-on | Online proctored | 2 years |
| Certified Kubernetes Administrator | CKA | Associate | $445 | 120 min / hands-on | Online proctored | 2 years |
| Certified Kubernetes Security Specialist | CKS | Specialty (requires CKA) | $445 | 120 min / hands-on | Online proctored | 2 years |

[Source: training.linuxfoundation.org] [Verified 2026-05-21]

- **Bundle discount**: CKA + CKAD + CKS bundle commonly discounted ~30% during sales (Black Friday, KubeCon). [Source: LF training promos] [Verified 2026-05-21]
- **CKA/CKAD/CKS allow `kubectl` autocomplete + the official kubernetes.io docs during exam** in a sandboxed browser. [Source: training.linuxfoundation.org candidate handbook] [Verified 2026-05-21]
- **CKA curriculum (2025+)**: storage 10%, troubleshooting 30%, workloads & scheduling 15%, cluster architecture 25%, services & networking 20%. [Source: LF CKA curriculum PDF] [Verified 2026-05-21]
- **CKS prerequisites**: must hold an active CKA. [Source: LF CKS page] [Verified 2026-05-21]

## Capital One Kubernetes signal

- Capital One self-hosts model serving on **EKS with KServe** — see job posting R239877: "Lead Machine Learning Engineer (MLOps, KServe — building Kubernetes Clusters, PyTorch, TensorFlow on AWS)". [Source: capitalone.wd12.myworkdayjobs.com] [Verified 2026-05-21 — already in Topic 04 FACTS.md]
- **Cloud Custodian** (C1 OSS, CNCF Incubating) operates at the AWS-API layer, not the K8s layer. K8s policy at Capital One is typically OPA Gatekeeper or Kyverno. [Source: cloud-custodian docs; C1 tech blog] [Verified 2026-05-21]

