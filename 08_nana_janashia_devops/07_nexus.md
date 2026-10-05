# 07 — Nexus — Artifact Repository Manager

> One of the "net-new" modules where Nana adds genuine value vs. the rest of this project. Most modern AWS-native shops have moved off Nexus to CodeArtifact + ECR + GitHub Packages, but Nexus still dominates regulated finance and on-prem.

## Why this module exists

Every CI/CD pipeline produces artifacts (jars, wheels, container images, npm packages, helm charts). Those artifacts need a home that:
- Stores immutable, versioned binaries
- Authenticates pull access (private repos)
- Proxies/caches public registries (so you're not dependent on npmjs.com being up)
- Integrates with build tools (Maven, npm, pip)

Sonatype Nexus Repository is the longest-standing answer. JFrog Artifactory is its closest competitor. Cloud-native shops use AWS CodeArtifact, GitHub Packages, Azure Artifacts, or GitLab Package Registry instead. *(Cap One uses JFrog Artifactory + ECR.)*

## 1. The artifact-repo categories

| Category | Why |
|---|---|
| **Hosted** | You publish to it (e.g., releases of your in-house libs) |
| **Proxy** | Caches a public registry (Maven Central, npmjs, PyPI) |
| **Group** | Virtual repo that aggregates multiple of the above (single URL for clients) |

A typical setup: `releases` (hosted, immutable), `snapshots` (hosted, mutable), `maven-central-proxy` (cache), and `maven-public` (group containing the above). Clients point at `maven-public`.

## 2. The Nexus 3 supported formats

Nexus 3 is format-agnostic: same engine, many formats:
- Maven 2/3 (Java)
- npm
- PyPI
- Docker (private container registry)
- Helm
- NuGet, RubyGems, Conan, Apt, Yum, Bower, Go, Conda, p2, R, raw

This is the *killer feature*: one tool for every artifact type. Same UI, same RBAC, same backup.

## 3. Concepts: Blob Store, Component, Asset

- **Blob Store**: where the actual bytes live. File-system based by default; can also be S3-backed (Pro feature, popular for cloud deploys).
- **Component**: a versioned thing (e.g., `com.example:my-lib:1.2.3`).
- **Asset**: the actual files in that component (e.g., the `.jar`, the `.pom`, the `-sources.jar`, the `-javadoc.jar`).

A component can have many assets. Cleanup policies operate on component age, asset count, etc.

## 4. Cleanup policies (the storage-cost lever)

Without cleanup, Nexus storage grows linearly forever. Define policies:
- "Delete snapshot artifacts older than 30 days that are not the latest"
- "Delete Docker images older than 90 days unless tagged `latest` or `stable`"
- "Delete components with no downloads in 180 days"

Run as scheduled tasks. Audit before deleting (dry-run mode).

## 5. REST API for automation

Nexus exposes a REST API:
```bash
# Upload a Maven artifact
curl -u admin:password -X POST \
  -F "maven2.groupId=com.example" \
  -F "maven2.artifactId=demo" \
  -F "maven2.version=1.2.3" \
  -F "maven2.asset1=@target/demo-1.2.3.jar" \
  -F "maven2.asset1.extension=jar" \
  "https://nexus.example.com/service/rest/v1/components?repository=releases"

# Search
curl "https://nexus.example.com/service/rest/v1/search?repository=releases&name=demo"

# Delete
curl -u admin:password -X DELETE \
  "https://nexus.example.com/service/rest/v1/components/<component-id>"
```

In a Jenkins pipeline, the `nexus-artifact-uploader` plugin wraps this.

## 6. Production deployment patterns

### Single-node (dev/small team)
```bash
docker run -d --name nexus \
  -p 8081:8081 \
  -v /opt/nexus-data:/nexus-data \
  sonatype/nexus3:3.74.0
# Get initial admin password
docker exec nexus cat /nexus-data/admin.password
```

### Production (regulated org)
- HA with replicated blob store (Nexus Pro)
- S3-backed blob store for cheap archive tier
- Behind reverse proxy (Nginx/Caddy) with TLS
- LDAP/SAML auth (Pro)
- Backup blob store + DB regularly
- Monitor via Prometheus exporter

## 7. Nexus vs alternatives (2026)

| Tool | Strengths | Weaknesses |
|---|---|---|
| **Nexus OSS** | Free, all formats, mature | Manual scaling, OSS feature gaps |
| **Nexus Pro** | HA, staging, IQ Server (SCA) | $$$$ |
| **JFrog Artifactory** | Best UI, best HA, dominant enterprise | $$$$$ (even more) |
| **GitHub Packages** | Free with GitHub, ties to repo permissions | Limited formats (npm, container, maven, nuget, rubygems) |
| **AWS CodeArtifact** | Native AWS IAM, S3-backed, pay-per-storage | Limited formats, AWS-only |
| **GitLab Package Registry** | Free with GitLab, integrates with pipelines | Best if you're all-in on GitLab |
| **Azure Artifacts** | Native AAD, ties to ADO | Azure-only |

### Decision framework

- **All-AWS shop**: CodeArtifact + ECR
- **All-GitHub shop**: GitHub Packages + GHCR
- **All-GitLab shop**: GitLab Package Registry
- **Multi-cloud or on-prem**: Nexus OSS (small) or JFrog Artifactory (large)
- **Regulated finance**: JFrog Artifactory (90%+ market share in that segment)

## 8. SCA + Nexus IQ Server (different product)

Sonatype sells **Nexus IQ Server** separately — a SCA scanner that audits open-source components for known vulnerabilities and license issues. Competes with Snyk, JFrog Xray, GitHub Dependabot + GHAS.

In a regulated pipeline: every build's dependencies get scanned; vulnerable releases blocked from promotion to production-grade Nexus repos.

## 9. Nexus + Docker (private container registry)

```bash
# Configure a Docker hosted repo on port 5000 (internal)
# Then push:
docker login nexus.example.com:5000
docker tag myapp:1.2.3 nexus.example.com:5000/myapp:1.2.3
docker push nexus.example.com:5000/myapp:1.2.3
```

This is the "self-hosted ECR equivalent." Almost any K8s cluster can pull from it (with imagePullSecrets).

## 10. Quick self-check

1. What are the three repo types in Nexus and what's each for?
2. What's the difference between a Component and an Asset?
3. Why use a Group repo?
4. Name three Nexus alternatives and when you'd pick each.
5. What's the relationship between Nexus Repository and Nexus IQ Server?

(Answers: hosted (you publish), proxy (caches public), group (aggregates many into one URL); component = versioned thing, asset = individual file in the component; single URL for clients regardless of where artifact lives; CodeArtifact for AWS-native, GitHub Packages for GitHub-native, JFrog Artifactory for regulated finance; Repository stores artifacts, IQ Server scans them for vulns/license issues — separate products.)
