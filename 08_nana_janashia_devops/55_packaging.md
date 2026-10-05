# 55 — Packaging Applications

## 1. What "packaging" means

Producing a deployable artifact:
- **JS/TS app** → bundled JS files + assets (dist/ directory)
- **Python** → wheel (.whl) or container
- **Java** → jar or war
- **Go** → static binary
- **Container** → Docker image (multi-stage)

## 2. JS/TS packaging — Vite

For SPAs:
```bash
npm run build
# produces dist/ — minified, hashed-filename bundles
```

`vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'utils': ['lodash-es', 'date-fns'],
        },
      },
    },
  },
})
```

Output is static files; deploy to any CDN (CloudFront, Cloudflare, Vercel, Netlify).

## 3. NodeJS app packaging

For backend Node apps:
- **Direct deploy** — copy source + `node_modules` to server
- **Docker image** — `npm ci --omit=dev` in builder, copy to slim runtime stage
- **Bundle to single file** — esbuild / ncc; reduces files but rarely necessary
- **Native binary** — `pkg` (deprecated) / `nexe` / `bun build --compile`

The 2026 pattern: container image.

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## 4. Python packaging

For a library: build a wheel.
For an app: build a container image.

```toml
# pyproject.toml
[project]
name = "my-tool"
version = "1.2.3"
dependencies = ["click>=8.0", "requests>=2.30"]

[project.scripts]
my-tool = "my_tool.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
uv build         # produces dist/my_tool-1.2.3-py3-none-any.whl
uv publish       # to PyPI / private registry
```

For app: container with `uv` in the build stage.

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
USER 10001
CMD ["python", "-m", "my_app"]
```

## 5. Container image best practices (recap from Module 8)

1. Multi-stage build
2. Pin versions (digest in production)
3. Non-root user
4. `.dockerignore`
5. Cache deps before app code (layer order)
6. Minimal base (distroless / alpine / chainguard)
7. Health check
8. Single concern per container
9. Sign with Cosign
10. Scan with Trivy

## 6. Distroless / Chainguard for security

```dockerfile
FROM python:3.13-slim AS builder
# ... build ...

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /app /app
COPY --from=builder /root/.local /home/nonroot/.local
WORKDIR /app
ENV PATH=/home/nonroot/.local/bin:$PATH
CMD ["main.py"]
```

Or Chainguard images:
```dockerfile
FROM cgr.dev/chainguard/python:latest-dev AS builder
# ... build ...
FROM cgr.dev/chainguard/python:latest
COPY --from=builder /app /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["main.py"]
```

Chainguard images: daily-rebuilt, signed, SBOM-included, mostly CVE-free.

## 7. Running an application from a package

### Node
```bash
node dist/index.js
# Or as a service:
pm2 start dist/index.js --name my-app
# Or as systemd unit:
systemctl start my-app
```

### Python
```bash
python -m my_app
# Or installed CLI:
my-tool --help
```

### Container
```bash
docker run -d --name my-app --restart=unless-stopped \
  -p 80:3000 \
  -e DATABASE_URL=... \
  my-app:1.2.3
```

### Kubernetes
```bash
kubectl set image deployment/my-app app=my-app:1.2.3
```

## 8. Semantic Versioning (semver)

`MAJOR.MINOR.PATCH`:
- **MAJOR** — breaking change
- **MINOR** — new feature, backward-compatible
- **PATCH** — bug fix, backward-compatible

Pre-release: `1.2.3-rc.1`, `2.0.0-alpha.5`
Build metadata: `1.2.3+sha.deadbeef`

In CI:
```bash
VERSION=$(git describe --tags --abbrev=7 --always)
# e.g., v1.2.3 or v1.2.3-5-g0a1b2c3 if commits since tag
```

## 9. Conventional Commits + automated releases

Conventional Commits (https://conventionalcommits.org):
```
feat: add user dashboard
fix: handle null pointer in auth
docs: update README
chore: bump dependencies
feat!: change API contract (breaking)
```

Tools that read these:
- **release-please** (Google) — auto-creates release PRs with bumped versions + changelogs
- **semantic-release** — fully automated; tags + publishes on every merge
- **changesets** (Atlassian) — monorepo-friendly

The pattern: commit → CI parses commit message → determines version bump → creates release.

## 10. SBOM as part of packaging

Generate SBOM during build:
```bash
syft dir:. -o cyclonedx-json > sbom.json
trivy sbom sbom.json   # scan
```

Attach SBOM to release / image:
```bash
cosign attest --predicate sbom.json --type cyclonedx myimage:1.2.3
```

## 11. Quick self-check

1. What does `npm run build` produce in a Vite project?
2. Why use multi-stage Dockerfile?
3. What's the difference between Distroless and Chainguard images?
4. What's a `feat!:` commit in Conventional Commits?
5. Why generate an SBOM as part of the package step?

(Answers: minified hashed-filename bundles in dist/; smaller runtime image, no build tools in deployed image, faster pulls; Distroless is Google project (debian-based, no shell/pkg-mgr), Chainguard is commercial daily-rebuilt distroless-style with SBOM/signing; breaking change — bumps major version under release-please/semantic-release; supply-chain transparency, required for SLSA, evidence for security audits.)
