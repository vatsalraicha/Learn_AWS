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
