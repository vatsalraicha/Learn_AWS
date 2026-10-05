# 47 — ⭐ Deploying to SageMaker, ECS/EKS, Lambda, ECR

> *"All four are common deploy targets. The OIDC + role-assumption pattern is identical. The CLI / SDK calls vary."*

## Why this module exists

The four most common AWS deploy targets you'll wire from GitHub Actions: SageMaker (model serving), ECS/EKS (containerized services), Lambda (serverless), and ECR (the container registry that feeds the others). This module covers each with idiomatic Actions snippets.

---

## 1. Deploying to SageMaker — endpoints, batch transform, pipelines

### Endpoint update (zero-downtime)

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ vars.PROD_DEPLOY_ROLE_ARN }}
    aws-region: us-east-1

- name: Create new endpoint config
  id: cfg
  run: |
    CFG_NAME="fraud-detector-prod-$(date +%s)"
    aws sagemaker create-endpoint-config \
      --endpoint-config-name "$CFG_NAME" \
      --production-variants '[{
        "VariantName":"variant-1",
        "ModelName":"${{ inputs.model_name }}",
        "InitialInstanceCount":2,
        "InstanceType":"ml.m5.large"
      }]'
    echo "name=$CFG_NAME" >> $GITHUB_OUTPUT

- name: Update endpoint
  run: |
    aws sagemaker update-endpoint \
      --endpoint-name fraud-detector-prod \
      --endpoint-config-name ${{ steps.cfg.outputs.name }}

- name: Wait for InService
  run: aws sagemaker wait endpoint-in-service --endpoint-name fraud-detector-prod
```

### Batch transform

```yaml
- name: Start batch transform job
  run: |
    aws sagemaker create-transform-job \
      --transform-job-name "batch-$(date +%s)" \
      --model-name ${{ inputs.model_name }} \
      --transform-input '{
        "DataSource": {"S3DataSource": {"S3Uri": "s3://my-bucket/input/", "S3DataType": "S3Prefix"}}
      }' \
      --transform-output '{"S3OutputPath": "s3://my-bucket/output/"}' \
      --transform-resources '{"InstanceType": "ml.m5.xlarge", "InstanceCount": 1}'
```

### Trigger SageMaker Pipeline

```yaml
- run: |
    aws sagemaker start-pipeline-execution \
      --pipeline-name fraud-detector-train \
      --pipeline-parameters '[
        {"Name":"InputData","Value":"s3://my-bucket/data/2026-05/"},
        {"Name":"Epochs","Value":"10"}
      ]'
```

---

## 2. Deploying to ECS

### Update an ECS service to use a new image

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }

- name: Download current task def
  run: |
    aws ecs describe-task-definition \
      --task-definition fraud-detector-prod \
      --query 'taskDefinition' \
      > task-definition.json

- name: Render new image into task def
  id: render
  uses: aws-actions/amazon-ecs-render-task-definition@v1
  with:
    task-definition: task-definition.json
    container-name: fraud-detector
    image: ${{ vars.ECR_REGISTRY }}/fraud-detector:${{ github.sha }}

- name: Deploy
  uses: aws-actions/amazon-ecs-deploy-task-definition@v2
  with:
    task-definition: ${{ steps.render.outputs.task-definition }}
    service: fraud-detector-prod
    cluster: capital-one-ml-prod
    wait-for-service-stability: true
    wait-for-minutes: 10
```

The `wait-for-service-stability` blocks until the new tasks are healthy. If they don't become healthy (failing health checks), the action fails → workflow fails → no false-positive "deployed."

---

## 3. Deploying to EKS / KServe (Capital One's stack)

EKS deploys via `kubectl apply` (and Helm for chart-based services). Capital One uses **KServe** for model serving on EKS — see Topic 04 module 54.

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }

- name: Configure kubectl
  run: aws eks update-kubeconfig --name capital-one-ml-prod --region us-east-1

- name: Apply KServe InferenceService
  run: |
    cat <<EOF | kubectl apply -f -
    apiVersion: serving.kserve.io/v1beta1
    kind: InferenceService
    metadata:
      name: fraud-detector
      namespace: ml-prod
    spec:
      predictor:
        sklearn:
          storageUri: s3://my-bucket/models/fraud-detector/v${{ github.run_number }}/
        minReplicas: 2
        maxReplicas: 10
    EOF

- name: Wait for rollout
  run: kubectl wait --for=condition=Ready inferenceservice/fraud-detector -n ml-prod --timeout=10m
```

For Helm:

```yaml
- run: |
    helm upgrade --install fraud-detector ./charts/fraud-detector \
      --namespace ml-prod \
      --values ./charts/values-prod.yaml \
      --set image.tag=${{ github.sha }} \
      --wait --timeout 10m
```

---

## 4. Deploying to Lambda

### Direct ZIP deploy

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }

- name: Build
  run: |
    pip install --target ./build -r requirements.txt
    cp -r src/* ./build/
    cd build && zip -r ../function.zip .

- name: Update Lambda code
  run: |
    aws lambda update-function-code \
      --function-name fraud-detector-lambda \
      --zip-file fileb://function.zip
    aws lambda wait function-updated --function-name fraud-detector-lambda

- name: Publish version
  id: ver
  run: |
    VERSION=$(aws lambda publish-version --function-name fraud-detector-lambda --query 'Version' --output text)
    echo "version=$VERSION" >> $GITHUB_OUTPUT

- name: Shift traffic via alias (canary 10%)
  run: |
    aws lambda update-alias \
      --function-name fraud-detector-lambda \
      --name prod \
      --function-version ${{ steps.ver.outputs.version }} \
      --routing-config "AdditionalVersionWeights={${{ steps.ver.outputs.version }}=0.1}"
```

### Container image-based Lambda

```yaml
- uses: docker/login-action@v3
  with:
    registry: ${{ vars.ECR_REGISTRY }}
    username: AWS
    password: ${{ steps.ecr-token.outputs.password }}

- run: docker build -t ${{ vars.ECR_REGISTRY }}/fraud-lambda:${{ github.sha }} .
- run: docker push ${{ vars.ECR_REGISTRY }}/fraud-lambda:${{ github.sha }}

- run: |
    aws lambda update-function-code \
      --function-name fraud-detector-lambda \
      --image-uri ${{ vars.ECR_REGISTRY }}/fraud-lambda:${{ github.sha }}
```

---

## 5. Publishing to ECR (container registry)

```yaml
- uses: aws-actions/configure-aws-credentials@v4
  with: { role-to-assume: ${{ vars.ECR_PUSH_ROLE_ARN }}, aws-region: us-east-1 }

- uses: aws-actions/amazon-ecr-login@v2
  id: ecr-login

- name: Build + push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: |
      ${{ steps.ecr-login.outputs.registry }}/fraud-detector:${{ github.sha }}
      ${{ steps.ecr-login.outputs.registry }}/fraud-detector:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
    platforms: linux/amd64,linux/arm64
    provenance: true                  # SLSA build provenance
    sbom: true                        # SBOM attestation

# Pair with attestation upload (see module 35)
- uses: actions/attest-build-provenance@v3
  with:
    subject-name: ${{ steps.ecr-login.outputs.registry }}/fraud-detector
    subject-digest: ${{ steps.push.outputs.digest }}
    push-to-registry: true
```

Notes:
- `docker/build-push-action@v6` supports inline GHA cache via `cache-to/cache-from` — speeds up subsequent builds.
- Set `provenance: true` and `sbom: true` for in-image attestations.
- ECR repo policy must allow push from the OIDC-assumed role.

---

## 6. The deploy pattern (full workflow)

```yaml
name: Deploy
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read
  attestations: write
  packages: write

jobs:
  build-image:
    runs-on: ubuntu-latest
    outputs:
      image-uri: ${{ steps.push.outputs.image-uri }}
      image-digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v6
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ vars.ECR_PUSH_ROLE_ARN }}, aws-region: us-east-1 }
      - uses: aws-actions/amazon-ecr-login@v2
        id: ecr
      - uses: docker/build-push-action@v6
        id: push
        with:
          push: true
          tags: ${{ steps.ecr.outputs.registry }}/fraud-detector:${{ github.sha }}
      - uses: actions/attest-build-provenance@v3
        with:
          subject-name: ${{ steps.ecr.outputs.registry }}/fraud-detector
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true

  deploy-staging:
    needs: build-image
    environment: staging
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ vars.STAGING_DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }
      - run: |
          aws ecs update-service \
            --cluster staging \
            --service fraud-detector \
            --force-new-deployment

  deploy-prod:
    needs: deploy-staging
    environment: prod          # required reviewers + main only
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ vars.PROD_DEPLOY_ROLE_ARN }}, aws-region: us-east-1 }
      - run: |
          # Canary first
          aws ecs update-service --cluster prod --service fraud-detector-canary --force-new-deployment
          aws ecs wait services-stable --cluster prod --services fraud-detector-canary
          # Then full
          aws ecs update-service --cluster prod --service fraud-detector --force-new-deployment
```

---

## 7. Smoke testing post-deploy

Every deploy step should be followed by a smoke test:

```yaml
- name: Smoke test
  run: |
    for i in 1 2 3; do
      if curl -sf https://fraud-detector-prod.capital-one.com/health; then
        echo "Healthy"
        exit 0
      fi
      sleep 10
    done
    echo "Health check failed"
    exit 1
```

For SageMaker endpoints: invoke with a known sample payload and verify response shape.

```yaml
- run: |
    aws sagemaker-runtime invoke-endpoint \
      --endpoint-name fraud-detector-prod \
      --body '{"feature1": 1.0, "feature2": "x"}' \
      --content-type application/json \
      response.json
    python -c "import json; r=json.load(open('response.json')); assert 'prediction' in r"
```

If smoke test fails → workflow fails → trigger rollback (see [module 45](45_mlops_retraining_rollback.md)).

---

## 8. The role-per-target pattern

Don't use one big "deploy everything" role. Split per service + per env:

- `ecr-push-role` — only ECR push to specific repos
- `ecs-deploy-staging-role` — only ECS update-service on staging cluster
- `ecs-deploy-prod-role` — only ECS update-service on prod cluster (env-bound)
- `sagemaker-deploy-staging-role`
- `sagemaker-deploy-prod-role`
- `lambda-deploy-prod-role`

Each role has minimum permissions. Each is bound by OIDC sub-claim to its specific scope.

A compromised staging workflow can't deploy to prod. A compromised ECS workflow can't update Lambda.

---

## 9. ECR image pull from the target

ECS / Lambda / SageMaker need to PULL from ECR. Their execution roles must have `ecr:GetAuthorizationToken`, `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer`. ECR repo policy allows the target's account.

For cross-account ECR pulls: ECR repo policy with `AllowPull` from the target account. SageMaker and ECS handle cross-account pulls transparently.

---

## 10. Cross-references

- The OIDC + IAM setup → [module 29](29_actions_oidc_aws.md), [module 46](46_aws_oidc_trust_policy_deep.md).
- Cross-account CDK + Terraform → [module 48](48_aws_cdk_cfn_tf_cross_account.md).
- Champion/challenger ECS production-variant pattern → [module 44](44_mlops_champion_challenger.md).
- Rollback workflows → [module 45](45_mlops_retraining_rollback.md).
- ARC for in-VPC builds → [module 28](28_actions_self_hosted_arc_gpu.md).
- Topic 04 modules 31 (ECS), 32 (Lambda), 33 (EKS), 34 (SageMaker), 54 (KServe).
