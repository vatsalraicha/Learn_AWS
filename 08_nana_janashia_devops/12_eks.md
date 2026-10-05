# 12 — Kubernetes on AWS — EKS

> Cross-link: [Topic 04 Module 33 — EKS foundations](../04_aws_for_ai_ml/) and [Topic 05 Module 26 — EKS data exposure](../05_docker_kubernetes/26_eks_data_exposure.md) for the full depth.
>
> This module is the **CI/CD-deploy angle** — how a pipeline gets a built artifact onto EKS.

## 1. EKS at 30,000 ft

- **Managed K8s control plane** ($0.10/hr ≈ $73/mo per cluster); you pay per node + LB + EBS.
- **Worker nodes**: managed node groups (AWS-managed ASG), self-managed nodes, or **Fargate** (serverless pods).
- **Auth**: maps IAM users/roles → K8s RBAC via the **aws-auth ConfigMap** (legacy) or **EKS Access Entries** (modern, GA 2024).
- **Pod identity**: IRSA (OIDC, mature) or EKS Pod Identity (newer, simpler — 2023 GA).

## 2. Creating an EKS cluster — three options

### Option A: AWS Console (learning)
Click through; not reproducible. Don't do this for real work.

### Option B: eksctl (CLI tool)
```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --version 1.32 \
  --nodegroup-name workers \
  --node-type t3.large \
  --nodes 2 --nodes-min 2 --nodes-max 5
```

Fast, opinionated, good for dev/test. Behind the scenes generates CloudFormation.

### Option C: Terraform (production)
```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "my-cluster"
  cluster_version = "1.32"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.intra_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  eks_managed_node_groups = {
    workers = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      instance_types = ["m5.large"]
    }
  }
}
```

Capital One: 100% Terraform-managed EKS clusters with custom modules + Cloud Custodian guardrails.

## 3. Autoscaling: Cluster Autoscaler vs Karpenter

- **Cluster Autoscaler (CAS)** — older, ASG-based; adds nodes when pods unschedulable.
- **Karpenter** — AWS-built (now CNCF), watches pending pods, **provisions exactly the right instance** without ASG. Spot-aware, consolidation-aware. **The 2026 default for new clusters.**

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: [amd64]
      - key: karpenter.k8s.aws/instance-category
        operator: In
        values: [c, m, r]
      - key: karpenter.sh/capacity-type
        operator: In
        values: [spot, on-demand]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
```

## 4. Fargate Profile

EKS Fargate runs pods on AWS-managed serverless capacity. No nodes to manage.

```hcl
fargate_profiles = {
  default = {
    selectors = [{ namespace = "default" }]
  }
}
```

Caveats: limited daemonset support, no privileged pods, no GPU, no EBS volumes (EFS yes). Good for stateless web/app workloads where node ops is overhead.

## 5. Authenticating with the cluster

```bash
aws eks update-kubeconfig --region us-east-1 --name my-cluster --profile prod
kubectl get nodes
```

Behind the scenes: kubectl calls `aws eks get-token` → exchanges IAM credentials for a K8s token → cluster validates via the OIDC provider.

## 6. Deploying from Jenkins/Actions/GitLab to EKS

The 2026 pattern:
1. CI builds the image
2. CI pushes to ECR (`aws ecr get-login-password | docker login`; `docker push`)
3. CI updates a K8s manifest in a "manifests" repo with the new image tag
4. **ArgoCD / Flux** detects the change and syncs the cluster (GitOps)

Or older:
1. CI builds + pushes image
2. CI runs `kubectl apply -f deployment.yaml` (with new image tag)
3. CI waits for rollout to succeed (`kubectl rollout status`)

Why GitOps wins: pipeline doesn't need cluster credentials; cluster pulls. Audit trail in Git.

## 7. Jenkins → EKS pipeline (Nana's bootcamp)

```groovy
pipeline {
  agent any
  environment {
    AWS_REGION = 'us-east-1'
    ECR_REGISTRY = '1234.dkr.ecr.us-east-1.amazonaws.com'
    APP_NAME = 'myapp'
    CLUSTER_NAME = 'my-cluster'
  }
  stages {
    stage('Build') {
      steps {
        sh 'docker build -t $APP_NAME:$BUILD_NUMBER .'
      }
    }
    stage('Push to ECR') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds',
            usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '''
            aws ecr get-login-password --region $AWS_REGION | \
              docker login --username AWS --password-stdin $ECR_REGISTRY
            docker tag $APP_NAME:$BUILD_NUMBER $ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
            docker push $ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
          '''
        }
      }
    }
    stage('Deploy to EKS') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds',
            usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '''
            aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
            kubectl set image deployment/$APP_NAME app=$ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
            kubectl rollout status deployment/$APP_NAME --timeout=5m
          '''
        }
      }
    }
  }
}
```

Replace `aws-creds` with OIDC + IAM role for production.

## 8. EKS at Capital One

- Self-host model serving on EKS via **KServe** (NOT SageMaker for inference)
- **Karpenter** for autoscaling
- **Istio ambient** for service mesh
- **External Secrets Operator** → AWS Secrets Manager
- **Cloud Custodian** for AWS-API-layer policy + **Kyverno** for K8s-API-layer policy
- See [Topic 04 Module 54 — KServe deep](../04_aws_for_ai_ml/) for full pattern

## 9. Quick self-check

1. What does `aws eks update-kubeconfig` actually do?
2. Why is Karpenter preferred over Cluster Autoscaler in 2026?
3. What is the difference between IRSA and EKS Pod Identity?
4. Why is GitOps deploy preferred over `kubectl apply` from CI?
5. What is the EKS control plane cost per month per cluster?

(Answers: writes a context to ~/.kube/config that calls `aws eks get-token` for auth; provisions exactly-right instance per pending pod, consolidation, spot-aware; IRSA uses OIDC + role per service account, Pod Identity uses agent + simpler binding; pipeline needs no cluster creds, audit in Git, drift detection; ~$73/mo at $0.10/hr.)
