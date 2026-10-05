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
