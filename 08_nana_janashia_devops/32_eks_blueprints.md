# 32 — EKS Blueprints + Cluster Bootstrapping

## Why this module exists

A bare EKS cluster is useless. You need: CNI, CSI driver, autoscaler, ingress controller, cert-manager, monitoring stack, GitOps controller, policy engine, secret operator. **EKS Blueprints** is the AWS-maintained Terraform/CDK pattern library that handles this.

## 1. The day-1 problem

A fresh `eksctl create cluster` gives you:
- A control plane
- A node group
- The minimal CNI (AWS VPC CNI)
- That's it

A production-ready cluster needs ~10-15 more components. Day-1 mistakes here cascade for years.

## 2. EKS Blueprints — the patterns

**EKS Blueprints for Terraform** (https://github.com/aws-ia/terraform-aws-eks-blueprints) provides:
- Cluster + node groups
- Add-ons (Karpenter, AWS Load Balancer Controller, External DNS, External Secrets Operator, etc.)
- Bootstrap argo
- IAM/IRSA wiring

It's a Terraform module collection — not a black-box product.

```hcl
module "eks_blueprints_addons" {
  source  = "aws-ia/eks-blueprints-addons/aws"
  version = "~> 1.20"

  cluster_name      = module.eks.cluster_name
  cluster_endpoint  = module.eks.cluster_endpoint
  cluster_version   = module.eks.cluster_version
  oidc_provider_arn = module.eks.oidc_provider_arn

  # Core AWS-managed add-ons
  eks_addons = {
    coredns = {}
    kube-proxy = {}
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {}
    eks-pod-identity-agent = {}
  }

  # Third-party Helm-installed add-ons
  enable_aws_load_balancer_controller = true
  enable_external_secrets             = true
  enable_external_dns                 = true
  enable_cert_manager                 = true
  enable_karpenter                    = true
  enable_metrics_server               = true
  enable_argocd                       = true
  enable_kube_prometheus_stack        = true
}
```

## 3. The add-ons every production cluster needs

| Add-on | Purpose |
|---|---|
| **AWS VPC CNI** | Pod networking; assigns ENIs |
| **CoreDNS** | Cluster DNS |
| **kube-proxy** | Service routing |
| **EBS CSI Driver** | Persistent volumes from EBS |
| **EFS CSI Driver** | Shared volumes from EFS |
| **AWS Load Balancer Controller** | Provisions ALBs/NLBs from Ingress + Service objects |
| **Karpenter** | Node autoscaling |
| **Cluster Autoscaler** | (alternative to Karpenter) |
| **cert-manager** | TLS cert lifecycle from Let's Encrypt/ACM |
| **External DNS** | Auto-create Route 53 records from Ingress hosts |
| **External Secrets Operator** | Sync AWS Secrets Manager → K8s Secrets |
| **Metrics Server** | HPA needs this |
| **kube-prometheus-stack** | Monitoring |
| **ArgoCD / Flux** | GitOps deploys |
| **Kyverno / OPA Gatekeeper** | Admission control |
| **Falco** | Runtime threat detection |
| **Istio / Linkerd / Cilium SM** | Service mesh (optional) |

EKS Blueprints covers most of these declaratively.

## 4. Karpenter — the autoscaler

Karpenter watches for unschedulable pods, **picks the right instance type**, and launches it directly (not via ASG). Faster + more efficient than Cluster Autoscaler.

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: general
spec:
  template:
    spec:
      requirements:
      - { key: kubernetes.io/arch, operator: In, values: [amd64] }
      - { key: karpenter.sh/capacity-type, operator: In, values: [spot, on-demand] }
      - { key: karpenter.k8s.aws/instance-category, operator: In, values: [c, m, r] }
      - { key: karpenter.k8s.aws/instance-cpu, operator: Lt, values: ["32"] }
      nodeClassRef:
        name: default
        kind: EC2NodeClass
        group: karpenter.k8s.aws
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
```

## 5. AWS Load Balancer Controller

Watches `Service type=LoadBalancer` and `Ingress` objects. Provisions:
- NLB (Network Load Balancer) for L4 (Service)
- ALB (Application Load Balancer) for L7 (Ingress)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip   # IP mode for IRSA pods
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:1234:certificate/abc
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
spec:
  rules:
  - host: app.example.com
    http:
      paths:
      - { path: /, pathType: Prefix, backend: { service: { name: app, port: { number: 80 } } } }
```

## 6. cert-manager + External DNS — auto TLS + DNS

cert-manager:
- Issues + renews TLS certs from Let's Encrypt or any ACME issuer
- Integrates with Route 53 for DNS-01 challenges
- Stores certs in K8s Secrets

External DNS:
- Reads Ingress hosts, Service annotations
- Creates Route 53 records automatically
- Removes records when objects deleted

Together: deploy an Ingress with a host name; cert-manager issues a cert + External DNS points Route 53 at the ALB; **automatic public TLS endpoint**.

## 7. Bootstrapping autoscaler tuning

Karpenter / Cluster Autoscaler need:
- IAM permissions (IRSA) to launch instances
- Cluster taint tolerance for system pods
- Resource requests on workloads (otherwise scheduler can't decide)
- Adequate PodDisruptionBudgets

Without PDBs, consolidation can evict everything at once.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: app-pdb }
spec:
  minAvailable: 2
  selector:
    matchLabels: { app: my-app }
```

## 8. Access Token Expiration (the deploy gotcha)

EKS API tokens (`aws eks get-token`) expire **after 15 minutes**. Long-running pipelines or scripts need to refresh.

Solutions:
- Re-run `aws eks update-kubeconfig` at start of each stage
- Use a refreshing helper script
- For ArgoCD: it uses a cluster-resident kubeconfig that doesn't depend on this

## 9. ArgoCD bootstrap pattern (App-of-Apps)

```
ArgoCD
  ├─ Application "root-app"
      ├─ Application "addons" → installs cert-manager, eso, prometheus
      ├─ Application "policies" → installs Kyverno + policies
      ├─ Application "team-a" → installs team-a's apps
      └─ Application "team-b" → installs team-b's apps
```

One bootstrap Application that creates other Applications. The cluster is then **fully described in Git**.

## 10. EKS Blueprints alternatives

| Alternative | When |
|---|---|
| **eksctl** | Simple CLI; good for dev/test, not production-grade IaC |
| **AWS CDK + cdk8s + cdk8s-plus** | TypeScript IaC + manifests in code |
| **terraform-aws-modules/eks** | More modular; you assemble add-ons yourself |
| **Spot/PEKS / Rafay / Loft** | Commercial multi-cluster platforms |
| **Capital One internal IDP** | Their own + Terraform modules |

## 11. Quick self-check

1. What's the day-1 problem with a fresh EKS cluster?
2. What's the difference between Karpenter and Cluster Autoscaler?
3. What does the AWS Load Balancer Controller provision?
4. What does cert-manager + External DNS together enable?
5. What's the App-of-Apps pattern in ArgoCD?

(Answers: missing most production essentials — CSI, LB controller, autoscaler, monitoring, GitOps, etc.; Karpenter picks the right instance per pending pod and provisions directly, CAS uses ASGs with predefined instance types; ALBs from Ingress objects + NLBs from Service type=LoadBalancer; automatic public-facing TLS endpoint with DNS, given just an Ingress; one root Application that creates other Applications — fully Git-described cluster bootstrap.)
