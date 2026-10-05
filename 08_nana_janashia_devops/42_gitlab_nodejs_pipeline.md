# 42 — Real Pipeline — Node.js App to Private Registry to DEV

## 1. The scenario

A Node.js app → unit tests → Docker image → push to GitLab Container Registry → deploy to DEV server via SSH + Docker.

## 2. The Node.js project

```
my-node-app/
├── package.json
├── package-lock.json
├── src/
│   └── index.js
├── tests/
│   └── index.test.js
├── Dockerfile
└── .gitlab-ci.yml
```

`Dockerfile`:
```dockerfile
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

FROM node:24-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=builder --chown=app:app /app .
USER app
EXPOSE 3000
CMD ["node", "src/index.js"]
```

## 3. The .gitlab-ci.yml

```yaml
stages: [test, build, deploy]

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  IMAGE_LATEST: $CI_REGISTRY_IMAGE:latest

default:
  image: node:24-alpine
  cache:
    key:
      files: [package-lock.json]
    paths: [node_modules/]

# ─────────────────────────────────────────────────
# Stage: test
# ─────────────────────────────────────────────────
unit-tests:
  stage: test
  script:
    - npm ci
    - npm run lint
    - npm test -- --reporter=junit --output=test-report.xml
  artifacts:
    when: always
    reports:
      junit: test-report.xml
    expire_in: 7 days

# ─────────────────────────────────────────────────
# Stage: build (Docker image + push to GitLab registry)
# ─────────────────────────────────────────────────
build-image:
  stage: build
  image: gcr.io/kaniko-project/executor:v1.23.0-debug
  script:
    - mkdir -p /kaniko/.docker
    - |
      cat > /kaniko/.docker/config.json <<EOF
      {
        "auths": {
          "$CI_REGISTRY": {
            "auth": "$(echo -n "$CI_REGISTRY_USER:$CI_REGISTRY_PASSWORD" | base64 | tr -d '\n')"
          }
        }
      }
      EOF
    - >
      /kaniko/executor
      --context $CI_PROJECT_DIR
      --dockerfile $CI_PROJECT_DIR/Dockerfile
      --destination $IMAGE_TAG
      --destination $IMAGE_LATEST
      --cache=true
      --cache-repo $CI_REGISTRY_IMAGE/cache
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

# ─────────────────────────────────────────────────
# Stage: deploy
# ─────────────────────────────────────────────────
deploy-dev:
  stage: deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - ssh-keyscan -H $DEV_SERVER >> ~/.ssh/known_hosts
  script:
    - |
      ssh deploy@$DEV_SERVER <<EOF
      set -euo pipefail
      docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
      docker pull $IMAGE_TAG
      docker stop my-app || true
      docker rm my-app || true
      docker run -d --name my-app --restart=unless-stopped \
        -p 80:3000 \
        $IMAGE_TAG
      EOF
  environment:
    name: dev
    url: http://dev.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

## 4. Variables you set in Settings → CI/CD → Variables

| Variable | Value | Settings |
|---|---|---|
| `SSH_PRIVATE_KEY` | the deploy user's private key | Masked + Protected + File |
| `DEV_SERVER` | dev.example.com | Plain |
| `$CI_REGISTRY_USER` / `$CI_REGISTRY_PASSWORD` | (predefined; GitLab provides automatically) | — |

For SSH key: type **File**, paste private key contents — GitLab writes to temp file and `$SSH_PRIVATE_KEY` contains the path.

## 5. GitLab Environments

```yaml
environment:
  name: dev
  url: http://dev.example.com
```

Creates an entry in **Operate → Environments** with deployment history. Rollback via UI (re-runs the deploy job at an older SHA).

For prod:
```yaml
deploy-prod:
  environment:
    name: production
    url: https://example.com
    deployment_tier: production
  rules:
    - if: '$CI_COMMIT_TAG'
      when: manual
```

`deployment_tier` (production / staging / testing / development / other) gives GitLab semantic awareness for compliance dashboards.

## 6. Test Reports + Coverage in MRs

GitLab parses test reports + coverage:

```yaml
unit-tests:
  script:
    - npm test -- --coverage --coverageReporters=cobertura --reporters=jest-junit
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
```

The `coverage:` regex extracts the percentage from job logs; displays in MR.

## 7. The Container Registry

GitLab's built-in registry is included free. Authentication via:
- `CI_REGISTRY_USER` / `CI_REGISTRY_PASSWORD` (predefined per-job)
- Or `CI_JOB_TOKEN` for short-lived
- Or deploy tokens for cross-project access

```bash
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

For ECR (instead of GitLab registry):
```yaml
build-image:
  before_script:
    - aws ecr get-login-password --region $AWS_REGION | docker login -u AWS --password-stdin $ECR_REGISTRY
  script:
    - docker build -t $ECR_REGISTRY/my-app:$CI_COMMIT_SHORT_SHA .
    - docker push $ECR_REGISTRY/my-app:$CI_COMMIT_SHORT_SHA
```

## 8. Deploying with Docker Compose

Sometimes you want compose, not raw `docker run`:

```yaml
deploy-dev:
  script:
    - |
      ssh deploy@$DEV_SERVER <<EOF
      cd /opt/app
      sed -i "s|image: .*my-app:.*|image: $IMAGE_TAG|" compose.yaml
      docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
      docker compose pull
      docker compose up -d
      EOF
```

The compose file lives on the server; CI updates the tag + pulls.

## 9. The security hardening for this pattern

What's wrong with the above:
- SSH from CI directly = inbound SSH on the server
- Long-lived SSH key in CI vars
- `docker login` with `CI_REGISTRY_PASSWORD` (job token works but is broader scoped than needed)

What to upgrade to:
- **AWS SSM RunCommand** instead of SSH (no inbound; IAM-based auth; CloudTrail audit)
- **OIDC to AWS Role** instead of long-lived SSH key
- **Deploy via K8s + GitOps** instead of raw docker on a VM (eliminates SSH entirely)

This is the Nana-bootcamp pattern; for production at Capital One it's the GitOps + EKS pattern.

## 10. Quick self-check

1. Why use Kaniko instead of `docker build` in this pipeline?
2. What does `$CI_REGISTRY_USER` give you for free?
3. What does GitLab Environments add over just running deploy jobs?
4. Why is SSH from CI to EC2 considered an anti-pattern?
5. What's the difference between `deployment_tier: production` and `name: production`?

(Answers: Kaniko builds images without requiring a privileged Docker daemon — works in unprivileged K8s pods; pre-authenticated credential to the project's container registry — no need to manage; deployment history per env, easy rollback, MR shows latest deploy URL; inbound SSH on prod hosts + long-lived SSH key in CI — SSM RunCommand removes both; tier is the semantic level used by GitLab for compliance dashboards, name is the display label.)
