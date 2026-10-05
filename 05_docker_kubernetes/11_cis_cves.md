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
