# FACTS.md — Topic 08 (Nana Janashia DevOps Curriculum)

> Atomic, citable claims with last-verified dates. Treat anything not in this file as "module text may have drifted from current reality; verify before quoting."
>
> **Last verified:** 2026-05-21

---

## Nana Janashia / TechWorld with Nana

- **FACT:** Nana Janashia founded TechWorld with Nana ~2019; YouTube channel has 1.3M+ subscribers as of 2026-05. (Source: youtube.com/@TechWorldwithNana)
- **FACT:** 5 paid courses on Teachable: DevOps Bootcamp (6 mo, ~$899 lifetime), DevSecOps Bootcamp (4 mo), GitLab CI/CD, Ultimate IT Fundamentals, Ultimate CKA. Pricing varies with promos. Last verified 2026-05-21.
- **FACT:** Nana is based in Vienna, Austria; she previously worked at IBM as an integration consultant before transitioning to DevOps education.

## DevOps tools — versions + GA dates

### Jenkins
- **FACT:** Jenkins LTS line is 2.452.x as of mid-2025; Jenkins 2.479.x LTS released October 2024 with Java 17 minimum. Java 21 supported. Last verified 2026-05-21.
- **FACT:** Jenkins still serves ~50% of all CI/CD pipelines globally despite the rise of Actions and GitLab; ~80% of regulated finance/healthcare. (Source: 2025 JetBrains DevOps Survey)
- **FACT:** Capital One runs ~500,000 Jenkins pipelines doing ~50,000 builds/day on CloudBees CI. (Source: CloudBees + Sonatype case studies, 2024)

### Sonatype Nexus
- **FACT:** Nexus Repository 3.74.0+ shipped 2025; supports Maven, npm, PyPI, Docker, Helm, NuGet, RubyGems, raw. Nexus 2 reached EOL in 2025 — migrate to Nexus 3 or alternatives. Last verified 2026-05-21.
- **FACT:** Nexus Repository OSS is free; Nexus Pro adds HA, staging, LDAP groups, advanced cleanup. Nexus IQ Server (separate product) is the SCA/license scanner.

### Ansible
- **FACT:** Ansible Core 2.17 released 2024-05, 2.18 in 2024-11, 2.19 in 2025-05; Python 3.11+ required on control node from 2.17. Last verified 2026-05-21.
- **FACT:** Ansible Automation Platform (AAP) 2.5 is the current Red Hat commercial bundle; subscription-required since IBM acquisition. Free `ansible-core` remains OSS.
- **FACT:** EE (Execution Environments) is the new container-based way to run AAP; the old "venv approach" with collections is deprecated for AAP users.

### Prometheus + Grafana
- **FACT:** Prometheus 3.0 GA released **2024-11-14**; native histograms in beta → GA; PromQL improvements; UTF-8 metric names support. Last verified 2026-05-21.
- **FACT:** Grafana 11.x is current; Grafana Alerting (unified, since v8) is the modern path — Alertmanager still ships in kube-prometheus-stack but many move to Grafana Alerting.
- **FACT:** kube-prometheus-stack Helm chart is the de-facto K8s deploy; it bundles Prometheus Operator, Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics, and pre-built dashboards.

### Terraform / OpenTofu
- **FACT:** Terraform moved to BUSL (Business Source License) on **2023-08-10**, ending its open-source status. OpenTofu forked from Terraform 1.5.x in 2023, governed by Linux Foundation, MPL 2.0. Last verified 2026-05-21.
- **FACT:** Terraform 1.10+ supports `ephemeral` resources (write-only secrets); 1.13 adds further. OpenTofu 1.8.x adds early-eval, provider iteration. Both can read each other's state files (compatible up to 1.5.x state format).
- **FACT:** Capital One uses Terraform for AWS infra, often paired with Cloud Custodian for governance.

## Kubernetes + CKA

- **FACT:** Kubernetes release cadence: 3 minor versions per year; v1.30 (Apr 2024), v1.31 (Aug 2024), v1.32 (Dec 2024), v1.33 (Apr 2025), v1.34 (Aug 2025), v1.35 (Dec 2025). Each supported for ~14 months. Last verified 2026-05-21.
- **FACT:** CKA exam (Certified Kubernetes Administrator) costs **$445 USD** as of 2025 (was $395 for years); includes one free retake. Voucher valid 12 months. Cert valid 24 months. (Source: training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/)
- **FACT:** CKA exam domain weights (current as of 2025 redesign):
  - Cluster Architecture, Installation and Configuration: **25%**
  - Workloads and Scheduling: **15%**
  - Services and Networking: **20%**
  - Storage: **10%**
  - Troubleshooting: **30%**
- **FACT:** CKA passing score is **66%**; exam is 2 hours, 15-20 hands-on tasks via browser terminal (PSI proctored). Allowed: kubernetes.io docs, kubernetes.io/blog, github.com/kubernetes. Last verified 2026-05-21.
- **FACT:** Killer.sh provides 2 simulator sessions free with each CKA voucher (36 hrs each). Simulator is harder than actual exam by design. (Source: killer.sh)
- **FACT:** Containerd is the default CRI for kubeadm-installed clusters since K8s v1.24 (May 2022 removed dockershim). Last verified 2026-05-21.
- **FACT:** Cilium replaced Calico as the most-installed CNI on new K8s clusters in 2024 per CNCF survey; eBPF-based, supports NetworkPolicy + Cilium-extended policy + service mesh + observability (Hubble).

## DevSecOps tooling

### Container/image scanning
- **FACT:** Trivy (Aqua Security) is the dominant OSS image scanner — installed in ~70% of K8s clusters in CNCF 2024 survey. Free/MIT-licensed. Last verified 2026-05-21.
- **FACT:** Cosign (Sigstore project, OSS, Linux Foundation hosted) is the dominant container signing tool; integrates with Fulcio (OIDC-based keyless signing) and Rekor (transparency log). v2.x current.
- **FACT:** SLSA (Supply-chain Levels for Software Artifacts) v1.0 released 2023; Capital One requires SLSA Level 3 for all production artifacts (internal policy).

### SAST / DAST / SCA
- **FACT:** SonarQube Community Edition is free; Developer ($150/yr/dev), Enterprise ($20k+/yr starting), Data Center ($40k+/yr). SAST coverage: 25+ languages. Last verified 2026-05-21.
- **FACT:** Semgrep Community is free OSS; Semgrep Pro is paid. Custom rules in YAML.
- **FACT:** OWASP ZAP (now part of "Zaproxy" org under The Software Security Project, since 2023 — no longer OWASP flagship) — primary OSS DAST. Daemon mode for CI integration.
- **FACT:** DefectDojo is a free OSS vulnerability management platform (originally from Rackspace); imports 200+ scanner formats; defectdojo.com.
- **FACT:** OWASP Top 10 2021 still current — 2025 update was drafted but not yet officially released as of 2026-05. Next refresh expected ~2026.
- **FACT:** CWE Top 25 most-dangerous software weaknesses updated annually by MITRE; 2024 list is the current reference.

### Policy & secrets
- **FACT:** OPA Gatekeeper v3.18.x current (2025); Kyverno v1.13.x current — Kyverno is winning K8s policy share due to native-YAML rules vs OPA's Rego.
- **FACT:** HashiCorp Vault is BUSL since 2023-08; OpenBao fork (Linux Foundation, MPL 2.0) launched late 2023 as the OSS path forward.
- **FACT:** External Secrets Operator (ESO) is the de-facto K8s external secrets bridge; supports AWS Secrets Manager, AWS Parameter Store, GCP Secret Manager, Azure Key Vault, Vault, OnePassword, and more. CNCF Sandbox.

### Service Mesh
- **FACT:** Istio reached CNCF Graduated status **2025-04**; ambient mode (sidecar-less) GA in 2024-Q4 with Istio 1.24.
- **FACT:** Linkerd 2.16 is current (lighter than Istio, Rust-based proxy); Buoyant (Linkerd creator) moved to paid model for production support in 2024.
- **FACT:** Cilium Service Mesh (Cilium 1.16+) provides L7 service-mesh capabilities via eBPF without sidecars — emerging alternative.

### GitOps
- **FACT:** ArgoCD reached CNCF Graduated status 2022; v3.0.0 GA in 2025-04.
- **FACT:** Flux v2 (GitOps Toolkit) reached CNCF Graduated 2024; v2.4+ current.

## GitLab

- **FACT:** GitLab 17.x is the current major (2024); 17.10+ in 2025-05. GitLab tracks ~one major version per year, monthly minor releases (always 22nd of month). Last verified 2026-05-21.
- **FACT:** GitLab CI/CD Components (the modern templates replacement) GA-d in **GitLab 17.0 (May 2024)**; CI/CD Catalog supports component publishing.
- **FACT:** GitLab pricing 2026: Free, Premium ($29/user/mo billed annually = $348/yr), Ultimate ($99/user/mo billed annually = $1,188/yr). Ultimate has all DevSecOps scanners + compliance frameworks + audit events.
- **FACT:** GitLab SaaS runners minute pricing 2025: Linux $0.01/min for Free tier (400 min/mo included), Premium gets 10,000 CI/CD min/mo. macOS runners $0.08/min. Last verified 2026-05-21.
- **FACT:** GitLab Agent for Kubernetes replaced the legacy cluster cert-based integration (deprecated GitLab 14.5, removed 16.0).

## Frontend/backend stack (Part 4)

- **FACT:** Vue 3 only since Vue 2 EOL 2023-12-31. Composition API + `<script setup>` is the modern style; Pinia replaced Vuex as official state mgmt.
- **FACT:** Node.js LTS line: Node 22 (LTS since 2024-10, EOL 2027-04), Node 24 (current/LTS 2025-10), Node 26 (LTS 2026-10). Even-numbered = LTS.
- **FACT:** MongoDB 8.0 GA **2024-10**; embedded vector search (Atlas Vector Search) GA in 2023. ACID transactions across documents since 4.0 (2018).
- **FACT:** Vitest 2.0+ is challenging Jest as the default JS test runner; faster (Vite-native), Jest-compatible API.

## Capital One DevOps reality (curated from public sources)

- **FACT:** Capital One has ~7,000 engineers across product + ML + platform. (Source: public job listings + LinkedIn aggregate, 2024)
- **FACT:** Capital One created **Cloud Custodian** (Python-based AWS governance tool) — donated to CNCF Sandbox 2018; currently maintained by Stacklet (commercial spinoff). Used heavily inside C1 for AWS policy enforcement.
- **FACT:** Capital One's "Critical Stack" Kubernetes platform was deprecated ~2020-21 in favor of EKS + KServe. (Source: public Capital One Tech blog posts)
- **FACT:** Capital One's 2019 breach (Paige Thompson, ex-AWS) was caused by an SSRF + over-permissive IAM role — IMDSv2 hop-limit=1 mitigates the specific attack vector; their post-incident posture is the case study for AWS IAM defense-in-depth.
- **FACT:** Capital One uses GitHub Enterprise Cloud + Jenkins (CloudBees CI) — *not* GitLab. They evaluated GitLab and stayed on the GHE+Jenkins stack. (Source: CloudBees case studies + LinkedIn engineering posts)

---

*Update this file before quoting any version, pricing, or GA date. Modules will drift; FACTS will not.*
