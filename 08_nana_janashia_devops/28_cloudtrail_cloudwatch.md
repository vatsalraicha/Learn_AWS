# 28 — CloudTrail + CloudWatch Logging for Security

## Why this module exists

If it's not logged, it didn't happen — or worse, you can't prove anything happened. CloudTrail = the AWS API audit log. CloudWatch = the metric + log + alarm system. Together they're the security observability backbone for any AWS-shop SOC.

## 1. CloudTrail at a glance

- **Records every AWS API call** — who called what, when, from where
- **Free** for last 90 days (Event History)
- **For >90 days, multi-region, or write to S3/CloudWatch**: configure a **Trail** ($2/100k events for management events; data events extra)
- **Trail destinations**: S3 bucket + optionally CloudWatch Logs + optionally Kinesis/EventBridge
- **Two event categories**:
  - **Management events** — control-plane (CreateBucket, AttachRolePolicy)
  - **Data events** — data-plane (S3 GetObject, Lambda Invoke)
- **Insights events** — anomaly detection (paid)

## 2. Setting up an org-wide multi-region trail

```hcl
resource "aws_cloudtrail" "main" {
  name                          = "org-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail.id
  is_organization_trail         = true
  is_multi_region_trail         = true
  include_global_service_events = true
  enable_logging                = true
  enable_log_file_validation    = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail_to_cw.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true
    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::sensitive-bucket/"]
    }
  }
}
```

`enable_log_file_validation = true` produces a hash file so tampering is detectable.

## 3. CloudTrail Event History (the free 90-day window)

UI / CLI:
```bash
aws cloudtrail lookup-events --max-items 10 \
  --lookup-attributes AttributeKey=Username,AttributeValue=alice
```

Useful for incident response when you don't have a Trail yet. Get one. Now.

## 4. CloudWatch Logs basics

```bash
# List log groups
aws logs describe-log-groups

# Tail a group
aws logs tail /aws/lambda/my-fn --follow

# Query via CloudWatch Logs Insights
aws logs start-query --log-group-name /aws/lambda/my-fn \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 20'
```

### Logs Insights query language (familiar SQL-ish):
```
fields @timestamp, @message, level, requestId
| filter level = "ERROR"
| stats count(*) by bin(5m)
| sort @timestamp desc
| limit 100
```

## 5. Custom Metric Filters — extract metrics from logs

Pattern: **Logs → Metric Filter → CloudWatch Metric → Alarm → SNS → PagerDuty/Slack**.

```hcl
resource "aws_cloudwatch_log_metric_filter" "failed_logins" {
  name           = "FailedLogins"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name
  pattern        = "{ ($.eventName = ConsoleLogin) && ($.errorMessage = \"Failed authentication\") }"

  metric_transformation {
    name      = "FailedConsoleLogins"
    namespace = "Security"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "failed_login_burst" {
  alarm_name          = "console-failed-login-burst"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FailedConsoleLogins"
  namespace           = "Security"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}
```

## 6. Security-relevant alarms (the must-haves)

| Alarm | Trigger |
|---|---|
| Root user activity | `eventName = ConsoleLogin` and `userIdentity.type = Root` |
| Failed console logins | `eventName = ConsoleLogin` and `errorMessage = "Failed authentication"` |
| IAM policy changes | `eventName` in [`PutUserPolicy`, `PutRolePolicy`, `AttachUserPolicy`, ...] |
| Security group changes | `eventName` in [`AuthorizeSecurityGroupIngress`, `RevokeSecurityGroupIngress`, ...] |
| CloudTrail config changes | `eventName` in [`StopLogging`, `DeleteTrail`, `UpdateTrail`] |
| KMS key disable/delete | `eventName` in [`DisableKey`, `ScheduleKeyDeletion`] |
| Unauthorized API calls | `errorCode = AccessDenied` (bursts indicate enumeration) |
| Network ACL changes | NACL/SG/VPC modifications |

CIS AWS Foundations Benchmark lists ~14 such alarms; Section 4. Implement all of them.

## 7. EC2-specific alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "ec2-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  dimensions          = { InstanceId = aws_instance.web.id }
  alarm_actions       = [aws_sns_topic.ops.arn]
}
```

## 8. AWS Budgets — cost as a security signal

Sudden cost spikes can be:
- A misconfiguration (orphaned NAT GW, huge query)
- A compromised account (crypto mining on stolen credentials)
- A runaway autoscaling group

```hcl
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-cap"
  budget_type  = "COST"
  limit_amount = "5000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["ops@example.com"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["finance@example.com", "ops@example.com"]
  }
}
```

Also: **AWS Cost Anomaly Detection** — ML-based; alerts on unusual spending patterns.

## 9. Forwarding to SIEM

For real SOC operations, CloudTrail goes from S3 → SIEM:
- **Splunk** (industry-default in regulated finance)
- **Datadog Cloud SIEM**
- **Sumo Logic Cloud SIEM**
- **AWS Security Lake** (newer, OCSF-format, central queryable lake)
- **Panther** (cloud-native, SQL/Python-based detection)
- **Wazuh + Elastic** (OSS path)

The pipeline:
```
CloudTrail → S3 → SIEM ingestion (S3-pull, Kinesis Firehose, SQS-fan-out)
            → Splunk / Datadog / Sumo / Panther
            → Detection rules (SIEM saved searches / Sigma rules)
            → Alerts → SOC analyst → Investigation
```

## 10. CloudTrail Lake (queryable trail without ETL)

CloudTrail Lake (2022) lets you SQL-query trail events directly without exporting:
```sql
SELECT eventName, userIdentity.arn, requestParameters
FROM   $event_data_store
WHERE  eventTime > '2026-05-01'
AND    errorCode IS NOT NULL
ORDER BY eventTime DESC
LIMIT 100;
```

Costs storage + per-TB-scanned. Useful for security teams who want quick lookups without a full SIEM bill.

## 11. The Capital One 2019 angle

The 2019 Capital One breach involved an attacker exploiting SSRF on a misconfigured ModSecurity WAF, then using the temporary credentials from IMDSv1 to access S3 buckets, exfiltrating ~100M records.

Detection chain that would have caught it:
- CloudTrail recorded the unusual S3 List + Get pattern from the WAF's role
- A SIEM rule on "WAF role accessing unusual S3 buckets" would have fired
- Macie scanning S3 would have flagged the sensitive data
- Detection-time was reported as 4+ months — the **gap was in detection rules, not logging**

Lessons baked into AWS since:
- IMDSv2 hop-limit=1 default for new AMIs
- GuardDuty added EC2 instance credential exfiltration detection
- Inspector v2 enhanced

## 12. Quick self-check

1. What's the difference between CloudTrail Event History and a CloudTrail Trail?
2. What's a Custom Metric Filter and what's the pipeline it's part of?
3. Why does `enable_log_file_validation = true` matter for compliance?
4. Name 3 CIS Foundations CloudTrail/CloudWatch alarms.
5. Why is AWS Budgets a security tool, not just a finance tool?

(Answers: Event History is the free 90-day UI lookup, a Trail is a configured stream of events to S3/CW with multi-region + long retention; pattern in logs → metric → alarm → SNS → notification; produces hash files that prove logs weren't tampered after-the-fact — required for SOC 2 + PCI; root login, IAM policy changes, SG changes, NACL changes, CloudTrail config changes, KMS delete, unauthorized API call bursts; sudden spikes can indicate compromised account doing crypto mining or runaway misconfig — security incident signal.)
