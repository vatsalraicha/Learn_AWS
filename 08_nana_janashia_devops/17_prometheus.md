# 17 — Monitoring with Prometheus + Grafana + Alertmanager

## Why this module exists

Prometheus is the de-facto K8s metrics stack. The full observability stack is **metrics (Prometheus) + logs (Loki/CloudWatch/Splunk) + traces (Tempo/Jaeger/X-Ray)**, often called the "three pillars." This module covers the metrics pillar and its alerting plumbing.

## 1. The Prometheus model — pull, not push

Prometheus **scrapes** HTTP `/metrics` endpoints at intervals (default 15s). Targets must expose metrics in Prometheus exposition format. Service discovery finds targets.

```
┌──────────────┐  scrape /metrics   ┌──────────────┐
│  Prometheus  │ ─────────────────► │  /metrics     │
│              │                    │   on app      │
│   - tsdb     │                    └──────────────┘
│   - PromQL   │
│   - alerting │  ┌────────────────────────┐
│              │─►│  Alertmanager           │
└──────────────┘  │  - dedup                │
                  │  - group                │
                  │  - route (email/Slack)  │
                  └────────────────────────┘
```

Why pull over push? Easier service discovery, no auth surface on Prometheus, target-down is naturally visible.

## 2. Prometheus 3.0 in 2026

Prometheus 3.0 GA on **2024-11-14**. Key changes:
- Native histograms (sparse, exponential bucketing) GA
- UTF-8 metric names support
- OTLP ingestion (push from OpenTelemetry collectors)
- Performance: ~30% faster ingestion, lower memory
- PromQL improvements (range vector improvements, `info` function)

## 3. Installing Prometheus on K8s — the kube-prometheus-stack chart

The kube-prometheus-stack Helm chart bundles the entire observability stack:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --version 65.3.1
```

What's installed:
- Prometheus (operator + statefulset)
- Grafana (deployment)
- Alertmanager (statefulset)
- node-exporter (DaemonSet — host metrics)
- kube-state-metrics (Deployment — K8s object metrics)
- Pre-built dashboards
- Pre-built alert rules (CPU, memory, disk, K8s API health, kubelet, etcd)

## 4. PromQL — the query language

```promql
# Instantaneous (gauge)
node_memory_MemAvailable_bytes

# Per-second rate (counter)
rate(http_requests_total[5m])

# By label
rate(http_requests_total{status="500"}[5m]) by (instance)

# Filter
{job="api", environment="prod"}

# Aggregation
sum(rate(http_requests_total[5m])) by (status)

# 95th percentile latency (from histogram)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Saturation / RED method
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m]))

# Up/down
up{job="my-app"}
```

The four metric types:
- **Counter** — monotonically increasing (requests_total). Use with `rate()`.
- **Gauge** — current value, can go up or down (memory_bytes).
- **Histogram** — pre-bucketed observations (request_duration_seconds_bucket + sum + count).
- **Summary** — pre-computed quantiles (less useful — can't aggregate across instances).

## 5. Service discovery — finding targets

For K8s, the **Prometheus Operator** introduces CRDs:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: monitoring
  labels: { release: monitoring }
spec:
  selector:
    matchLabels: { app: my-app }
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
```

`ServiceMonitor` selects K8s Services with the `app: my-app` label; Prometheus auto-discovers their endpoints and scrapes.

`PodMonitor` works without a Service. `Probe` for blackbox-exporter-style synthetic checks.

## 6. Alert rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: my-app-alerts
  namespace: monitoring
  labels: { release: monitoring }
spec:
  groups:
  - name: my-app
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{job="my-app",status=~"5.."}[5m]))
          / sum(rate(http_requests_total{job="my-app"}[5m])) > 0.05
      for: 5m
      labels:
        severity: page
      annotations:
        summary: "5xx rate above 5% for 5min on {{ $labels.job }}"
        runbook: "https://runbooks.example.com/high-error-rate"

    - alert: PodCrashLooping
      expr: rate(kube_pod_container_status_restarts_total[10m]) > 0.1
      for: 5m
      labels: { severity: warning }
      annotations:
        summary: "Pod {{ $labels.pod }} restarting"
```

`for: 5m` = condition must hold 5 minutes before firing (suppresses transients).

## 7. Alertmanager — routing + grouping

```yaml
route:
  receiver: default
  group_by: [alertname, severity, namespace]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  routes:
  - matchers: [severity="page"]
    receiver: pagerduty
  - matchers: [severity="warning"]
    receiver: slack

receivers:
- name: default
  email_configs:
  - to: ops@example.com
- name: pagerduty
  pagerduty_configs:
  - service_key: "<integration-key>"
- name: slack
  slack_configs:
  - api_url: "https://hooks.slack.com/services/..."
    channel: "#alerts"
```

`group_wait` — wait this long collecting more alerts before sending.
`repeat_interval` — re-send if still firing after this.
Inhibition rules — suppress one alert when another fires (e.g., suppress per-pod alerts when whole-cluster alert fires).

## 8. Grafana — dashboards + alerts

```bash
# Get Grafana admin password
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d
# Port-forward
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

Login → import dashboard ID **315** (K8s cluster overview), **1860** (Node Exporter Full).

**Grafana Alerting** (since v8, unified in v11) is a serious alternative to Alertmanager — manages alert rules across Prometheus, Loki, CloudWatch, Postgres data sources. Some teams move all alerting to Grafana; others keep Prometheus alert rules + Alertmanager for the metrics pipeline.

## 9. Instrumenting your app — the Prometheus client library

### Python
```python
from prometheus_client import Counter, Histogram, start_http_server
import time

REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency",
                    ["endpoint"], buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10])

def handle_request(method, endpoint):
    start = time.time()
    try:
        # ... handle
        status = 200
    except Exception:
        status = 500
        raise
    finally:
        LATENCY.labels(endpoint=endpoint).observe(time.time() - start)
        REQUESTS.labels(method=method, endpoint=endpoint, status=status).inc()

if __name__ == "__main__":
    start_http_server(8001)   # /metrics
```

Standard label cardinality discipline: **never label by user_id / customer_id / URL with path parameters baked in** — cardinality explodes. Use endpoint templates (`/users/:id`, not `/users/12345`).

## 10. Exporters — for things you don't write

| Exporter | Metrics |
|---|---|
| **node-exporter** | Linux host (CPU, mem, disk, network) |
| **kube-state-metrics** | K8s object state (deployments, pods, etc.) |
| **postgres-exporter** | Postgres internals |
| **mysqld-exporter** | MySQL |
| **redis-exporter** | Redis |
| **blackbox-exporter** | HTTP/TCP/ICMP probes |
| **jmx-exporter** | Java apps via JMX |
| **windows-exporter** | Windows hosts |
| **nginx-exporter / nginx-prometheus-exporter** | nginx |

Pick the right exporter, scrape it, dashboard it.

## 11. Long-term storage

Prometheus default storage is local TSDB on the node, typically 15 day retention. For longer:

- **Thanos** — Prometheus sidecar + object-store backend (S3); query across many Prometheus instances
- **Cortex** — multi-tenant Prometheus-as-a-service
- **Mimir** — Grafana Labs's Cortex fork (preferred in 2026 for new shops)
- **VictoriaMetrics** — Prometheus-compatible TSDB, single binary, faster + cheaper than Prometheus at scale
- **AWS Managed Prometheus (AMP)** — fully managed (Capital One uses this pattern)
- **Grafana Cloud** — SaaS

## 12. OpenTelemetry crossover

The 2025-2026 narrative: **OpenTelemetry is eating observability**. Modern apps emit OTLP (OpenTelemetry Protocol); the **OTel Collector** receives OTLP, batches, and forwards to Prometheus (via remote-write), Loki, Tempo, vendor backends.

The pattern emerging:
- App → OTel SDK → OTel Collector → Prometheus / Loki / Tempo
- This unifies the three pillars in one pipeline

Prometheus 3.0 added native OTLP ingestion to ride this wave.

## 13. The four golden signals (SRE book) + RED method

**Four golden signals** (Google SRE book):
- Latency
- Traffic
- Errors
- Saturation

**RED method** (Weaveworks; service-level):
- Rate (requests/sec)
- Errors (errors/sec)
- Duration (latency percentiles)

**USE method** (Brendan Gregg; host/resource-level):
- Utilization
- Saturation
- Errors

Pick RED for services, USE for hosts, and you've covered the bases.

## 14. Capital One angle

Capital One's MLOps observability:
- **AMP (AWS Managed Prometheus)** for metrics
- **AMG (AWS Managed Grafana)** for dashboards
- **CloudWatch + Datadog** for log aggregation
- **X-Ray** for distributed tracing
- **rubicon-ml** (their open-source) for ML experiment + lineage tracking
- **Custom dashboards** per LOB for model performance

See [Topic 04 Module M — Observability & Cost](../04_aws_for_ai_ml/).

## 15. Quick self-check

1. Why is Prometheus pull-based, not push-based?
2. What's the difference between a counter and a gauge metric?
3. What's the kube-prometheus-stack Helm chart and what does it install?
4. Why does cardinality explosion break Prometheus, and how do you avoid it?
5. What's the relationship between Prometheus and OpenTelemetry in 2026?

(Answers: simpler auth, target-down naturally visible, ergonomic for K8s SD; counter only grows (use with rate()), gauge can go up or down; Prometheus operator + Prometheus + Grafana + Alertmanager + node-exporter + kube-state-metrics + dashboards; high-cardinality labels (user IDs, URLs with path params) blow up the index — use templates and finite label values; OTel is the emerging emission standard, Prometheus 3.0 ingests OTLP natively, both will coexist with OTel Collector as the bridge.)
