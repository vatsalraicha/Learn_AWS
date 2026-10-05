# Module 47 — Databricks Networking on AWS

> **What this is:** AWS PrivateLink for Databricks, Secure Cluster Connectivity (SCC), BYO VPC, NAT GW requirements, classic vs serverless network paths.

---

## 1. AWS PrivateLink for Databricks

Databricks supports **two PrivateLink paths**:

- **Front-end PrivateLink** — users → Databricks UI/API via PrivateLink. No traffic on public internet.
- **Back-end PrivateLink** — cluster (your VPC) → Databricks control plane via PrivateLink.

For regulated finance, both are typically required.

## 2. Secure Cluster Connectivity (SCC)

**SCC** is Databricks' name for back-end PrivateLink. The cluster initiates an outbound connection to the control plane via PrivateLink — **no inbound from Databricks needed**.

This means:
- Cluster nodes don't need public IPs.
- Inbound SG can be locked down.
- All control-plane communication encrypted and private.

## 3. BYO VPC (Customer-managed VPC)

Default Databricks behavior creates a VPC for you. **BYO VPC** lets you use your own — required for org-managed networking standards.

**Subnet sizing constraints:**
- VPC: `/16` to `/25`.
- Subnets: `/17` to `/26`.
- **2 IPs per cluster node** (one for driver, one for executor — and possibly more for shared storage).

So a `/24` subnet (251 IPs) supports ~125 concurrent cluster nodes.

## 4. NAT Gateway requirements

Classic compute clusters need **internet egress** for:
- Pulling DBR (Databricks Runtime) images.
- Accessing Maven/PyPI/CRAN for libraries.
- Webhook callbacks.

**Solution:** NAT GW with restricted egress (allowlist Databricks-related domains via Network Firewall) **OR** VPC endpoints for AWS services + private mirror for Maven/PyPI.

**Serverless compute** uses **NCC (Network Connectivity Configuration)** instead — a Databricks-managed egress story.

## 5. Classic vs serverless data plane network paths

### Classic
```
User → Databricks UI → API call →
  Control plane creates cluster in your VPC →
  Cluster (in your VPC) reads S3 via S3 endpoint →
  Results back to control plane via SCC →
  User sees results
```

### Serverless
```
User → Databricks UI → API call →
  Serverless compute in Databricks' VPC →
  Cluster reads S3 via Databricks' connectivity (NCC) →
  Results back to control plane →
  User sees results
```

Serverless requires you to allow the Databricks VPC to reach your S3 — this is the trickier compliance conversation.

## 6. Network Connectivity Configuration (NCC)

NCC defines how serverless compute reaches **your** resources:
- **S3** access: PrivateLink from Databricks serverless to your S3 endpoint.
- **Network Firewall rules** to restrict egress.

This is the equivalent of "BYO VPC" for the serverless world.

## 7. Cross-account considerations

The cross-account IAM role that Databricks assumes to manage EC2 needs:
- `ec2:RunInstances`, `ec2:TerminateInstances` on cluster instances.
- `iam:PassRole` on the instance profile.
- VPC + ENI permissions.

Capital One pattern: explicit `Condition` restricting role to specific subnets/AMIs/instance types.

## 8. Pitfalls

- **Subnet too small** → can't scale beyond N nodes.
- **No NAT GW or VPC endpoints** → classic clusters can't pull DBR.
- **Direct S3 IAM** alongside UC governance → users bypass UC.
- **Public IP on cluster nodes** with no SCC → security risk.
- **No PrivateLink on UI** → users hit public Databricks endpoints.

## 9. Capital One lens

Almost certainly:
- **Front-end + back-end PrivateLink** for both UI and SCC.
- **BYO VPC** in their network account, shared via RAM with workspace accounts.
- **Private mirrors** for PyPI/Maven (CodeArtifact or internal Artifactory).
- **AWS Network Firewall** in front of internet egress where needed.

## 10. Sanity check

1. Front-end vs back-end PrivateLink — what does each protect?
2. What is SCC, and what does it remove the need for?
3. Why might `/24` subnet limit you to ~125 cluster nodes?
4. What does NCC let serverless compute reach?
5. What classic-compute needs to pull from the internet, and how do you restrict it?

## 11. Cross-references

- **Module 8** — multi-VPC + PrivateLink
- **Module 6** — VPC + endpoints
- **Topic 02 Module 20** — Azure Databricks networking (the Azure contrast)

## Primary sources

- [`databricks_aws_privatelink.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/databricks_aws_privatelink.html)
- [`databricks_aws_byovpc.html`](../../research_inputs/04_aws_for_ai_ml/downloads/databricks_on_aws/databricks_aws_byovpc.html)
- Research report: [`11_databricks_on_aws.md`](../../research_inputs/04_aws_for_ai_ml/11_databricks_on_aws.md)
