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
