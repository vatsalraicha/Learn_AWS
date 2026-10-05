# 25 — Observability & runtime security: Prometheus, OpenTelemetry, Falco, Hubble

## Why this module exists

You can't secure or operate what you can't observe. K8s ships nothing for observability — you bring the stack. The de facto: Prometheus + Grafana for metrics, OpenTelemetry for traces, Loki/Elasticsearch for logs, Falco for runtime security, Hubble for network flows, DCGM for GPUs.

---

## 1. The CNCF observability triad

| Signal | Open standard | K8s stack default |
|---|---|---|
| Metrics | OpenMetrics | Prometheus + Grafana |
| Traces | OpenTelemetry | OTel + Jaeger or Tempo |
| Logs | OpenTelemetry Logs | Loki, Elasticsearch, or Cloud-native |

OpenTelemetry is the unifying protocol. Auto-instrumentation for Python/Java/Go/.NET is mature.

---

## 2. kube-prometheus-stack (the standard install)

```bash
helm install kube-prom prometheus-community/kube-prometheus-stack -n monitoring
```

Bundles:
- Prometheus Operator + Prometheus (HA pair).
- Alertmanager.
- Grafana with prebuilt K8s dashboards.
- Node Exporter (per-node metrics).
- kube-state-metrics (object metrics).
- ServiceMonitor / PodMonitor CRDs (declarative scrape config).

Custom metrics: any app exposing `/metrics` in OpenMetrics format. Add a `ServiceMonitor`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata: { name: infer-server, namespace: monitoring }
spec:
  namespaceSelector: { matchNames: [ml-serving] }
  selector: { matchLabels: { app: infer-server } }
  endpoints: [{ port: http, path: /metrics, interval: 15s }]
```

---

## 3. AI/ML-specific metrics

Beyond the generic K8s metrics:

| Metric | Source | Why |
|---|---|---|
| GPU utilization / memory / temp | DCGM Exporter (NVIDIA) | Cost control, capacity planning |
| Inference latency p50/p95/p99 | App | SLO basis |
| Tokens-per-second / requests/sec | App | Throughput |
| Cost per token (compound metric) | Recording rule combining cost + token metrics | Capital One–style FinOps |
| Cache hit rate (LLM KV-cache, RAG retrieval) | App | Cost optimization |
| GPU OOM count / Cgroup throttle events | DCGM, cAdvisor | Reliability |

DCGM Exporter as DaemonSet on GPU nodes:

```yaml
helm install dcgm-exporter nvidia/dcgm-exporter -n monitoring \
  --set serviceMonitor.enabled=true
```

---

## 4. OpenTelemetry — the unification

OTel SDKs auto-instrument web servers, DB clients, HTTP/gRPC. Collector receives signals, exports to backend (Tempo, Jaeger, X-Ray, Datadog, Honeycomb, etc).

```yaml
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata: { name: otel-collector, namespace: monitoring }
spec:
  mode: deployment
  config: |
    receivers:
      otlp: { protocols: { grpc: {}, http: {} } }
    processors:
      batch: {}
      memory_limiter: { check_interval: 5s, limit_mib: 512 }
    exporters:
      otlp/tempo:    { endpoint: tempo:4317, tls: { insecure: true } }
      prometheus:    { endpoint: 0.0.0.0:8889 }
    service:
      pipelines:
        traces:  { receivers: [otlp], processors: [memory_limiter, batch], exporters: [otlp/tempo] }
        metrics: { receivers: [otlp], processors: [memory_limiter, batch], exporters: [prometheus] }
```

The OpenTelemetry **Operator** can auto-inject SDKs into pods via annotation — `instrumentation.opentelemetry.io/inject-python: "true"` and the operator mutates the pod to include the SDK + collector endpoint. Zero-code instrumentation.

---

## 5. Loki — logs as a time series

[Loki](https://grafana.com/oss/loki/) treats logs like Prometheus treats metrics: label-indexed, content not indexed. Cheap at scale; query language (LogQL) similar to PromQL.

```bash
helm install loki grafana/loki-distributed -n monitoring
helm install promtail grafana/promtail -n monitoring \
  --set "loki.serviceName=loki"
```

Promtail (or Vector, or Fluent Bit) tails pod logs and ships to Loki. Storage: S3 / GCS / Azure Blob / on-prem MinIO.

---

## 6. Runtime security — Falco

[Falco](https://falco.org/) is **CNCF Graduated**. eBPF-based runtime security agent. Watches syscalls + K8s audit log + container events; matches against rules.

Detection examples:

- Shell spawned in a container (suspicious for prod ML inference).
- Outbound connection to crypto-mining pool (Tesla 2018 pattern).
- Write to `/etc/shadow` or `/proc/self/exe`.
- ServiceAccount token accessed from unusual process.
- IMDS access from container (Capital One pattern).

```yaml
- rule: Container shell spawned
  desc: A shell was opened inside a container
  condition: spawned_process and container and shell_procs
  output: "Shell in container (user=%user.name container=%container.name cmdline=%proc.cmdline)"
  priority: WARNING
```

Falco emits to **Falcosidekick** which forwards to: Slack, PagerDuty, SIEM (Splunk, Sumo), AWS Security Hub, GCP Security Command Center, Webhook.

For regulated finance: Falco DaemonSet + custom rules + falcosidekick → Security Hub. Standard.

---

## 7. Hubble — Cilium's flow log

If you've installed Cilium (module 18), Hubble gives you L7 network flow visibility:

```bash
hubble observe --namespace ml-serving --since 1m
hubble observe -n ml-serving --to-fqdn s3.amazonaws.com
hubble observe -n ml-serving --verdict DROPPED   # what's getting NetworkPolicy-blocked
```

Hubble UI gives a service-map visualization (which service talks to which, what verbs).

For "what is my pod actually connecting to" debugging: Hubble beats anything else by an order of magnitude.

---

## 8. Tracee — the Aqua eBPF tool

[Tracee](https://github.com/aquasecurity/tracee) is similar to Falco but with a slightly different lineage. eBPF-based, runtime threat detection. Choose one — running both is overkill.

---

## 9. Kubescape / Trivy K8s — scanning for misconfig

- [Kubescape](https://kubescape.io/) (CNCF Sandbox) — scans clusters for NSA + CIS + MITRE ATT&CK violations.
- `trivy k8s` — same idea, plus image vuln + secret scanning across the cluster.

CI integration: scan manifests before they're applied.

---

## 10. The cost-observability angle

Container cost is dominated by **GPU hours** for ML and **request volume** for serving. Tools:

- **OpenCost** (CNCF Sandbox) — cost-allocation per namespace / pod / label using cloud-provider billing data + K8s metrics.
- **Kubecost** (commercial) — same plus richer UI.
- **AWS Cost Anomaly Detection** + **AWS Cost Explorer** with cost-allocation tags from K8s labels.
- **Custom Prom recording rules** that multiply GPU-hours × $/hour.

For Capital One–style FinOps: OpenCost / Kubecost dashboards per business unit, monthly true-up.

---

## 11. The observability checklist for ML on K8s

- [ ] kube-prometheus-stack installed; ServiceMonitor for every prod app.
- [ ] DCGM Exporter on GPU nodes; Grafana dashboard for GPU SM utilization, memory.
- [ ] OpenTelemetry instrumentation for inference services (Python SDK auto-instrumentation).
- [ ] Logs to Loki / OpenSearch / CloudWatch Logs.
- [ ] Falco DaemonSet + custom rules → SIEM.
- [ ] Hubble enabled (or Cilium in cluster).
- [ ] Kubescape in CI + scheduled scans.
- [ ] OpenCost/Kubecost dashboards.
- [ ] SLOs defined per service (latency, error rate) with multi-window alerts.
- [ ] Runbooks linked from every alert.

---

## Sanity check

1. Why is Loki cheaper than Elasticsearch for K8s logs at scale?
2. DCGM Exporter — what does it expose, and on which pods does it need to run?
3. OpenTelemetry Operator's auto-injection — how does it work mechanically?
4. Falco vs Hubble — different purposes. Describe each.
5. OpenCost computes cost per namespace from what inputs?
6. What's the ML-specific recording rule for "cost per million tokens" combining what metrics?

---

## Sources

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [DCGM Exporter](https://github.com/NVIDIA/dcgm-exporter)
- [OpenTelemetry Operator](https://github.com/open-telemetry/opentelemetry-operator)
- [Grafana Loki](https://grafana.com/oss/loki/)
- [Falco](https://falco.org/)
- [Cilium Hubble](https://docs.cilium.io/en/stable/observability/hubble/)
- [Kubescape](https://kubescape.io/)
- [OpenCost](https://www.opencost.io/)

→ Next: [26 — **EKS deep — IRSA, Pod Identity, EFS/FSx/S3 CSI, ASCP, KMS**](26_eks_data_exposure.md)
