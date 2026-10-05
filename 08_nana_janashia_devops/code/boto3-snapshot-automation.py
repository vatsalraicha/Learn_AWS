#!/usr/bin/env python3
"""
boto3-snapshot-automation.py — EBS snapshot + cleanup automation
Pairs with Module 15 (Boto3 Automation)

Pattern: Lambda-friendly (works as `lambda_handler`) or standalone CLI.
- backup_tagged_volumes: snapshot all EBS volumes tagged Backup=true
- cleanup_old_snapshots: delete AutoBackup snapshots older than retain_days
- main: combined daily run

Usage (CLI):
    python boto3-snapshot-automation.py backup
    python boto3-snapshot-automation.py cleanup --retain-days 30
    python boto3-snapshot-automation.py main --retain-days 30

Usage (Lambda):
    Handler: boto3_snapshot_automation.lambda_handler
    Trigger: EventBridge daily schedule
    Permissions:
        ec2:CreateSnapshot, ec2:CreateTags,
        ec2:DescribeVolumes, ec2:DescribeSnapshots, ec2:DeleteSnapshot
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_BOTO_CFG = Config(retries={"max_attempts": 10, "mode": "adaptive"})


def _client(region: str = "us-east-1"):
    return boto3.client("ec2", region_name=region, config=_BOTO_CFG)


def backup_tagged_volumes(region: str = "us-east-1") -> list[str]:
    """Snapshot every EBS volume tagged Backup=true."""
    ec2 = _client(region)
    paginator = ec2.get_paginator("describe_volumes")
    created: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")

    for page in paginator.paginate(
        Filters=[{"Name": "tag:Backup", "Values": ["true"]}]
    ):
        for vol in page["Volumes"]:
            vol_id = vol["VolumeId"]
            name = _tag_value(vol.get("Tags", []), "Name") or vol_id
            try:
                snap = ec2.create_snapshot(
                    VolumeId=vol_id,
                    Description=f"Auto-backup {name} {ts}",
                    TagSpecifications=[{
                        "ResourceType": "snapshot",
                        "Tags": [
                            {"Key": "AutoBackup", "Value": "true"},
                            {"Key": "Name", "Value": f"{name}-{ts}"},
                            {"Key": "VolumeId", "Value": vol_id},
                            {"Key": "CreatedBy", "Value": "boto3-snapshot-automation"},
                        ],
                    }],
                )
                created.append(snap["SnapshotId"])
                log.info("Created snapshot %s for volume %s", snap["SnapshotId"], vol_id)
            except ClientError as e:
                log.error("Failed to snapshot %s: %s", vol_id, e)
    return created


def cleanup_old_snapshots(region: str = "us-east-1", retain_days: int = 30) -> list[str]:
    """Delete snapshots tagged AutoBackup=true older than retain_days."""
    ec2 = _client(region)
    cutoff = datetime.now(timezone.utc) - timedelta(days=retain_days)
    deleted: list[str] = []

    paginator = ec2.get_paginator("describe_snapshots")
    for page in paginator.paginate(
        OwnerIds=["self"],
        Filters=[{"Name": "tag:AutoBackup", "Values": ["true"]}],
    ):
        for snap in page["Snapshots"]:
            if snap["StartTime"] >= cutoff:
                continue
            try:
                ec2.delete_snapshot(SnapshotId=snap["SnapshotId"])
                deleted.append(snap["SnapshotId"])
                log.info("Deleted snapshot %s (age %s days)",
                         snap["SnapshotId"],
                         (datetime.now(timezone.utc) - snap["StartTime"]).days)
            except ClientError as e:
                log.error("Failed to delete %s: %s", snap["SnapshotId"], e)
    return deleted


def _tag_value(tags: Iterable[dict], key: str) -> str | None:
    return next((t["Value"] for t in tags if t["Key"] == key), None)


def lambda_handler(event: dict, context):
    """EventBridge → Lambda entrypoint."""
    region = event.get("region", "us-east-1")
    retain_days = int(event.get("retain_days", 30))
    created = backup_tagged_volumes(region)
    deleted = cleanup_old_snapshots(region, retain_days)
    return {
        "statusCode": 200,
        "created": created,
        "deleted": deleted,
        "summary": f"created={len(created)} deleted={len(deleted)}",
    }


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("backup")
    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("--retain-days", type=int, default=30)
    full = sub.add_parser("main")
    full.add_argument("--retain-days", type=int, default=30)
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    if args.cmd == "backup":
        created = backup_tagged_volumes(args.region)
        print(f"Created {len(created)} snapshots")
    elif args.cmd == "cleanup":
        deleted = cleanup_old_snapshots(args.region, args.retain_days)
        print(f"Deleted {len(deleted)} old snapshots")
    elif args.cmd == "main":
        created = backup_tagged_volumes(args.region)
        deleted = cleanup_old_snapshots(args.region, args.retain_days)
        print(f"Created {len(created)} | Deleted {len(deleted)}")


if __name__ == "__main__":
    main()
