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
