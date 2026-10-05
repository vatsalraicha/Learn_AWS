# 05 — Build Tools & Package Managers

## Why this module exists

Every CI/CD pipeline starts with "build the artifact." The artifact is what gets deployed. If you can't reproduce the artifact byte-for-byte from a Git SHA, you have a supply-chain liability. This module covers the major language-stack build tools and the principles that survive across them.

## 1. The build-tool landscape by language stack

| Language | Build tool(s) | Lockfile | Artifact |
|---|---|---|---|
| **Java/Kotlin** | Maven (mvn), Gradle | pom.xml / build.gradle | .jar, .war |
| **JavaScript/TypeScript** | npm, pnpm, yarn, Bun | package-lock.json, pnpm-lock.yaml | dist/ bundle |
| **Python** | pip + setuptools, Poetry, **uv** (new dominant), Hatch | requirements.txt, poetry.lock, uv.lock | .whl, .tar.gz |
| **Go** | go (built-in) | go.sum | binary |
| **Rust** | cargo | Cargo.lock | binary |
| **C/C++** | make, cmake, bazel | — | binary |
| **.NET** | dotnet, msbuild | packages.lock.json | .dll |
| **Ruby** | bundler, rake | Gemfile.lock | gem |

In 2026, **uv** (from Astral, Rust-written, ~10-100x faster than pip) has displaced Poetry/pip+pip-tools as the modern Python default. See [Topic 07 Module 18](../07_git_github_devops/18_python_ml_repo_structure.md).

## 2. The four phases every build goes through

1. **Fetch dependencies** — from package registry (npm, PyPI, Maven Central) or private (Nexus, Artifactory, CodeArtifact)
2. **Compile / transpile** — source → bytecode/JS-bundle/binary
3. **Test** — unit + integration; build fails on test fail
4. **Package** — produce the artifact (jar, wheel, container image, zip)

CI/CD pipelines may add: lint, format, type-check, SAST, SCA, image scan, sign, push to registry.

## 3. Reproducible builds — the unattainable but essential ideal

A build is **reproducible** if rebuilding from the same source produces the same artifact bytes. Why it matters:
- Supply-chain attack detection — if your artifact's hash changes without source change, something is wrong
- SLSA compliance levels
- Debugging — "the build last week worked but this week's doesn't" → narrow to env, not source

Practical reproducibility hurdles:
- **Timestamps** in artifacts (use SOURCE_DATE_EPOCH)
- **Random IDs** in dist tar
- **Float-typing locale-dependence** (LC_ALL=C)
- **Mutable dependencies** (lockfiles partially help)
- **Build-tool versions** (pin in CI: `actions/setup-python@v5 with: python-version-file: .python-version`)

Tooling: Nix (most reproducible), Bazel (Google's), buildah/podman for containers, Renovate to manage lockfile drift.

## 4. Lockfiles — the supply chain's first line

```
requirements.txt        → loose, pip-tools or uv generates pinned
poetry.lock             → exact resolution of dep tree
uv.lock                 → uv's exact resolution
package-lock.json       → npm exact resolution
pnpm-lock.yaml          → pnpm
go.sum                  → Go exact (cryptographic hashes!)
Cargo.lock              → Rust
```

Rule: **always commit the lockfile** for applications. **Never commit the lockfile** for libraries (let the consumer resolve). Renovate / Dependabot bump these for you.

## 5. Building JavaScript applications (the modern stack)

Build tools have consolidated around fast Rust/Go-written native bundlers:
- **Vite** — dominant for SPAs in 2026
- **esbuild** — Vite's underlying bundler
- **swc** — Rust-written replacement for Babel
- **Rspack** / **Turbopack** — Rust-written Webpack-compatible

The old guard (Webpack, Babel, Rollup, Gulp, Grunt) is legacy maintenance now.

```bash
# Modern Vite-based React/Vue/Svelte app
npm create vite@latest my-app
cd my-app
npm install
npm run dev    # dev server (HMR)
npm run build  # production bundle (dist/)
```

## 6. Build tools in Docker

The pattern: multi-stage build. Stage 1 builds; stage 2 packages just the artifact + runtime.

```dockerfile
# Stage 1: build
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: runtime (smaller, no build tools)
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

Smaller image, smaller attack surface, faster pull.

## 7. Publishing artifacts

Common destinations:
- **Maven Central / Sonatype OSSRH** — Java
- **npmjs.com** — JS
- **PyPI** — Python
- **Docker Hub / GHCR / ECR / GAR / ACR** — containers
- **Crates.io** — Rust
- **Internal Nexus / Artifactory / CodeArtifact / GitHub Packages** — private artifacts

Versioning: **Semantic Versioning** (semver) — MAJOR.MINOR.PATCH. Pre-release suffixes (`-alpha.1`, `-rc.2`). Build metadata (`+sha.deadbeef`).

In CI: `version = git describe --tags --abbrev=7` produces `v1.2.3-5-g0a1b2c3` automatically.

## 8. Quick self-check

1. What replaced Poetry as the modern Python default in 2025-2026 and why?
2. Why is `npm ci` preferred over `npm install` in CI?
3. What is a multi-stage Docker build and why use it?
4. What does SOURCE_DATE_EPOCH do for reproducible builds?
5. When should you commit a lockfile vs not?

(Answers: uv — much faster, single binary, lockfile-first; ci uses lockfile exactly, fails on mismatch, doesn't write to lockfile; build artifact in one stage, runtime in another → smaller image; fixes timestamps in artifacts to a known value; commit for apps, don't commit for libs.)
