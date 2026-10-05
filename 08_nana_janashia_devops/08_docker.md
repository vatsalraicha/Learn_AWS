# 08 — Containers with Docker

> Cross-link: [Topic 05 Modules 1–11](../05_docker_kubernetes/01_linux_primitives.md) cover Docker exhaustively: Linux primitives, dockerd→containerd→runc→OCI, Dockerfile patterns, image security (Trivy/Cosign/SLSA/SBOM), registries, networking, storage, secrets, Compose, hardening checklist, CIS, CVEs.
>
> This module is a **Nana-Janashia-flavored DevOps refresher**: the workflow-driven slice — what you actually do in a CI pipeline.

## 1. The 2026 container reality

- **Docker Inc.** still makes Docker Desktop; Docker CE (the CLI/daemon) is in the OSS / Mirantis hand.
- **Docker Hub** still hosts most public images; pull-rate limits (100/6hr unauth, 200/6hr free auth) drive teams to mirror via Nexus/Artifactory.
- **containerd + nerdctl** is the K8s default; the `docker` CLI on a K8s node may not exist.
- **Podman** is a serious daemonless alternative (Red Hat-led); rootless-by-default.
- **BuildKit / buildah** for builds; Docker Desktop uses BuildKit by default.
- **OCI** (Open Container Initiative) — the standard. Docker images are OCI images.

## 2. Container vs Image vs VM

- **Image** = immutable, layered, content-addressed filesystem + metadata. The blueprint.
- **Container** = running instance of an image. Process(es) isolated via Linux namespaces + cgroups.
- **VM** = full guest OS via hypervisor. Heavier, slower, more isolated.

Container vs VM, quick:
| | VM | Container |
|---|---|---|
| Boot | 30s–min | ms |
| Overhead | 5-15% | <1% |
| Isolation | Hardware | Process |
| Density per host | 10s | 100s–1000s |

## 3. Main Docker commands (the ones you actually use)

```bash
# Images
docker pull nginx:1.27-alpine
docker images
docker rmi <image>
docker image prune -a               # delete unused

# Containers
docker run -d --name web -p 8080:80 nginx:1.27-alpine
docker ps
docker ps -a                        # include stopped
docker stop web
docker rm web
docker logs -f web

# Exec into a running container
docker exec -it web sh

# Inspect
docker inspect web | jq '.[0].NetworkSettings'

# Cleanup
docker system prune -a --volumes    # nukes unused images, containers, networks, volumes
```

## 4. Dockerfile — the production patterns

```dockerfile
# Multi-stage; pinned versions; non-root user
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.13-slim
RUN useradd -m -u 10001 app
WORKDIR /app
COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app . .
USER app
ENV PATH=/home/app/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Patterns that matter:
- **Multi-stage** — build tools stay in builder; runtime image stays small.
- **Pin versions** — `python:3.13-slim` not `python:slim`; pin to digest in CI for true immutability.
- **`--no-cache-dir`** for pip; cleanup apt cache.
- **Non-root user** — required by Pod Security Standards `restricted`.
- **`COPY` then `RUN pip install`** — only the requirements.txt change re-runs install (layer caching).
- **`.dockerignore`** — exclude `.git/`, `__pycache__/`, `*.pyc`, `.env`, `node_modules/`.
- **`HEALTHCHECK`** — for Compose/Swarm; K8s uses its own probes.
- **Single concern per container** — don't run sshd + cron + app in one container.

## 5. Docker Compose (multi-container local dev)

```yaml
# compose.yaml — note no version: key (Compose Spec, Compose v2)
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://app:app@db:5432/appdb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: appdb
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 2s
      retries: 5

volumes:
  db-data:
```

```bash
docker compose up -d
docker compose logs -f api
docker compose down -v       # -v also removes volumes
```

In 2026 use `docker compose` (v2, Go-written, plugin) not the legacy `docker-compose` (v1, Python).

## 6. Private Docker registries

Push to private registry (Nexus, ECR, GHCR, ACR, GAR, Harbor):
```bash
docker login nexus.example.com:5000 -u admin
docker tag myapp:1.2.3 nexus.example.com:5000/myapp:1.2.3
docker push nexus.example.com:5000/myapp:1.2.3
```

In Jenkins/GitLab/Actions: use a credential store, not `docker login` with literal passwords. AWS ECR specifically uses short-lived tokens via `aws ecr get-login-password`.

## 7. Docker Volumes (persisting state)

Three options:
- **Named volumes** — Docker-managed (`docker volume create`); preferred for portability
- **Bind mounts** — host path mounted into container; useful for local dev
- **tmpfs** — RAM-backed, ephemeral

```bash
docker run -d --name db -v db-data:/var/lib/postgresql/data postgres:17
```

In K8s, this becomes PV/PVC; see [Topic 05 Module 19](../05_docker_kubernetes/19_k8s_storage.md).

## 8. Deploying Docker on a server (Nana's bootcamp path)

The bootcamp progression: build locally → push to Nexus → SSH into droplet → docker pull → docker run. This is the **manual baseline** before Jenkins automates it.

```bash
# On the server
ssh deploy@server
docker login nexus.example.com:5000
docker pull nexus.example.com:5000/myapp:1.2.3
docker stop myapp || true
docker rm myapp || true
docker run -d --name myapp --restart=unless-stopped \
  -p 80:8000 nexus.example.com:5000/myapp:1.2.3
```

Better: use `docker compose` + a `compose.yaml` per environment.
Best: containerize + ship to K8s + GitOps deploy (Module 33 — ArgoCD).

## 9. Docker Best Practices (the 12-point checklist)

1. **Multi-stage builds** to minimize image size + attack surface
2. **Pin base image versions** (digest-pin for production)
3. **Non-root user** (`USER app`, not `USER root`)
4. **`.dockerignore`** to exclude secrets + bloat
5. **Combine RUN steps** to minimize layers; clean up in same step
6. **`COPY` deps before app code** for layer caching
7. **Health checks** in Dockerfile + at K8s probe level
8. **No secrets baked in** — use BuildKit secret mount or runtime env
9. **Sign images** (Cosign) and verify at deploy (admission control)
10. **Scan images** (Trivy, Snyk, ECR enhanced) — fail build on Critical CVEs
11. **SBOM generation** (`docker buildx build --sbom=true`)
12. **Distroless** or `chainguard-images` for ultra-minimal runtime

## 10. Quick self-check

1. What's the difference between an image and a container?
2. Why use a multi-stage Dockerfile?
3. What's the difference between a Docker volume and a bind mount?
4. Why is `docker-compose` (v1) deprecated in favor of `docker compose` (v2)?
5. Name three things you should never bake into a Docker image.

(Answers: image is immutable blueprint, container is running instance; smaller final image, no build tools in runtime, faster pull; volume Docker-managed and portable, bind mount tied to host path; v2 is Go-rewrite + plugin to docker CLI, v1 is unmaintained Python; secrets, source-control history, build tools (unless multi-stage), cleartext credentials.)
