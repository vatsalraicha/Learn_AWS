# Chapter 54 — Network Isolation for ML: VPC-only Studio, Private Endpoints

> **Goal of this chapter.** Take you from "I understand VPCs" (Chapter 7) to "I can design and defend a production no-egress ML platform on a whiteboard at a bank interview, and recognise the same architecture in a scenario stem on the exam." Network isolation is one of the highest-density topics in MLA-C01 Domain 4 because it is the architecture that *every* regulated AWS customer — banks, insurers, healthcare payers, defence, GovCloud — converges on, and the AWS exam team writes scenarios as thinly veiled versions of it. By the end of this chapter you should be able to write the seven API parameters (`EnableNetworkIsolation`, `VpcConfig`, `AppNetworkAccessType`, `EnableInterContainerTrafficEncryption`, `PrivateDnsEnabled`, plus the gateway-vs-interface distinction and the centralised-endpoint-VPC break-even) on a napkin in the right order, explain why each one exists, and trace a `pip install pandas` packet from a Jupyter cell in VPC-only Studio all the way to PyPI without it ever touching the public internet.

---

## 54.1 Why this chapter exists separately from Chapter 7

Chapter 7 taught you the **primitives**: VPCs, subnets, route tables, security groups, NACLs, internet gateways, NAT gateways, the gateway-vs-interface endpoint distinction, the AmazonProvidedDNS resolver at `.2`. That material is necessary, and we will not repeat it here. If any of those primitives feel hazy, stop now and re-read §7.4 through §7.9 — every sentence in this chapter depends on them.

This chapter is about the **production reference architecture that wraps those primitives into a coherent ML posture**: no container egress, no public internet, encrypted in transit between every hop, audited at every endpoint, signed by KMS at every byte. It is the architecture you will be asked to *design* in a real job and to *recognise* in a multiple-choice question. Where Chapter 7 told you what the primitives are, this chapter tells you which combination of them is the right answer when the scenario says *"a bank's security team requires that no ML traffic leave the AWS network at any point and that container code be incapable of reaching the internet even if compromised."*

There is also a historical reason this chapter exists. The 2019 Capital One breach (§54.2 below) made network isolation a board-level concern at every Fortune 500 financial institution within roughly twelve months, and AWS's customer engineering team responded by publishing the exact reference architecture this chapter walks through. Most of what is now considered "the default way to run regulated SageMaker" did not exist as a documented pattern before late 2019 — it was assembled in the years after, in direct response to one teenager with a misconfigured WAF.

---

## 54.2 The Capital One IMDSv1 SSRF — the canonical reason this chapter exists

In July 2019 a former AWS engineer, working from her apartment, exfiltrated 106 million customer records from a Capital One S3 bucket. The attack chain is the most important six-step sequence in the entire MLA-C01 security domain because **every control you build in the remainder of this chapter is, ultimately, mitigating one specific step of it**.

The chain, reconstructed from the Krebs analysis (krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/) and the later ACM systematic analysis (dl.acm.org/doi/full/10.1145/3546068):

1. **A misconfigured ModSecurity WAF on EC2** allowed server-side request forgery (SSRF). The WAF would happily relay an attacker-controlled URL to any backend the attacker named.
2. **The attacker pointed it at the EC2 Instance Metadata Service** — specifically at `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`. This is the IMDSv1 endpoint, which accepts an unauthenticated GET request and returns the temporary STS credentials for whatever IAM role is attached to the instance.
3. **The WAF returned the credentials in its HTTP response.** From the attacker's perspective, IMDS was just another internal endpoint, and the WAF was a credential-laundering machine.
4. **The IAM role had `s3:ListBucket` and `s3:GetObject` on `*`.** Not on specific buckets, not with a `aws:SourceVpc` condition, not with a `kms:ViaService` clause — on every S3 bucket in the account.
5. **The attacker used the stolen credentials from her own laptop**, anywhere in the world, to call `s3:ListBucket` followed by `s3:GetObject` on 106 million records of credit-card applicants' personal data.
6. **CloudTrail recorded the calls but no one was watching.** The exfiltration looked, on paper, like legitimate WAF activity. Detection happened months later via a tip on GitHub.

Five lessons matter for the ML engineer specifically, and they recur throughout the rest of this chapter:

**Lesson 1 — IMDSv1 is a credential-exposure surface that lives *inside the instance*, not at the VPC perimeter.** Network isolation at the VPC level (no IGW, no NAT) does *nothing* to mitigate IMDSv1 SSRF, because IMDS is `169.254.169.254` — a link-local address that does not traverse the VPC at all. The mitigation is **IMDSv2**, which requires a PUT-then-GET token handshake that no SSRF library will reflexively perform. SageMaker training, processing, and notebook instances default to IMDSv2 since 2023; **verify yours do** by checking the `InstanceMetadataOptions` on the launched instance description. The exam phrases this as: *"How do you prevent SSRF in a training script from exfiltrating the instance's temporary credentials?"* — answer is IMDSv2-only, full stop.

**Lesson 2 — A leaked execution role is a leaked execution role.** Your SageMaker training job's IAM role can be exfiltrated by any SSRF in your training script or any of its transitive Python dependencies. If you `pip install` an untrusted package and that package opens a socket to `169.254.169.254` from inside the training container, it can read the role's credentials (on an IMDSv1 instance) or attempt to (on an IMDSv2 instance — and fail). The defence is two-layered: (a) IMDSv2-only at the instance, (b) `EnableNetworkIsolation: true` on the training job so the container literally cannot reach the IMDS endpoint at all.

**Lesson 3 — Least privilege on execution roles is non-negotiable.** A SageMaker execution role with `s3:*` on `arn:aws:s3:::*` is a Capital One waiting to happen. Scope to specific bucket prefixes (`arn:aws:s3:::corp-ml-training-data/fraud-2026/*`), restrict by `aws:CalledVia` to specific services, and add `aws:SourceVpce` conditions so even a leaked credential cannot be used from outside your endpoint VPC. We covered execution-role scoping in Chapter 53; this chapter assumes you've done it.

**Lesson 4 — Defence in depth, not defence in single line.** Network isolation is *one* layer. The other layers are IAM least privilege, KMS key policies that deny non-VPCE callers, GuardDuty IMDS-exfiltration findings (specifically `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.InsideAWS` and `.OutsideAWS`), and CloudTrail Lake queries that look for `GetCallerIdentity` from unexpected source IPs. If any single layer fails, the others should still hold.

**Lesson 5 — For ML in 2026, the new SSRF surface is the prompt.** An LLM that can call tools (function-calling, agentic frameworks, Bedrock Agents) is essentially a *programmable* SSRF gadget — the prompt is the attacker-controlled URL and the tool-calling layer is the WAF that obediently relays it. Treat the tool-call egress like you treat a WAF: deny all by default, allow-list specific destinations at the network layer, and never give the LLM's execution role broader IAM than the narrowest tool needs. Chapter 56 returns to this in the GenAI security context.

The architecture in §54.3 below is the AWS-customer-engineering consensus answer to "how do we make sure a Capital One cannot happen to us through our ML platform." Every piece of it traces back to one or more of the five lessons.

---

## 54.3 The no-egress reference architecture — one diagram, in full

This is the architecture roughly every regulated AWS customer converges on for production ML. It is also the architecture the MLA-C01 exam keeps describing in scenario stems without ever naming it. Memorise the diagram; the rest of this chapter unpacks each piece.

```mermaid
flowchart TB
    subgraph TGW_HUB["Transit Gateway hub (network account)"]
        TGW1[(TGW)]
    end

    subgraph EP_VPC["Endpoint VPC (shared services account) — centralised PrivateLink"]
        direction TB
        IE_API[".sagemaker.api"]
        IE_RT[".sagemaker.runtime"]
        IE_FS[".sagemaker.featurestore-runtime"]
        IE_STU[".sagemaker.studio"]
        IE_NB[".sagemaker.notebook"]
        IE_ECR_API["ecr.api"]
        IE_ECR_DKR["ecr.dkr"]
        IE_KMS["kms"]
        IE_LOGS["logs"]
        IE_STS["sts"]
        IE_CA["codeartifact.api / .repositories"]
        IE_SM["secretsmanager"]
        PHZ[("Private hosted zones + R53 Resolver inbound EP")]
    end

    subgraph ML_VPC["ML Workload VPC (data-science account)"]
        direction TB
        subgraph AZ_a["AZ us-east-1a (isolated)"]
            S_TRAIN["SageMaker training ENIs<br/>EnableNetworkIsolation=true<br/>VpcConfig two-ENI model"]
            S_STUDIO["VpcOnly Studio ENIs<br/>AppNetworkAccessType=VpcOnly"]
            S_EP["SageMaker endpoint ENIs<br/>cross-account PrivateLink-reachable"]
        end
        subgraph AZ_b["AZ us-east-1b (isolated)"]
            S_MIRROR["…mirror of AZ-a…"]
        end
        GW_S3{{"S3 gateway endpoint<br/>FREE — prefix-list route"}}
        GW_DDB{{"DynamoDB gateway endpoint"}}
        CMK[("KMS CMK<br/>kms:ViaService gated")]
    end

    subgraph S3["S3 (regional service)"]
        TD["s3://co-ml-training-data"]
        MA["s3://co-ml-model-artifacts"]
    end

    ML_VPC <--> TGW1
    EP_VPC <--> TGW1
    S_TRAIN -. private DNS .-> IE_API
    S_TRAIN -. /443 .-> IE_ECR_API
    S_TRAIN -. /443 .-> IE_ECR_DKR
    S_TRAIN -. /443 .-> IE_LOGS
    S_TRAIN -. /443 .-> IE_KMS
    S_STUDIO -. /443 .-> IE_STU
    S_STUDIO -. /443 .-> IE_CA
    S_EP -. /443 .-> IE_RT
    S_TRAIN -. prefix-list .-> GW_S3
    GW_S3 --> TD
    GW_S3 --> MA
```

Notable properties, each of which the rest of the chapter expands:

- **No IGW. No NAT Gateway.** The ML VPC has *zero* route to `0.0.0.0/0`. The instances literally cannot ping `8.8.8.8`. Egress is not "restricted" — it is **impossible at the routing layer**. The CIDR has no path out.
- **Every AWS API call traverses an interface endpoint** in the centralised endpoint VPC, reached over Transit Gateway. PrivateLink is the only door.
- **S3 traffic uses the per-VPC gateway endpoint** (free, prefix-list route) — not the interface endpoint — because gateway endpoints are free and S3 throughput is the bottleneck of every training job. We'll cover the cost math (and the on-prem trap) in §54.10 and §54.13.
- **Container code itself** has `EnableNetworkIsolation: true`, so even if the model code is malicious or compromised, it has no socket to anywhere, including S3 (SageMaker downloads/uploads on its behalf via the execution role, outside the container). This is the strongest container-level posture SageMaker offers.
- **One KMS CMK per data domain**, with `kms:ViaService` condition pinning the CMK to S3 + SageMaker only.
- **Studio runs in `VpcOnly` mode**, so the Jupyter kernel ENIs live in the same isolated subnets — same SG, same KMS, same audit path.

The headline insight: this architecture is the answer to a class of question, not to one question. If a scenario stem mentions "no public internet," "container code must not have credentials," "regulated industry," "cross-account model invocation must not traverse the internet," "minimise endpoint cost across an org," or "training job stuck in Starting" — the relevant answer comes from §54.4–§54.14 below.

---

## 54.4 `EnableNetworkIsolation` — the most-misunderstood flag in SageMaker

### 54.4.1 What it actually does (verbatim from AWS)

From the AWS docs on internet-free mode (docs.aws.amazon.com/sagemaker/latest/dg/mkt-algo-model-internet-free.html):

> "When you enable network isolation, your training and inference containers can't make any outbound network calls to any service, including Amazon S3. **No AWS credentials are made available to the container runtime environment.** For training jobs with multiple instances, network inbound and outbound traffic is limited to communication between training container peers."

Read that twice. Two distinct guarantees are doing all the work:

1. **No container egress.** The container has no socket to anything — not S3, not the SageMaker API, not the internet, not your VPC, not even the instance metadata service. It cannot phone home. The docker run is `--network=none` or equivalent.
2. **No credentials.** SageMaker does not inject the execution-role's STS credentials into the container's environment. There is no `AWS_ACCESS_KEY_ID` to steal. There is no IMDS endpoint to query (and even if there were, it would be unreachable). A `boto3.client('s3')` inside the container will fail credential discovery.

This is the strongest container-level posture SageMaker offers. It is **the default expectation in regulated industries** and **required** for AWS Marketplace algorithms.

The Capital One link: notice that this flag closes *both* of the holes the breach exploited. The container has no network (mitigating SSRF that might try to reach IMDS), *and* the container has no credentials (so even a successful SSRF inside the container has nothing to exfiltrate). It is the closest thing SageMaker provides to a single-flag mitigation for the IMDSv1 SSRF class of attacks.

### 54.4.2 How SageMaker still gets data in and out

If the container can't talk to S3, how does training data get in?

> "SageMaker AI still handles all necessary Amazon S3 download and upload operations using your SageMaker AI execution role. This happens **apart from your training and inference containers**, ensuring that your training data and model artifacts are still accessible while maintaining container isolation."

The flow:

```mermaid
sequenceDiagram
    participant SM as SageMaker Control Plane
    participant Host as Training host VM
    participant Container as Training Container (isolated)
    participant S3
    SM->>S3: GetObject(training-data) [uses execution role]
    SM->>Host: Stage data at /opt/ml/input/data/
    SM->>Host: docker run --network=none container
    Note over Container: Container reads from local volume<br/>(no network at all)
    Container->>Host: writes /opt/ml/model/*
    SM->>S3: PutObject(model.tar.gz) [uses execution role]
```

Key implication: training-data S3 access is governed by the **execution role's identity policy + S3 bucket policy + KMS key policy**, *not* by anything the container does. This is why misconfigured KMS key policies are the most common cause of "my isolated training job is silently failing" — Chapter 55 will return to KMS lifecycle in detail.

### 54.4.3 Which APIs accept `EnableNetworkIsolation`

The flag is accepted on:

- `CreateTrainingJob` — the gold-standard use case
- `CreateHyperParameterTuningJob` — each child training job inherits it
- `CreateProcessingJob` — for SageMaker Processing
- `CreateModel` — used by `CreateEndpoint` and `CreateTransformJob` downstream
- `CreateTransformJob` (inherited from the model)
- `CreateAutoMLJob` / `CreateAutoMLJobV2` (with caveats — Autopilot uses managed containers, some of which don't support it)

The flag is **not** available on:

- Studio user-profile / app creation (Studio kernel apps run in the platform's own isolated network model, governed by `AppNetworkAccessType` instead — see §54.6)
- `CreateNotebookInstance` (classic notebooks have `DirectInternetAccess` instead, a coarser knob)

### 54.4.4 Containers that do *not* support network isolation

From the docs, three categories of managed SageMaker containers can't run with network isolation because they need outbound calls at runtime:

- **Chainer** managed container (legacy)
- **SageMaker AI Reinforcement Learning** containers (Coach, Ray) — they pull additional packages at job start
- A small set of **community-uploaded Marketplace algorithms** that bundle telemetry call-home logic

For these, the alternative is `VpcConfig` (the container *can* reach the network, but only your VPC + endpoints you've allow-listed) without `EnableNetworkIsolation`. See §54.5.

### 54.4.5 `EnableNetworkIsolation` + `VpcConfig` — they compose

You can — and in a regulated environment, you *should* — set **both** flags on the same training job:

```python
sm_client.create_training_job(
    TrainingJobName="fraud-train-2026-05-27",
    AlgorithmSpecification={...},
    RoleArn=execution_role_arn,
    EnableNetworkIsolation=True,                # container has no network at all
    EnableInterContainerTrafficEncryption=True, # distributed peers use IPsec
    VpcConfig={                                  # data-download path uses your VPC
        "Subnets": ["subnet-isolated-a", "subnet-isolated-b"],
        "SecurityGroupIds": ["sg-ml-training"],
    },
    OutputDataConfig={"KmsKeyId": cmk_arn, "S3OutputPath": "s3://..."},
    ResourceConfig={"VolumeKmsKeyId": cmk_arn, ...},
)
```

Per the AWS docs:

> "Network isolation can be used in conjunction with a VPC. In this scenario, the download and upload of customer data and model artifacts are routed through your VPC subnet. However, the training and inference containers themselves continue to be isolated from the network."

This is the gold pattern. The audit-friendly answer to "where did training data go?" is *"through your VPC's gateway endpoint to your S3 bucket, encrypted with your CMK, container had no way to leak it."* That sentence is the whole point of this chapter.

---

## 54.5 `VpcConfig` and the two-ENI cross-account model SageMaker injects

### 54.5.1 The parameter, verbatim

From the SageMaker training-VPC docs (docs.aws.amazon.com/sagemaker/latest/dg/train-vpc.html):

```json
"VpcConfig": {
    "Subnets": [
        "subnet-0123456789abcdef0",
        "subnet-0123456789abcdef1",
        "subnet-0123456789abcdef2"
    ],
    "SecurityGroupIds": [
        "sg-0123456789abcdef0"
    ]
}
```

Constraints:

- Up to **16 subnets** (must all be in the same VPC). Specifying multiple AZs is best practice for both ENI capacity and AZ failover.
- Up to **5 security groups** per ENI (standard EC2 limit).
- Subnets must be **default-tenancy** (no dedicated/host tenancy — a common gotcha for defence customers running on dedicated hardware).

### 54.5.2 How SageMaker lands in your VPC: cross-account ENIs

When `VpcConfig` is set, SageMaker does something subtle that the exam loves to test by drawing it on a diagram and asking which ENI you can see:

1. SageMaker provisions the EC2 instance(s) in a **SageMaker-owned AWS account** (you never see them in your `ec2:DescribeInstances`).
2. SageMaker creates an **ENI in *your* chosen subnet(s)** — these *do* show up in your `ec2:DescribeNetworkInterfaces`, owned by you, billed to you.
3. SageMaker performs a **cross-account attach** of the ENI to its managed instance. From the instance's perspective, your VPC is its only network.
4. Per the docs: *"The communication between the container and the resources in your VPC takes place securely within your VPC network."*

This is the **two-ENI model** people refer to:

- **ENI #1 (yours)**: lives in your subnet, has your SG, gets a private IP from your CIDR. Used for *all* container egress and ingress. Counts against your subnet's available IPs.
- **ENI #2 (SageMaker's)**: lives in SageMaker's internal account on the same instance. You never see it, never configure it. It is how SageMaker pulls status, streams logs, etc.

The implication that catches people out: **the training instance bill shows up in the SageMaker line item, not the EC2 line item**, but the ENI bill (and the subnet IP consumption) shows up in *your* VPC line item. Cost allocation tags on the SageMaker side are what surface this correctly in Cost Explorer.

### 54.5.3 IP-address sizing rules (verbatim from AWS)

> "Training instances that *don't use* an Elastic Fabric Adapter (EFA) should have at least 2 private IP addresses. Training instances that use an EFA should have at least 5 private IP addresses."

> "Your VPC subnets should have at least two private IP addresses for each instance in a training job."

In practice: for distributed training with EFA-enabled `p4d.24xlarge` × 8 nodes, that's 40 IPs just for one job. For a busy team running dozens of concurrent jobs + Studio + endpoints, you want `/20` (4,094 IPs) per AZ minimum — `/22` if you ever want to scale to organisation-wide hosting. The single most common production failure here is undersized subnets that exhaust IPs mid-distributed-training and produce the opaque error "could not provision ENI."

### 54.5.4 The two-rule security group pattern for distributed training

The training SG needs:

1. **Self-referencing inbound rule** on all TCP ports (or at minimum `0-65535`) from itself, so the training peers can talk to each other for AllReduce/MPI/NCCL.
2. **Outbound 443** to the SGs (or prefix lists) of every interface endpoint you use.

Verbatim from the docs:

> "In distributed training, you must allow communication between the different containers in the same training job. To do that, configure a rule for your security group that allows inbound connections between members of the same security group. **For EFA-enabled instances, ensure that both inbound and outbound connections allow all traffic from the same security group.**"

A minimal SG example:

```
sg-ml-training:
  Inbound:
    - Source: sg-ml-training (self), Protocol: All, Port: All
  Outbound:
    - Destination: sg-ml-training (self), Protocol: All, Port: All     # for EFA / IPsec
    - Destination: pl-s3 (prefix list), Protocol: TCP, Port: 443
    - Destination: sg-endpoints, Protocol: TCP, Port: 443
```

`sg-endpoints` is attached to all interface VPC endpoint ENIs and allows 443 inbound from `sg-ml-training`. SG-to-SG references mean you don't track IPs and the rules survive subnet changes.

---

## 54.6 Studio `AppNetworkAccessType` — the `VpcOnly` trap

### 54.6.1 The two values

`CreateDomain` and the Studio onboarding flow accept an `AppNetworkAccessType` argument with exactly two valid values:

| Value | Behavior |
|---|---|
| `PublicInternetOnly` (default) | All non-EFS traffic flows through a **SageMaker-managed VPC** with an internet gateway. Your VPC parameter is used **only** for EFS mounting. This is the convenient-but-wrong-for-prod setting that every quickstart picks. |
| `VpcOnly` | All Studio traffic — kernels, JupyterServer, EFS, internet calls — flows through **your VPC** via ENIs in **your subnets**. No SageMaker-managed internet at all. |

Verbatim from the Studio internet-access docs (docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html):

> "To stop SageMaker AI from providing internet access to your Studio notebooks, disable internet access by specifying the `VPC only` network access type. … As a result, you won't be able to run a Studio notebook unless: your VPC has an interface endpoint to the SageMaker API and runtime, or a NAT gateway with internet access; your security groups allow outbound connections."

### 54.6.2 The "pip install fails" trap — three industry fixes

`VpcOnly` is a one-line API change. The work to make it actually function is real, and the most common production failure is `pip install`. Teams that ship this carelessly find that every single one of the operations below silently breaks:

| Use case | What breaks | Required fix |
|---|---|---|
| `pip install scikit-learn==1.5.0` | PyPI unreachable | **CodeArtifact** repository with upstream `pypi-store`, plus interface endpoints `codeartifact.api` and `codeartifact.repositories` |
| `apt-get install` of OS packages | Amazon Linux repos blocked | Custom S3 endpoint policy that explicitly *allows* `packages.<region>.amazonaws.com` and `repo.<region>.amazonaws.com` (the AWS-provided OS mirror buckets) |
| `git clone https://github.com/org/repo` | Public github.com unreachable | CodeCommit, or GitHub via PrivateLink (GHE), or a Git proxy in a peered VPC |
| Custom kernel image | Docker Hub blocked | Build with CodeBuild, push to **ECR private repo** — ECR pulled via `ecr.api` + `ecr.dkr` interface endpoints + S3 gateway (ECR layers live in S3) |
| Hugging Face model download | huggingface.co blocked | Mirror models to S3 ahead of time; or use Bedrock-managed FMs |
| Conda packages | conda-forge blocked | Mirror to S3 + use `s3://` as a conda channel; or use CodeArtifact's conda support |

The three industry solutions, in increasing strictness:

**Fix A — CodeArtifact + PyPI upstream (most common, 80% of shops).** The native AWS answer. CodeArtifact's `repositories` interface endpoint terminates inside your VPC. Setting up an upstream connection to the AWS-managed `pypi-store` makes CodeArtifact a transparent caching proxy: the first `pip install` of a package fetches it through AWS's own connection to PyPI and stores it in your domain; subsequent installs are private. Pros: AWS-managed, no servers to run, IAM-aware. Cons: still requires a one-time outbound fetch on the AWS side (not in your VPC) which some FedRAMP High shops disallow.

**Fix B — Bandersnatch on ECS Fargate (full self-hosted mirror).** Bandersnatch (github.com/pypa/bandersnatch) is the canonical Python software for running a complete PyPI mirror. Deployed on ECS Fargate with an EFS or S3 backing store and a public-egress NAT *only on the mirror task*, the mirror is exposed inside the VPC via an internal ALB. `pip.conf` points to `https://pypi.internal.corp.com/simple/`. Pros: zero AWS-side egress; defence-org-friendly; full offline operation. Cons: ~3 TB storage, daily sync job, you own the patching, no IAM auth (you bolt on mTLS or Cognito at the ALB).

**Fix C — Custom ECR kernel images (strictest, used for production training).** For training jobs with `EnableNetworkIsolation=True`, the network stack is *disabled* entirely — even the Studio CodeArtifact setup is unreachable from inside the container. The only working pattern is to bake every dependency into the image at build time, push it to a private ECR repo with `imageTagMutability=IMMUTABLE`, and reference it as the `TrainingImage`:

```dockerfile
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.2.0-gpu-py310
ARG CODEARTIFACT_AUTH_TOKEN
RUN pip config set global.index-url \
    https://aws:${CODEARTIFACT_AUTH_TOKEN}@corp-ml-111122223333.d.codeartifact.us-east-1.amazonaws.com/pypi/corp-shared-python/simple/
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip config unset global.index-url   # wipe credentials from final layer
```

The training job then runs with `EnableNetworkIsolation=True` — it has **zero network access**, which is what regulators want to see.

### 54.6.3 The CodeArtifact 12-hour token TTL gotcha

CodeArtifact tokens expire after **12 hours by default** — and that 12h is also the maximum (`aws codeartifact get-authorization-token --duration-seconds 43200`). Long-running training jobs that `pip install` mid-run will fail at hour 12 with a 403 from the repository endpoint. Two production fixes:

1. **Front-load installs.** Bake everything into the container at build time — no installs in the training script. This is the recommended pattern for `EnableNetworkIsolation=true` jobs anyway, because there's no other choice.
2. **Lifecycle Configuration refresh.** For Studio, add an on-start LCC that runs every 6 hours via cron to re-fetch the token:
   ```bash
   echo "0 */6 * * * /home/sagemaker-user/.codeartifact-refresh.sh" | crontab -
   ```

> **⚠️ Exam alert.** A common scenario stem is *"A Studio user reports `pip install` worked yesterday but returns 403 today. Studio is in VpcOnly mode with CodeArtifact configured. What is the most likely cause?"* The answer is the **12-hour token TTL** — the user's `pip.conf` token has expired. The fix is `aws codeartifact login` to refresh; the systemic fix is a lifecycle-config cron. Do not pick "missing interface endpoint" or "security group misconfiguration" — those would have failed yesterday too.

### 54.6.4 The minimum endpoint set for `VpcOnly` Studio

From AWS (docs.aws.amazon.com/sagemaker/latest/dg/studio-notebooks-and-internet-access.html):

> "To remove internet access, create interface VPC endpoints (AWS PrivateLink) to allow Studio to access the following services with the corresponding service names. You must also associate the security groups for your VPC with these endpoints."

The full practical list for a `VpcOnly` Studio doing real ML work — sixteen services, plus the S3 gateway:

| # | Service | Endpoint name | Type | Why |
|---|---|---|---|---|
| 1 | SageMaker API | `com.amazonaws.<region>.sagemaker.api` | interface | All control-plane calls: `CreateTrainingJob`, `DescribeEndpoint`, etc. |
| 2 | SageMaker Runtime | `com.amazonaws.<region>.sagemaker.runtime` | interface | `InvokeEndpoint` from Studio |
| 3 | SageMaker FeatureStore Runtime | `com.amazonaws.<region>.sagemaker.featurestore-runtime` | interface | `PutRecord`, `GetRecord` for online feature store |
| 4 | SageMaker Studio | `com.amazonaws.<region>.sagemaker.studio` | interface | Studio websocket + UI traffic |
| 5 | SageMaker Notebook | `com.amazonaws.<region>.sagemaker.notebook` | interface | Classic notebook instances + JupyterServer for Studio |
| 6 | ECR API | `com.amazonaws.<region>.ecr.api` | interface | Authenticate to ECR |
| 7 | ECR Docker | `com.amazonaws.<region>.ecr.dkr` | interface | Pull container images |
| 8 | S3 | `com.amazonaws.<region>.s3` | **gateway** (preferred) | Data + model + ECR layer storage |
| 9 | CloudWatch Logs | `com.amazonaws.<region>.logs` | interface | Training/Studio logs |
| 10 | CloudWatch Monitoring | `com.amazonaws.<region>.monitoring` | interface | Metrics `PutMetricData` |
| 11 | STS | `com.amazonaws.<region>.sts` | interface | `AssumeRole` for cross-account, SDK |
| 12 | KMS | `com.amazonaws.<region>.kms` | interface | Encrypt/Decrypt with CMK |
| 13 | Secrets Manager | `com.amazonaws.<region>.secretsmanager` | interface | Pull DB creds, API keys |
| 14 | Service Catalog | `com.amazonaws.<region>.servicecatalog` | interface | SageMaker Projects, MLOps templates |
| 15 | CodeArtifact API | `com.amazonaws.<region>.codeartifact.api` | interface | PyPI/npm/conda mirror metadata |
| 16 | CodeArtifact Repos | `com.amazonaws.<region>.codeartifact.repositories` | interface | Actual package download |
| 17 | Glue (optional) | `com.amazonaws.<region>.glue` | interface | Wrangler crawls + jobs |
| 18 | Athena (optional) | `com.amazonaws.<region>.athena` | interface | Query Glue catalog |

That's 16–17 interface endpoints in the common case, 18+ if you do data wrangling. At $7.30/AZ/endpoint/month, 17 × 2 AZs × $7.30 ≈ **$248/month per VPC** just for endpoints — which is exactly why §54.13 (centralised endpoint VPC) matters at organisational scale.

### 54.6.5 FIPS-runtime endpoint-policy limitation

A critical exam detail buried in the docs (docs.aws.amazon.com/sagemaker/latest/dg/interface-vpc-endpoint.html):

> "VPC endpoint policies aren't supported for Federal Information Processing Standard (FIPS) SageMaker AI runtime endpoints for `InvokeEndpoint`."

If you are in a FedRAMP or GovCloud workflow and need FIPS 140-2 cipher suites for `InvokeEndpoint`, you use the FIPS variant of the runtime endpoint — but you **cannot attach a VPC endpoint policy to it**. You then have to enforce access at a different layer (IAM identity policy + endpoint resource policy + SG).

> **⚠️ Exam alert.** Watch for scenarios that combine "FIPS endpoint" with "endpoint policy restricting cross-account access." The endpoint-policy approach **does not work on FIPS runtime endpoints**. The correct mitigation is identity-based: SCP + permission boundary + execution-role conditions with `aws:SourceVpce`. A distractor that says "attach an endpoint policy to the FIPS endpoint" is wrong by construction.

---

## 54.7 `EnableInterContainerTrafficEncryption` — distributed training over IPsec

### 54.7.1 What it does

For distributed training, peers communicate over the VPC for gradient AllReduce and parameter-server traffic. By default this is **plaintext TCP** inside the VPC (which AWS argues is "encrypted at the physical layer by Nitro," but compliance teams want application-layer crypto too).

Setting `EnableInterContainerTrafficEncryption: true` on `CreateTrainingJob`, `CreateProcessingJob`, or `CreateHyperParameterTuningJob` forces SageMaker to **establish IPsec tunnels between all training peers** before training starts. AllReduce, MPI, and NCCL traffic then flows over ESP-encapsulated IPsec.

### 54.7.2 The two costs

1. **Latency / throughput overhead.** IPsec adds roughly 5–15% overhead on distributed training throughput (varies by instance type, message size, and how many ranks are participating). For tightly coupled GPU clusters running NCCL AllReduce at line rate, this is non-trivial. AWS recommends disabling it for performance-critical short-duration training where compliance allows.
2. **Security-group rules for IPsec protocols.** This is the bit candidates miss on the exam. IPsec uses two protocols that are *not* TCP or UDP in the conventional sense:
   - **UDP port 500** (IKE — Internet Key Exchange — for tunnel setup)
   - **IP protocol 50** (ESP — Encapsulating Security Payload — the actual encrypted data plane)

If your training SG only allows TCP and UDP 1024-65535 self-referencing, IPsec will fail at tunnel setup with an opaque error that looks like a generic distributed-training failure. The recipe is:

```
sg-ml-training (additions for ICTE):
  Inbound:
    - Source: sg-ml-training (self), Protocol: UDP, Port: 500      # IKE
    - Source: sg-ml-training (self), Protocol: 50 (ESP), Port: -   # tunnel data
  Outbound: mirror
```

In practice, teams set the SG to **"All traffic from self"** to cover IKE, ESP, NCCL ports, and EFA in one rule. The exam may still test that *both* UDP/500 and IP/50 are required (not just TCP/443) — pick the answer that lists both.

### 54.7.3 When you must enable it

- **Almost always for regulated industries.** HIPAA, PCI-DSS, and SOC 2 mandated controls usually require application-layer encryption between any pair of compute nodes processing regulated data.
- **For all SageMaker Distributed Training on multiple instances** when policy mandates in-transit encryption.
- **Mandatory** when the training algorithm or dataset is itself classified at a higher tier than the VPC default (defence and intelligence-community workloads).

### 54.7.4 Algorithms that don't support it

Same caveat as `EnableNetworkIsolation`: a small set of legacy managed containers (older Chainer, certain RL agents) don't support inter-container encryption. The current PyTorch, TensorFlow, MXNet, and XGBoost managed containers all support it.

---

## 54.8 The five SageMaker interface endpoint names — memorise these

These are the *exact* service names you need to recognise on the exam. They follow the pattern `com.amazonaws.<region>.<name>`. The five SageMaker-specific ones:

| Endpoint suffix | Service it connects to | When you need it |
|---|---|---|
| `sagemaker.api` | SageMaker control plane (all `Create*`, `Describe*`, `Delete*` APIs) | Always — anyone calling `boto3.client('sagemaker')` from inside a VPC |
| `sagemaker.runtime` | SageMaker hosted-endpoint `InvokeEndpoint` data plane | Production inference clients in your VPC |
| `sagemaker.featurestore-runtime` | Feature Store online-store `PutRecord`/`GetRecord` | Real-time feature lookup for inference |
| `sagemaker.notebook` | Notebook-instance proxy (and JupyterServer for Studio) | Classic notebook instances; Studio in `VpcOnly` |
| `sagemaker.studio` | SageMaker Studio app traffic (websocket, UI) | Studio in `VpcOnly` |

Memorise the five. The exam writes distractors that look like real endpoint names but don't exist (e.g., `sagemaker.training` is *not* a real endpoint — training control plane is under `sagemaker.api`; data download goes through S3 gateway).

Sub-resources for FeatureStore have a special hostname template (verbatim from docs):

```
{VPC_Endpoint_ID.api}.featurestore-runtime.sagemaker.{region}.vpce.amazonaws.com
```

### 54.8.1 The "presigned notebook URL" carve-out (verbatim)

> "If you use the `AuthorizedUrl` from the `CreatePresignedNotebookInstanceUrl` command, your traffic will go over the public internet. You can't only use a VPC endpoint to access the presigned URL, the request must go through the internet gateway."

This is a real production gotcha and a great exam distractor. Even in a fully locked-down VPC, classic-notebook presigned URLs require public-internet routing for the URL fetch (the *resulting* notebook session is private, but the URL handshake is not). Studio's pre-signed app URLs have a similar pattern. Plan for browser routing via corporate VPN/proxy to the public AWS endpoint.

---

## 54.9 VPC endpoint policies — restricting cross-account exfil

### 54.9.1 What an endpoint policy is

A **VPC endpoint policy** is a JSON resource policy attached to the endpoint itself. It is evaluated *in addition to* identity-based policies. It is the place to enforce: *"requests through this endpoint can only target accounts or resources I bless."*

The default endpoint policy is wide-open: `"Action": "*", "Principal": "*", "Resource": "*"`. In a regulated environment you replace this immediately.

### 54.9.2 The cross-account exfil pattern it blocks

Without an endpoint policy, a malicious actor with credentials to an S3 bucket in *another* AWS account can use *your* VPC's S3 gateway endpoint to exfiltrate data: their stolen creds + your endpoint = network-laundered exfiltration that appears in your VPC Flow Logs as a "VPC-internal" request, indistinguishable from legitimate traffic. The fix is a `aws:PrincipalOrgID` or `aws:ResourceOrgID` condition, or an explicit account allow-list, in the endpoint policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOnlyOurOrg",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-1234567890",
          "aws:ResourceOrgID": "o-1234567890"
        }
      }
    }
  ]
}
```

### 54.9.3 SageMaker-specific endpoint policy example (verbatim)

From the docs:

```json
{
  "Statement": [
    {
      "Action": "sagemaker:InvokeEndpoint",
      "Effect": "Allow",
      "Resource": "arn:aws:sagemaker:us-west-2:123456789012:endpoint/myEndpoint",
      "Principal": "*"
    }
  ]
}
```

> "In this example, the following are denied: Other SageMaker API actions, such as `sagemaker:CreateEndpoint` and `sagemaker:CreateTrainingJob`. Invoking SageMaker AI hosted endpoints other than `myEndpoint`."

Use case: a tightly scoped endpoint VPC where the only thing the VPC's clients should ever do is invoke one specific production model. Anyone trying to call `CreateTrainingJob` through this endpoint is silently denied at the network layer.

### 54.9.4 Layered defence

The endpoint policy is a *cap*. It does not grant access; identity-based and resource-based policies still need to allow. Use it as the **last line** before the network layer: "even if IAM gets misconfigured, this endpoint will not pass cross-org traffic."

---

## 54.10 PrivateLink for cross-account inference

A real production scenario: the **fraud team in Account A** owns a model. The **customer-facing app in Account B** needs to invoke it. Public internet is not an option (regulated). VPC peering doesn't scale beyond ~50 peerings. PrivateLink makes B's clients reach A's endpoint as if it were a local service.

### 54.10.1 The provider/consumer model

```mermaid
flowchart LR
    subgraph A["Account A — model owner"]
        E[SageMaker endpoint]
        NLB["NLB or<br/>SageMaker Runtime"]
        ES["Endpoint service<br/>com.amazonaws.vpce.<br/>us-east-1.vpce-svc-XYZ"]
    end
    subgraph B["Account B — model consumer"]
        Client[Inference client app]
        IE["Interface endpoint<br/>connected to A's service"]
    end
    Client --> IE
    IE -. PrivateLink .-> ES
    ES --> NLB
    NLB --> E
```

### 54.10.2 Two patterns to expose

**Pattern A — SageMaker Runtime direct (simpler).** Account B creates its own `com.amazonaws.<region>.sagemaker.runtime` interface endpoint. As long as A's `sagemaker:InvokeEndpoint` identity policy and the endpoint's resource policy allow B's role to call A's endpoint by ARN, traffic from B → SageMaker Runtime → A's endpoint flows entirely over the AWS backbone via PrivateLink. **B never touches A's VPC.** This is the default pattern for almost every cross-account SageMaker inference deployment and it does *not* require a VPC endpoint service in Account A. The exam tends to write this as the right answer when the scenario explicitly mentions a SageMaker endpoint as the target.

**Pattern B — Custom VPC Endpoint Service (Lambda/ECS+NLB proxy).** Account A puts a Network Load Balancer in front of a custom service — typically a fronting Lambda, an ECS task, or an API Gateway — and exposes it as a **VPC endpoint service** with a name like `com.amazonaws.vpce.<region>.vpce-svc-<id>`. Account B then creates an interface endpoint *to that service name*. A whitelists B's principals at the endpoint-service ACL. The proxy layer is necessary because **SageMaker Runtime is a service endpoint, not a private NLB target** — you cannot directly back a VPC Endpoint Service with `sagemaker-runtime`. The proxy is also where you can:

- Strip caller IAM and attach producer-side IAM with least-privilege per consumer
- Apply WAF, rate limiting, and per-tenant token validation
- Multiplex multiple SageMaker endpoints behind one PrivateLink service (URL routing)

The exam loves Pattern A as the "right" answer for cross-account SageMaker inference. Pattern B shows up when the scenario says "we want to expose a non-SageMaker service" or "we need to multiplex multiple model endpoints behind one PrivateLink service."

### 54.10.3 Cross-account model deploy — the role/KMS dance

When Account B *deploys* a model whose artefacts live in Account A's S3 bucket, five things must align:

1. B's deployment role needs `s3:GetObject` on `arn:aws:s3:::A-model-bucket/path/*`.
2. A's bucket policy must allow B's role.
3. A's CMK key policy must grant `kms:Decrypt` to B's role (key policy alone is necessary and sufficient for cross-account KMS — this is the one place the resource-based-policy shortcut covered in Chapter 5 does *not* apply).
4. B's deployment role needs `iam:PassRole` on B's execution role.
5. B's execution role needs `kms:Decrypt` on A's CMK and `s3:GetObject` on A's bucket — duplicated trust at both deploy time and runtime.

Miss any one of these and the failure is opaque (the SageMaker error message just says "model artefact unavailable"). This is one of the most fertile sources of MLA-C01 multi-step troubleshooting questions, and the answer almost always comes down to "trust at both endpoints of the cross-account hop."

---

## 54.11 Multi-account network architecture — Transit Gateway + RAM

### 54.11.1 The motivation

A real enterprise has dozens of AWS accounts: ML-dev, ML-prod, data-lake, security, audit, shared-services, observability, payment, fraud, ad-targeting, and so on. Putting interface endpoints in **every** VPC is wasteful — 17 endpoints × 3 AZs × ~$7.30/mo = roughly $373/month per VPC just in idle endpoint fees, before any data processing.

The pattern that converges in industry:

```mermaid
flowchart TB
    subgraph Net["Network account"]
        TGW[Transit Gateway]
        EP_VPC["Endpoint VPC<br/>has all 17 interface endpoints"]
        TGW --- EP_VPC
    end
    subgraph DS["Data-science account"]
        DS_VPC["ML workload VPC<br/>NO interface endpoints<br/>NO NAT<br/>S3 gateway endpoint local"]
        DS_VPC --- TGW
    end
    subgraph Prod["ML-prod account"]
        Prod_VPC["ML prod VPC<br/>NO interface endpoints<br/>NO NAT"]
        Prod_VPC --- TGW
    end
    subgraph Lake["Data-lake account"]
        DL_VPC[Data lake VPC]
        DL_VPC --- TGW
    end
```

- All workload VPCs route to the Endpoint VPC over Transit Gateway.
- The Endpoint VPC hosts one copy of each interface endpoint.
- DNS is shared via **Route 53 Resolver inbound endpoints** + **private hosted zones** + **resolver rules** propagated by **AWS RAM** (Resource Access Manager). Workload accounts resolve `api.sagemaker.us-east-1.amazonaws.com` to the central endpoint VPC's private IPs.

### 54.11.2 What RAM shares

- **Transit Gateway attachments** (so any account can attach a VPC to the TGW).
- **Route 53 Resolver rules** (so any account inherits private DNS overrides).
- **Subnets** (less common — most teams keep subnets per-account but share the TGW).

### 54.11.3 The break-even formula

The economics question the exam asks in scenario form: *"at what scale does the centralised endpoint VPC pay back?"* The answer comes from a closed-form formula. For `E` endpoint types and `N` VPCs, centralisation wins when:

```
N > (7.30 · E + 36.50) / (7.30 · E - 36.50)
```

Where $7.30 is the monthly cost per interface endpoint per AZ, and $36.50 is the monthly cost of a TGW attachment. Tabulated:

| E (endpoint types) | Break-even N (VPCs) |
|---|---|
| 3–5 | Never (TGW attachment cost dominates) |
| 6 | 11 VPCs |
| 7 | **7 VPCs** ← the rule of thumb |
| 8 | 5 VPCs |
| 10 | 3 VPCs |
| 15+ | 2 VPCs |

**Rule of thumb for ML platform teams: centralisation breaks even around 7 VPCs.** A typical SageMaker-using enterprise has 15–30 endpoint types (every entry in §54.6.4 plus EC2 Messages, SSM, SSM Messages, Lambda, EventBridge, SNS, SQS, Athena, Glue, Redshift Data API, etc.), so centralisation pays back at 2–3 VPCs.

### 54.11.4 Real-world ROI — the AllCloud $119K/yr saving

AllCloud published a case study (allcloud.io/go/reduce-costs-and-boost-security-with-centralized-vpc-shared-endpoints-model/) where a customer dropped VPC endpoint spend from **$10,655/month to ~$745/month — $119,000/year saved** — by consolidating endpoints in a shared services VPC and using TGW. That figure is canonical in AWS networking forums and is a likely "headline" answer in a cost-optimisation question.

### 54.11.5 The Route 53 PHZ trick

The hidden gotcha at multi-account scale: when consumer VPCs sit on the *spoke* side of TGW and want to resolve `api.sagemaker.us-east-1.amazonaws.com` to a centralised endpoint, **AWS-managed private DNS will not work** — the managed PHZ is associated only with the hub VPC where the endpoint was created.

The fix (aws.amazon.com/blogs/networking-and-content-delivery/centralize-access-using-vpc-interface-endpoints/):

1. Create the interface endpoint in the hub VPC with `--no-private-dns-enabled`.
2. Manually create a Route 53 private hosted zone named `api.sagemaker.us-east-1.amazonaws.com`.
3. Add an ALIAS A record `api.sagemaker.us-east-1.amazonaws.com` → the regional VPCE DNS name.
4. Associate the PHZ with every spoke VPC (cross-account if needed via PHZ-association authorisation).

Now spoke-VPC workloads resolve the standard SageMaker DNS name to the central endpoint's private IP and route over TGW.

### 54.11.6 S3 stays local

S3 gateway endpoints **cannot be shared across VPCs**. So each workload VPC keeps **its own S3 gateway endpoint** (free) and ideally its own KMS endpoint locally too if traffic volume is high. The shared endpoint VPC carries the lower-volume control plane (SageMaker API, ECR API, etc.). This split — control plane centralised, S3 local — is the configuration the exam asks about when the question is "minimise endpoint cost without losing performance for training data."

---

## 54.12 Hybrid connectivity — DX, VPN, and the gateway-endpoint trap

### 54.12.1 The two hybrid pipes

- **Site-to-Site VPN**: IPsec tunnel between your on-prem VPN device and an AWS Virtual Private Gateway (VGW) or Transit Gateway. Goes over the public internet (encrypted). Easy to set up, lower throughput, latency-sensitive.
- **Direct Connect (DX)**: dedicated physical connection from your data centre to AWS via a partner facility. Higher bandwidth (1, 10, 100 Gbps), predictable latency, not over the public internet. Add a **MACsec** option for layer-2 encryption.

Both terminate at a VGW or TGW. From the AWS docs: *"To call the SageMaker API and SageMaker AI Runtime through your VPC, you have to connect from an instance that is inside the VPC or connect your private network to your VPC by using an AWS Virtual Private Network (Site-to-Site VPN) or Direct Connect."*

### 54.12.2 The on-prem-to-S3 trap

**S3 gateway endpoints do NOT work from on-prem.** This is the single most-tested network-isolation gotcha on the MLA-C01.

A gateway endpoint installs a *prefix-list route* into your VPC route tables. From on-prem, you're not in those route tables. So:

| Source | Reaches S3 via |
|---|---|
| VPC instance | **Gateway endpoint** (free, prefix list) — preferred |
| VPC instance via NAT | Public S3 endpoint over internet — wasteful |
| On-prem via DX/VPN → VGW → VPC | **NOT the gateway endpoint.** Either traffic exits your VPC back to public S3, or you must use an **interface endpoint for S3** in the VPC. |

The fix: deploy an **S3 interface endpoint** (a 2021 feature) alongside the gateway endpoint. On-prem traffic over DX/VPN can resolve `bucket.s3.region.amazonaws.com` to the interface endpoint's private IPs (via private hosted zone or resolver rules) and reach S3 privately. The gateway endpoint stays in place for in-VPC traffic (free) and the interface endpoint handles only the on-prem case.

> **⚠️ Exam alert.** *"Data scientists at the on-prem office need to read training data from S3 over Direct Connect without internet exposure. The team has a gateway endpoint already. What additional configuration is needed?"* → **Create an S3 interface endpoint** (and Resolver rules for DNS). The gateway endpoint does not serve on-prem traffic, period. If an answer says "the gateway endpoint will route the DX traffic," it is wrong by construction. This is the single highest-probability exam question in this chapter.

> **⚠️ Exam alert.** The corollary trap: **never replace the in-VPC S3 gateway endpoint with the interface endpoint** to "simplify." Interface endpoints charge $0.01/GB data-processing; gateway endpoints are free. A 200 GB training job through an S3 interface endpoint costs $2 per job; through the gateway endpoint it costs $0. Add the interface endpoint *alongside* the gateway endpoint, exclusively for on-prem traffic.

---

## 54.13 The cost math — interface vs gateway vs NAT

### 54.13.1 Per-component pricing (us-east-1, 2025)

| Resource | Hourly | Monthly (730h) | Data processing |
|---|---|---|---|
| Interface endpoint (per AZ) | $0.01/hr | **$7.30/AZ/month** | $0.01/GB |
| Gateway endpoint (S3, DynamoDB) | **$0 (free)** | $0 | $0 |
| NAT Gateway (per AZ) | $0.045/hr | **$32.85/AZ/month** | $0.045/GB |
| Transit Gateway attachment | $0.05/hr | **$36.50/month** | $0.02/GB |

Three rules drop out of this table:

1. **Gateway endpoints are free → use them whenever possible.** S3 and DynamoDB are the only two services with gateway endpoints. **Always** install the S3 gateway endpoint — its data-processing cost is zero. Even at 1 TB/day training data, S3 gateway is free.
2. **Interface endpoints replace NAT GW if you have ≥ 4 endpoints per AZ.** A NAT Gateway costs $32.85/AZ/month plus $0.045/GB data; an interface endpoint is $7.30/AZ/month plus $0.01/GB. Past 4 endpoints per AZ, dedicated interface endpoints + zero NAT is cheaper *and* more secure (no general egress). This is the algebra behind every "remove the NAT GW" project at every regulated shop.
3. **Centralise at organisational scale.** Past ~7 workload VPCs, the centralised endpoint VPC pattern (§54.11) saves thousands per month. Below that, per-VPC endpoints are simpler operationally.

### 54.13.2 The hidden cost: data processing

Interface-endpoint data processing is $0.01/GB. A training job streaming 200 GB from S3 *through an S3 interface endpoint* costs $2. The same job through the **S3 gateway endpoint** is $0. This is the reason every architecture in §54.3 keeps the S3 gateway endpoint local to every workload VPC and never centralises it.

### 54.13.3 Cost-attribution discipline

- Tag endpoints with `Owner=Network`, `CostCenter=Shared` so the right team sees the bill in Cost Explorer.
- Use **VPC Flow Logs** + Athena to attribute data-processing fees to the workload VPC of origin if needed (for chargeback).
- AWS Cost Explorer's "Endpoint hours" line item rolls up by account; for shared endpoints, split via internal chargeback.

---

## 54.14 Defence at the perimeter — Network Firewall, Suricata, and WAF

### 54.14.1 AWS Network Firewall + Suricata for ML egress control

When an ML workload *must* have some controlled egress (e.g., to pull from a specific external dataset URL, or to call a third-party API for enrichment), the toolkit is **AWS Network Firewall** — a managed Suricata implementation that supports domain-name allow-listing via TLS SNI inspection and HTTP Host headers.

Deployment pattern — a "firewall VPC" sits between application VPCs and the internet:

```
[Spoke VPC: Studio] -- TGW --> [Firewall VPC: NF endpoints] -- IGW --> Internet
```

Network Firewall is implemented as Gateway Load Balancer-fronted firewall endpoints, one per AZ. Routing is asymmetric: spoke route tables send `0.0.0.0/0` to the TGW; the firewall VPC's TGW attachment route table sends `0.0.0.0/0` to the NF endpoint; the NF endpoint sends inspected traffic to the IGW.

Two rule-group modes are common for ML egress:

**Mode A — Domain allow-list (simplest).** NF's stateful domain list with default-deny:

```
Allowed domains:
  .pypi.org
  .pythonhosted.org
  .docker.io
  .github.com
  .githubusercontent.com
  .huggingface.co
Action: PASS on match, DROP on no-match
```

This handles 80% of the data-science egress need and is configurable in the console with no Suricata knowledge.

**Mode B — Custom Suricata stateful rules (FedRAMP / sensitive workloads).** Explicit TLS SNI checks with custom signatures:

```
# Allow only HTTPS to PyPI, explicit SNI check
pass tls $HOME_NET any -> $EXTERNAL_NET 443 (
  msg:"Allow PyPI";
  tls.sni; content:"pypi.org"; nocase; endswith;
  flow:established,to_server;
  sid:1000001; rev:1;
)

# Block known LLM exfiltration paths from training VPC
drop tls $TRAINING_NET any -> $EXTERNAL_NET 443 (
  msg:"Block LLM egress from training";
  tls.sni; content:"api.openai.com"; nocase;
  flow:established,to_server;
  sid:1000003; rev:1;
)

# Default-deny for everything else
drop tls $HOME_NET any -> $EXTERNAL_NET any (
  msg:"Default deny TLS";
  flow:established,to_server;
  sid:1099999; rev:1;
)
```

NF writes flow logs and alert logs to S3, Firehose, or CloudWatch. The standard SIEM pattern: stream alerts to Splunk or Security Lake, build a saved query for "any DROP from SageMaker subnet CIDRs," and alert on >5/min as an "ML environment trying to reach the internet" signal.

### 54.14.2 WAF for SageMaker endpoints behind API Gateway or ALB

`InvokeEndpoint` itself is not directly behind WAF — it's a SageMaker-managed endpoint and you do not own its DNS. The pattern is to front it:

```
client → CloudFront → WAF web ACL → API Gateway / ALB → Lambda → SageMaker Runtime InvokeEndpoint
```

WAF protects the *public-facing* tier (API Gateway / ALB). The Lambda has VPC access and reaches SageMaker over the `sagemaker.runtime` interface endpoint. This is the "ML behind a managed front door" pattern that is standard for customer-facing inference, and it is also the only way to do mTLS to a model endpoint (since ALB now supports mTLS termination).

WAF rule groups typical for ML endpoints:

- **Rate limiting** per IP or per token — stop credential-stuffing of an inference endpoint
- **Geo restrictions** — only serve customers from approved countries
- **AWS Managed Rules** — Bot Control, OWASP Core Rule Set
- **Body inspection** for prompt-injection signatures (LLM inference behind Bedrock or self-hosted endpoints)

---

## 54.15 DNS resolution layers — the three places things go wrong

### 54.15.1 The three layers of VPC DNS

```mermaid
flowchart TB
    A["1. VPC-wide DNS toggles<br/>enableDnsSupport=true<br/>enableDnsHostnames=true"] --> B
    B["2. AmazonProvidedDNS at .2<br/>(VPC's local Route 53 Resolver)"] --> C
    C["3. Private hosted zones (PHZs)<br/>override public hostnames<br/>created by interface endpoints w/ PrivateDNS"]
    D["Route 53 Resolver inbound endpoint<br/>on-prem queries AWS-private names"] -. for hybrid .-> B
    E["Route 53 Resolver outbound endpoint<br/>+ forwarding rules<br/>(shared via RAM)"] -. for hybrid .-> B
    F["VPC peering / TGW spoke"] -. PHZ-association needed .-> C
```

1. **VPC-wide DNS toggles**: `enableDnsSupport` (default on) and `enableDnsHostnames` (off by default). **Both must be on** for VPC endpoints' private DNS to work. If you forget the second one, instances get IPs but no PTR records and many SDK clients fail credential discovery.
2. **AmazonProvidedDNS at the `.2` address** in every subnet (the VPC's local Route 53 Resolver). This is what every EC2 and SageMaker ENI uses by default.
3. **Private hosted zones (PHZs)** attached to one or more VPCs. Override public hostnames with private records. Created automatically by interface endpoints with PrivateDNS enabled.

### 54.15.2 The `Enable PrivateDNS` toggle and what it actually does

Every interface endpoint has two DNS names:

- The **endpoint-specific name**: `vpce-0abc123.api.sagemaker.us-east-1.vpce.amazonaws.com` — always works from anywhere with route to the endpoint.
- The **standard public service hostname**: `api.sagemaker.us-east-1.amazonaws.com` — by default resolves to AWS's public IPs.

When you check **"Enable Private DNS"** on the endpoint, AWS creates a private hosted zone in your VPC that *overrides* the public hostname to resolve to the endpoint's private IPs. This means existing code using `boto3.client('sagemaker')` transparently uses the endpoint with **no SDK changes**.

Requirements (subtle, exam-worthy):

- VPC must have `enableDnsSupport=true` and `enableDnsHostnames=true`.
- For SageMaker Runtime specifically, **the interface endpoint must be activated in the same AZ as the client** for private DNS resolution to work (verbatim AWS warning).

If you didn't enable private DNS, you must explicitly point boto3 at the endpoint URL:

```python
boto3.client('sagemaker-runtime',
             endpoint_url=f'https://{vpce_id}.runtime.sagemaker.us-east-1.vpce.amazonaws.com')
```

### 54.15.3 The Studio "kernel never starts" DNS failure

Symptom: Studio launches but the JupyterLab kernel hangs forever. Cause: Studio's container makes API calls to `api.sagemaker.<region>.amazonaws.com` for kernel lifecycle. If your VPC's DHCP option set uses a custom DNS server (e.g., on-prem Active Directory DNS) and that server doesn't forward AWS-internal DNS queries back to the VPC `.2` resolver, the API endpoint resolves to a public IP and times out behind no-NAT routing.

Fix: in DHCP options, prepend `AmazonProvidedDNS` or use Route 53 Resolver outbound forwarding to on-prem *only* for your corporate zones (e.g., `corp.local`), leaving AWS zones to the VPC resolver. See repost.aws/knowledge-center/sagemaker-studio-kernel-gateway-connect for the official troubleshooting.

### 54.15.4 Common DNS error → root cause cheat sheet

| Error | Root cause | Fix |
|---|---|---|
| `Could not connect to api.sagemaker...` | Private DNS not enabled on endpoint | `modify-vpc-endpoint --private-dns-enabled` |
| `Name or service not known` for `*.amazonaws.com` | VPC DNS support off | `enableDnsSupport=true` |
| DNS resolves to public IP in private subnet | DHCP option set points to custom DNS that doesn't forward | Fix DHCP options or use Resolver rules |
| Studio Apps stuck in `Pending` | Studio subnet in wrong AZ vs endpoint AZ | Put endpoint in *every* Studio AZ |
| Resolves OK but connect times out | SG on endpoint blocks 443 from Studio SG | Allow 443 from Studio SG to endpoint SG |

---

## 54.16 The troubleshooting table — the failures you will actually see

The most common failures in a no-egress VPC-only Studio + isolated training architecture. Tape this inside the cover of your notebook:

| Symptom | Likely cause | Fix |
|---|---|---|
| Training job stuck in "Starting" → fails with `InternalServerError` | SageMaker can't pull container image — no `ecr.api`+`ecr.dkr` endpoints, OR SG blocks 443 outbound to endpoint SG | Add ECR endpoints; SG outbound 443 → endpoint SG; verify S3 gateway endpoint is on the right route table (ECR layers live in S3) |
| `pip install` fails: "Could not find a version that satisfies the requirement" | No PyPI access; no CodeArtifact endpoint; pip not configured to use CodeArtifact | Create CodeArtifact domain + `pypi-store` upstream repo; create `codeartifact.api`+`codeartifact.repositories` endpoints; set `pip config set global.index-url` in lifecycle config |
| `pip install` worked yesterday, 403 today | **CodeArtifact 12h token TTL expired** | Re-run `aws codeartifact login`; add cron to refresh every 6h |
| Training reads training-data succeeds, fails to write model artefact | KMS `kms:Decrypt` granted but not `kms:GenerateDataKey` for the bucket CMK | Add `kms:GenerateDataKey` on the output-bucket CMK to the execution role |
| `EnableNetworkIsolation=true` + container uses `boto3` | No credentials in container — boto3 fails credential discovery | Use SageMaker's built-in `print()` → CloudWatch (handled by SageMaker outside the container) |
| Studio kernel won't start ("InService" timeout) | VpcOnly mode but no SG self-reference on Jupyter↔Kernel websocket ports | Add inbound TCP `8192-65535` from same SG |
| Studio works but `git clone` fails for github.com | Expected — no public internet | Use CodeCommit; or GHE via PrivateLink; or pre-clone to S3 and `aws s3 sync` |
| Endpoint deployment succeeds but `InvokeEndpoint` from another account fails | Cross-account: missing `sagemaker:InvokeEndpoint` on consumer role OR consumer VPC has no `sagemaker.runtime` endpoint | Add IAM permission; create runtime endpoint in consumer VPC |
| Distributed training works without encryption, fails with `EnableInterContainerTrafficEncryption=true` | SG missing UDP/500 (IKE) and IP/50 (ESP) self-ref rules | Add `All traffic from self` to SG |
| `Describe*` calls work from VPC, but `InvokeEndpoint` resolves to public IP | `sagemaker.runtime` endpoint not in same AZ as client | Activate endpoint in *all* AZs the clients live in |
| Application Auto Scaling on endpoint doesn't scale | The endpoint's CloudWatch metrics need `monitoring` endpoint to publish | Verify `monitoring` (CloudWatch) endpoint exists |
| Training fails after `EnableNetworkIsolation=true` with "Could not download X" | Container is trying to phone home (license check, telemetry) | Pick a container that supports network isolation, or run with `VpcConfig` only |
| Studio in `VpcOnly` but DNS resolves SageMaker API to public IP | VPC `enableDnsHostnames=false` OR DHCP options point to on-prem DNS without forwarding | Set both VPC DNS toggles; fix DHCP options |

---

## 54.17 Six rapid-fire scenario-to-answer mappings

The compressed version of the chapter. Memorise these six; they account for roughly two-thirds of the network-isolation questions on the MLA-C01.

1. **"Bank requires no container internet egress AND container code must have no AWS credentials."** → `EnableNetworkIsolation=true`. Add `VpcConfig` for the data path; SageMaker performs S3 I/O outside the container.

2. **"Studio users can't `pip install`."** → `VpcOnly` Studio with no PyPI mirror. Fix: CodeArtifact repo with `pypi-store` upstream + `codeartifact.api` + `codeartifact.repositories` interface endpoints + pip config in lifecycle. If the symptom is "worked yesterday, 403 today," the answer is the **12-hour token TTL**.

3. **"Distributed training; compliance requires in-transit encryption between training nodes."** → `EnableInterContainerTrafficEncryption=true`. SG must allow self-reference on UDP/500 *and* IP protocol 50 (ESP), not just TCP/443.

4. **"From the on-prem office over Direct Connect, training data in S3 is not reachable privately."** → Gateway endpoints don't work from on-prem. Add S3 **interface** endpoint + Resolver rules. Keep the gateway endpoint for in-VPC traffic (free).

5. **"Reduce monthly endpoint cost across 30 workload VPCs."** → Centralised endpoint VPC + Transit Gateway + Route 53 Resolver inbound + RAM-shared rules. Break-even is ~7 VPCs at 7 endpoint types; the AllCloud case study saved $119K/yr at this scale.

6. **"Cross-account inference: app in Account B must call model in Account A without going over internet."** → Account B creates its own `sagemaker.runtime` interface endpoint. Account A grants B's role `sagemaker:InvokeEndpoint` and the endpoint's resource policy allows B's principal. This is Pattern A in §54.10; the custom PrivateLink Service (Pattern B) is only needed if the target is not a SageMaker endpoint or if you need a Lambda/ECS proxy in front for rate limiting or multi-tenant routing.

---

## 54.18 Exercises

1. **Architecture recall.** Without looking back, draw the no-egress reference architecture from §54.3 on paper. Label every component with its role: TGW, Endpoint VPC, ML Workload VPC, the S3 gateway endpoint, two AZs of isolated subnets, the KMS CMK, and at least seven interface endpoints in the Endpoint VPC. Then mark, with a coloured pen, every path a packet could leave the ML VPC and explain in one sentence why each path is closed.

2. **Flag composition.** Write the four-line Python snippet that creates a training job with: (a) container fully network-isolated, (b) data path routed through your VPC in two subnets, (c) IPsec encryption between distributed training peers, (d) output artefacts encrypted with your CMK. Then explain in a sentence what would change about the security model if you set `EnableNetworkIsolation=False` while keeping everything else.

3. **Endpoint inventory.** A team is migrating a Studio domain from `PublicInternetOnly` to `VpcOnly`. They have an existing data-prep workflow that uses Athena and Glue, an inference workflow that hits a SageMaker hosted endpoint, and a model-versioning workflow that uses CodeCommit. List the *minimum* interface endpoints they need (you do not need to list S3, which is already covered by a gateway endpoint). Then estimate the monthly endpoint-hour cost for two AZs at $7.30/AZ.

4. **The on-prem DX trap.** Write a short answer (three sentences max) to this scenario: *"Our data scientists at the on-prem Boston office need to read training data from S3 over our Direct Connect link to AWS, without internet exposure. The ML VPC already has an S3 gateway endpoint. Why do they still get DNS-resolution failures, and what is the fix?"*

5. **Cost break-even.** A network engineer pushes back on the centralised-endpoint-VPC pattern because "TGW attachments cost $36.50/month each, which adds up." For an organisation with 12 workload VPCs and 8 endpoint types, compute (a) the monthly cost of per-VPC endpoints in two AZs, (b) the monthly cost of the centralised pattern (one Endpoint VPC + 12 TGW attachments), and (c) the annual saving. Show the arithmetic; use $7.30/endpoint-AZ-month and $36.50/TGW-attachment-month.

6. **Capital One forensic.** In one paragraph, trace the 2019 Capital One breach chain through the five steps in §54.2 and identify, for each step, which AWS-2026 control (IMDSv2, `EnableNetworkIsolation`, scoped execution role, KMS `kms:ViaService`, VPC endpoint policy, GuardDuty IMDS finding) would have prevented or detected that step. Then state which single control you would prioritise if you could only enable one — and defend the choice in three sentences.

7. **PrivateLink architecture.** A new requirement: your ML platform team in Account A operates fraud, recommendations, and credit-risk models. Twelve consumer LOB teams in Accounts B–M need to call them, all from inside their own VPCs, all without traversing the internet. Draw the two viable PrivateLink patterns (Pattern A: per-consumer `sagemaker.runtime` endpoint; Pattern B: custom VPC endpoint service backed by Lambda+NLB proxy). For each, list one production scenario where it is the correct choice and one where it is the wrong one.

---

## 54.19 Cross-links

- **Back to Chapter 7 — VPC fundamentals.** Subnets, route tables, security groups, NACLs, the gateway-vs-interface distinction, the AmazonProvidedDNS resolver, and the difference between an IGW and a NAT GW are introduced there. This chapter assumes you have them cold; if anything in §54.3 felt unfamiliar, page back to §7.4–§7.9 before proceeding.
- **Back to Chapter 22 — Studio anatomy.** The internals of the SageMaker Studio domain (user profiles, apps, kernel gateways, EFS home directory) are introduced there. This chapter assumes you know what a Studio app is and only extends Studio into the `VpcOnly` posture; it does not re-explain user-profile management or the Studio IDE.
- **Back to Chapter 53 — IAM for ML, execution roles, IMDSv2.** The execution-role scoping and IMDSv2 controls referenced throughout §54.2 live there. This chapter is what you wrap *around* a properly scoped execution role; if the role itself is over-permissive, the network controls in this chapter only reduce the blast radius, they do not eliminate it.
- **Forward to Chapter 55 — KMS lifecycle, CMKs, key policies, grants, rotation.** The `KmsKeyId` parameters scattered through §54.4 and §54.5 — and the `kms:ViaService` condition shown in the reference architecture — are the surface of a much deeper topic. Chapter 55 picks up the key lifecycle, multi-region keys, the difference between `kms:Decrypt` and `kms:GenerateDataKey`, and the audit story for KMS Grants.
- **Forward to Chapter 56 — Compliance and residency: HIPAA, PCI-DSS, FedRAMP, IL5, data sovereignty.** This chapter set up the *technical* architecture; Chapter 56 takes the same architecture and walks through the compliance frameworks that require it, the artefacts you must produce for an auditor, and the data-residency constraints (e.g., GovCloud isolation, EU-only deployments) that shape how the architecture varies by region.

---

## 54.20 What to take into the exam from this chapter

A packing list, the kind you would tape inside the cover of your notes the night before the test:

- **The five SageMaker interface-endpoint suffixes**: `sagemaker.api`, `sagemaker.runtime`, `sagemaker.featurestore-runtime`, `sagemaker.studio`, `sagemaker.notebook`. The exam writes distractors that look like real names but aren't (`sagemaker.training` does not exist; training control plane lives behind `sagemaker.api`).
- **Two flags, two semantics.** `EnableNetworkIsolation=true` → no container egress *and* no credentials in container. `VpcConfig` → SageMaker data path routes through your VPC via the two-ENI cross-account model. They compose; the gold pattern uses both.
- **`AppNetworkAccessType=VpcOnly`** is the Studio analogue. Required-endpoint count is 16+ services; the most-overlooked are `sagemaker.studio`, `sagemaker.notebook`, `codeartifact.api`, and `codeartifact.repositories`.
- **The "pip install fails" trap has three fixes**, in order: CodeArtifact + PyPI upstream (most common), Bandersnatch on Fargate (full mirror), and bake-into-ECR (strictest, the only option for `EnableNetworkIsolation=true`). The 12-hour token TTL is its own gotcha.
- **`EnableInterContainerTrafficEncryption`** requires SG rules for UDP/500 (IKE) *and* IP protocol 50 (ESP), not just TCP. Distractors that mention only TCP/443 are wrong.
- **Gateway vs interface for S3**: gateway is free, interface is $0.01/GB. Use the gateway endpoint inside the VPC. Add the interface endpoint **only** for on-prem traffic over DX/VPN — gateway endpoints do not serve on-prem.
- **FIPS runtime endpoints do not support VPC endpoint policies.** Enforce access at the IAM identity layer for FIPS workloads.
- **Centralised endpoint VPC break-even** is roughly 7 workload VPCs at 7 endpoint types, using the formula `N > (7.30·E + 36.50) / (7.30·E - 36.50)`. Real-world saving: AllCloud $119K/yr at one customer. Route 53 PHZ manual association is the DNS plumbing that makes it work across spokes.
- **Cross-account inference defaults to Pattern A** (consumer creates its own `sagemaker.runtime` interface endpoint; producer grants `sagemaker:InvokeEndpoint` by ARN). Pattern B (custom VPC endpoint service + NLB + Lambda/ECS proxy) is for non-SageMaker targets or per-tenant routing.
- **The Capital One chain** — misconfigured WAF → SSRF → IMDSv1 → over-permissive role → S3 exfil → unmonitored CloudTrail — is the canonical story behind every control in this chapter. The single most powerful mitigation is IMDSv2-only; the single most powerful posture is `EnableNetworkIsolation=true` on the training container.

---

*End of Chapter 54. The next chapter (Ch 55) takes the `KmsKeyId` parameter you saw scattered through §54.4 and §54.5 and pulls the cover off KMS itself — the customer-managed key lifecycle, the `kms:ViaService` and `kms:CallerAccount` condition keys, KMS Grants and their audit trail, multi-region replicas, and the small set of failures (missing `kms:GenerateDataKey`, cross-account key-policy gaps) that cause silent training-job failures in exactly the architecture this chapter just built.*
