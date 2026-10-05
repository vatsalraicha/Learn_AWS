# 30 — EKS Access Management — IRSA + RBAC

## 1. Two-layer authorization on EKS

For a pod to access AWS resources (S3, DynamoDB), authorization happens at **two layers**:

1. **K8s RBAC** — what ServiceAccount can do inside the cluster
2. **AWS IAM** — what AWS Role the pod can assume to call AWS APIs

You need both. Misalign them and pods can't do their work, or do too much.

## 2. The K8s RBAC primitives

- **ServiceAccount** — identity for a pod (default: namespace `default`)
- **Role** — permissions in one namespace
- **ClusterRole** — permissions cluster-wide
- **RoleBinding** — binds Role to user/group/ServiceAccount in a namespace
- **ClusterRoleBinding** — same, cluster-wide

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: my-app
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
  namespace: my-app
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-binding
  namespace: my-app
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: my-app
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
```

## 3. EKS Access Entries (modern) vs aws-auth ConfigMap (legacy)

### Legacy: aws-auth ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: aws-auth
  namespace: kube-system
data:
  mapRoles: |
    - rolearn: arn:aws:iam::1234:role/eksAdmins
      username: admin
      groups:
        - system:masters
    - rolearn: arn:aws:iam::1234:role/eksReadOnly
      username: readonly
      groups:
        - reader
```

Problems with aws-auth:
- Edit it wrong → lock yourself out of cluster
- No native IAM permissions on it
- No EKS API to manage
- Auditable only via Kubernetes audit logs

### Modern: EKS Access Entries (GA late 2023)
```bash
aws eks create-access-entry \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::1234:role/eksAdmins \
  --type STANDARD

aws eks associate-access-policy \
  --cluster-name my-cluster \
  --principal-arn arn:aws:iam::1234:role/eksAdmins \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy \
  --access-scope type=cluster
```

Benefits:
- Native AWS API
- IAM-permission-controllable
- CloudTrail-audited
- No way to lock yourself out from a single bad ConfigMap edit
- Built-in AWS-managed access policies

## 4. IRSA — IAM Roles for Service Accounts

The original (and still widely used) pattern. How it works:
1. EKS cluster has an OIDC provider (`https://oidc.eks.us-east-1.amazonaws.com/id/ABC123`)
2. You register the OIDC provider in IAM
3. You create an IAM role with trust policy allowing assumption from that OIDC provider for a specific ServiceAccount
4. You annotate the ServiceAccount with the role ARN
5. The EKS Pod Identity webhook injects env vars + projected token into pods using that SA
6. AWS SDK in the pod automatically uses the token to AssumeRoleWithWebIdentity

```hcl
# 1. Get cluster OIDC issuer
data "aws_eks_cluster" "main" { name = "my-cluster" }
data "tls_certificate" "main" {
  url = data.aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# 2. Register OIDC provider
resource "aws_iam_openid_connect_provider" "main" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.main.certificates[0].sha1_fingerprint]
  url             = data.aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# 3. IAM role with trust policy
resource "aws_iam_role" "app" {
  name = "app-irsa"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.main.arn }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.main.url, "https://", "")}:sub" = "system:serviceaccount:my-app:app-sa"
          "${replace(aws_iam_openid_connect_provider.main.url, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "app_s3" {
  role       = aws_iam_role.app.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}
```

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: my-app
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::1234:role/app-irsa
```

Now pods using ServiceAccount `app-sa` automatically get temporary AWS credentials for the `app-irsa` role.

## 5. EKS Pod Identity (the newer, simpler way)

EKS Pod Identity (GA Nov 2023) replaces IRSA's complexity:
- No OIDC provider registration needed
- No annotations on ServiceAccount
- Uses **Pod Identity Agent** DaemonSet
- Associate IAM role to (cluster, namespace, ServiceAccount) tuple via EKS API

```bash
aws eks create-pod-identity-association \
  --cluster-name my-cluster \
  --namespace my-app \
  --service-account app-sa \
  --role-arn arn:aws:iam::1234:role/app-pod-identity
```

```hcl
resource "aws_eks_pod_identity_association" "app" {
  cluster_name    = "my-cluster"
  namespace       = "my-app"
  service_account = "app-sa"
  role_arn        = aws_iam_role.app.arn
}

# Trust policy is simpler:
resource "aws_iam_role" "app" {
  name = "app-pod-identity"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "pods.eks.amazonaws.com" }
      Action = ["sts:AssumeRole", "sts:TagSession"]
    }]
  })
}
```

IRSA vs Pod Identity decision:
- New clusters → Pod Identity (simpler trust policy, no per-cluster OIDC mgmt)
- Existing IRSA clusters → migrate gradually; both can coexist
- Cross-account scenarios → IRSA still has edge cases

## 6. Cluster admin pattern (the "break glass" role)

```hcl
# Break-glass: only when you really need full admin
resource "aws_iam_role" "eks_break_glass" {
  name = "eks-break-glass"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { AWS = data.aws_caller_identity.current.account_id }
      Action = "sts:AssumeRole"
      Condition = {
        Bool = { "aws:MultiFactorAuthPresent" = "true" }
        StringEquals = { "aws:RequestTag/break-glass" = "true" }
      }
    }]
  })
}
```

Plus an EKS Access Entry for this role with `AmazonEKSClusterAdminPolicy` scope. Audit every assumption — it should be rare.

## 7. Day-to-day developer access pattern

The pattern for engineers:
1. Engineer auths via Identity Center SSO
2. Assumes a permission-set role (e.g., `EKSDeveloper`)
3. `aws eks update-kubeconfig --name cluster-x --profile dev` — kubectl now auths as that role
4. EKS Access Entry maps that role to K8s group `developers`
5. Cluster has Role/RoleBinding granting `developers` namespace-scoped read + log access

No human has admin. Admin requires break-glass + ticket + audit.

## 8. The ServiceAccount + IAM Role anti-patterns

1. **Using default SA in every pod** — same identity for everything; no per-pod permissions
2. **`automountServiceAccountToken: true` on SA that doesn't need K8s API** — token has nothing to do but is a credential to steal
3. **Wildcard IAM permissions on pod role** — pod compromise = AWS account compromise
4. **Sharing IAM role across many SAs** — can't tell which pod did what
5. **Long-lived AWS keys in K8s Secrets** — IRSA + Pod Identity exist for a reason

## 9. Quick self-check

1. What's the difference between K8s RBAC and AWS IAM in the EKS context?
2. What replaced PodSecurityPolicy? (recap from Module 29)
3. What's the difference between IRSA and EKS Pod Identity?
4. Why is the legacy aws-auth ConfigMap risky?
5. What's the security advantage of `automountServiceAccountToken: false` on a SA?

(Answers: RBAC = what SA can do inside cluster, IAM = what AWS Role the pod can assume to call AWS APIs; Pod Security Admission with PSS profiles; IRSA uses OIDC provider + trust policy on SA name, Pod Identity uses Pod Identity Agent + EKS API association — simpler trust policy + simpler ops; bad edit can lock you out of cluster + no IAM controls on its modification + only K8s-audit; no token mounted means no K8s API credential for an attacker to steal from a compromised pod.)
