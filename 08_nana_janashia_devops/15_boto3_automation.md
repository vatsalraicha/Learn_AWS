# 15 — Automation with Python (Boto3)

## Why this module exists

Boto3 is the AWS SDK for Python. Every AWS-shop DevOps engineer writes Boto3 scripts daily — for things Terraform can't (or shouldn't) do: backup snapshots, health checks, tag enforcement, drift remediation, cost reports.

## 1. Boto3 vs Terraform — when each wins

| Task | Use Terraform | Use Boto3 |
|---|---|---|
| Provision infra (VPC, EC2, RDS) | ✅ | — |
| Configure infra in-place after provisioning | — | ✅ |
| One-time data migration | — | ✅ |
| Scheduled tasks (backup, cleanup) | — | ✅ (often as Lambda) |
| Drift detection + auto-remediation | — | ✅ (Custodian = Boto3 under the hood) |
| Ad-hoc queries / reports | — | ✅ |
| Bulk operations across many accounts | — | ✅ |
| Things that need *logic* (if-then) | — | ✅ |

Capital One: Terraform for infra, **Cloud Custodian** (Python on Boto3) for governance, internal Python tools for everything else.

## 2. Boto3 basics

```bash
uv pip install boto3
```

```python
import boto3

# Client (low-level, 1:1 with AWS API)
ec2 = boto3.client("ec2", region_name="us-east-1")
resp = ec2.describe_instances()
for r in resp["Reservations"]:
    for inst in r["Instances"]:
        print(inst["InstanceId"], inst["State"]["Name"])

# Resource (higher-level, OO, deprecated for new code but still used)
s3 = boto3.resource("s3")
for bucket in s3.buckets.all():
    print(bucket.name)

# Session (multi-credential, multi-region patterns)
session = boto3.Session(profile_name="prod", region_name="us-east-1")
s3 = session.client("s3")
```

**2026 reality:** AWS deprecated boto3 **resource** interface — use **client** + paginators. The new high-level alternative is the AWS Cloud Development Kit (CDK) for infra, while runtime AWS automation stays on boto3 client.

## 3. Authentication chain

Boto3 looks for credentials in this order:
1. Explicit `aws_access_key_id` arg
2. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`)
3. AWS shared credentials file (`~/.aws/credentials`)
4. AWS config file (`~/.aws/config` — SSO profiles)
5. Container credentials (ECS, App Runner — via `AWS_CONTAINER_CREDENTIALS_RELATIVE_URI`)
6. EC2 instance metadata (IMDSv2) — auto-discovered on EC2

On EC2/EKS/Lambda: **never pass keys**. Use instance profile / IRSA / Pod Identity / Lambda execution role.

## 4. Pagination (the trap)

AWS APIs paginate. Most `describe_*` / `list_*` calls return up to 100 items + a `NextToken`. Without pagination, you miss data silently.

```python
# Wrong — silently truncates at 100
inst = ec2.describe_instances()["Reservations"]

# Right
paginator = ec2.get_paginator("describe_instances")
for page in paginator.paginate():
    for r in page["Reservations"]:
        for i in r["Instances"]:
            ...
```

## 5. EC2 Status Checks (Nana's "health check" project)

```python
import boto3

def check_health(region: str) -> dict:
    ec2 = boto3.client("ec2", region_name=region)
    unhealthy = []
    paginator = ec2.get_paginator("describe_instance_status")
    for page in paginator.paginate(IncludeAllInstances=True):
        for s in page["InstanceStatuses"]:
            if s["InstanceState"]["Name"] != "running":
                continue
            if s["InstanceStatus"]["Status"] != "ok" or s["SystemStatus"]["Status"] != "ok":
                unhealthy.append(s["InstanceId"])
    return {"region": region, "unhealthy": unhealthy}

if __name__ == "__main__":
    print(check_health("us-east-1"))
```

## 6. EBS snapshot automation (backup + cleanup)

```python
import boto3
from datetime import datetime, timezone, timedelta

ec2 = boto3.client("ec2", region_name="us-east-1")

def backup_tagged_volumes():
    paginator = ec2.get_paginator("describe_volumes")
    for page in paginator.paginate(Filters=[{"Name": "tag:Backup", "Values": ["true"]}]):
        for v in page["Volumes"]:
            ec2.create_snapshot(
                VolumeId=v["VolumeId"],
                Description=f"Auto-backup {datetime.now().isoformat()}",
                TagSpecifications=[{
                    "ResourceType": "snapshot",
                    "Tags": [
                        {"Key": "AutoBackup", "Value": "true"},
                        {"Key": "VolumeId", "Value": v["VolumeId"]},
                    ],
                }],
            )

def cleanup_old_snapshots(retain_days: int = 30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=retain_days)
    paginator = ec2.get_paginator("describe_snapshots")
    for page in paginator.paginate(OwnerIds=["self"],
                                    Filters=[{"Name": "tag:AutoBackup", "Values": ["true"]}]):
        for s in page["Snapshots"]:
            if s["StartTime"] < cutoff:
                ec2.delete_snapshot(SnapshotId=s["SnapshotId"])
```

Schedule via:
- `cron` on an EC2 instance (legacy)
- **EventBridge → Lambda** (cloud-native; serverless; pay-per-execution)
- AWS Backup service (managed; for production volume / RDS / EFS / DynamoDB)

## 7. Tag enforcement (a common DevOps task)

```python
def enforce_tags(required: list[str]):
    paginator = ec2.get_paginator("describe_instances")
    violations = []
    for page in paginator.paginate():
        for r in page["Reservations"]:
            for inst in r["Instances"]:
                tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                missing = [k for k in required if k not in tags]
                if missing:
                    violations.append({"id": inst["InstanceId"], "missing": missing})
    return violations
```

In production, use **AWS Config rules** or **Cloud Custodian policies** for this. Custodian is the open-source Python framework for declarative policy-as-code (built by Capital One).

## 8. EKS cluster info via Boto3

```python
eks = boto3.client("eks", region_name="us-east-1")
clusters = eks.list_clusters()["clusters"]
for name in clusters:
    desc = eks.describe_cluster(name=name)["cluster"]
    print(f"{name}: {desc['version']} ({desc['status']})")
```

## 9. Website monitoring + auto-restart (Nana's project)

```python
import httpx
import boto3
from typing import Iterable

ec2 = boto3.client("ec2", region_name="us-east-1")
sns = boto3.client("sns", region_name="us-east-1")

def check_url(url: str) -> bool:
    try:
        r = httpx.get(url, timeout=10.0)
        return r.status_code < 500
    except Exception:
        return False

def reboot_instance(instance_id: str):
    ec2.reboot_instances(InstanceIds=[instance_id])

def notify(topic_arn: str, msg: str):
    sns.publish(TopicArn=topic_arn, Subject="Site down", Message=msg)

def monitor(targets: Iterable[tuple[str, str]], topic_arn: str):
    for url, instance_id in targets:
        if not check_url(url):
            notify(topic_arn, f"{url} unhealthy; rebooting {instance_id}")
            reboot_instance(instance_id)
```

For real production: use **CloudWatch Synthetics** or **Route 53 Health Checks** + **Auto Scaling Group** health-based replacement, not a Boto3 script.

## 10. Error handling + retries

```python
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)

try:
    ec2.terminate_instances(InstanceIds=["i-12345"])
except ClientError as e:
    code = e.response["Error"]["Code"]
    if code == "InvalidInstanceID.NotFound":
        logger.warning("instance already gone")
    elif code == "DryRunOperation":
        logger.info("dry run ok")
    else:
        raise
```

Boto3 has built-in retry config:
```python
from botocore.config import Config
ec2 = boto3.client("ec2", config=Config(retries={"max_attempts": 10, "mode": "adaptive"}))
```

## 11. Boto3 in Lambda (the serverless automation pattern)

```python
# lambda_function.py
import boto3, os, json

def lambda_handler(event, context):
    ec2 = boto3.client("ec2")
    # event from EventBridge schedule
    ec2.create_snapshot(VolumeId=event["volume_id"])
    return {"status": "ok"}
```

Package: `requirements.txt` + `lambda_function.py` → zip → upload (or use container image deployment for >50MB packages or for libs with native binaries).

## 12. Quick self-check

1. What does `boto3.client(...)` vs `boto3.resource(...)` give you, and which is preferred in 2026?
2. Why is pagination essential when calling AWS APIs?
3. How does Boto3 discover credentials on an EC2 instance?
4. When should you use Boto3 vs Terraform?
5. What's Cloud Custodian and who built it?

(Answers: client = low-level 1:1 with API, resource = OO higher-level but deprecated direction; pages are limited and silent truncation breaks scripts; via IMDSv2 instance profile token; Boto3 for runtime/operations/automation, Terraform for static infra; declarative Python policy-as-code framework for AWS, built and OSS'd by Capital One.)
