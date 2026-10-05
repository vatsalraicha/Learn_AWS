# 23 — Build a CD Pipeline + AWS ECR

## 1. CI/CD as one pipeline

Continuous Integration (CI) ends when the artifact is built + tested. Continuous Delivery (CD) takes that artifact through environments to production. **CD = deploy to staging automatically + prod with approval. Continuous Deployment = no approval, every green build to prod.**

A pipeline stage map:
```
Lint → Test → SAST → SCA → Build Image → Image Scan → Push to ECR → Deploy DEV → DAST → Deploy STG → Approval → Deploy PROD
```

## 2. Security gates per stage (the DevSecOps mapping)

| Stage | Security gate |
|---|---|
| Lint | Pre-commit hooks: gitleaks, secrets scan |
| Test | Unit + integration tests pass |
| SAST | SonarQube / Semgrep / Bandit critical findings = 0 |
| SCA | Trivy fs / Snyk; Critical CVEs = 0 |
| Build | Reproducible build; non-root user |
| Image scan | Trivy image / ECR enhanced scanning; Critical CVEs = 0 |
| Push | Sign with Cosign; attach SBOM |
| Deploy | Admission control (Kyverno) verifies signature + policy |
| DAST | ZAP baseline scan against deployed app |
| Prod approval | Manual gate; CODEOWNERS-style approval |

## 3. The 80/20 GitLab CI pipeline

```yaml
stages: [test, build, scan, deploy-dev, dast, deploy-prod]

variables:
  IMAGE: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}

test:
  stage: test
  image: python:3.13-slim
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - pytest --cov

sast:
  stage: test
  include: { template: Jobs/SAST.gitlab-ci.yml }

dep-scan:
  stage: test
  include: { template: Jobs/Dependency-Scanning.gitlab-ci.yml }

build:
  stage: build
  image: gcr.io/kaniko-project/executor:latest
  script:
    - /kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $IMAGE

container-scan:
  stage: scan
  image: aquasec/trivy
  script:
    - trivy image --severity CRITICAL,HIGH --exit-code 1 $IMAGE

deploy-dev:
  stage: deploy-dev
  environment: { name: dev, url: https://dev.example.com }
  script: kubectl set image deployment/app app=$IMAGE
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

dast:
  stage: dast
  image: owasp/zap2docker-stable
  script:
    - zap-baseline.py -t https://dev.example.com -r dast-report.html
  artifacts:
    paths: [dast-report.html]
  allow_failure: true

deploy-prod:
  stage: deploy-prod
  environment: { name: prod, url: https://example.com }
  script: kubectl set image deployment/app app=$IMAGE
  when: manual
  only: [tags]
```

## 4. ECR — Elastic Container Registry

### Authenticate
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  1234.dkr.ecr.us-east-1.amazonaws.com
```

In CI, use **OIDC + IAM Role** instead of long-lived keys:

```yaml
# GitHub Actions
permissions: { id-token: write, contents: read }
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::1234:role/github-actions-ecr-push
    aws-region: us-east-1
- run: |
    aws ecr get-login-password | docker login --username AWS --password-stdin 1234.dkr.ecr.us-east-1.amazonaws.com
    docker buildx build --push -t 1234.dkr.ecr.us-east-1.amazonaws.com/app:${{ github.sha }} .
```

### ECR features
- **Image scanning (basic, free)** — Clair-based on push
- **Enhanced scanning (Inspector, paid)** — continuous CVE rescans, OS + OSS package coverage
- **Lifecycle policies** — auto-delete old images
- **Replication** — multi-region or cross-account
- **Pull-through cache** — proxy Docker Hub/Quay/GHCR (avoids public rate limits)
- **Repository policies** — IAM-based cross-account access
- **Signing** — supports Notation / Cosign signature artifacts

### Lifecycle policy (essential for cost)
```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 tagged images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": { "type": "expire" }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": { "type": "expire" }
    }
  ]
}
```

## 5. Deploying to EC2 (Nana's bootcamp baseline)

For an EC2 target with Docker, the pattern:
1. SSH from CI to EC2 (or use SSM RunCommand — modern, no inbound 22)
2. Pull new image from ECR
3. Stop + start container
4. Health check

```bash
ssh deploy@$EC2_HOST <<EOF
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin $ECR_REGISTRY
  docker pull $ECR_REGISTRY/app:$VERSION
  docker stop app || true
  docker rm app || true
  docker run -d --name app --restart=unless-stopped \
    -p 80:8000 $ECR_REGISTRY/app:$VERSION
EOF
```

Better: SSM RunCommand (Module 26 covers this) avoids inbound SSH.

## 6. Self-managed GitLab Runner on EC2

```bash
# On EC2
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner
useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register
gitlab-runner register --url https://gitlab.com --token <runner-auth-token> \
  --executor docker --docker-image alpine:3.20
```

Considerations:
- Runners on EC2 in a private subnet; pipelines connect outbound to GitLab.com (or to self-hosted GitLab).
- Tag runners by capability (e.g., `aws`, `large-runner`, `gpu`).
- Auto-scaling via AWS Fleet executor.

## 7. Docker caching on self-managed runner

Each build re-runs `docker build` cold = slow. Options:
- **BuildKit local cache mount** — cache between builds on same runner
- **--cache-from / --cache-to** with registry-based cache
- **buildx with `--cache-to type=registry`** — push cache to ECR cache repo

```bash
docker buildx build \
  --cache-from type=registry,ref=$ECR/cache:buildcache \
  --cache-to type=registry,ref=$ECR/cache:buildcache,mode=max \
  -t $IMAGE --push .
```

10x+ build speedup for incremental changes.

## 8. Multi-environment deploys (Dev → Staging → Prod)

The pattern:
```
main branch push → deploy DEV → run DAST → on success → deploy STG → manual approval → deploy PROD
```

Environment-specific config:
- AWS account per environment (Capital One: separate accounts under one Organization)
- Different K8s namespace or whole separate clusters per env
- DB per environment (never shared between envs)
- Secrets per env in Secrets Manager

## 9. Quick self-check

1. What's the difference between Continuous Delivery and Continuous Deployment?
2. Why use OIDC + IAM Role over AWS access keys in CI?
3. What's an ECR lifecycle policy and why is it essential?
4. What's the modern alternative to SSH-from-CI-to-EC2?
5. How does BuildKit registry-cache speed up Docker builds in CI?

(Answers: Delivery = automated to staging + manual prod, Deployment = no manual; short-lived creds, no long-lived secrets to rotate or leak, audited via CloudTrail; auto-deletes old images to control storage cost — ECR is pay-per-GB; SSM RunCommand — no inbound 22, IAM-based auth, fully audited; caches built layers in a registry so subsequent builds pull cached layers instead of rebuilding.)
