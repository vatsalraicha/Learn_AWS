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
