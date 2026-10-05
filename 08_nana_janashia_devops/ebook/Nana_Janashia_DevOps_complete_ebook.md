---
title: "Nana Janashia DevOps Curriculum"
subtitle: "DevOps · DevSecOps · GitLab CI/CD · IT Fundamentals · CKA (Career_upskill — Topic 08)"
author: "Vatsal Raicha"
date: "May 2026"
lang: "en-US"
rights: "© 2026 Vatsal Raicha. Personal use only."
description: "80-module compendium covering Nana Janashia's five paid courses, written for a senior AI/ML engineer at Optum targeting Capital One Sr Lead AI/ML."
---

# Topic 08 — Nana Janashia DevOps Curriculum (5-Course Compendium)

> **Source curriculum:** [TechWorld with Nana](https://techworld-with-nana.com) — five paid courses + the YouTube channel
>
> **Compiled by:** Vatsal Raicha, May 2026 — for the Career_upskill project
>
> **Lens:** Sr AI/ML Engineer at Optum → targeting AI Engineering Manager / AI Architect (Capital One Sr Lead AI/ML as primary frame). This is a DevOps-completeness pass — not a "learn DevOps from scratch" run. Modules read at senior-engineer cadence: assume Linux + Git + at-least-some-K8s baseline; cross-link to existing topics 04, 05, 07 where overlap is significant; go deep where Nana adds genuine value (Nexus, Ansible, Prometheus, GitLab CI/CD, DevSecOps tool chain, CKA exam mechanics).

---

## Why this topic exists

Nana Janashia is the single most-recommended DevOps educator on the internet. Her 5-course bundle (DevOps Bootcamp, DevSecOps Bootcamp, GitLab CI/CD, IT Fundamentals, CKA) is the de-facto canon for the "I want to call myself a DevOps engineer" outcome. For Vatsal — an AI/ML engineer not a pure DevOps eng — the *value* in working through her curriculum is:

1. **Cert-adjacent breadth.** Capital One's Sr Lead AI/ML role expects "I have shipped MLOps to production, I know how the CI/CD + K8s + cloud security plumbing actually works." Nana's bootcamps map almost 1:1 onto what that engineer is expected to wield.
2. **Gap filling.** Topic 04 (AWS) is wide. Topic 05 (Docker/K8s) is deep. Topic 07 (Git/GitHub/CI-CD) is enterprise-finance. But Nexus + Ansible + Prometheus + GitLab CI/CD + DevSecOps tool chain + CKA exam mechanics are *not* covered elsewhere in the project. This topic backfills.
3. **CKA roadmap.** The CKA exam is the credential that says "I can run a K8s cluster, not just kubectl apply." Capital One values it. This topic includes the full exam-prep playbook.
4. **DevSecOps language.** Capital One has both a "data-engineering pipeline" and a "security-engineering pipeline." Knowing SAST/DAST/SCA/Secret-Scanning/IaC-scan/Image-scan/Admission/Policy-as-Code lets you join the security conversation as a peer, not a beneficiary.

---

## How this topic is organized (5 parts, 78 modules)

The 5 parts mirror Nana's 5 courses. Within each part, every sub-section from `Topic_8_Nana_Janashia_Topics.md` is covered. Modules that overlap heavily with prior topics are intentionally brief and cross-linked; modules where Nana adds unique value (or where the project hadn't covered it) are full-depth.

| Part | Course | Modules | Cross-links | Lens |
|---|---|---:|---|---|
| **1** | DevOps Bootcamp (6 mo) | 1–16 | Topics 05, 07 | The "what does a DevOps engineer do" pass |
| **2** | DevSecOps Bootcamp (4 mo) | 17–37 | Topic 04 (sec/compliance), Topic 07 (GHAS) | Shift-everywhere security |
| **3** | GitLab CI/CD | 38–45 | Topic 07 (Actions) | GitLab vs Actions vs Jenkins |
| **4** | IT Fundamentals | 46–58 | (mostly net-new, beginner) | Full SDLC for context |
| **5** | CKA (Cert) | 59–78 | Topic 05 | Exam-focused K8s admin |

Total: 78 modules + FACTS.md + CAPITAL_ONE.md + code/ + quizzes/ + ebook/

## Module list — Part 1 (DevOps Bootcamp)

1. Introduction to DevOps — what it is, why it exists
2. Operating Systems + Linux Basics (cross-link Topic 05)
3. Version Control with Git (cross-link Topic 07)
4. Databases in the development process
5. Build Tools & Package Managers
6. Cloud & IaaS basics (DigitalOcean lens)
7. **Nexus** — Artifact Repository Manager *(deep)*
8. Containers with Docker (cross-link Topic 05)
9. Build Automation & CI/CD with **Jenkins** *(deep)*
10. AWS Services for DevOps (cross-link Topic 04)
11. Kubernetes Orchestration (cross-link Topic 05)
12. **Kubernetes on AWS — EKS** (cross-link Topic 04)
13. Infrastructure as Code with **Terraform** *(deep, net new)*
14. Programming Basics with **Python** (skim — Vatsal is Python-fluent)
15. **Automation with Python (Boto3)** *(deep)*
16. **Configuration Management with Ansible** *(deep)*
17. **Monitoring with Prometheus + Grafana + Alertmanager** *(deep)*

## Module list — Part 2 (DevSecOps Bootcamp, 21 chapters)

18. Security Essentials + OWASP Top 10
19. Introduction to DevSecOps
20. **Application Vulnerability Scanning — GitLeaks + Pre-commit**
21. **Vulnerability Management — DefectDojo + CWE**
22. **SCA — Software Composition Analysis**
23. CD Pipeline + AWS ECR integration
24. **Image Scanning — Trivy + Cosign + ECR**
25. AWS Cloud Security Essentials (IAM deep)
26. **Secure CD + DAST (OWASP ZAP)**
27. IaC + **GitOps for DevSecOps**
28. CloudTrail + CloudWatch Logging for security
29. K8s Security Overview
30. K8s Access Management on EKS (IRSA + RBAC)
31. Secure IaC Pipeline (GitLab OIDC + AWS)
32. **EKS Blueprints** + Cluster Bootstrapping
33. **ArgoCD** for application delivery
34. **OPA Gatekeeper** — Policy as Code
35. **Secrets Management — Vault + ESO + AWS Secrets Manager**
36. **Service Mesh — Istio (mTLS + AuthZ)**
37. **Compliance as Code — AWS Config + CIS Benchmarks**
38. Introducing DevSecOps in Organizations (culture/change mgmt)

## Module list — Part 3 (GitLab CI/CD)

39. GitLab CI/CD vs GitHub Actions vs Jenkins — decision matrix
40. Core concepts — jobs, stages, needs, rules, workflow
41. GitLab Architecture — Runners + Executors
42. Real Pipeline — Node.js app to private registry to DEV
43. Pipeline optimization — caching, multi-stage, `extends`
44. Microservices CI/CD — monorepo + polyrepo
45. CI/CD Components (the 2024 templates replacement)
46. Deploy to Kubernetes from GitLab (GitLab Agent)

## Module list — Part 4 (IT Fundamentals)

47. AI study assistants for engineers
48. Agile + Scrum + Jira (modern reality)
49. Web fundamentals — HTML / CSS / JS in 2026
50. Frontend frameworks — React vs Vue vs Svelte vs Angular
51. VueJS 3 deep (Composition API, Pinia, Nuxt)
52. NodeJS backend — Express vs Fastify vs Hono
53. MongoDB + SQL vs NoSQL (when each wins)
54. Test Automation — Jest + Vitest + Playwright
55. Packaging applications (npm, esbuild, Vite)
56. Linux server deployment (Ubuntu 24.04, Caddy, Docker)
57. Multi-env configuration + secrets
58. Git for application teams (cross-link Topic 07)
59. AI tools for engineers (Copilot / Cursor / Claude Code)

## Module list — Part 5 (CKA exam)

60. CKA exam — logistics + 2025 changes + domain weights
61. K8s Core Concepts (cross-link Topic 05 Module 16)
62. Build K8s Cluster from scratch — kubeadm + containerd + Cilium
63. Deployments, Services & DNS
4. External Services — NodePort, LoadBalancer, Ingress
65. RBAC + ServiceAccounts + Certificates API
66. Troubleshooting Applications (the 30% exam domain)
67. Multi-container pods — Sidecar + Init
68. Volumes deep — PV/PVC/SC + HostPath + emptyDir
69. ConfigMap + Secret (env + volume)
70. Resource Requests + Limits
71. Scheduling — NodeSelector, Affinity, Taints, Tolerations
72. Liveness + Readiness Probes
73. Deployment strategies — Rolling Update, Recreate
74. **etcd backup + restore** (high-stakes exam task)
75. Kubernetes REST API (with and without kubectl proxy)
76. Cluster Upgrade (the kubeadm upgrade dance)
77. Kube Contexts (multi-cluster)
78. Certificate management + renewal
79. **NetworkPolicy** deep
80. CKA exam tips + 12-week study plan

(Numbering will be sequential 1-80 in the actual files; this README groups by part for clarity.)

---

## Files in this topic

- `00_Table_Of_Contents.md` — sequential module list with one-line summary
- `01_*.md` to `80_*.md` — module files
- `FACTS.md` — atomic citable claims with last-verified dates
- `CAPITAL_ONE.md` — interview-ready dossier mapping topics to Cap One stack
- `README.md` — this file
- `code/` — runnable artifacts (Jenkinsfile, .gitlab-ci.yml, Ansible playbook, Prometheus alert rules, OPA policy, kubeadm setup script, Vue+Node demo)
- `quizzes/` — grouped quizzes per part block
- `ebook/` — EPUB + PDF + combined markdown + build script

## Research provenance

Four deep-research subagents commissioned for the unique-content parts:

| Dossier | Coverage |
|---|---|
| `research_inputs/08_nana_janashia/01_nexus_ansible_prometheus.md` | Nexus, Ansible, Prometheus+Grafana+Alertmanager |
| `research_inputs/08_nana_janashia/02_devsecops_tooling.md` | GitLeaks, DefectDojo, SAST/SCA/DAST, Trivy/Cosign, OPA, Vault, ArgoCD, Istio, Compliance |
| `research_inputs/08_nana_janashia/03_gitlab_cicd_cka.md` | GitLab CI/CD + CKA exam |
| `research_inputs/08_nana_janashia/04_it_fundamentals_stack.md` | Vue, Node, Mongo, Jest, modern frontend, AI dev tools |

The dossiers contain primary-source citations, atomic facts, and config examples. Modules draw from them; `FACTS.md` consolidates citable claims.

## Build the ebook

```bash
bash topics/08_nana_janashia_devops/ebook/build_ebook.sh
```

Outputs:
- `Nana_Janashia_DevOps_complete_ebook.md` (combined markdown)
- `Nana_Janashia_DevOps_complete_ebook.epub`
- `Nana_Janashia_DevOps_complete_ebook.pdf`

## Cross-links to other topics

| Topic | Modules referenced |
|---|---|
| **04 AWS for AI/ML** | Part 1 Module 10 (AWS), Part 1 Module 12 (EKS), Part 2 Module 25 (IAM), Part 2 Module 28 (CloudTrail) |
| **05 Docker & K8s** | Part 1 Module 2 (Linux), Part 1 Module 8 (Docker), Part 1 Module 11 (K8s), Part 5 entire (CKA) |
| **07 Git, GitHub & DevOps** | Part 1 Module 3 (Git), Part 1 Module 9 (Jenkins), Part 2 Module 18 (security), Part 4 Module 58 (Git for apps) |
| **02 Databricks** | Part 3 Module 46 (Databricks integration via GitLab) |

---

*"DevOps is a culture, not a job title. But if you want the title, you need to be able to do all of these things."* — paraphrasing Nana



ewpage


# Table of Contents — Topic 08 (Nana Janashia DevOps Curriculum)

> 78 modules across 5 parts. Read top-to-bottom for full sweep, or jump to part. Modules marked 🔗 cross-link heavily to a prior topic.

## Part 1 — DevOps Bootcamp (modules 1–17)

1. [Introduction to DevOps](01_intro_devops.md)
2. [Operating Systems + Linux Basics](02_linux_basics.md) 🔗 Topic 05
3. [Version Control with Git](03_git_devops.md) 🔗 Topic 07
4. [Databases in the development process](04_databases.md)
5. [Build Tools & Package Managers](05_build_tools.md)
6. [Cloud & IaaS — DigitalOcean](06_iaas_digitalocean.md)
7. [Nexus — Artifact Repository Manager](07_nexus.md)
8. [Containers with Docker](08_docker.md) 🔗 Topic 05
9. [Jenkins — Build automation + CI/CD](09_jenkins.md)
10. [AWS Services for DevOps](10_aws_devops.md) 🔗 Topic 04
11. [Kubernetes Orchestration](11_k8s_overview.md) 🔗 Topic 05
12. [Kubernetes on AWS — EKS](12_eks.md) 🔗 Topic 04
13. [Infrastructure as Code with Terraform](13_terraform.md)
14. [Python basics for DevOps](14_python_basics.md)
15. [Automation with Python (Boto3)](15_boto3_automation.md)
16. [Configuration Management with Ansible](16_ansible.md)
17. [Monitoring with Prometheus + Grafana + Alertmanager](17_prometheus.md)

## Part 2 — DevSecOps Bootcamp (modules 18–38)

18. [Security Essentials + OWASP Top 10](18_security_essentials.md)
19. [Introduction to DevSecOps](19_devsecops_intro.md)
20. [App Vuln Scanning — GitLeaks + Pre-commit](20_gitleaks_precommit.md)
21. [Vulnerability Management — DefectDojo + CWE](21_defectdojo.md)
22. [SCA — Software Composition Analysis](22_sca.md)
23. [Build a CD Pipeline + AWS ECR](23_cd_pipeline.md)
24. [Image Scanning — Trivy + Cosign + ECR](24_image_scanning.md)
25. [AWS Cloud Security Essentials (IAM deep)](25_aws_security.md)
26. [Secure CD + DAST with OWASP ZAP](26_dast_zap.md)
27. [IaC + GitOps for DevSecOps](27_iac_gitops.md)
28. [CloudTrail + CloudWatch Logging for Security](28_cloudtrail_cloudwatch.md)
29. [K8s Security Overview](29_k8s_security.md)
30. [EKS Access Management — IRSA + RBAC](30_eks_access.md)
31. [Secure IaC Pipeline — GitLab OIDC to AWS](31_gitlab_oidc.md)
32. [EKS Blueprints + Cluster Bootstrapping](32_eks_blueprints.md)
33. [ArgoCD for Application Delivery](33_argocd.md)
34. [OPA Gatekeeper — Policy as Code](34_opa_gatekeeper.md)
35. [Secrets Management — Vault + ESO + AWS SM](35_secrets_management.md)
36. [Service Mesh — Istio (mTLS + AuthZ)](36_istio.md)
37. [Compliance as Code — AWS Config + CIS](37_compliance_as_code.md)
38. [Introducing DevSecOps in Organizations](38_devsecops_org_change.md)

## Part 3 — GitLab CI/CD (modules 39–46)

39. [GitLab CI/CD vs Actions vs Jenkins](39_gitlab_vs_actions_jenkins.md)
40. [Core concepts — jobs, stages, needs, rules](40_gitlab_core.md)
41. [GitLab Architecture — Runners + Executors](41_gitlab_runners.md)
42. [Real Pipeline — Node.js to private registry to DEV](42_gitlab_nodejs_pipeline.md)
43. [Optimization — caching, multi-stage, extends](43_gitlab_optimization.md)
44. [Microservices CI/CD — monorepo + polyrepo](44_gitlab_microservices.md)
45. [CI/CD Components (2024 templates replacement)](45_gitlab_components.md)
46. [Deploy to Kubernetes from GitLab](46_gitlab_to_k8s.md)

## Part 4 — IT Fundamentals (modules 47–59)

47. [AI study assistants for engineers](47_ai_study_assistants.md)
48. [Agile + Scrum + Jira (modern reality)](48_agile_scrum_jira.md)
49. [Web fundamentals — HTML/CSS/JS in 2026](49_web_fundamentals.md)
50. [Frontend framework landscape](50_frontend_frameworks.md)
51. [VueJS 3 deep](51_vuejs.md)
52. [NodeJS backend](52_nodejs.md)
53. [MongoDB + SQL vs NoSQL](53_mongodb_sql_nosql.md)
54. [Test Automation — Jest + Vitest + Playwright](54_testing.md)
55. [Packaging applications](55_packaging.md)
56. [Linux server deployment](56_linux_deploy.md)
57. [Multi-env configuration + secrets](57_multienv_config.md)
58. [Git for application teams](58_git_for_app_teams.md) 🔗 Topic 07
59. [AI tools for engineers in 2026](59_ai_tools_2026.md)

## Part 5 — CKA (modules 60–80)

60. [CKA exam — logistics, domain weights, 2025 changes](60_cka_exam_logistics.md)
61. [K8s Core Concepts](61_k8s_core_concepts.md) 🔗 Topic 05
62. [Build K8s Cluster from scratch — kubeadm + containerd + Cilium](62_kubeadm_cluster_build.md)
63. [Deployments, Services & DNS](63_deployments_services_dns.md)
64. [External Services — NodePort, LoadBalancer, Ingress](64_external_services.md)
65. [RBAC + ServiceAccounts + Certificates API](65_rbac_certificates_api.md)
66. [Troubleshooting Applications (30% exam domain)](66_troubleshooting.md)
67. [Multi-container Pods — Sidecar + Init](67_multicontainer_pods.md)
68. [Volumes — PV/PVC/SC + HostPath + emptyDir](68_volumes.md)
69. [ConfigMap + Secret (env + volume)](69_configmap_secret.md)
70. [Resource Requests + Limits](70_resources_limits.md)
71. [Scheduling — NodeSelector, Affinity, Taints](71_scheduling.md)
72. [Liveness + Readiness Probes](72_probes.md)
73. [Deployment Strategies — Rolling Update](73_deployment_strategies.md)
74. [etcd Backup + Restore](74_etcd_backup_restore.md)
75. [Kubernetes REST API](75_k8s_rest_api.md)
76. [Cluster Upgrade with kubeadm](76_cluster_upgrade.md)
77. [Kube Contexts (multi-cluster)](77_kube_contexts.md)
78. [Certificate Management + Renewal](78_cert_management.md)
79. [NetworkPolicy deep](79_network_policy.md)
80. [CKA exam tips + 12-week study plan](80_cka_study_plan.md)

---

Total: 80 modules + FACTS.md + CAPITAL_ONE.md + README.md + code/ + quizzes/ + ebook/



ewpage


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



ewpage





ewpage


# 01 — Introduction to DevOps

> *"DevOps is the practice of operations and development engineers participating together in the entire service lifecycle, from design through the development process to production support."* — Jez Humble

## Why this module exists

Senior engineers in 2026 still get tripped up on what "DevOps" actually *is* — culture, role, or toolchain. Nana's curriculum starts here because every subsequent module presupposes you can answer: *what problem does DevOps solve, and what's been added to the toolchain since the 2009 Patrick Debois conference?*

## 1. The 30-second history

| Year | Event |
|---|---|
| **2009** | Patrick Debois organizes **DevOpsDays Ghent** — first use of "DevOps" as a movement label. |
| **2010** | "Continuous Delivery" (Humble + Farley) book formalizes the deployment pipeline. |
| **2013** | "The Phoenix Project" (Kim/Behr/Spafford) — the parable that put DevOps on every CIO's desk. |
| **2014** | DORA (Forsgren, Humble, Kim) start the State of DevOps report. |
| **2015–2016** | Kubernetes 1.0 (2015-07-21) + Docker mainstreaming. The pipeline tooling shifts. |
| **2017–2019** | "DevSecOps" coined; "shift left security" emerges. |
| **2020–2022** | GitOps (Weaveworks coined ~2017, GA in tooling around 2021); SRE practices (Google's 2016 book) mainstream. |
| **2023–2026** | Platform Engineering (Backstage, IDP) consolidates; AI dev tools enter the pipeline. |

## 2. The three pillars (the canonical CALMS)

- **C — Culture.** Dev and Ops share the on-call pager, share the goals, share the language. The org-chart change is half the battle.
- **A — Automation.** If a human does it twice, the third time it should be a script. CI/CD, IaC, config management.
- **L — Lean.** Small batches, fast feedback, eliminate waste. Toyota Production System genealogy.
- **M — Measurement.** DORA's four key metrics (deploy freq, lead time, MTTR, change fail rate).
- **S — Sharing.** Postmortems, internal docs, brown bags, blameless reviews.

## 3. DORA metrics (the only metrics that matter for DevOps maturity)

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| **Deployment Frequency** | Multiple/day | Daily–weekly | Weekly–monthly | < monthly |
| **Lead Time for Changes** | < 1 day | 1 day–1 week | 1 week–1 month | 1–6 months |
| **MTTR** (mean time to restore) | < 1 hour | < 1 day | < 1 week | > 1 week |
| **Change Failure Rate** | 0–15% | 16–30% | 16–30% | > 30% |

The 2024 State of DevOps Report added a 5th: **Reliability** (uptime + SLO attainment). Use these to *baseline* a team's maturity, not as KPIs (Goodhart's law kicks in fast).

## 4. The DevOps engineer's day (what Nana's curriculum prepares for)

A "DevOps engineer" — itself a contested title — typically:
- **Designs + maintains the CI/CD pipeline** (Jenkins/GitLab/GitHub Actions).
- **Provisions cloud infrastructure** via Terraform/CloudFormation/CDK.
- **Configures servers** via Ansible/cloud-init/immutable images.
- **Containerizes apps + runs orchestrators** (Docker, Kubernetes).
- **Monitors systems** (Prometheus + Grafana + Alertmanager + OpenTelemetry).
- **Hardens security** (secret scanning, image scanning, IaC scanning, IAM, NetworkPolicy).
- **On-call rotation** for production incidents.

The 2024 reality: "Platform Engineering" is eating the DevOps role. Instead of every team having a DevOps engineer, a small Platform team builds an **Internal Developer Platform (IDP)** (Backstage, Humanitec, port.io) that abstracts the toolchain for product teams. This is the *long arc* of DevOps as a discipline: from "you build it, you run it" → "we built the paved road, you walk it."

## 5. AI/ML engineer's angle (Vatsal's lens)

For an AI/ML engineer at a regulated-finance shop (Capital One): you are *not* the DevOps engineer, but you must be **fluent in DevOps**. Why:
- Your model is the artifact; the pipeline (CI → train → eval → register → serve) *is* DevOps.
- Your model serving runs on the same EKS cluster the platform team runs.
- Your security gates (SAST, SCA, image scan, IAM) are the same as any other service.
- Your monitoring (latency, error rate, drift, fairness) flows through the same Prometheus + Grafana.

This topic is **the breadth pass**. Topic 04 (AWS) and Topic 05 (Docker/K8s) were the depth.

## 6. Anti-patterns (the things that get teams labeled "not real DevOps")

- **DevOps as a team.** The whole point is shared ownership. A "DevOps team" is just Ops with a new name unless they're explicitly building the platform.
- **CI without CD.** Pipelines that build but never deploy. The hardest part is automating production deploys safely; if you stop at "tests pass", you're not done.
- **Configuration drift.** Servers tweaked by hand. The fix: IaC + immutable infrastructure (rebuild, never patch).
- **Manual approvals as the only gate.** A human in the loop for *every* deploy = your pipeline is broken. Reserve manual approvals for production crown jewels.
- **No rollback story.** Forward-only deployments fail catastrophically. Every deploy must be reversible.

## 7. Capital One angle

Capital One's public DevOps posture (from talks, blog posts, job listings):
- All-in on AWS since ~2015 (closed last data center 2020).
- Heavy Jenkins (CloudBees CI Enterprise) for CI/CD — ~500k pipelines.
- Internal Terraform + Cloud Custodian (their own OSS) for governance.
- GitHub Enterprise Cloud (not GitLab).
- Internal IDP layer (private; not Backstage publicly).
- DORA metrics tracked per LOB (line of business).

This is the operating environment you're stepping into. Read [Topic 04 CAPITAL_ONE.md](../04_aws_for_ai_ml/CAPITAL_ONE.md) and [Topic 07 CAPITAL_ONE.md](../07_git_github_devops/CAPITAL_ONE.md) alongside this curriculum.

## 8. Quick self-check

1. What are DORA's four (now five) key metrics?
2. What's the difference between DevOps and SRE?
3. Why is "DevOps engineer" a controversial job title?
4. Name three CALMS pillars and give a concrete example of each.
5. What's the difference between "shift left" and "shift everywhere"?

(Answers in [quizzes/part1_quiz.md](quizzes/part1_quiz.md).)



ewpage


# 02 — Operating Systems + Linux Basics

> Cross-link: [Topic 05 Module 1 — Linux primitives](../05_docker_kubernetes/01_linux_primitives.md). This module is a *DevOps-task-driven* refresher — what you actually do in a pipeline, on a Jenkins agent, on a Linux VM.

## Why this module exists

A senior AI/ML engineer can write Python all day but freeze on "find the process eating CPU on this Jenkins agent and kill it." This module is the muscle memory.

## 1. Why Linux dominates DevOps

- **~96% of public cloud workloads** run Linux as of 2025 (AWS, GCP, Azure surveys).
- **~100% of K8s clusters** run Linux node pools (Windows nodes exist but rare).
- **Container runtimes** (runc, containerd, crun) are Linux-kernel-feature-dependent (namespaces, cgroups).
- **Ubuntu LTS** is the default for most dev shops (Ubuntu 24.04 "Noble Numbat" is current LTS, EOL Apr 2029). RHEL/Rocky/Alma for regulated shops. Amazon Linux 2023 for AWS-native.

## 2. Virtualization vs containers

| Concept | VM | Container |
|---|---|---|
| **Isolation** | Hardware (hypervisor) | Process (namespaces + cgroups) |
| **Boot time** | 10s–minutes | Milliseconds |
| **Resource overhead** | ~5–15% | < 1% |
| **OS** | Full guest OS | Shares host kernel |
| **Use case** | Multi-tenant, full isolation | App packaging + portability |

Hypervisors: KVM (Linux kernel module), Xen, VMware ESXi, Hyper-V. Cloud VMs (EC2, GCE, Azure VM) run on these.

## 3. The Linux file system tree (DevOps essentials)

```
/etc/         # config files (nginx.conf, ssh_config, systemd units)
/var/log/     # log files (syslog, auth.log, app logs)
/var/lib/     # persistent app state (docker, postgres, etcd)
/usr/local/bin/  # user-installed binaries
/opt/         # third-party software (often Java apps)
/home/<user>/ # user homes
/tmp/         # ephemeral, world-writable, often cleared on reboot
/proc/        # virtual fs exposing kernel + process info
/sys/         # virtual fs exposing devices + kernel objects
/dev/         # device files (/dev/null, /dev/sda1)
```

When debugging a container: `/proc/<pid>/cgroup` shows which cgroup the process is in (and thus which container).

## 4. The CLI commands you actually use daily

### Filesystem navigation
```bash
ls -lah                # long, all, human-readable
cd -                   # previous directory
pwd                    # where am I
find /var/log -name "*.log" -mtime -1   # logs modified in last day
du -sh /var/lib/docker # disk usage, human-readable
df -h                  # disk free, human-readable
```

### Text + log triage (replace `grep` with `rg` ripgrep)
```bash
rg "ERROR" /var/log/app.log         # ripgrep — 5-10x faster than grep
tail -f /var/log/syslog             # follow live
journalctl -u nginx --since "1 hour ago"  # systemd logs
less +F /var/log/app.log            # follow with scrollback
awk -F'|' '{print $3}' file         # column extract
sed -i 's/old/new/g' file           # in-place substitute
```

### Process + resource
```bash
ps aux | rg python                  # processes
top                                 # real-time CPU/mem; press M for mem-sort
htop                                # nicer top (install separately)
btop                                # modern alternative
kill -9 <pid>                       # SIGKILL
kill -15 <pid>                      # SIGTERM (graceful)
lsof -i :8080                       # what's listening on port 8080
ss -tulpn                           # modern netstat
```

### Pipes + redirects
```bash
cmd1 | cmd2                         # stdout → stdin
cmd > file                          # stdout overwrite file
cmd >> file                         # stdout append
cmd 2> err.log                      # stderr to file
cmd > out.log 2>&1                  # both to file
cmd &> all.log                      # bash shorthand for above
cmd < input.txt                     # stdin from file
```

## 5. Package managers (the DevOps reality)

| Distro | PM | Example |
|---|---|---|
| Ubuntu/Debian | apt | `sudo apt update && sudo apt install -y jq curl` |
| RHEL/CentOS/Rocky | dnf (yum legacy) | `sudo dnf install -y jq` |
| Alpine | apk | `apk add --no-cache jq` |
| Amazon Linux 2023 | dnf | `sudo dnf install -y jq` |
| macOS | brew | `brew install jq` |

For Dockerfiles, prefer Alpine-based images (smaller) unless you need glibc compatibility — then use Debian-slim or Ubuntu-minimal.

## 6. Vim (the survival subset)

You will SSH into a server with no editor but vim. Survive with:

- `i` insert mode, `Esc` back to normal mode
- `:w` save, `:q` quit, `:wq` save+quit, `:q!` quit without saving
- `dd` delete line, `yy` copy line, `p` paste below
- `/pattern` search, `n` next, `N` previous
- `:s/old/new/g` substitute on current line, `:%s/old/new/g` whole file
- `u` undo, `Ctrl+r` redo
- `gg` top, `G` bottom, `:42` go to line 42

For real work, use VS Code with Remote SSH, but vim is the unavoidable fallback.

## 7. Users, groups, permissions

```bash
sudo adduser alice               # create user
sudo usermod -aG sudo alice      # add to sudo group
sudo usermod -aG docker alice    # add to docker group (avoid sudo for docker)
groups alice                     # list user's groups
chmod 755 script.sh              # rwxr-xr-x
chmod +x script.sh               # add execute for all
chown alice:alice file           # change owner + group
```

Permission octal cheat sheet:
- `4` = read, `2` = write, `1` = execute
- `755` = owner rwx, group rx, other rx → standard for executable scripts/dirs
- `644` = owner rw, group r, other r → standard for files
- `600` = owner rw only → SSH keys, sensitive config

## 8. Shell scripting essentials

```bash
#!/usr/bin/env bash
set -euo pipefail   # -e exit on error, -u undefined vars error, -o pipefail
IFS=$'\n\t'         # safe word splitting

# Variables
NAME="world"
echo "Hello, ${NAME}"

# Conditionals
if [[ -f /etc/passwd ]]; then
  echo "exists"
elif [[ "${1:-}" == "test" ]]; then
  echo "test mode"
else
  echo "other"
fi

# Loops
for host in web1 web2 web3; do
  ssh "$host" "uptime"
done

# Functions
deploy() {
  local env="$1"
  echo "deploying to $env"
}
deploy "prod"

# Trap errors
trap 'echo "FAIL on line $LINENO"' ERR
```

Tip: every CI/CD pipeline boils down to "run shell scripts on a Linux box." Mastering bash is the highest-leverage skill for pipeline debugging.

## 9. Environment variables

```bash
export AWS_REGION=us-east-1            # set for current shell + children
echo $AWS_REGION
env | rg AWS                           # all AWS-related env vars
unset AWS_REGION
```

In Jenkins/GitLab/Actions, env vars are how secrets and config flow into your build. The pattern: secrets manager → CI/CD masked variable → env var in build job → app reads it.

## 10. Networking + SSH primer

```bash
ping google.com                       # ICMP
curl -fsSL https://example.com         # HTTP test (fail silently, follow redirects)
dig +short example.com                # DNS lookup
nslookup example.com                  # alternative
traceroute google.com                 # path
mtr google.com                        # mtr = traceroute + ping
```

### SSH
```bash
ssh-keygen -t ed25519 -C "vatsal@laptop"  # generate key (ed25519, not RSA in 2026)
ssh-copy-id user@host                     # copy public key to server
ssh -i ~/.ssh/id_ed25519 user@host        # connect with specific key
ssh -L 8080:localhost:8080 user@host      # local port forward
ssh -A user@host                          # forward agent (use with care)
~/.ssh/config                             # define aliases
```

Sample `~/.ssh/config`:
```
Host bastion
  HostName bastion.example.com
  User vatsal
  IdentityFile ~/.ssh/id_ed25519

Host prod-jump
  HostName 10.0.1.42
  User ec2-user
  ProxyJump bastion
```

## 11. Quick self-check

1. Where do systemd logs live, and what command tails them?
2. What's the difference between `kill -9` and `kill -15`?
3. Which group should you add a user to so they can run docker without sudo?
4. What does `set -euo pipefail` do?
5. Which SSH key algorithm should you generate in 2026 and why not RSA?

(Answers: journalctl + journal log; SIGKILL is immediate, SIGTERM is graceful; `docker` group; exit on error, error on unset, fail pipelines on mid-pipe failure; ed25519 — smaller, faster, simpler than RSA-4096 with equivalent security.)



ewpage


# 03 — Version Control with Git (DevOps angle)

> Cross-link: [Topic 07 Part A — Git fundamentals (Modules 1–7)](../07_git_github_devops/01_git_architecture_objects.md) covers the object model, internals, signing, recovery, hooks. This module is the **DevOps-specific subset**: what your CI/CD pipeline actually does with Git.

## Why this module exists

In a DevOps pipeline, Git is the *trigger* and the *source of truth*. Push to a branch → webhook fires → pipeline runs → artifacts produced. Tag a commit → release pipeline fires. Merge to main → deploy pipeline fires. If Git isn't disciplined, the pipeline is chaos.

## 1. The minimal Git you must know for pipelines

```bash
git clone <url>
git status
git add <files>
git commit -m "msg"
git push origin <branch>
git pull --ff-only             # avoid surprise merges
git checkout -b feat/new-thing
git rebase main                # linear history (most CI/CD pipelines prefer this)
git merge --no-ff branch       # merge commit (some teams prefer this for traceability)
git tag -a v1.2.3 -m "release"
git push origin v1.2.3
```

## 2. Branching strategies (the three serious options)

See [Topic 07 Module 15 — Branching strategies](../07_git_github_devops/15_branching_strategies.md) for the full deep dive. Short version:

| Strategy | When to use | DevOps fit |
|---|---|---|
| **Git Flow** (Vincent Driessen 2010) | Versioned products, slow release cadence | Out of favor; Driessen himself recants for web apps |
| **GitHub Flow** | Web apps, continuous deploy | Default for SaaS |
| **Trunk-based development** | High-velocity teams, feature flags | Industry gold standard 2026; DORA elite teams use this |

Capital One: trunk-based with very-short-lived branches (< 1 day), feature flags, every merge to `main` triggers prod deploy candidate.

## 3. The CI/CD trigger model

The pipeline lifecycle is driven by Git events:

| Event | Trigger |
|---|---|
| `push` to a branch | Run build + tests; deploy to dev if branch is `main` |
| `pull_request` opened/updated | Run build + tests + static analysis; block merge if fail |
| `tag` push (e.g., `v*`) | Run release pipeline; publish artifact |
| `schedule` (cron) | Nightly builds, dependency scans |
| `workflow_dispatch` / manual | Ad-hoc runs |

Webhook configuration: Jenkins, GitLab, GitHub all use HTTP POST from the Git server → CI server endpoint. Secret-shared signature verifies authenticity.

## 4. Merge requests / pull requests as the DevOps gate

The PR (GitHub) / MR (GitLab) is **the** quality gate. CI status checks must pass before merge:
- Lint passes
- Unit tests pass
- Integration tests pass
- SAST scan green
- SCA scan green
- Code review approval (CODEOWNERS-enforced)
- Branch up-to-date with target

**Branch protection** (GitHub) / **Push Rules + Protected Branches** (GitLab) enforce this. See [Topic 07 Module 11 — Branch protection + Rulesets + CODEOWNERS](../07_git_github_devops/11_branch_protection_rulesets_codeowners.md).

## 5. Rebase vs merge — the DevOps debate

Rebase camp:
- Linear history; easier to `git bisect` for failure introduction
- Cleaner GitHub PR list

Merge camp:
- Preserves the *actual* history (when you branched, when you merged)
- Safer for shared branches (rebasing public history rewrites it for everyone)

**The rule of thumb:** rebase your own feature branch onto target *before* opening the PR; merge (or squash-merge) the PR into target. Never rebase a branch others have pulled.

## 6. `.gitignore` for DevOps repos

Essentials for a Python+Terraform+K8s mixed repo:
```
# Python
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/

# Terraform
.terraform/
*.tfstate
*.tfstate.backup
*.tfvars
crash.log

# K8s
kubeconfig
*.kubeconfig

# Editor
.vscode/
.idea/
*.swp
.DS_Store

# Secrets
.env
.env.local
*.pem
*.key
credentials.json

# Build artifacts
dist/
build/
*.egg-info/
```

Add `*.tfvars` not `terraform.tfvars` — sometimes you want a *.example.tfvars in repo.

## 7. Git stash + reflog (recovery skills)

```bash
git stash                       # save uncommitted changes
git stash list
git stash pop                   # apply + drop top stash
git stash apply stash@{0}       # apply specific
git stash branch new-branch     # create branch from stash

git reflog                      # the safety net — every HEAD change for 90 days
git reset --hard HEAD@{5}       # restore HEAD to 5 ago
```

Reflog has saved more careers than any tool. If you `git reset --hard` and lose work, reflog → recover.

## 8. Git hooks for DevOps

- `pre-commit` — run linters, secret scanners locally before commit
- `commit-msg` — enforce Conventional Commits format
- `pre-push` — block pushes that would fail CI
- `post-receive` (server-side) — trigger CI/CD

The **pre-commit framework** (https://pre-commit.com) is the industry standard wrapper. Sample `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=500']
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
      - id: ruff-format
```

Run `pre-commit install` to wire it up, `pre-commit run --all-files` to scan everything.

## 9. Commit signing — required at most regulated shops

SR 11-7 (Federal Reserve model-risk guidance) and SOC 2 both effectively require provable commit attribution. SSH or GPG signed commits provide this.

```bash
# SSH signing (simpler, GitHub-supported since 2022)
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
```

GitHub/GitLab will display "Verified" on signed commits. See [Topic 07 Module 12](../07_git_github_devops/12_auth_pat_ssh_signing.md).

## 10. Resolving merge conflicts (you will, every week)

```bash
git pull origin main           # conflict reported
# Edit files; look for <<<<<<<, =======, >>>>>>> markers
git add <resolved-files>
git commit                     # merge commit auto-message
# OR if rebasing:
git rebase --continue
git rebase --abort             # bail out
```

Conflict markers:
```
<<<<<<< HEAD
my version
=======
their version
>>>>>>> main
```

Use a 3-way merge tool (VS Code's built-in, Beyond Compare, Meld) for non-trivial conflicts.

## 11. Quick self-check

1. What's the difference between `git pull` and `git fetch`?
2. When should you NOT rebase a branch?
3. How do you recover a commit you reset --hard away?
4. What's the most aggressive trunk-based-development rule about branch lifetime?
5. Which Git config makes commits SSH-signed by default?

(Answers: pull = fetch + merge/rebase, fetch is read-only; never rebase branches others have pulled or that are public; `git reflog` then `git reset --hard HEAD@{n}`; ≤ 1 day branch lifetime, integrate to trunk daily; `gpg.format ssh` + `commit.gpgsign true` + `user.signingkey` to public key.)



ewpage


# 04 — Databases in the Development Process

> Nana's curriculum places this as a "bonus" inside Phase 1. For an AI/ML engineer who already runs Snowflake/Databricks/RDS/DynamoDB regularly, this is review — but the **DevOps angle** (where databases fit in the pipeline, schema migrations, backups, secrets) is worth a quick pass.

## 1. Why databases matter to DevOps

A DevOps pipeline touches the database every deploy:
- Schema migrations must run safely (forward AND reversibly)
- Backups must verify (untested backups are not backups)
- Credentials must rotate (secrets manager → app config)
- Test environments need realistic data (anonymized prod or synthetic)
- Production data must never leak into non-prod

## 2. The database landscape in 2026

| Category | Examples | Use case |
|---|---|---|
| **Relational (SQL)** | Postgres, MySQL, SQL Server, Oracle | Default choice; transactional, ACID, joins |
| **Cloud-managed relational** | RDS, Aurora, Cloud SQL, Azure SQL, Supabase, Neon, PlanetScale | Same as above but managed |
| **NoSQL document** | MongoDB, DynamoDB, CosmosDB, Firestore | Flexible schema, sharding by default |
| **NoSQL key-value** | Redis, DynamoDB, Memcached, ElastiCache | Cache, session store, rate limit |
| **NoSQL wide-column** | Cassandra, ScyllaDB, BigTable, Keyspaces | Massive write scale, time-series, sensor |
| **Graph** | Neo4j, Neptune, ArangoDB, TigerGraph | Relationships are the access pattern |
| **Time-series** | InfluxDB, TimescaleDB, Prometheus (internal), VictoriaMetrics | Metrics, IoT, financial ticks |
| **Vector** | Pinecone, Weaviate, Qdrant, Milvus, pgvector, OpenSearch, Atlas Vector Search | RAG, semantic search |
| **Search** | OpenSearch, Elasticsearch, Algolia, Typesense | Full-text + faceting |
| **OLAP / Data Warehouse** | Snowflake, BigQuery, Redshift, Databricks SQL | Analytical queries on TBs+ |
| **Lakehouse** | Databricks (Delta), Iceberg + Trino, S3 Tables | Warehouse-lake hybrid |
| **NewSQL** | CockroachDB, Spanner, Aurora DSQL (May 2025 GA), YugabyteDB | Distributed SQL with strong consistency |

The 2026 vibe: **Postgres has won** the "default OLTP" tier (with all its extensions: pgvector, PostGIS, TimescaleDB, Citus). Anything else needs a justification.

## 3. Schema migrations — the DevOps blocker

Tools:
- **Flyway** (Java, SQL-first, paid + OSS) — banking standard
- **Liquibase** (Java, XML/YAML/JSON/SQL) — banking alternative
- **Alembic** (Python, SQLAlchemy ecosystem) — Python apps
- **golang-migrate** — Go apps
- **Rails Active Record migrations** — Ruby
- **Prisma Migrate** — Node/TS apps
- **DBmate** — language-agnostic, simple

Migration discipline:
1. **Forward-only with backfill, not destructive.** Add column nullable → backfill → mark NOT NULL in next migration → remove old column in third migration. Three deploys, never one.
2. **Migration runs before app deploy.** Pipeline: migrate → deploy → smoke test.
3. **Migrations are tested in CI** against a fresh DB.
4. **Rollback plan documented per migration** (most teams forward-fix; the more disciplined have explicit DOWN migrations tested).

## 4. Database connection patterns in the pipeline

- **Local dev**: `.env` file with DATABASE_URL, gitignored.
- **CI**: ephemeral DB container (Postgres in docker-compose), seeded with fixtures.
- **Staging**: managed instance, anonymized prod snapshot or synthetic data.
- **Production**: managed instance with secrets in Secrets Manager, IAM auth where supported.

```yaml
# docker-compose snippet for CI
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_PASSWORD: ci_password
      POSTGRES_DB: app_test
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 2s
```

## 5. Backups — the production reality

Cloud-managed DBs handle backups for you:
- **RDS / Aurora**: automated backups (1-35 day retention), continuous backup for PITR, manual snapshots
- **DynamoDB**: PITR (35 days), on-demand backups
- **Atlas (MongoDB)**: continuous + scheduled snapshots, queryable backups

Self-managed: `pg_dump`, `pg_basebackup`, `mongodump` on cron + offsite copy.

**The test that matters**: can you actually restore in < your RTO? Run a quarterly restore drill. Capital One does this for every critical system.

## 6. Quick self-check

1. Why is "destructive migration on prod" a DevOps anti-pattern?
2. What's the 3-deploy column-rename pattern?
3. How does DynamoDB PITR differ from on-demand backups?
4. Why is Postgres the 2026 default for OLTP?
5. Where do you store the database password in a Jenkins pipeline?

(Answers: irreversible breakage, no rollback path; add new nullable → backfill → enforce NOT NULL → drop old; PITR = continuous to any second in last 35 days, snapshots = point-in-time copies; battle-tested + ecosystem + extensions; in Jenkins Credentials store referenced by ID, never inline in Jenkinsfile.)



ewpage


# 05 — Build Tools & Package Managers

## Why this module exists

Every CI/CD pipeline starts with "build the artifact." The artifact is what gets deployed. If you can't reproduce the artifact byte-for-byte from a Git SHA, you have a supply-chain liability. This module covers the major language-stack build tools and the principles that survive across them.

## 1. The build-tool landscape by language stack

| Language | Build tool(s) | Lockfile | Artifact |
|---|---|---|---|
| **Java/Kotlin** | Maven (mvn), Gradle | pom.xml / build.gradle | .jar, .war |
| **JavaScript/TypeScript** | npm, pnpm, yarn, Bun | package-lock.json, pnpm-lock.yaml | dist/ bundle |
| **Python** | pip + setuptools, Poetry, **uv** (new dominant), Hatch | requirements.txt, poetry.lock, uv.lock | .whl, .tar.gz |
| **Go** | go (built-in) | go.sum | binary |
| **Rust** | cargo | Cargo.lock | binary |
| **C/C++** | make, cmake, bazel | — | binary |
| **.NET** | dotnet, msbuild | packages.lock.json | .dll |
| **Ruby** | bundler, rake | Gemfile.lock | gem |

In 2026, **uv** (from Astral, Rust-written, ~10-100x faster than pip) has displaced Poetry/pip+pip-tools as the modern Python default. See [Topic 07 Module 18](../07_git_github_devops/18_python_ml_repo_structure.md).

## 2. The four phases every build goes through

1. **Fetch dependencies** — from package registry (npm, PyPI, Maven Central) or private (Nexus, Artifactory, CodeArtifact)
2. **Compile / transpile** — source → bytecode/JS-bundle/binary
3. **Test** — unit + integration; build fails on test fail
4. **Package** — produce the artifact (jar, wheel, container image, zip)

CI/CD pipelines may add: lint, format, type-check, SAST, SCA, image scan, sign, push to registry.

## 3. Reproducible builds — the unattainable but essential ideal

A build is **reproducible** if rebuilding from the same source produces the same artifact bytes. Why it matters:
- Supply-chain attack detection — if your artifact's hash changes without source change, something is wrong
- SLSA compliance levels
- Debugging — "the build last week worked but this week's doesn't" → narrow to env, not source

Practical reproducibility hurdles:
- **Timestamps** in artifacts (use SOURCE_DATE_EPOCH)
- **Random IDs** in dist tar
- **Float-typing locale-dependence** (LC_ALL=C)
- **Mutable dependencies** (lockfiles partially help)
- **Build-tool versions** (pin in CI: `actions/setup-python@v5 with: python-version-file: .python-version`)

Tooling: Nix (most reproducible), Bazel (Google's), buildah/podman for containers, Renovate to manage lockfile drift.

## 4. Lockfiles — the supply chain's first line

```
requirements.txt        → loose, pip-tools or uv generates pinned
poetry.lock             → exact resolution of dep tree
uv.lock                 → uv's exact resolution
package-lock.json       → npm exact resolution
pnpm-lock.yaml          → pnpm
go.sum                  → Go exact (cryptographic hashes!)
Cargo.lock              → Rust
```

Rule: **always commit the lockfile** for applications. **Never commit the lockfile** for libraries (let the consumer resolve). Renovate / Dependabot bump these for you.

## 5. Building JavaScript applications (the modern stack)

Build tools have consolidated around fast Rust/Go-written native bundlers:
- **Vite** — dominant for SPAs in 2026
- **esbuild** — Vite's underlying bundler
- **swc** — Rust-written replacement for Babel
- **Rspack** / **Turbopack** — Rust-written Webpack-compatible

The old guard (Webpack, Babel, Rollup, Gulp, Grunt) is legacy maintenance now.

```bash
# Modern Vite-based React/Vue/Svelte app
npm create vite@latest my-app
cd my-app
npm install
npm run dev    # dev server (HMR)
npm run build  # production bundle (dist/)
```

## 6. Build tools in Docker

The pattern: multi-stage build. Stage 1 builds; stage 2 packages just the artifact + runtime.

```dockerfile
# Stage 1: build
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: runtime (smaller, no build tools)
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

Smaller image, smaller attack surface, faster pull.

## 7. Publishing artifacts

Common destinations:
- **Maven Central / Sonatype OSSRH** — Java
- **npmjs.com** — JS
- **PyPI** — Python
- **Docker Hub / GHCR / ECR / GAR / ACR** — containers
- **Crates.io** — Rust
- **Internal Nexus / Artifactory / CodeArtifact / GitHub Packages** — private artifacts

Versioning: **Semantic Versioning** (semver) — MAJOR.MINOR.PATCH. Pre-release suffixes (`-alpha.1`, `-rc.2`). Build metadata (`+sha.deadbeef`).

In CI: `version = git describe --tags --abbrev=7` produces `v1.2.3-5-g0a1b2c3` automatically.

## 8. Quick self-check

1. What replaced Poetry as the modern Python default in 2025-2026 and why?
2. Why is `npm ci` preferred over `npm install` in CI?
3. What is a multi-stage Docker build and why use it?
4. What does SOURCE_DATE_EPOCH do for reproducible builds?
5. When should you commit a lockfile vs not?

(Answers: uv — much faster, single binary, lockfile-first; ci uses lockfile exactly, fails on mismatch, doesn't write to lockfile; build artifact in one stage, runtime in another → smaller image; fixes timestamps in artifacts to a known value; commit for apps, don't commit for libs.)



ewpage


# 06 — Cloud & Infrastructure as a Service (DigitalOcean lens)

## Why this module exists

Nana picks DigitalOcean for her bootcamp because it's the cheapest way for a learner to spin up a real Linux VM ($4-6/mo droplets). The principles transfer to EC2/Compute Engine/Azure VM — and from a Capital One perspective, AWS EC2 is the production reality. This module is the bridge.

## 1. The IaaS / PaaS / SaaS taxonomy

| Layer | You manage | Examples |
|---|---|---|
| **On-prem** | Everything: power, network, hardware, OS, runtime, app | Your data center |
| **IaaS** | OS, runtime, app | EC2, GCE, Azure VM, DigitalOcean Droplets |
| **PaaS** | App + config | App Engine, App Runner, Render, Fly.io, Vercel |
| **CaaS** | Container + config | ECS, Cloud Run, Fargate, Container Apps |
| **FaaS** | Function + event | Lambda, Cloud Functions, Azure Functions |
| **SaaS** | Nothing — just use it | Snowflake, Salesforce, GitHub, Notion |

The boundary you choose determines your team's ops burden.

## 2. DigitalOcean essentials (cheap learning lab)

- **Droplet**: their VM. Smallest = $4/mo (1vCPU, 512MB), reasonable = $6/mo (1vCPU, 1GB).
- **Spaces**: their S3-compatible object storage ($5/mo for 250GB).
- **Managed K8s (DOKS)**: free control plane, pay for nodes (cheap for learning).
- **Managed Databases**: Postgres / MySQL / Redis / MongoDB.
- **App Platform**: their PaaS, similar to Heroku.

Why use it? Sandbox + learning. **Not** for serious production at scale (~10% of AWS's service breadth).

## 3. The "set up a server" lifecycle (universal across IaaS)

```bash
# 1. Provision (DO CLI, AWS CLI, etc.)
doctl compute droplet create web1 \
  --region nyc3 --size s-1vcpu-1gb --image ubuntu-24-04-x64 \
  --ssh-keys "your-key-id" --enable-monitoring

# Or AWS:
aws ec2 run-instances --image-id ami-0abc \
  --instance-type t3.micro --key-name mykey \
  --security-group-ids sg-0abc --subnet-id subnet-0abc

# 2. Connect
ssh root@<ip>     # DO uses root by default; AWS uses ec2-user or ubuntu

# 3. Initial hardening (every server, every time)
adduser deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# Disable root SSH + password auth
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Updates
apt update && apt upgrade -y
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

## 4. Deploying an artifact on a Droplet (the manual baseline)

```bash
# As deploy user
scp app-1.2.3.jar deploy@<ip>:/opt/app/
ssh deploy@<ip>
sudo systemctl restart app
```

This works once. It does NOT scale. The next 10 modules of this curriculum are about replacing this manual flow with: Jenkins → build artifact → push to Nexus → deploy to EC2 via Ansible → containerize → K8s → IaC → GitOps.

## 5. Cloud-init — the bootstrap mechanism

Most clouds let you pass a "user-data" script that runs on first boot:

```bash
#!/bin/bash
apt update
apt install -y docker.io
systemctl enable --now docker
usermod -aG docker ubuntu
```

This script bakes baseline config into the VM at provisioning time. It's the simplest form of configuration management; Ansible (Module 16) is the more powerful version.

## 6. From IaaS to immutable infrastructure

The 2026 best practice: **never SSH into a server to fix something**. Instead:
- Build a new AMI (Packer) or container image (Docker) with the fix
- Roll out via auto-scaling group / K8s rolling update
- Old instances terminated

Why: ephemeral, reproducible, auditable. The "Cattle vs Pets" metaphor — your servers are interchangeable cattle, not beloved pets you name and nurse back to health.

## 7. AWS equivalents at a glance

| DO concept | AWS equivalent |
|---|---|
| Droplet | EC2 instance |
| Spaces | S3 |
| DOKS | EKS |
| Managed Postgres | RDS |
| App Platform | App Runner (or Elastic Beanstalk for older shops) |
| Load Balancer | ALB / NLB |
| VPC | VPC (same name) |
| Floating IP | Elastic IP |

See [Topic 04 — AWS for AI/ML Engineers](../04_aws_for_ai_ml/) for the full AWS depth.

## 8. Quick self-check

1. What's the difference between IaaS and PaaS?
2. What does "cattle vs pets" mean?
3. Name three baseline hardening steps for a new Ubuntu droplet.
4. What's cloud-init / user-data?
5. Why isn't `scp + ssh + systemctl restart` enough for production deploys?

(Answers: IaaS = OS+up; PaaS = app+up; treat servers as fungible not unique; create non-root user, disable root SSH, ufw firewall + unattended-upgrades; bootstrap script run on first boot; manual, error-prone, no rollback, no audit trail, doesn't scale.)



ewpage


# 07 — Nexus — Artifact Repository Manager

> One of the "net-new" modules where Nana adds genuine value vs. the rest of this project. Most modern AWS-native shops have moved off Nexus to CodeArtifact + ECR + GitHub Packages, but Nexus still dominates regulated finance and on-prem.

## Why this module exists

Every CI/CD pipeline produces artifacts (jars, wheels, container images, npm packages, helm charts). Those artifacts need a home that:
- Stores immutable, versioned binaries
- Authenticates pull access (private repos)
- Proxies/caches public registries (so you're not dependent on npmjs.com being up)
- Integrates with build tools (Maven, npm, pip)

Sonatype Nexus Repository is the longest-standing answer. JFrog Artifactory is its closest competitor. Cloud-native shops use AWS CodeArtifact, GitHub Packages, Azure Artifacts, or GitLab Package Registry instead. *(Cap One uses JFrog Artifactory + ECR.)*

## 1. The artifact-repo categories

| Category | Why |
|---|---|
| **Hosted** | You publish to it (e.g., releases of your in-house libs) |
| **Proxy** | Caches a public registry (Maven Central, npmjs, PyPI) |
| **Group** | Virtual repo that aggregates multiple of the above (single URL for clients) |

A typical setup: `releases` (hosted, immutable), `snapshots` (hosted, mutable), `maven-central-proxy` (cache), and `maven-public` (group containing the above). Clients point at `maven-public`.

## 2. The Nexus 3 supported formats

Nexus 3 is format-agnostic: same engine, many formats:
- Maven 2/3 (Java)
- npm
- PyPI
- Docker (private container registry)
- Helm
- NuGet, RubyGems, Conan, Apt, Yum, Bower, Go, Conda, p2, R, raw

This is the *killer feature*: one tool for every artifact type. Same UI, same RBAC, same backup.

## 3. Concepts: Blob Store, Component, Asset

- **Blob Store**: where the actual bytes live. File-system based by default; can also be S3-backed (Pro feature, popular for cloud deploys).
- **Component**: a versioned thing (e.g., `com.example:my-lib:1.2.3`).
- **Asset**: the actual files in that component (e.g., the `.jar`, the `.pom`, the `-sources.jar`, the `-javadoc.jar`).

A component can have many assets. Cleanup policies operate on component age, asset count, etc.

## 4. Cleanup policies (the storage-cost lever)

Without cleanup, Nexus storage grows linearly forever. Define policies:
- "Delete snapshot artifacts older than 30 days that are not the latest"
- "Delete Docker images older than 90 days unless tagged `latest` or `stable`"
- "Delete components with no downloads in 180 days"

Run as scheduled tasks. Audit before deleting (dry-run mode).

## 5. REST API for automation

Nexus exposes a REST API:
```bash
# Upload a Maven artifact
curl -u admin:password -X POST \
  -F "maven2.groupId=com.example" \
  -F "maven2.artifactId=demo" \
  -F "maven2.version=1.2.3" \
  -F "maven2.asset1=@target/demo-1.2.3.jar" \
  -F "maven2.asset1.extension=jar" \
  "https://nexus.example.com/service/rest/v1/components?repository=releases"

# Search
curl "https://nexus.example.com/service/rest/v1/search?repository=releases&name=demo"

# Delete
curl -u admin:password -X DELETE \
  "https://nexus.example.com/service/rest/v1/components/<component-id>"
```

In a Jenkins pipeline, the `nexus-artifact-uploader` plugin wraps this.

## 6. Production deployment patterns

### Single-node (dev/small team)
```bash
docker run -d --name nexus \
  -p 8081:8081 \
  -v /opt/nexus-data:/nexus-data \
  sonatype/nexus3:3.74.0
# Get initial admin password
docker exec nexus cat /nexus-data/admin.password
```

### Production (regulated org)
- HA with replicated blob store (Nexus Pro)
- S3-backed blob store for cheap archive tier
- Behind reverse proxy (Nginx/Caddy) with TLS
- LDAP/SAML auth (Pro)
- Backup blob store + DB regularly
- Monitor via Prometheus exporter

## 7. Nexus vs alternatives (2026)

| Tool | Strengths | Weaknesses |
|---|---|---|
| **Nexus OSS** | Free, all formats, mature | Manual scaling, OSS feature gaps |
| **Nexus Pro** | HA, staging, IQ Server (SCA) | $$$$ |
| **JFrog Artifactory** | Best UI, best HA, dominant enterprise | $$$$$ (even more) |
| **GitHub Packages** | Free with GitHub, ties to repo permissions | Limited formats (npm, container, maven, nuget, rubygems) |
| **AWS CodeArtifact** | Native AWS IAM, S3-backed, pay-per-storage | Limited formats, AWS-only |
| **GitLab Package Registry** | Free with GitLab, integrates with pipelines | Best if you're all-in on GitLab |
| **Azure Artifacts** | Native AAD, ties to ADO | Azure-only |

### Decision framework

- **All-AWS shop**: CodeArtifact + ECR
- **All-GitHub shop**: GitHub Packages + GHCR
- **All-GitLab shop**: GitLab Package Registry
- **Multi-cloud or on-prem**: Nexus OSS (small) or JFrog Artifactory (large)
- **Regulated finance**: JFrog Artifactory (90%+ market share in that segment)

## 8. SCA + Nexus IQ Server (different product)

Sonatype sells **Nexus IQ Server** separately — a SCA scanner that audits open-source components for known vulnerabilities and license issues. Competes with Snyk, JFrog Xray, GitHub Dependabot + GHAS.

In a regulated pipeline: every build's dependencies get scanned; vulnerable releases blocked from promotion to production-grade Nexus repos.

## 9. Nexus + Docker (private container registry)

```bash
# Configure a Docker hosted repo on port 5000 (internal)
# Then push:
docker login nexus.example.com:5000
docker tag myapp:1.2.3 nexus.example.com:5000/myapp:1.2.3
docker push nexus.example.com:5000/myapp:1.2.3
```

This is the "self-hosted ECR equivalent." Almost any K8s cluster can pull from it (with imagePullSecrets).

## 10. Quick self-check

1. What are the three repo types in Nexus and what's each for?
2. What's the difference between a Component and an Asset?
3. Why use a Group repo?
4. Name three Nexus alternatives and when you'd pick each.
5. What's the relationship between Nexus Repository and Nexus IQ Server?

(Answers: hosted (you publish), proxy (caches public), group (aggregates many into one URL); component = versioned thing, asset = individual file in the component; single URL for clients regardless of where artifact lives; CodeArtifact for AWS-native, GitHub Packages for GitHub-native, JFrog Artifactory for regulated finance; Repository stores artifacts, IQ Server scans them for vulns/license issues — separate products.)



ewpage


# 08 — Containers with Docker

> Cross-link: [Topic 05 Modules 1–11](../05_docker_kubernetes/01_linux_primitives.md) cover Docker exhaustively: Linux primitives, dockerd→containerd→runc→OCI, Dockerfile patterns, image security (Trivy/Cosign/SLSA/SBOM), registries, networking, storage, secrets, Compose, hardening checklist, CIS, CVEs.
>
> This module is a **Nana-Janashia-flavored DevOps refresher**: the workflow-driven slice — what you actually do in a CI pipeline.

## 1. The 2026 container reality

- **Docker Inc.** still makes Docker Desktop; Docker CE (the CLI/daemon) is in the OSS / Mirantis hand.
- **Docker Hub** still hosts most public images; pull-rate limits (100/6hr unauth, 200/6hr free auth) drive teams to mirror via Nexus/Artifactory.
- **containerd + nerdctl** is the K8s default; the `docker` CLI on a K8s node may not exist.
- **Podman** is a serious daemonless alternative (Red Hat-led); rootless-by-default.
- **BuildKit / buildah** for builds; Docker Desktop uses BuildKit by default.
- **OCI** (Open Container Initiative) — the standard. Docker images are OCI images.

## 2. Container vs Image vs VM

- **Image** = immutable, layered, content-addressed filesystem + metadata. The blueprint.
- **Container** = running instance of an image. Process(es) isolated via Linux namespaces + cgroups.
- **VM** = full guest OS via hypervisor. Heavier, slower, more isolated.

Container vs VM, quick:
| | VM | Container |
|---|---|---|
| Boot | 30s–min | ms |
| Overhead | 5-15% | <1% |
| Isolation | Hardware | Process |
| Density per host | 10s | 100s–1000s |

## 3. Main Docker commands (the ones you actually use)

```bash
# Images
docker pull nginx:1.27-alpine
docker images
docker rmi <image>
docker image prune -a               # delete unused

# Containers
docker run -d --name web -p 8080:80 nginx:1.27-alpine
docker ps
docker ps -a                        # include stopped
docker stop web
docker rm web
docker logs -f web

# Exec into a running container
docker exec -it web sh

# Inspect
docker inspect web | jq '.[0].NetworkSettings'

# Cleanup
docker system prune -a --volumes    # nukes unused images, containers, networks, volumes
```

## 4. Dockerfile — the production patterns

```dockerfile
# Multi-stage; pinned versions; non-root user
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.13-slim
RUN useradd -m -u 10001 app
WORKDIR /app
COPY --from=builder /root/.local /home/app/.local
COPY --chown=app:app . .
USER app
ENV PATH=/home/app/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:8000/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Patterns that matter:
- **Multi-stage** — build tools stay in builder; runtime image stays small.
- **Pin versions** — `python:3.13-slim` not `python:slim`; pin to digest in CI for true immutability.
- **`--no-cache-dir`** for pip; cleanup apt cache.
- **Non-root user** — required by Pod Security Standards `restricted`.
- **`COPY` then `RUN pip install`** — only the requirements.txt change re-runs install (layer caching).
- **`.dockerignore`** — exclude `.git/`, `__pycache__/`, `*.pyc`, `.env`, `node_modules/`.
- **`HEALTHCHECK`** — for Compose/Swarm; K8s uses its own probes.
- **Single concern per container** — don't run sshd + cron + app in one container.

## 5. Docker Compose (multi-container local dev)

```yaml
# compose.yaml — note no version: key (Compose Spec, Compose v2)
services:
  api:
    build: ./api
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://app:app@db:5432/appdb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: appdb
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 2s
      retries: 5

volumes:
  db-data:
```

```bash
docker compose up -d
docker compose logs -f api
docker compose down -v       # -v also removes volumes
```

In 2026 use `docker compose` (v2, Go-written, plugin) not the legacy `docker-compose` (v1, Python).

## 6. Private Docker registries

Push to private registry (Nexus, ECR, GHCR, ACR, GAR, Harbor):
```bash
docker login nexus.example.com:5000 -u admin
docker tag myapp:1.2.3 nexus.example.com:5000/myapp:1.2.3
docker push nexus.example.com:5000/myapp:1.2.3
```

In Jenkins/GitLab/Actions: use a credential store, not `docker login` with literal passwords. AWS ECR specifically uses short-lived tokens via `aws ecr get-login-password`.

## 7. Docker Volumes (persisting state)

Three options:
- **Named volumes** — Docker-managed (`docker volume create`); preferred for portability
- **Bind mounts** — host path mounted into container; useful for local dev
- **tmpfs** — RAM-backed, ephemeral

```bash
docker run -d --name db -v db-data:/var/lib/postgresql/data postgres:17
```

In K8s, this becomes PV/PVC; see [Topic 05 Module 19](../05_docker_kubernetes/19_k8s_storage.md).

## 8. Deploying Docker on a server (Nana's bootcamp path)

The bootcamp progression: build locally → push to Nexus → SSH into droplet → docker pull → docker run. This is the **manual baseline** before Jenkins automates it.

```bash
# On the server
ssh deploy@server
docker login nexus.example.com:5000
docker pull nexus.example.com:5000/myapp:1.2.3
docker stop myapp || true
docker rm myapp || true
docker run -d --name myapp --restart=unless-stopped \
  -p 80:8000 nexus.example.com:5000/myapp:1.2.3
```

Better: use `docker compose` + a `compose.yaml` per environment.
Best: containerize + ship to K8s + GitOps deploy (Module 33 — ArgoCD).

## 9. Docker Best Practices (the 12-point checklist)

1. **Multi-stage builds** to minimize image size + attack surface
2. **Pin base image versions** (digest-pin for production)
3. **Non-root user** (`USER app`, not `USER root`)
4. **`.dockerignore`** to exclude secrets + bloat
5. **Combine RUN steps** to minimize layers; clean up in same step
6. **`COPY` deps before app code** for layer caching
7. **Health checks** in Dockerfile + at K8s probe level
8. **No secrets baked in** — use BuildKit secret mount or runtime env
9. **Sign images** (Cosign) and verify at deploy (admission control)
10. **Scan images** (Trivy, Snyk, ECR enhanced) — fail build on Critical CVEs
11. **SBOM generation** (`docker buildx build --sbom=true`)
12. **Distroless** or `chainguard-images` for ultra-minimal runtime

## 10. Quick self-check

1. What's the difference between an image and a container?
2. Why use a multi-stage Dockerfile?
3. What's the difference between a Docker volume and a bind mount?
4. Why is `docker-compose` (v1) deprecated in favor of `docker compose` (v2)?
5. Name three things you should never bake into a Docker image.

(Answers: image is immutable blueprint, container is running instance; smaller final image, no build tools in runtime, faster pull; volume Docker-managed and portable, bind mount tied to host path; v2 is Go-rewrite + plugin to docker CLI, v1 is unmaintained Python; secrets, source-control history, build tools (unless multi-stage), cleartext credentials.)



ewpage


# 09 — Jenkins — Build Automation & CI/CD

> Cross-link: [Topic 07 Modules 49–51](../07_git_github_devops/49_jenkins_architecture_jenkinsfile.md) cover Jenkins architecture, Jenkinsfile, multibranch + shared libraries, and credentials/GH→Jenkins→AWS pipelines.
>
> This module is the **Nana-flavored sweep**: every Jenkins concept she covers, in one tight pass.

## 1. Why Jenkins still matters in 2026

Despite Actions and GitLab CI eating share, Jenkins still runs ~50% of CI/CD globally and ~80% of regulated finance. Capital One: ~500k pipelines on CloudBees CI Enterprise. The reasons it survives:

- **Plugin ecosystem** — 1800+ plugins, every conceivable integration.
- **Self-hostable, air-gappable** — works in regulated/disconnected environments.
- **Battle-tested at scale** — runs 50k+ builds/day in big shops.
- **Familiar to senior engineers** — entrenched skill base.

Drawbacks: groovy DSL footguns, single-master scaling pain (mitigated by CloudBees CI multi-master), plugin churn + security CVEs.

## 2. Installing Jenkins

The modern way: **on Kubernetes** via the Helm chart or the JCasC + JenkinsFile approach.

The classroom way (Nana's): on Ubuntu via apt:
```bash
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | \
  sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y openjdk-17-jre jenkins
sudo systemctl enable --now jenkins
# Initial password:
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Java 17 is the minimum since LTS 2.452.x (April 2024). Java 21 supported.

## 3. Jenkins core concepts

- **Controller (formerly "master")** — runs the UI, schedules builds, stores config + history
- **Agent (formerly "slave")** — executes builds; can be ephemeral (Docker, K8s pods, EC2)
- **Job / Pipeline** — a unit of work
- **Build / Run** — execution of a job
- **Workspace** — directory on the agent where source is checked out + builds happen
- **Executor** — slot for running a build on an agent

## 4. Job types

| Type | When to use |
|---|---|
| **Freestyle** | Legacy; UI-driven; minimal scripting; avoid for new projects |
| **Pipeline (Jenkinsfile)** | The modern way; code-as-config in repo |
| **Multibranch Pipeline** | Auto-detects branches in a repo, runs Jenkinsfile per branch — modern default |
| **Folder / Organization Folder** | Scans whole GitHub org / GitLab group |
| **Maven / Gradle Project** | Specialized for those build tools; less common in 2026 |

Modern Jenkins = **Multibranch Pipeline** + **Jenkinsfile** in repo + **Shared Library** for common logic.

## 5. Jenkinsfile syntax — Declarative pipeline

```groovy
pipeline {
  agent { docker { image 'python:3.13-slim' } }
  options {
    timeout(time: 30, unit: 'MINUTES')
    timestamps()
    ansiColor('xterm')
  }
  environment {
    APP_NAME = 'myapp'
    REGISTRY = 'nexus.example.com:5000'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Install') {
      steps { sh 'pip install -r requirements.txt' }
    }
    stage('Test') {
      steps { sh 'pytest --junitxml=test-results.xml' }
      post { always { junit 'test-results.xml' } }
    }
    stage('Build Image') {
      steps {
        sh "docker build -t ${REGISTRY}/${APP_NAME}:${env.BUILD_NUMBER} ."
      }
    }
    stage('Push Image') {
      when { branch 'main' }
      steps {
        withCredentials([usernamePassword(credentialsId: 'nexus-creds',
            usernameVariable: 'U', passwordVariable: 'P')]) {
          sh '''
            echo "$P" | docker login $REGISTRY -u "$U" --password-stdin
            docker push $REGISTRY/$APP_NAME:$BUILD_NUMBER
          '''
        }
      }
    }
    stage('Deploy') {
      when { branch 'main' }
      steps {
        input message: 'Deploy to prod?', ok: 'Go'
        sh "./deploy.sh ${BUILD_NUMBER}"
      }
    }
  }
  post {
    failure { slackSend(channel: '#deploys', color: 'danger', message: "FAILED ${env.JOB_NAME} #${env.BUILD_NUMBER}") }
    success { slackSend(channel: '#deploys', color: 'good', message: "OK ${env.JOB_NAME} #${env.BUILD_NUMBER}") }
  }
}
```

The two flavors:
- **Declarative** (`pipeline { ... }`) — opinionated, validated, easier — use this.
- **Scripted** (`node { ... }`) — Groovy script, more flexible, more rope. Only when declarative can't express what you need.

## 6. Multibranch pipelines

Configure a multibranch job pointing at a Git repo. Jenkins scans the repo, finds each branch with a `Jenkinsfile`, creates a sub-job per branch. PRs (in GitHub multibranch source plugin) also become sub-jobs. Each branch's Jenkinsfile runs that branch's pipeline.

This is how you get "every branch, every PR builds automatically" without manual job-per-branch config.

## 7. Credentials in Jenkins

Use the **Credentials Store** (built-in or HashiCorp Vault integration via plugin). Refer to credentials by **ID** in Jenkinsfile:

```groovy
withCredentials([
  string(credentialsId: 'aws-secret-access-key', variable: 'AWS_SECRET_ACCESS_KEY'),
  string(credentialsId: 'aws-access-key-id', variable: 'AWS_ACCESS_KEY_ID')
]) {
  sh 'aws s3 ls'
}
```

For AWS specifically, prefer **OIDC + IAM Role** (Jenkins agents assume role) over long-lived access keys. See [Topic 07 Module 51](../07_git_github_devops/51_jenkins_credentials_ghaws.md).

## 8. Jenkins Shared Library — DRY across pipelines

A Git repo with `vars/` (global pipeline steps) and `src/` (Groovy classes), referenced from any Jenkinsfile:

```groovy
@Library('my-org-library@v1.4') _

pipeline {
  agent any
  stages {
    stage('Build') { steps { myBuildStep() } }
    stage('Deploy') { steps { myDeployStep(env: 'prod') } }
  }
}
```

`myBuildStep()` is defined in the shared library's `vars/myBuildStep.groovy`. This is how big shops keep 1000 pipelines DRY.

## 9. Webhooks (auto-trigger pipelines)

Configure on the Git server: GitHub → Settings → Webhooks → URL = `https://jenkins.example.com/github-webhook/`. Push to repo → webhook fires → Jenkins multibranch detects new SHA → builds.

For self-hosted GitLab → Jenkins: `https://jenkins.example.com/project/<job-name>` with GitLab token.

## 10. Dynamic versioning in Jenkins

The pattern:
```groovy
def version = sh(returnStdout: true, script: 'git describe --tags --abbrev=7').trim()
echo "Building version ${version}"
```

Or auto-increment via Maven Release Plugin / npm version / `git tag` + push from pipeline. Tag-driven release pipelines are the modern norm; "build number" alone is fragile.

## 11. Docker-in-Jenkins (the agents-on-K8s pattern)

Jenkins on K8s with the **kubernetes plugin**: each build spins up a pod with whatever containers you need:

```groovy
pipeline {
  agent {
    kubernetes {
      yaml '''
        apiVersion: v1
        kind: Pod
        spec:
          containers:
          - name: python
            image: python:3.13-slim
            command: ["sleep","infinity"]
          - name: docker
            image: docker:27-cli
            command: ["sleep","infinity"]
            volumeMounts:
            - name: docker-sock
              mountPath: /var/run/docker.sock
          volumes:
          - name: docker-sock
            hostPath:
              path: /var/run/docker.sock
      '''
    }
  }
  stages { stage('Build') { steps { container('docker') { sh 'docker build ...' } } } }
}
```

This is the **autoscaling Jenkins** answer — no idle agents.

## 12. Jenkins anti-patterns

1. **Storing secrets in Jenkinsfile** — use Credentials Store
2. **Long-lived agents** — prefer ephemeral (K8s pods, EC2 ASG)
3. **`master` branch builds via cron only** — webhook + multibranch
4. **No shared library** — copy-paste pipelines breed bugs
5. **Plugin sprawl** — every plugin is attack surface; audit + prune
6. **Direct kubectl from pipeline** — prefer GitOps (push manifests, ArgoCD pulls)

## 13. Quick self-check

1. What's the difference between declarative and scripted pipeline syntax?
2. What does a multibranch pipeline give you over a regular Pipeline job?
3. Where do credentials live in Jenkins and how do you reference them?
4. What is a Shared Library and what problem does it solve?
5. Why is ephemeral K8s-pod agents preferred over long-lived EC2 agents?

(Answers: declarative is opinionated YAML-ish DSL, scripted is full Groovy; auto-discover branches and PRs, run Jenkinsfile per; in Credentials Store, by `credentialsId`; reusable steps + classes across many pipelines; cost + reproducibility + clean state every build.)



ewpage


# 10 — AWS Services for DevOps

> Cross-link: [Topic 04 — AWS for AI/ML Engineers (57 modules)](../04_aws_for_ai_ml/) is the deep dive. This module is the **DevOps-focused subset** — the 12 services every CI/CD pipeline touches.

## 1. The DevOps-essential AWS services

| Service | Why DevOps cares |
|---|---|
| **IAM** | Who can do what; principle of least privilege |
| **EC2** | Compute for build agents, deploys |
| **VPC + Subnets + SGs** | Network isolation |
| **S3** | Artifact storage, Terraform state, log archives |
| **ECR** | Private container registry |
| **EKS / ECS / Fargate** | Container orchestration |
| **Lambda** | Event-driven automation |
| **CloudWatch** | Logs + metrics + alarms |
| **CloudTrail** | API audit log (security) |
| **Secrets Manager + Parameter Store** | Secret storage |
| **Systems Manager (SSM)** | Patch, SSH-less shell, parameter store |
| **CodeBuild / CodePipeline / CodeDeploy** | AWS-native CI/CD (less popular than Jenkins/GitLab/Actions but exists) |

See [Topic 04 README](../04_aws_for_ai_ml/README.md) for full scope.

## 2. Creating an AWS account (the production way)

Don't use the root account for daily work. Set up:
1. Root account: MFA on a hardware key (YubiKey), used only for billing changes.
2. **AWS Organizations** + multiple accounts (one per env: dev/staging/prod or one per team).
3. **AWS Control Tower** (preferred for new orgs in 2026) sets up baseline guardrails.
4. **IAM Identity Center** (formerly AWS SSO) for human user access.
5. **Service Control Policies (SCPs)** at OU level for deny-by-default policies.

Capital One: hundreds of AWS accounts under a single Organization, with Control Tower + Custodian governance.

## 3. IAM essentials for DevOps

- **Users** — long-lived identities; humans should use Identity Center SSO instead
- **Groups** — collections of users sharing permissions
- **Roles** — temporary credentials, assumed by services or federated principals
- **Policies** — JSON documents granting/denying actions
- **Permission Boundaries** — max-permissions cap on a role
- **Resource-based policies** — attached to S3 buckets, KMS keys, etc.

The 2026 pattern for CI/CD: **OIDC + IAM Role**, never long-lived access keys.
- GitHub Actions → OIDC → AssumeRoleWithWebIdentity → role
- GitLab CI → OIDC → role
- Jenkins on EC2/EKS → instance profile or pod identity → role

See [Topic 07 Module 46](../07_git_github_devops/46_aws_oidc_trust_policy_deep.md) for the trust-policy deep dive.

## 4. Regions, AZs, Edge

- **Region** — a geographic area (us-east-1, eu-west-1). Independent failure domain.
- **Availability Zone (AZ)** — datacenter cluster within a region. 3+ AZs per region. Independent power/network within a region.
- **Edge locations** — CloudFront PoPs (200+ globally).
- **Local Zones** — sub-region extensions (us-east-1-bos-1a in Boston).
- **Outposts** — AWS hardware in your data center.

DevOps rule: **multi-AZ by default** for prod workloads. Multi-region only when business requires it (cost + complexity).

## 5. VPC + networking essentials

A VPC is your private network in AWS. Default VPC exists per region; for serious work, create your own.

```
VPC: 10.0.0.0/16
├── Public Subnet (us-east-1a): 10.0.1.0/24    → has route to IGW
├── Public Subnet (us-east-1b): 10.0.2.0/24    → has route to IGW
├── Private Subnet (us-east-1a): 10.0.11.0/24  → routes via NAT GW
├── Private Subnet (us-east-1b): 10.0.12.0/24  → routes via NAT GW
└── Subnets per service tier (db, lb, app)
```

- **Internet Gateway (IGW)** — public subnets attach to this for inbound/outbound internet
- **NAT Gateway** — private subnets reach internet outbound only
- **VPC Endpoints (Gateway + Interface)** — reach AWS services privately (S3, ECR, SSM)
- **Security Groups** — stateful instance-level firewall
- **NACLs** — stateless subnet-level firewall (use sparingly)

See [Topic 04 Part B](../04_aws_for_ai_ml/) for the full networking depth.

## 6. CIDR blocks (the math you'll do)

`10.0.0.0/16` = 65,536 IPs. `/24` = 256 IPs. `/28` = 16 IPs.

VPC must be in RFC1918 ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`. Don't use overlapping CIDRs across VPCs you'll peer.

## 7. EC2 essentials

- **Instance type families** — t (burstable, cheap), m (general), c (compute), r (memory), p/g (GPU)
- **Pricing models** — On-Demand, Spot (up to 90% off, can be reclaimed), Reserved, Savings Plans
- **AMI** — Amazon Machine Image; Ubuntu/Amazon Linux 2023/RHEL
- **Key Pairs** — SSH keys for initial access (prefer Session Manager + SSM for prod)
- **Instance Profile** — IAM role attached to instance (so app code uses temporary creds)
- **User Data** — cloud-init script on first boot
- **IMDSv2** — instance metadata service; v2 is token-required, mandatory for new instances (mitigates SSRF, Capital One 2019 breach root cause)

## 8. AWS CLI essentials

```bash
aws configure                          # legacy: stores ~/.aws/credentials
aws configure sso                      # modern: SSO-based
aws sts get-caller-identity            # who am I
aws s3 ls                              # list buckets
aws s3 cp local.txt s3://bucket/        # upload
aws ec2 describe-instances --query "Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]" --output table
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 1234.dkr.ecr.us-east-1.amazonaws.com
```

CLI v2 is current (v1 EOL'd 2024). Use `--profile` to switch between roles/accounts.

## 9. ECR (Elastic Container Registry)

- **Private** by default; public registry separate (public.ecr.aws).
- IAM-controlled push/pull.
- Image scanning: basic (Clair-based) + enhanced (Inspector, paid).
- Lifecycle policies for cleanup.
- Cross-region replication.
- ECR Public for OSS images.

Authenticate via short-lived token:
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  1234.dkr.ecr.us-east-1.amazonaws.com
```

## 10. Container services on AWS — the decision matrix

| Service | When |
|---|---|
| **ECS on EC2** | Container orchestration without K8s complexity; AWS-native; deep in 2026 still |
| **ECS on Fargate** | Serverless containers; no node management |
| **EKS** | Kubernetes; cross-cloud portability; ecosystem |
| **App Runner** | Simple PaaS for containers |
| **Lambda (Container image)** | Function as image, max 15min runtime |
| **Batch** | Long-running batch jobs |

Capital One: EKS-dominant for ML serving (KServe), some ECS for legacy.

## 11. AWS + Terraform (preview — full in Module 13)

```hcl
provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "main" }
}

resource "aws_instance" "web" {
  ami           = "ami-0c7217cdde317cfec"  # Ubuntu 24.04 us-east-1
  instance_type = "t3.micro"
  user_data     = file("bootstrap.sh")
}
```

## 12. Quick self-check

1. What's the difference between a Security Group and a NACL?
2. Why is IMDSv2 strictly required in 2026?
3. What's the modern alternative to AWS access keys for CI/CD authentication?
4. Name three reasons to prefer Session Manager over SSH for EC2 access.
5. What's the difference between EKS and ECS?

(Answers: SG is stateful + instance-level, NACL is stateless + subnet-level; mitigates SSRF→credential theft (Capital One 2019); OIDC + IAM Role; no inbound ports, IAM-based auth, fully audited via CloudTrail; EKS is Kubernetes — portable, ecosystem; ECS is AWS-native — simpler ops, locked to AWS.)



ewpage


# 11 — Kubernetes Orchestration

> Cross-link: [Topic 05 Modules 16–25](../05_docker_kubernetes/16_k8s_architecture.md) cover K8s exhaustively. This module is the **Nana-curriculum sweep** — touching every concept her DevOps Bootcamp covers in one pass.
>
> Full CKA depth lives in [Part 5 — Modules 60–80](60_cka_exam_logistics.md).

## 1. What problem does K8s solve

You have 50 containers across 10 nodes. Things to do that don't scale manually:
- Place containers across nodes optimally
- Restart crashed containers
- Replace dead nodes
- Roll out new versions safely (with rollback)
- Scale up/down based on load
- Route traffic to healthy instances
- Expose secrets + config
- Persist data across pod restarts

Kubernetes is the **distributed-systems answer**. Born inside Google (Borg → Omega → K8s), open-sourced 2014, CNCF since 2015, v1.0 in July 2015.

## 2. Core architecture

```
┌──────────────────────────────────────────┐    ┌─────────────────┐
│        Control Plane (HA: 3 nodes)        │    │   Worker Node   │
│  ┌─────────────────────────────────────┐ │    │  ┌───────────┐  │
│  │  kube-apiserver (REST API)         │ │◀───┤  │  kubelet  │  │
│  │  etcd (state)                       │ │    │  └─────┬─────┘  │
│  │  kube-scheduler                      │ │    │        │       │
│  │  kube-controller-manager             │ │    │  ┌─────▼─────┐  │
│  │  cloud-controller-manager (cloud)    │ │    │  │ container │  │
│  └─────────────────────────────────────┘ │    │  │  runtime  │  │
└──────────────────────────────────────────┘    │  │  (cri-o,  │  │
                                                  │  │ containerd│  │
                                                  │  └───────────┘  │
                                                  │  ┌───────────┐  │
                                                  │  │ kube-proxy│  │
                                                  │  └───────────┘  │
                                                  └─────────────────┘
```

- **etcd** — the single source of truth; everything else is stateless
- **kube-apiserver** — the only thing that talks to etcd; all components go through it
- **kube-scheduler** — assigns pods to nodes based on resources + constraints
- **controller-manager** — runs the controllers (Deployment, ReplicaSet, etc.)
- **kubelet** — node agent; receives pod specs, asks runtime to start containers
- **kube-proxy** — implements Service IPs via iptables/IPVS

## 3. The objects you'll use weekly

| Object | What |
|---|---|
| **Pod** | The smallest deployable unit; 1+ containers sharing network + storage |
| **Deployment** | Manages a ReplicaSet which manages pod replicas; supports rolling updates |
| **StatefulSet** | Stable identity per replica (pod-0, pod-1); ordered start/stop |
| **DaemonSet** | One pod per node (logging agent, GPU driver) |
| **Job / CronJob** | Run-to-completion; cron-scheduled jobs |
| **Service** | Stable virtual IP + DNS pointing to a set of pods |
| **Ingress** | HTTP routing into the cluster (alternative: Gateway API) |
| **ConfigMap** | Non-secret config injected as env or file |
| **Secret** | Secret data, base64-encoded, ideally external-secrets-mounted |
| **PersistentVolume / PersistentVolumeClaim** | Storage provisioning |
| **Namespace** | Logical isolation within cluster |
| **Role / ClusterRole / RoleBinding / ClusterRoleBinding** | RBAC |
| **NetworkPolicy** | Pod-level firewall rules |

## 4. Minikube + kubectl (local-cluster setup)

```bash
# Mac
brew install minikube kubectl
minikube start --driver=docker --cpus=4 --memory=8192

# verify
kubectl get nodes
kubectl get pods -A
```

Alternatives in 2026: **kind** (Kubernetes-in-Docker, faster than minikube), **k3d** (k3s-in-Docker, lighter), **Docker Desktop** (built-in K8s toggle), **Rancher Desktop** (alt to Docker Desktop).

## 5. kubectl essentials

```bash
kubectl get pods                                # list pods in current namespace
kubectl get pods -A                             # all namespaces
kubectl get pods -o wide                        # more info
kubectl get pods --watch                        # follow
kubectl describe pod <name>                     # events + spec
kubectl logs <pod>                              # logs
kubectl logs -f <pod> -c <container>            # follow specific container
kubectl exec -it <pod> -- bash                  # shell into pod
kubectl apply -f manifest.yaml                  # declarative create/update
kubectl delete -f manifest.yaml
kubectl rollout status deploy/my-app
kubectl rollout undo deploy/my-app              # rollback
kubectl scale deploy my-app --replicas=5
kubectl port-forward svc/my-svc 8080:80         # local port → service
kubectl run debug --rm -it --image=alpine -- sh # ephemeral debug pod
```

## 6. Sample Deployment + Service manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels: { app: web }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
      - name: web
        image: nginx:1.27-alpine
        ports: [{ containerPort: 80 }]
        resources:
          requests: { cpu: 100m, memory: 64Mi }
          limits:   { cpu: 500m, memory: 256Mi }
        readinessProbe:
          httpGet: { path: /, port: 80 }
        livenessProbe:
          httpGet: { path: /, port: 80 }
---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector: { app: web }
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

```bash
kubectl apply -f web.yaml
kubectl get pods,svc
kubectl port-forward svc/web 8080:80
curl http://localhost:8080
```

## 7. Service types

| Type | When |
|---|---|
| **ClusterIP** | Internal-only (default) |
| **NodePort** | Exposes on every node at a high port; rarely used in production |
| **LoadBalancer** | Cloud-provider LB (AWS NLB/ALB, GCP TCP/HTTP LB, Azure LB); production |
| **ExternalName** | DNS CNAME alias |

Modern alternative: **Gateway API** (GA in K8s 1.31, late 2024) replacing Ingress for HTTP/L7.

## 8. Ingress (HTTP routing into cluster)

Need: an Ingress Controller (nginx, Traefik, HAProxy, AWS Load Balancer Controller).

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service: { name: web, port: { number: 80 } }
  tls:
  - hosts: [app.example.com]
    secretName: web-tls
```

## 9. Volumes + ConfigMap + Secret

```yaml
volumes:
- name: config
  configMap:
    name: my-config
- name: secrets
  secret:
    secretName: my-secret

volumeMounts:
- name: config
  mountPath: /etc/app/
- name: secrets
  mountPath: /etc/secrets/
  readOnly: true
```

PersistentVolumeClaim → PersistentVolume (statically or dynamically provisioned by StorageClass):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: gp3
  resources:
    requests: { storage: 10Gi }
```

## 10. Helm — the K8s package manager

```bash
helm install my-app ./chart
helm upgrade my-app ./chart
helm list
helm rollback my-app 1
```

Charts are templated YAML manifests with values. Standard charts: kube-prometheus-stack, ingress-nginx, cert-manager, ArgoCD. See [Topic 05 Modules](../05_docker_kubernetes/).

## 11. Managed K8s services

| Cloud | Service |
|---|---|
| AWS | EKS (covered Module 12) |
| GCP | GKE |
| Azure | AKS |
| Oracle | OKE |
| Linode | LKE (Nana uses this in her bootcamp) |
| DigitalOcean | DOKS |

All of them give you a managed control plane; you bring worker nodes (or use Fargate-like serverless).

## 12. Microservices in K8s + Best Practices preview

Patterns covered deeper in Part 5 (CKA modules):
- Pod Security Standards (restricted profile)
- NetworkPolicy default-deny
- ResourceQuotas + LimitRanges per namespace
- HPA / VPA / KEDA for autoscaling
- Cilium / Calico as CNI
- Prometheus + Grafana for monitoring
- ArgoCD / Flux for GitOps deploys

## 13. Quick self-check

1. What does etcd store?
2. What's the difference between a Deployment and a StatefulSet?
3. Why does a Service need to exist if Pods have IPs?
4. What's the difference between a ClusterIP and a LoadBalancer Service?
5. What's the modern alternative to Ingress as of late 2024?

(Answers: all cluster state — the source of truth; StatefulSet has stable identity + ordered start/stop for stateful workloads like databases; Pod IPs are ephemeral, Service IPs are stable; ClusterIP is internal-only, LoadBalancer provisions a cloud LB for external traffic; Gateway API.)



ewpage


# 12 — Kubernetes on AWS — EKS

> Cross-link: [Topic 04 Module 33 — EKS foundations](../04_aws_for_ai_ml/) and [Topic 05 Module 26 — EKS data exposure](../05_docker_kubernetes/26_eks_data_exposure.md) for the full depth.
>
> This module is the **CI/CD-deploy angle** — how a pipeline gets a built artifact onto EKS.

## 1. EKS at 30,000 ft

- **Managed K8s control plane** ($0.10/hr ≈ $73/mo per cluster); you pay per node + LB + EBS.
- **Worker nodes**: managed node groups (AWS-managed ASG), self-managed nodes, or **Fargate** (serverless pods).
- **Auth**: maps IAM users/roles → K8s RBAC via the **aws-auth ConfigMap** (legacy) or **EKS Access Entries** (modern, GA 2024).
- **Pod identity**: IRSA (OIDC, mature) or EKS Pod Identity (newer, simpler — 2023 GA).

## 2. Creating an EKS cluster — three options

### Option A: AWS Console (learning)
Click through; not reproducible. Don't do this for real work.

### Option B: eksctl (CLI tool)
```bash
eksctl create cluster \
  --name my-cluster \
  --region us-east-1 \
  --version 1.32 \
  --nodegroup-name workers \
  --node-type t3.large \
  --nodes 2 --nodes-min 2 --nodes-max 5
```

Fast, opinionated, good for dev/test. Behind the scenes generates CloudFormation.

### Option C: Terraform (production)
```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "my-cluster"
  cluster_version = "1.32"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.intra_subnets

  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true

  eks_managed_node_groups = {
    workers = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      instance_types = ["m5.large"]
    }
  }
}
```

Capital One: 100% Terraform-managed EKS clusters with custom modules + Cloud Custodian guardrails.

## 3. Autoscaling: Cluster Autoscaler vs Karpenter

- **Cluster Autoscaler (CAS)** — older, ASG-based; adds nodes when pods unschedulable.
- **Karpenter** — AWS-built (now CNCF), watches pending pods, **provisions exactly the right instance** without ASG. Spot-aware, consolidation-aware. **The 2026 default for new clusters.**

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: [amd64]
      - key: karpenter.k8s.aws/instance-category
        operator: In
        values: [c, m, r]
      - key: karpenter.sh/capacity-type
        operator: In
        values: [spot, on-demand]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s
```

## 4. Fargate Profile

EKS Fargate runs pods on AWS-managed serverless capacity. No nodes to manage.

```hcl
fargate_profiles = {
  default = {
    selectors = [{ namespace = "default" }]
  }
}
```

Caveats: limited daemonset support, no privileged pods, no GPU, no EBS volumes (EFS yes). Good for stateless web/app workloads where node ops is overhead.

## 5. Authenticating with the cluster

```bash
aws eks update-kubeconfig --region us-east-1 --name my-cluster --profile prod
kubectl get nodes
```

Behind the scenes: kubectl calls `aws eks get-token` → exchanges IAM credentials for a K8s token → cluster validates via the OIDC provider.

## 6. Deploying from Jenkins/Actions/GitLab to EKS

The 2026 pattern:
1. CI builds the image
2. CI pushes to ECR (`aws ecr get-login-password | docker login`; `docker push`)
3. CI updates a K8s manifest in a "manifests" repo with the new image tag
4. **ArgoCD / Flux** detects the change and syncs the cluster (GitOps)

Or older:
1. CI builds + pushes image
2. CI runs `kubectl apply -f deployment.yaml` (with new image tag)
3. CI waits for rollout to succeed (`kubectl rollout status`)

Why GitOps wins: pipeline doesn't need cluster credentials; cluster pulls. Audit trail in Git.

## 7. Jenkins → EKS pipeline (Nana's bootcamp)

```groovy
pipeline {
  agent any
  environment {
    AWS_REGION = 'us-east-1'
    ECR_REGISTRY = '1234.dkr.ecr.us-east-1.amazonaws.com'
    APP_NAME = 'myapp'
    CLUSTER_NAME = 'my-cluster'
  }
  stages {
    stage('Build') {
      steps {
        sh 'docker build -t $APP_NAME:$BUILD_NUMBER .'
      }
    }
    stage('Push to ECR') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds',
            usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '''
            aws ecr get-login-password --region $AWS_REGION | \
              docker login --username AWS --password-stdin $ECR_REGISTRY
            docker tag $APP_NAME:$BUILD_NUMBER $ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
            docker push $ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
          '''
        }
      }
    }
    stage('Deploy to EKS') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'aws-creds',
            usernameVariable: 'AWS_ACCESS_KEY_ID', passwordVariable: 'AWS_SECRET_ACCESS_KEY')]) {
          sh '''
            aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
            kubectl set image deployment/$APP_NAME app=$ECR_REGISTRY/$APP_NAME:$BUILD_NUMBER
            kubectl rollout status deployment/$APP_NAME --timeout=5m
          '''
        }
      }
    }
  }
}
```

Replace `aws-creds` with OIDC + IAM role for production.

## 8. EKS at Capital One

- Self-host model serving on EKS via **KServe** (NOT SageMaker for inference)
- **Karpenter** for autoscaling
- **Istio ambient** for service mesh
- **External Secrets Operator** → AWS Secrets Manager
- **Cloud Custodian** for AWS-API-layer policy + **Kyverno** for K8s-API-layer policy
- See [Topic 04 Module 54 — KServe deep](../04_aws_for_ai_ml/) for full pattern

## 9. Quick self-check

1. What does `aws eks update-kubeconfig` actually do?
2. Why is Karpenter preferred over Cluster Autoscaler in 2026?
3. What is the difference between IRSA and EKS Pod Identity?
4. Why is GitOps deploy preferred over `kubectl apply` from CI?
5. What is the EKS control plane cost per month per cluster?

(Answers: writes a context to ~/.kube/config that calls `aws eks get-token` for auth; provisions exactly-right instance per pending pod, consolidation, spot-aware; IRSA uses OIDC + role per service account, Pod Identity uses agent + simpler binding; pipeline needs no cluster creds, audit in Git, drift detection; ~$73/mo at $0.10/hr.)



ewpage


# 13 — Infrastructure as Code with Terraform

## Why this module exists

Terraform (and its 2023 OSS fork **OpenTofu**) is the lingua franca of cloud infrastructure. Capital One uses Terraform. AWS-shop interviews assume Terraform fluency. This is a net-new module (no other Topic in the project goes deep on Terraform).

## 1. The IaC tool landscape (2026)

| Tool | Lang | Cloud | When |
|---|---|---|---|
| **Terraform** (HashiCorp, BUSL since Aug 2023) | HCL | All | Industry default; BUSL = source-available, not OSS |
| **OpenTofu** (Linux Foundation, fork) | HCL | All | OSS Terraform-compatible; growing 2024–2026 |
| **AWS CloudFormation** | YAML/JSON | AWS-only | AWS-native; weak DX vs Terraform |
| **AWS CDK** | TS/Py/Java/Go | AWS-only | Programming language; transpiles to CFN |
| **Pulumi** | TS/Py/Go/.NET | All | Real-language IaC; smaller community |
| **Crossplane** | YAML (K8s CRDs) | All | K8s-native IaC; for GitOps shops |
| **Bicep** | DSL | Azure-only | CFN-equivalent for Azure |

The 2026 reality:
- **Pure OSS shops** → OpenTofu
- **Established Terraform shops** → mostly still on Terraform; some moving to OpenTofu
- **AWS-only shops** → Terraform or CDK
- **K8s-native shops** → Crossplane increasing

## 2. Terraform installation + first project

```bash
brew install terraform   # or: brew install opentofu
terraform version
terraform init           # download providers, init backend
terraform plan           # preview
terraform apply          # apply
terraform destroy        # tear down
```

Minimal project:
```
.
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── terraform.tfvars     # gitignored — secrets/env-specific
```

```hcl
# versions.tf
terraform {
  required_version = ">= 1.10"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
  backend "s3" {
    bucket         = "my-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "tf-state-lock"   # state locking
    encrypt        = true
  }
}

# variables.tf
variable "region" {
  type    = string
  default = "us-east-1"
}

# main.tf
provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "logs" {
  bucket = "my-logs-${random_id.suffix.hex}"
  force_destroy = false

  tags = {
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

resource "random_id" "suffix" {
  byte_length = 4
}

# outputs.tf
output "bucket_name" {
  value = aws_s3_bucket.logs.id
}
```

## 3. Resources, Data Sources, Providers

- **Resource** — something you create + manage (`aws_instance`, `aws_s3_bucket`).
- **Data Source** — something you read but don't manage (`data "aws_ami" "ubuntu"`).
- **Provider** — the plugin that talks to a cloud (AWS, Azure, K8s, GitHub, Datadog).

```hcl
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
}
```

## 4. The Terraform commands you'll run

```bash
terraform init                # download providers + init backend
terraform fmt -recursive      # canonical formatting
terraform validate            # syntax + basic checks
terraform plan                # show what will change
terraform plan -out=p.tfplan  # save plan
terraform apply p.tfplan      # apply saved plan (CI/CD pattern)
terraform apply -auto-approve # skip prompt
terraform destroy             # tear down
terraform state list          # what's in state
terraform state show <addr>   # inspect resource state
terraform state mv <old> <new>  # rename without recreate
terraform import <addr> <id>  # adopt existing resource into state
terraform output              # values
terraform workspace list      # workspaces (not for env separation — use dir + backend)
```

## 5. State — the most important concept

Terraform tracks **what it manages** in a state file. State maps resource addresses → cloud IDs. Without state, Terraform can't tell what to create vs update vs destroy.

- **Local state** (`terraform.tfstate` in directory) — for solo learning only
- **Remote state** — S3 + DynamoDB locking (AWS), Azure Storage + lease, GCS + locks, Terraform Cloud/Enterprise
- **State is sensitive** — contains computed values, sometimes secrets — encrypt at rest, restrict access
- **Never edit state by hand** — use `terraform state` commands

## 6. Variables + Environment Variables

```hcl
variable "region" {
  type    = string
  default = "us-east-1"
}

variable "tags" {
  type    = map(string)
  default = {}
}
```

Set values via:
- `terraform.tfvars` file (auto-loaded)
- `*.auto.tfvars` files
- `-var "region=us-west-2"` flag
- `TF_VAR_region=us-west-2` env var
- Prompted at runtime if no default

For secrets: never put in `.tf` or committed `.tfvars`. Use `TF_VAR_*` env vars (from CI/CD secret store) or read from Vault/Secrets Manager via data source.

## 7. Output Values

```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}

output "db_endpoint" {
  value     = aws_rds_cluster.main.endpoint
  sensitive = true   # masks from console output
}
```

Outputs are consumed by other Terraform configs (via `terraform_remote_state` data source) or by CI/CD scripts.

## 8. Provisioners (use sparingly)

```hcl
resource "aws_instance" "web" {
  # ...
  provisioner "remote-exec" {
    inline = ["sudo apt update", "sudo apt install -y nginx"]
    connection {
      type     = "ssh"
      user     = "ubuntu"
      host     = self.public_ip
      private_key = file("~/.ssh/id_ed25519")
    }
  }
}
```

**Anti-pattern.** Use Ansible (Module 16), cloud-init `user_data`, or baked AMIs. Provisioners are non-idempotent escape hatches.

## 9. Modules — the DRY mechanism

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway = true
}
```

**Public Terraform Registry** (https://registry.terraform.io) hosts thousands of modules. Quality varies; prefer modules from cloud-provider orgs (terraform-aws-modules, hashicorp, etc.). For Capital One scale: internal-private module registry with vetted modules.

## 10. CI/CD for Terraform

```yaml
# GitHub Actions snippet
on: pull_request
jobs:
  tf-plan:
    runs-on: ubuntu-latest
    permissions: { id-token: write, contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_ROLE_ARN }}, aws-region: us-east-1 }
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - run: terraform plan -no-color -out=tfplan
      - uses: actions/github-script@v7
        with:
          script: |
            const plan = require('child_process').execSync('terraform show -no-color tfplan').toString();
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner, repo: context.repo.repo,
              body: `\`\`\`\n${plan.slice(0, 65000)}\n\`\`\``
            })
```

Patterns:
1. **Plan in CI on PR**, apply on merge to main (after manual approval)
2. **Atlantis** or **Terraform Cloud** for governance
3. **Open Policy Agent (Rego)** or **checkov / tfsec** for policy-as-code gates

## 11. Best practices (the 12-point checklist)

1. **Remote state with locking** — never local state for shared infra
2. **One state per env** — separate directories or workspaces; never share prod + dev state
3. **Pin provider + module versions** — `~> 5.80`, not unconstrained
4. **`terraform fmt` + `validate` in CI** — enforce
5. **Run plan in CI on PR** — block merge if plan fails
6. **Apply gated by manual approval** — for prod
7. **No secrets in repo** — env vars from CI secret store
8. **Tag every resource** — Environment, Owner, ManagedBy, CostCenter
9. **Modules for repeatable patterns** — DRY at scale
10. **`for_each` over `count`** for resources from collections (count breaks on reorder)
11. **`terraform import` for adopting existing resources** — don't recreate
12. **Drift detection** — scheduled plan against prod, alert on drift

## 12. Quick self-check

1. What does `terraform init` do?
2. Why is local state dangerous for team work?
3. When would you use `data` vs `resource`?
4. Why are provisioners considered an anti-pattern?
5. What's the difference between Terraform and OpenTofu, and why does it matter?

(Answers: downloads providers + initializes backend; no locking, single source of truth lost, secrets in plaintext; data for existing resources you reference, resource for things you manage; non-idempotent, run-once nature breaks Terraform's declarative model; OpenTofu is the OSS fork after HashiCorp's BUSL relicense — matters for OSS-purity shops and avoiding vendor lock-in.)



ewpage


# 14 — Python Basics for DevOps

> **Skim module** for Vatsal — he is Python-fluent. Included for curriculum completeness. The next module (15 — Boto3 automation) is the actual DevOps Python content.

## Why this module exists in Nana's curriculum

Nana's DevOps Bootcamp Module 13 teaches Python from zero. For DevOps specifically, the relevant Python skills are:
1. **Scripting** (replace bash when logic gets complex)
2. **Boto3** (AWS SDK — Module 15)
3. **Click / Typer** for CLIs
4. **Requests / httpx** for REST APIs
5. **PyYAML / ruamel.yaml** for manifest manipulation
6. **kubernetes Python client** for K8s automation
7. **Jinja2** for templating

## 1. Why Python wins DevOps scripting

- Cross-platform (one script runs on macOS dev box + Linux CI agent + Windows where forced)
- Huge ecosystem (boto3, kubernetes, requests, pyyaml, jinja2)
- Readable (the team-lead's case for picking it over bash)
- The same language as the data/ML side of the house

When to pick bash over Python: short, single-machine, shell-pipe-friendly. When to pick Python: anything involving APIs, JSON/YAML, > 30 lines of logic, retries/error handling.

## 2. Setting up modern Python (2026)

```bash
# Install Python via conda (the project's standard)
conda create -n devops-py python=3.13 -y
conda activate devops-py

# Or just use uv directly — it manages Python versions too
brew install uv
uv python install 3.13
uv venv .venv
source .venv/bin/activate

# Install packages
uv pip install boto3 click pyyaml requests jinja2

# Modern project mgmt
uv init my-project
cd my-project
uv add click boto3
uv run my-script.py
```

**uv** is Astral's Rust-written tool replacing pip + pip-tools + venv + pyenv in one binary. ~10-100x faster. The 2026 default.

## 3. The patterns you'll write

### A CLI with Click
```python
import click

@click.group()
def cli(): pass

@cli.command()
@click.argument("env")
@click.option("--dry-run", is_flag=True)
def deploy(env, dry_run):
    """Deploy app to ENV."""
    click.echo(f"Deploying to {env} (dry_run={dry_run})")
    # ...

if __name__ == "__main__":
    cli()
```

```bash
$ python deploy.py deploy prod --dry-run
Deploying to prod (dry_run=True)
```

### Reading + manipulating YAML
```python
import yaml
from pathlib import Path

manifest = yaml.safe_load(Path("deployment.yaml").read_text())
manifest["spec"]["replicas"] = 5
Path("deployment.yaml").write_text(yaml.safe_dump(manifest))
```

### Calling a REST API with retry
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(min=1, max=30))
def get_status(url):
    r = httpx.get(url, timeout=10.0)
    r.raise_for_status()
    return r.json()
```

### Error handling with try/except
```python
try:
    result = risky_op()
except SpecificError as e:
    logger.error("op failed: %s", e)
    raise
except Exception:
    logger.exception("unexpected")
    raise
```

### Type hints (write them)
```python
from typing import Iterable

def deploy_to(envs: Iterable[str], version: str) -> dict[str, bool]:
    return {e: True for e in envs}
```

Use `mypy` or `pyright` in CI. Modern code without type hints is a code smell.

## 4. Python project structure

```
my-tool/
├── pyproject.toml
├── README.md
├── src/
│   └── my_tool/
│       ├── __init__.py
│       ├── cli.py
│       └── core.py
└── tests/
    └── test_core.py
```

`pyproject.toml`:
```toml
[project]
name = "my-tool"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "click>=8.1",
  "boto3>=1.35",
]

[project.scripts]
my-tool = "my_tool.cli:cli"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = ["pytest>=8", "ruff>=0.8", "mypy>=1.13"]

[tool.ruff]
line-length = 100
```

See [Topic 07 Module 18 — Python ML repo structure](../07_git_github_devops/18_python_ml_repo_structure.md) for the full layout.

## 5. Testing with pytest

```python
# tests/test_core.py
from my_tool.core import deploy_to

def test_deploy_to_returns_dict():
    result = deploy_to(["dev", "prod"], "1.2.3")
    assert result == {"dev": True, "prod": True}

def test_deploy_to_empty():
    assert deploy_to([], "1.2.3") == {}
```

```bash
pytest -v
pytest --cov=my_tool --cov-report=term-missing
```

## 6. Modules + Packages + PyPI

```python
# At top of file
from boto3 import client
import json
from collections import defaultdict

# Or relative
from .core import deploy_to
```

PyPI publishing (when you have a tool worth sharing):
```bash
uv build
uv publish --token <pypi-token>
```

For internal: publish to **Nexus** (Module 7), **AWS CodeArtifact**, **GitHub Packages**, or **GitLab Package Registry**. Configure `pip` / `uv` to use the private index URL.

## 7. OOP — when to use classes

For DevOps scripts: **rarely**. Prefer functions + dataclasses for state. Use classes when:
- Resource with lifecycle (connection, file handle) → `__init__` + `close()` + context manager
- Plugin/strategy pattern with multiple implementations
- Long-lived state across methods

```python
from dataclasses import dataclass

@dataclass
class Deployment:
    name: str
    version: str
    replicas: int = 1
```

## 8. The "Countdown App" / "Spreadsheet automation" / "GitLab API" projects (Nana's)

These are intro projects in her curriculum. Equivalents for senior engineers:
- **Countdown** → systemd timer + Python script
- **Spreadsheets** → openpyxl, pandas-to-Excel for reports
- **GitLab API** → `python-gitlab` library; great for "audit all repos for X"

Skip these unless you want the muscle memory.

## 9. Quick self-check

1. Why is `uv` displacing pip + Poetry + pyenv?
2. When should you write Python instead of bash?
3. What's the modern alternative to setup.py?
4. Why use type hints in DevOps Python?
5. Where do you publish a private Python package?

(Answers: single binary, ~10-100x faster, lockfile-first, manages Python versions; > 30 lines, API calls, JSON/YAML, retries, cross-platform; pyproject.toml; catches bugs at lint/CI time and serves as API documentation; Nexus, AWS CodeArtifact, GitHub Packages, GitLab Package Registry.)



ewpage


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



ewpage


# 16 — Configuration Management with Ansible

## Why this module exists

Ansible is the dominant configuration-management tool (vs declining Salt/Puppet/Chef). It's also the most useful "you have a fleet of VMs and need to do something to them" tool. Net-new module — no other topic in this project covers Ansible.

## 1. Why Ansible (vs alternatives)

| | Ansible | Salt | Puppet | Chef | cloud-init |
|---|---|---|---|---|---|
| **Agent** | Agentless (SSH) | Agent (Salt master+minions) | Agent | Agent | First-boot only |
| **Lang** | YAML | YAML + Python | DSL | Ruby DSL | Bash/cloud-config |
| **2026 trajectory** | Dominant + IBM-stable | Declining | Declining | Declining | Stable / different niche |
| **Push vs Pull** | Push | Pull (default) | Pull | Pull | N/A |

Ansible won the war ~2018-2020 because:
- Agentless (just needs SSH + Python on target)
- Readable YAML
- Idempotent built-in modules
- Red Hat backing (acquired AnsibleWorks 2015, then IBM acquired Red Hat 2019)

## 2. Architecture

```
┌──────────────────┐         SSH         ┌──────────────────┐
│   Control Node   │  ─────────────────► │  Managed Node 1  │
│  (your laptop /  │  ─────────────────► │  Managed Node 2  │
│   bastion EC2)   │  ─────────────────► │       ...        │
└──────────────────┘                     └──────────────────┘
   ansible-core
   collections
   inventory
   playbooks
```

The control node runs Python + ansible-core. It SSHes to managed nodes (which need Python — typically already there on Linux). No agent on managed nodes.

## 3. Install

```bash
# macOS
brew install ansible
# Or pip
uv pip install ansible-core ansible

# Verify
ansible --version
```

Latest ansible-core 2.18+ requires Python 3.11+ on control node.

## 4. Inventory — who you're managing

### Static INI
```ini
[web]
web1.example.com
web2.example.com

[db]
db1.example.com ansible_user=admin ansible_port=2222

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

### Static YAML
```yaml
all:
  children:
    web:
      hosts:
        web1.example.com:
        web2.example.com:
    db:
      hosts:
        db1.example.com:
          ansible_user: admin
          ansible_port: 2222
```

### Dynamic — query the cloud
```yaml
# inventory.aws_ec2.yml
plugin: amazon.aws.aws_ec2
regions: [us-east-1]
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: placement.region
    prefix: aws_region
filters:
  tag:Environment: prod
```

Then: `ansible-inventory -i inventory.aws_ec2.yml --graph`. Pulls EC2 instances tagged Environment=prod into groups by their Role tag.

## 5. Ad-hoc commands

```bash
ansible all -i inventory.ini -m ping                   # check connectivity
ansible web -m apt -a "name=nginx state=present" -b   # install nginx with sudo (-b)
ansible all -m shell -a "uptime"
ansible all -m copy -a "src=local.conf dest=/etc/app/"
```

`-b` = become root (sudo). `-m <module>` = use specific module. `-a "args"` = module args.

## 6. Playbooks — the real work

```yaml
# site.yaml
- name: Configure web servers
  hosts: web
  become: true
  vars:
    nginx_version: "1.27.*"
  tasks:
    - name: Install nginx
      apt:
        name: "nginx={{ nginx_version }}"
        state: present
        update_cache: true

    - name: Render nginx config
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        mode: '0644'
      notify: Reload nginx

    - name: Ensure nginx running
      systemd:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Reload nginx
      systemd:
        name: nginx
        state: reloaded
```

```bash
ansible-playbook -i inventory.ini site.yaml
ansible-playbook -i inventory.ini site.yaml --check    # dry run
ansible-playbook -i inventory.ini site.yaml --diff     # show file changes
ansible-playbook -i inventory.ini site.yaml --tags nginx --limit web1.example.com
```

## 7. Modules + Collections

Modules are units of work (apt, yum, copy, template, systemd, file, etc.). **Collections** are bundles of modules + roles. Since Ansible 2.10, modules ship in collections via Ansible Galaxy.

```bash
ansible-galaxy collection install community.general
ansible-galaxy collection install amazon.aws
ansible-galaxy collection install kubernetes.core
```

Reference: `amazon.aws.ec2_instance`, `kubernetes.core.k8s`, `community.general.terraform`.

## 8. Variables

Hierarchy (lowest to highest precedence — abbreviated):
1. Role defaults (`defaults/main.yml`)
2. Inventory group vars
3. Inventory host vars
4. Playbook vars
5. Task vars
6. Extra vars (`-e foo=bar`) — wins everything

Best practice: `group_vars/<group>.yml` and `host_vars/<host>.yml` for per-environment config.

```yaml
# group_vars/web.yml
nginx_worker_processes: 4
nginx_server_name: example.com

# group_vars/all.yml
timezone: UTC
admin_email: ops@example.com
```

## 9. Ansible Vault — encrypted secrets

```bash
ansible-vault create group_vars/prod/vault.yml
# Opens editor; type secrets:
# db_password: super-secret
ansible-vault edit group_vars/prod/vault.yml
ansible-vault view group_vars/prod/vault.yml
ansible-playbook -i inv site.yaml --ask-vault-pass
# Or
ansible-playbook -i inv site.yaml --vault-password-file ~/.vault_pass
```

Vault encrypts values at rest in the repo. Decrypt at runtime via password (or CI secret). For dynamic secrets prefer **HashiCorp Vault integration** or external lookup plugins.

## 10. Roles — reusable, modular

```
roles/
└── nginx/
    ├── defaults/main.yml     # default vars
    ├── files/                # static files
    ├── handlers/main.yml     # restart/reload handlers
    ├── tasks/main.yml        # actual tasks
    ├── templates/            # Jinja2 templates
    ├── vars/main.yml         # role vars (high precedence)
    └── meta/main.yml         # role metadata + dependencies
```

```yaml
# site.yaml using roles
- hosts: web
  become: true
  roles:
    - { role: common }
    - { role: nginx, nginx_worker_processes: 8 }
    - { role: app, app_version: "1.2.3" }
```

Ansible Galaxy has thousands of community roles: `ansible-galaxy install geerlingguy.nginx` (Jeff Geerling's roles are particularly well-maintained).

## 11. Ansible + Terraform together (the common pattern)

- **Terraform** provisions the EC2 instances + VPC + Security Groups
- **Terraform output** writes the instance IPs to a file or to Ansible inventory
- **Ansible** configures the instances (install nginx, deploy app)

This is "Terraform for the metal, Ansible for the meat." Pure Terraform with `remote-exec` provisioner is an anti-pattern (Module 13).

For modern setups, **Packer** + Ansible bakes an AMI, then Terraform provisions VMs from the AMI = immutable. No runtime config drift.

## 12. Ansible in Jenkins (the bootcamp project)

```groovy
stage('Configure servers') {
  steps {
    sshagent(credentials: ['deploy-key']) {
      sh '''
        ansible-playbook -i inventory.ini site.yaml \
          --extra-vars "app_version=$BUILD_NUMBER"
      '''
    }
  }
}
```

The Jenkinsfile runs `ansible-playbook` from the agent. Credentials managed via `sshagent` or vault password from secret store.

## 13. Ansible deploying to K8s

```yaml
- hosts: localhost
  tasks:
    - name: Apply deployment
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata: { name: myapp }
          spec:
            replicas: 3
            selector: { matchLabels: { app: myapp } }
            template:
              metadata: { labels: { app: myapp } }
              spec:
                containers:
                - name: app
                  image: "myapp:{{ app_version }}"
```

Honestly: for K8s deploys, prefer **Helm + ArgoCD/Flux** over Ansible. Ansible-to-K8s is a relic of the early days.

## 14. AAP (Ansible Automation Platform) — Red Hat commercial

What you get with AAP:
- Web UI for running playbooks (formerly Tower)
- Job scheduling
- RBAC
- Workflow chaining
- Execution Environments (containerized runner — replaces "install all collections everywhere")
- Event-Driven Ansible (EDA) — react to webhooks/events

Subscription-required since IBM acquisition. Pricing varies by node count (~$10-20k/yr for small teams up to enterprise).

## 15. The 2026 reality — where is Ansible going

- **Strong:** traditional VM-based infra, network device config (Cisco/Juniper/Arista), Windows VM mgmt
- **Weaker:** K8s-native shops (prefer Helm/Kustomize/ArgoCD); immutable-infra shops (prefer Packer + Terraform); GitOps shops (prefer pull-based agents)
- **Niche but growing:** Event-Driven Ansible for incident-response automation

For an AI/ML engineer at Capital One: Ansible knowledge is a "nice to have" but K8s + Helm + GitOps + Terraform is the daily reality.

## 16. Quick self-check

1. Why is Ansible agentless an advantage over Puppet/Chef?
2. What does `become: true` do?
3. When should you use dynamic inventory?
4. What's the difference between a role and a collection?
5. Why is Ansible-to-K8s an anti-pattern in 2026?

(Answers: no agent install/upgrade burden, just SSH + Python; equivalent to sudo on the target; for cloud resources where IPs/hostnames change — query the cloud at runtime; role = reusable bundle of tasks + vars + templates for one thing, collection = bundle of modules + roles + plugins for a vendor/topic; K8s has native declarative tooling, Helm/Kustomize/ArgoCD beat Ansible's imperative push model.)



ewpage


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



ewpage


# 18 — Security Essentials + OWASP Top 10

## Why this module exists

DevSecOps presupposes baseline security literacy. This module is the 30-minute primer on attack categories, OWASP Top 10, and the layered-defense framing that everything in Part 2 will build on.

## 1. The cost of breaches (the business case for shift-left)

- **Average data breach cost 2024**: $4.88M (IBM Cost of a Data Breach Report 2024)
- **Capital One 2019 breach**: 100M+ records, $190M+ in fines + legal, plus reputation damage and SR 11-7 scrutiny
- **Equifax 2017 breach**: 147M records, ~$1.4B in costs over the following years
- **Stripe-grade scrutiny**: SOC 2 / PCI-DSS / FedRAMP / HIPAA — non-compliance blocks revenue, not just penalties

## 2. The CIA triad (the security north star)

- **Confidentiality** — only authorized parties see the data
- **Integrity** — data is not tampered with (signing, hashing, checksums)
- **Availability** — the system is up when needed (DDoS protection, redundancy)

Add three more (the AAA/non-rep additions):
- **Authentication** — proving who you are
- **Authorization** — what you can do
- **Non-repudiation** — proving who did what

## 3. Attack categories at a glance

| Category | Example |
|---|---|
| **Injection** | SQL injection, command injection, LDAP injection |
| **XSS** (Cross-site scripting) | Reflected, stored, DOM-based |
| **CSRF** | Forge requests using user's session |
| **SSRF** (Server-side request forgery) | Make the server fetch URLs you choose — **Capital One 2019 root cause** |
| **Authentication bypass** | Weak passwords, MFA bypass, session hijacking |
| **Privilege escalation** | Lateral movement after initial foothold |
| **DoS / DDoS** | Volumetric or app-layer flooding |
| **Supply chain** | Compromised dependencies (SolarWinds 2020, xz utils 2024) |
| **Insider threat** | Authorized user misusing access |
| **Physical** | Datacenter breach, stolen laptop |
| **Social engineering** | Phishing, vishing, business email compromise |

## 4. OWASP Top 10 (2021 — current, with 2025 update in flight)

| # | Risk | Defense |
|---|---|---|
| **A01** | **Broken Access Control** | Authorization checks server-side, deny-by-default, RBAC |
| **A02** | **Cryptographic Failures** | TLS everywhere, no weak ciphers, no plaintext secrets |
| **A03** | **Injection** | Parameterized queries, input validation, output encoding |
| **A04** | **Insecure Design** | Threat modeling, secure-by-default architecture |
| **A05** | **Security Misconfiguration** | Hardening baselines, no defaults, no debug in prod |
| **A06** | **Vulnerable + Outdated Components** | SCA, Dependabot, patch SLAs |
| **A07** | **Identification + Authentication Failures** | MFA, strong session mgmt, no credential stuffing |
| **A08** | **Software + Data Integrity Failures** | Signed artifacts (Cosign), SLSA, CI integrity |
| **A09** | **Security Logging + Monitoring Failures** | Centralized logs, SIEM, alerting |
| **A10** | **SSRF** | Allowlist outbound, no metadata-service access from app |

The 2025 draft (not yet finalized as of 2026-05) reportedly raises Insecure Design and Supply Chain Integrity higher.

## 5. CWE Top 25 (MITRE's complement)

Where OWASP Top 10 is web-focused, **CWE Top 25 Most Dangerous Software Weaknesses** is software-wide and updated annually. Cross-references between the two:
- CWE-79 (XSS) ↔ OWASP A03
- CWE-89 (SQL injection) ↔ OWASP A03
- CWE-787 (Out-of-bounds write) — not in OWASP but high in CWE
- CWE-918 (SSRF) ↔ OWASP A10

DefectDojo (Module 21) imports scanner reports and maps findings to CWE for normalized tracking.

## 6. Defense in layers (the onion model)

```
┌──────────────────────────────────────────────────────────┐
│  Network                                                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Perimeter                                          │  │
│  │  ┌──────────────────────────────────────────────┐  │  │
│  │  │  Host                                          │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │  Application                              │  │  │  │
│  │  │  │  ┌──────────────────────────────────────┐  │  │  │  │
│  │  │  │  │  Data                                  │  │  │  │  │
│  │  │  │  └──────────────────────────────────────┘  │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

Each layer has its own controls:
- **Network**: VPC, NACL, NetworkPolicy, segmentation
- **Perimeter**: WAF, rate limiting, IP allowlists, DDoS
- **Host**: hardened OS, EDR, FIM (file integrity monitoring)
- **Application**: input validation, output encoding, AuthN/AuthZ
- **Data**: encryption at rest + transit, tokenization (Capital One: Databolt), key rotation

Defense-in-depth: assume any one layer will fail; the next must catch it.

## 7. Threat modeling — STRIDE + PASTA + LINDDUN

Threat modeling is "think like an attacker before you ship." Frameworks:

- **STRIDE** (Microsoft, oldest): Spoofing, Tampering, Repudiation, Info disclosure, DoS, Elevation of privilege
- **PASTA** (Process for Attack Simulation and Threat Analysis) — risk-driven
- **LINDDUN** (privacy-focused)
- **OWASP Threat Dragon** — free tool

In practice: a 30-min whiteboard with engineering + security per major feature. Document the trust boundaries; enumerate threats per boundary; prioritize fixes.

## 8. Compliance frameworks that drive what you build

| Framework | Domain | Touch points |
|---|---|---|
| **SOC 2** | All SaaS | Access controls, monitoring, change mgmt, vendor mgmt |
| **PCI-DSS v4** (2024 effective) | Card data | Tokenization, network segmentation, scanning, pen test |
| **HIPAA** | US healthcare | PHI handling, BAA, audit logs (6yr retention), encryption |
| **GDPR** | EU citizens' data | Consent, data minimization, right to erasure, breach disclosure |
| **CCPA / CPRA** | California consumers | Similar to GDPR for CA |
| **SR 11-7** | US bank model risk | Model validation, audit trails, separation of duties |
| **FedRAMP** | US federal cloud | NIST 800-53 controls, continuous monitoring |
| **ISO 27001** | Global infosec | ISMS — Information Security Mgmt System |

Capital One operates under: PCI-DSS v4, SR 11-7, GLBA, SOC 1+2+3, ISO 27001, FFIEC.

## 9. The DevSecOps remit

DevSecOps shifts security:
- **Left** (earlier in lifecycle) — into design, into IDE
- **Right** (later in lifecycle) — into runtime detection/response
- **Everywhere** (the 2025 reframe) — at every stage of the pipeline

The remaining 20 modules of Part 2 map directly onto these stages.

## 10. Quick self-check

1. What's the CIA triad?
2. What was the root cause of the Capital One 2019 breach and which OWASP item is it?
3. Why is shift-left security more cost-effective than shift-right?
4. What does STRIDE stand for?
5. What's the difference between SOC 2 and PCI-DSS?

(Answers: Confidentiality, Integrity, Availability; SSRF + over-permissive IAM role + IMDSv1 — OWASP A10; finding bugs in design or IDE is ~100x cheaper than finding in prod; Spoofing/Tampering/Repudiation/Information disclosure/DoS/Elevation of privilege; SOC 2 is a SaaS-controls-attestation, PCI-DSS is a card-data-specific compliance standard.)



ewpage


# 19 — Introduction to DevSecOps

## 1. The problem DevSecOps solves

Traditional security:
- Security review at the end (waterfall)
- Bottleneck: 1 security engineer for 100 devs
- "No" by default; slows releases
- Findings come back weeks after code shipped
- Fix cost: 100x what it would have been at design

The result: teams ship insecure code OR security blocks the business. Neither works.

## 2. The DevSecOps reframe

- Security is **everyone's** job — devs own remediation
- Security tools **shift left** into IDE, pre-commit, PR checks
- Security **automates** what humans did manually (scanning, policy enforcement)
- Security teams **build platforms** that scale — paved roads, not gatekeeping

## 3. DORA + DevSecOps — the data

The 2024 DORA report adds **security** as a 5th capability dimension. Findings:
- **Elite teams** integrate security into delivery; medium teams have security as a separate gate
- **Elite teams** have higher security AND higher velocity (the security/speed tradeoff is false)
- **Elite teams** automate ~80% of security checks

The DevSecOps thesis empirically holds.

## 4. The DevSecOps pipeline (the canonical view)

```
Plan        Design          Code           Build          Test            Release/Deploy    Monitor
│           │               │              │              │               │                 │
threat      secure          IDE             SAST           DAST            signing            SIEM
modeling    design          security        SCA            IAST            admission control  EDR
            review          extensions      secrets scan   compliance      runtime defense    incident response
                            pre-commit      image scan     scans
```

Each pipeline stage gets its own security gate. Findings flow to **DefectDojo** (or equivalent) for triage.

## 5. Roles & responsibilities

| Role | DevSecOps mandate |
|---|---|
| **Developer** | Write secure code; respond to scan findings; threat model their feature |
| **Security Engineer** | Build the platform; tune rules; investigate alerts; train devs |
| **DevOps / Platform Engineer** | Wire scanners into pipelines; harden infra |
| **AI/ML Engineer** | Same as developer + model-specific risks (data leakage, adversarial inputs, prompt injection) |
| **Compliance / Audit** | Map controls to frameworks; produce evidence |
| **Manager / EM** | Make security explicit in OKRs; defend remediation time |

Capital One: ~1:30 ratio (security engineers : product engineers) — they build the platform, not the reviews.

## 6. The DevSecOps maturity ladder

| Level | Posture |
|---|---|
| **0 — None** | No scans; security only via pen test at release |
| **1 — Manual** | Some scanners exist but findings not enforced |
| **2 — Automated** | CI gates on Critical findings |
| **3 — Integrated** | Scanners + DefectDojo + SLA + rotation; metrics tracked |
| **4 — Continuous** | Policy-as-code + runtime defense + auto-remediation; elite DORA |

Most regulated finance is at L3 trending L4.

## 7. The 11 capabilities (and where each maps in this curriculum)

| # | Capability | Module |
|---|---|---|
| 1 | Secret scanning | 20 |
| 2 | SAST | 22 (mentioned in 20-22) |
| 3 | SCA | 22 |
| 4 | DAST | 26 |
| 5 | Container/image scanning | 24 |
| 6 | IaC scanning | 27 |
| 7 | Cloud security (IAM, CSPM) | 25, 28 |
| 8 | K8s security (RBAC, admission) | 29-30, 34 |
| 9 | Secrets management | 35 |
| 10 | Service mesh + mTLS | 36 |
| 11 | Compliance as code | 37 |

## 8. The metrics that matter (DevSecOps KPIs)

- **MTTR for security findings** — by severity, by team
- **% of findings remediated within SLA**
- **Critical CVEs in production** (should be 0)
- **% pipelines with security scans enabled** (should be 100)
- **Mean time from scanner alert to ticket creation** (should be < 1hr; automate)
- **Security debt aging** (oldest unfixed Critical)

## 9. The shift-everywhere progression

| Stage | Where security lives |
|---|---|
| Old | Pre-release pen test |
| Shift-left | Pre-commit + IDE + CI scans |
| Shift-right | Runtime detection + EDR + admission |
| **Shift-everywhere** (2025+) | All of above + threat modeling at design |

The 2026 mindset: security is a non-functional requirement, not a phase.

## 10. The cultural unblockers

What kills DevSecOps in practice:
- **Punitive findings disposition** — devs game the tool, hide work
- **No remediation time in sprints** — "we'll get to it" never happens
- **Vendor sprawl** — 20 scanners, 0 normalization (this is what DefectDojo solves)
- **No exec backing** — security loses to feature pressure

What unblocks:
- Blameless culture
- Time explicitly budgeted for security work
- Findings normalized into one platform with SLAs
- Sec engineers embedded in dev teams, not in a separate ivory tower

## 11. Quick self-check

1. What's the "shift-everywhere" reframe over "shift-left"?
2. Why is the speed/security tradeoff considered false by DORA?
3. Name three signs of a DevSecOps maturity ladder L1 (manual) team.
4. What's the role of DefectDojo in the DevSecOps pipeline?
5. What's the most common cultural anti-pattern that kills DevSecOps in practice?

(Answers: security lives at every stage including design + runtime, not just CI; elite teams have higher velocity AND security — they automate the tradeoff away; scanners exist but findings not enforced + no SLAs + no normalized triage + no remediation budget; normalizes findings from many scanners into one trackable backlog with CWE mapping; punitive disposition that punishes devs for findings causes hiding and gaming.)



ewpage


# 20 — Application Vulnerability Scanning: GitLeaks + Pre-commit

## Why this module exists

The #1 supply-chain leak vector in 2026: **secrets committed to Git**. A leaked AWS access key gets discovered + exploited within minutes by automated scanners. GitLeaks is the OSS scanner; the pre-commit framework is the wrapper that runs it (and other linters) before code ever leaves your laptop.

## 1. The secret-leak problem

The numbers:
- **GitGuardian's 2024 State of Secrets Sprawl**: 23.7M new secrets detected in public repos in 2023
- **Average time-to-detection** by attackers for a leaked AWS key on GitHub public: ~5 minutes
- **Average cleanup cost** of a secret leak (rotate, audit, comms): $400-2000 per incident
- **GitHub Secret Scanning** (free for public repos, paid for private orgs via GHAS) catches 200+ secret patterns

## 2. GitLeaks — the OSS leader

GitLeaks scans commits, repos, files for high-entropy strings + known patterns (AWS keys, GitHub tokens, Stripe keys, JWT, RSA private keys, etc.).

```bash
# Install
brew install gitleaks
# Or
docker run -v $(pwd):/path zricethezav/gitleaks:latest detect -v --source=/path

# Run
gitleaks detect --source . --verbose
gitleaks protect --staged --verbose      # check staged before commit
gitleaks git history --source .          # scan full git history
```

### Config (.gitleaks.toml)
```toml
title = "gitleaks config"

[extend]
useDefault = true

[[rules]]
id = "company-api-key"
description = "Internal API key"
regex = '''[a-z]{4}_live_[A-Za-z0-9]{32}'''
keywords = ["live_"]

[allowlist]
description = "test fixtures"
paths = [
  '''tests/fixtures/.*''',
  '''docs/examples/.*''',
]
regexes = ['''dummy-key-.*''']
```

Allowlisting is essential — test fixtures + docs often contain dummy-looking strings.

## 3. Pre-commit framework

`pre-commit` (https://pre-commit.com) is the orchestrator. One YAML config runs many hooks:

```yaml
# .pre-commit-config.yaml
repos:
  # Core hygiene
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-merge-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: ['--branch', 'main']

  # Secret scanning
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Python
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]

  # Shell
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.10.0.1
    hooks:
      - id: shellcheck

  # YAML / Markdown
  - repo: https://github.com/adrienverge/yamllint.git
    rev: v1.35.1
    hooks:
      - id: yamllint
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.42.0
    hooks:
      - id: markdownlint

  # IaC
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.1
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_checkov
```

Install and run:
```bash
pip install pre-commit
pre-commit install              # install hooks in .git/hooks/pre-commit
pre-commit install --hook-type commit-msg
pre-commit run --all-files      # run on all files (not just staged)
pre-commit autoupdate           # bump hook versions
```

## 4. Running GitLeaks in CI (defense in depth)

Pre-commit catches at commit time. But devs can `--no-verify`. **CI must verify again.**

```yaml
# .github/workflows/security.yml
on: [push, pull_request]
jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }     # full history for git-history scanning
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}   # for org-level scanning
```

GitLab CI equivalent:
```yaml
gitleaks:
  image: zricethezav/gitleaks:latest
  script: gitleaks detect --source . --verbose --report-format sarif --report-path gitleaks.sarif
  artifacts:
    reports:
      sast: gitleaks.sarif
```

## 5. The `fix the leak` runbook

A leak found in commit history. The myth: "just delete the commit." The reality: assume the secret is compromised. Steps:

1. **Rotate the secret first** (AWS console / Secrets Manager / wherever) — before doing anything to Git
2. **Audit usage** of the old credential — CloudTrail for AWS, vendor audit logs
3. **Investigate** whether the secret was exploited (probably; act as if it was)
4. **Optionally** rewrite history with `git filter-repo` or BFG Repo-Cleaner — but only after rotation, and only if you control all clones
5. **Add a regex pattern** to detect this type in your `.gitleaks.toml`
6. **Postmortem** with the team — what process gap let it through?

GitHub Push Protection (GHAS) blocks the push *before* the leak. Use it where licensed.

## 6. False positives — the operational reality

Common FP patterns:
- Test fixtures with realistic-looking dummy data
- Doc examples (`AWS_KEY=AKIA...EXAMPLE`)
- Hex strings in checksums or git SHAs
- Base64 encoded test payloads

Manage by:
- **`#gitleaks:allow` inline comment** on the line
- **Allowlist in `.gitleaks.toml`** for files/patterns
- **Baseline file** with currently-known findings (don't break the build for legacy)

Discipline: every allowlist entry justified in a comment.

## 7. Beyond GitLeaks: the secret-scanning ecosystem

| Tool | When |
|---|---|
| **GitLeaks** | OSS, fast, default |
| **TruffleHog** | OSS, deep entropy analysis, **verifies secrets are live** (calls the API) |
| **GitHub Secret Scanning + Push Protection** | GitHub-native; 200+ partner patterns; push protection blocks at git server |
| **GitLab Secret Detection** | GitLab-native (Premium/Ultimate) |
| **AWS Macie** | Detects sensitive data in S3 (PII), not just credentials |
| **Snyk** | Commercial; broader DevSecOps platform |
| **GitGuardian** | Commercial; org-wide scanning + monitoring |

For Capital One scale: GitHub Secret Scanning + Push Protection + GitGuardian-equivalent commercial layer for monitoring + GitLeaks in dev pre-commit + CI.

## 8. SAST in pre-commit (a brief preview — full SCA in module 22)

Pre-commit can also run SAST:

```yaml
- repo: https://github.com/PyCQA/bandit
  rev: 1.7.10
  hooks:
    - id: bandit
      args: ['-c', 'pyproject.toml']
- repo: https://github.com/returntocorp/semgrep
  rev: v1.92.0
  hooks:
    - id: semgrep
      args: ['--config=auto', '--error']
```

Cost: slower commits. Calibrate to keep pre-commit < 10s total or devs will `--no-verify`.

## 9. Quick self-check

1. What does pre-commit do that running scanners individually doesn't?
2. Why must CI also scan even if pre-commit is installed?
3. What's the first step when a leaked secret is found in history?
4. What's TruffleHog's differentiator vs GitLeaks?
5. What's GitHub Push Protection and what advantage does it have over scanning at CI time?

(Answers: orchestrates many hooks from a single declarative config + version-pins them; devs can bypass with --no-verify; rotate the secret before doing anything to git; verifies the secret is actually live by calling the corresponding API; blocks the push at the git server before secret ever reaches remote — earliest possible mitigation.)



ewpage


# 21 — Vulnerability Management — DefectDojo + CWE

## Why this module exists

You have 6+ scanners (GitLeaks, Trivy, Snyk, ZAP, SonarQube, Checkov, Dependabot). Each outputs findings in its own format. Without normalization you can't:
- Dedupe (same CVE flagged by 3 tools = 3 tickets if not normalized)
- SLA-track (fix Critical in 7 days, High in 30 days)
- Report ("how many open Criticals on team X?")
- Prove compliance ("we triage every finding")

**DefectDojo** is the OSS aggregator. The commercial alternatives: **Snyk** (vendor's own platform), **Mend (WhiteSource)**, **Veracode**, **Checkmarx**, **GitLab Vulnerability Report** (built into Ultimate).

## 1. DefectDojo at a glance

- OSS (originally OWASP DefectDojo, now under SecurityCompass + community)
- Python + Django + Postgres
- Supports **200+ scanner formats** (parses JSON, SARIF, XML, etc.)
- Free; commercial **DefectDojo Pro** for SaaS deployment
- Self-hosted in Docker / K8s; many ASPM (Application Security Posture Mgmt) vendors built ON DefectDojo

## 2. Concepts

```
Product Type
  └─ Product (an application or service)
      └─ Engagement (a security activity: pen test, code scan campaign, etc.)
          └─ Test (one scanner run)
              └─ Finding (one vulnerability)
```

**Finding** properties:
- Severity (Critical / High / Medium / Low / Info)
- CWE
- CVE (if applicable)
- Status: Active / Verified / Mitigated / False-Positive / Out-of-Scope
- SLA dates
- Mitigation steps
- Notes

## 3. Install (Docker Compose for learning)

```bash
git clone https://github.com/DefectDojo/django-DefectDojo
cd django-DefectDojo
./dc-up.sh
# Wait, then:
./dc-up.sh --build-pull
# Get admin password:
docker compose -f docker-compose.yml logs initializer | grep "Admin password"
```

Browse http://localhost:8080. Login as `admin` + the password.

For production: K8s Helm chart from `https://github.com/DefectDojo/django-DefectDojo` charts dir.

## 4. Importing scanner results

Each scanner has its own DefectDojo "parser." Examples:

| Scanner | DefectDojo parser |
|---|---|
| Trivy | "Trivy Scan" |
| Bandit | "Bandit Scan" |
| GitLeaks | "Gitleaks Scan" |
| ZAP | "ZAP Scan" |
| Semgrep | "Semgrep JSON Report" |
| Checkov | "Checkov Scan" |
| Snyk | "Snyk Scan" |
| SARIF (universal) | "SARIF" |

Upload via UI or API:

```bash
curl -X POST "$DD_URL/api/v2/import-scan/" \
  -H "Authorization: Token $DD_API_TOKEN" \
  -F "scan_date=2026-05-22" \
  -F "minimum_severity=Low" \
  -F "active=true" \
  -F "verified=false" \
  -F "scan_type=Trivy Scan" \
  -F "file=@trivy-report.json" \
  -F "engagement=42" \
  -F "test_title=Trivy scan of api:1.2.3"
```

**reimport-scan** vs **import-scan**: reimport dedupes against existing findings → ticket already exists, no new one created. Use reimport in CI for repeated scans.

## 5. CI integration (the production pattern)

```yaml
# GitHub Actions snippet
- name: Trivy scan
  run: trivy image --format json -o trivy.json ghcr.io/me/app:${{ github.sha }}

- name: Upload to DefectDojo
  env:
    DD_URL: ${{ secrets.DD_URL }}
    DD_TOKEN: ${{ secrets.DD_TOKEN }}
  run: |
    curl -fsSL -X POST "$DD_URL/api/v2/reimport-scan/" \
      -H "Authorization: Token $DD_TOKEN" \
      -F "scan_date=$(date +%F)" \
      -F "scan_type=Trivy Scan" \
      -F "active=true" -F "verified=false" \
      -F "engagement=${{ vars.DD_ENGAGEMENT_ID }}" \
      -F "file=@trivy.json"
```

## 6. CWE — the taxonomy DefectDojo speaks

CWE = Common Weakness Enumeration. Maintained by MITRE. Hierarchical:
- **CWE-1000** view (research view, full tree)
- **CWE-1003** view (mapping into SDLC weaknesses)
- **CWE Top 25** annual list of most-dangerous

Examples:
- CWE-79 → XSS
- CWE-89 → SQL Injection
- CWE-22 → Path Traversal
- CWE-918 → SSRF
- CWE-787 → Out-of-bounds Write (most-dangerous in 2024)

DefectDojo uses CWE as the canonical taxonomy across scanners. CVE-XXXX (specific instance) maps to CWE-NNN (weakness category).

## 7. SLA + automation

Configure SLA per severity in DefectDojo:
- Critical: 7 days
- High: 30 days
- Medium: 60 days
- Low: 90 days

Findings past SLA show in the SLA dashboard. Integration with Jira/GitLab/GitHub Issues auto-creates tickets.

Other automation:
- **JIRA integration** — sync findings → tickets bidirectionally
- **Slack notifications** — on new Critical findings
- **API webhooks** — on finding-state changes

## 8. Risk acceptance + false-positive triage

Most scanners produce false positives. DefectDojo workflow:
1. **New finding** appears (Active, Unverified)
2. Triage: developer + security review
3. Set status: **Verified** (real) or **False-Positive** (incorrect)
4. Set **Mitigation** if accepted risk with compensating control
5. **Risk Acceptance** for findings that aren't false-positive but can't be fixed (compensating control + expiry date)

Risk Acceptance is reviewed quarterly. SR 11-7-style audit asks: "show me all accepted risks, their justifications, and their compensating controls."

## 9. Reporting + dashboards

DefectDojo dashboards:
- Open findings by severity + age
- Product risk scores
- Trends (findings/week, MTTR)
- SLA compliance

Export reports as PDF/CSV for auditors. SOC 2 / PCI-DSS auditors love this artifact.

## 10. Alternatives at a glance

| Tool | Comparison |
|---|---|
| **GitLab Vulnerability Report** | Built into GitLab Ultimate; tight CI integration; auto-dedupe; vendor-locked |
| **Snyk** | Best UX; commercial scanner + tracker; per-developer pricing |
| **GitHub Code Scanning** (CodeQL) | GitHub-native; SARIF-based; less rich tracking |
| **Checkmarx One** | Enterprise SAST/SCA/DAST + tracker |
| **Veracode** | Long-standing, enterprise; binary-analysis SAST |
| **OX Security / Apiiro / Cycode** | ASPM challengers — full lifecycle |

For Capital One scale: enterprise ASPM tool (Apiiro, Cycode, or similar) + GHAS Code Security + internal triage workflows.

## 11. Quick self-check

1. What problem does DefectDojo solve that running scanners individually doesn't?
2. What's the difference between import-scan and reimport-scan?
3. What's CWE vs CVE?
4. What's a "Risk Acceptance" in DefectDojo and why is it audited?
5. Name three commercial alternatives to DefectDojo.

(Answers: normalizes findings from many scanners into one trackable backlog with dedup + SLA + reporting; reimport dedupes findings vs existing ones, import creates fresh — use reimport in CI; CWE is a category of weakness, CVE is a specific instance/identifier; finding kept open with compensating control and expiry instead of fixed — auditors check justification + control + expiry; Snyk, Mend, Veracode, Checkmarx, GitLab Vulnerability Report, GitHub Code Scanning.)



ewpage


# 22 — SCA — Software Composition Analysis

## Why this module exists

Your app is 5% your code and 95% open-source dependencies. SCA scans your dependency tree for known CVEs, license issues, and dangerous transitive deps. **xz utils backdoor (CVE-2024-3094, March 2024)** was a wake-up call — supply chain risk is real.

## 1. The SCA scope

What SCA covers:
1. **Known CVEs in dependencies** — match dep → NVD / GHSA / OSV databases
2. **License compliance** — GPL in proprietary code, license incompatibilities
3. **End-of-life packages** — unmaintained deps
4. **Transitive deps** — your direct dep brings 50 transitive deps; SCA scans them all
5. **Container base images** — image deps are also dependencies

## 2. The vuln-data sources

| Source | What |
|---|---|
| **NVD** (NIST National Vulnerability Database) | Authoritative CVE feed |
| **GHSA** (GitHub Advisory Database) | GitHub's curated DB; often faster than NVD |
| **OSV.dev** (Google) | Multi-ecosystem; structured |
| **PyPA Advisory DB** | Python-specific |
| **rustsec advisory DB** | Rust |
| **npm Advisory** | JS |
| **CVE.org / MITRE** | The numbering authority |

CVSS = Common Vulnerability Scoring System (0-10 severity). EPSS = Exploit Prediction Scoring System (probability of exploitation in next 30 days — newer + more actionable than CVSS).

## 3. SCA tool landscape

| Tool | Lang/Ecosystem | License |
|---|---|---|
| **Dependabot** (GitHub) | All | Free with GitHub |
| **Renovate** | All | OSS |
| **Snyk Open Source** | All | Commercial |
| **OWASP Dependency-Check** | Java + others | OSS |
| **Trivy fs** | All | OSS |
| **Grype** | All | OSS |
| **GitHub Dependency Graph** | All | Free with GitHub |
| **GitLab Dependency Scanning** | All | GitLab Ultimate |
| **JFrog Xray** | All | Commercial |
| **Sonatype Nexus IQ** | All | Commercial |
| **Mend (formerly WhiteSource)** | All | Commercial |
| **OSV-Scanner** (Google) | All | OSS |

## 4. Dependabot — the GitHub default

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 10
    groups:
      python-deps:
        patterns: ["*"]
        update-types: ["minor", "patch"]
    ignore:
      - dependency-name: "numpy"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }

  - package-ecosystem: "docker"
    directory: "/"
    schedule: { interval: "weekly" }
```

Dependabot:
- Opens PRs for vulnerable + outdated deps
- Free; included with GitHub
- "Dependabot security updates" auto-open PRs for known CVEs even without schedule
- Use **groups** to bundle related deps (avoid 50 PRs)

## 5. Renovate — the more powerful alternative

Renovate (originally GitLab; now Mend-owned, still OSS) supersedes Dependabot for serious shops:
- Customizable group rules (e.g., "all minor TS deps in one PR weekly")
- Auto-merge when CI passes
- Dependency dashboard issue with all pending updates
- Better monorepo support (per-workspace updates)
- Supports more ecosystems
- Available as GitHub App, GitLab integration, or self-hosted

`renovate.json`:
```json
{
  "extends": ["config:recommended"],
  "schedule": ["before 6am on monday"],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true,
      "automergeType": "branch"
    },
    {
      "matchPackageNames": ["torch", "transformers"],
      "schedule": ["before 6am on the first day of the month"]
    }
  ],
  "vulnerabilityAlerts": { "labels": ["security"], "automerge": false }
}
```

## 6. Trivy fs — SCA for any repo, CLI-friendly

```bash
# Scan a project directory
trivy fs --severity HIGH,CRITICAL --exit-code 1 .

# JSON output for DefectDojo
trivy fs -f json -o trivy-fs.json .

# Specific dep file
trivy fs --scanners vuln,secret,misconfig requirements.txt
```

Trivy combines: dep scanning + secret scanning + misconfig (IaC) scanning in one tool. The OSS Swiss Army knife.

## 7. License compliance

A few cases where SCA flags licenses:
- **GPL in proprietary code** — copyleft viral license; can force open-sourcing
- **AGPL** — even network use triggers source disclosure
- **No license** — defaults to "All rights reserved"; legally can't use
- **License mismatch with corporate policy** — many shops forbid AGPL, GPL > v2

Tools:
- **FOSSology** — OSS license scanner
- **ScanCode** — OSS license + provenance
- **Snyk License Compliance / Mend Licenses** — commercial
- **Software Bill of Materials (SBOM)** — see Module 24

## 8. Pinning + lockfiles (the supply-chain discipline)

The 2026 best practice:
- **Pin direct deps to exact versions** in your dependency file (e.g., `pandas==2.2.3` not `pandas>=2.0`)
- **Commit the lockfile** (poetry.lock, uv.lock, package-lock.json, go.sum)
- **For lockfile in cryptographic-hash form** (npm has integrity hashes, Go has go.sum hashes, uv has hash-verified lock)
- **For pip:** `pip-tools` or `uv` + hash-checking mode
- **Renovate / Dependabot** to bump deliberately

The xz utils backdoor exploited *new versions* — pinning doesn't fully protect (you'd update eventually) but **dependency review before merge** does.

## 9. SCA in CI

```yaml
# GitLab Ultimate has built-in
sast: { stage: test }
dependency_scanning: { stage: test }
include:
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/SAST.gitlab-ci.yml
```

```yaml
# GitHub Actions with Trivy
- name: SCA
  run: trivy fs --severity HIGH,CRITICAL --exit-code 1 --format sarif -o trivy.sarif .

- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: trivy.sarif }
```

```yaml
# GitHub Actions with Snyk
- uses: snyk/actions/python-3.10@master
  env: { SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }} }
  with: { command: monitor }
```

## 10. EPSS — the prioritization tool

EPSS (Exploit Prediction Scoring System) gives each CVE a probability of being exploited in the next 30 days. Far more actionable than CVSS.

- CVSS 10.0 + EPSS 0.0001 → critical but no known exploit; lower urgency
- CVSS 6.0 + EPSS 0.85 → medium but actively exploited; **fix now**

Modern SCA tools (Snyk, Mend) surface EPSS alongside CVSS. CISA's Known Exploited Vulnerabilities (KEV) catalog is the binary version: it's on the list or not.

## 11. The remediation playbook

For each SCA finding:
1. **Is it reachable?** If your code doesn't call the vulnerable function, severity may be lower (Snyk Reachability / Phylum / Endor Labs sell this analysis).
2. **Is there a fix?** Upgrade to patched version.
3. **No fix yet?** Workaround? Compensating control? Risk-accept with expiry?
4. **Mark in DefectDojo** with status.
5. **Track SLA** — Critical: 7 days; High: 30; Medium: 60.

## 12. Quick self-check

1. What's the difference between Dependabot and Renovate?
2. What's EPSS and why is it more actionable than CVSS alone?
3. Why does pinning direct deps not fully protect against supply-chain attacks?
4. What's the OSV.dev project?
5. What does "reachability analysis" do for SCA findings?

(Answers: Dependabot is GitHub-built, simple; Renovate is more configurable, OSS, group rules, automerge, monorepo-friendly; EPSS predicts exploit probability in next 30d — CVSS only measures theoretical severity; eventually you upgrade and pick up the malicious version (xz pattern); Google's multi-ecosystem structured vuln DB; tells you whether your code actually calls the vulnerable function — lowers severity for unreachable findings.)



ewpage


# 23 — Build a CD Pipeline + AWS ECR

## 1. CI/CD as one pipeline

Continuous Integration (CI) ends when the artifact is built + tested. Continuous Delivery (CD) takes that artifact through environments to production. **CD = deploy to staging automatically + prod with approval. Continuous Deployment = no approval, every green build to prod.**

A pipeline stage map:
```
Lint → Test → SAST → SCA → Build Image → Image Scan → Push to ECR → Deploy DEV → DAST → Deploy STG → Approval → Deploy PROD
```

## 2. Security gates per stage (the DevSecOps mapping)

| Stage | Security gate |
|---|---|
| Lint | Pre-commit hooks: gitleaks, secrets scan |
| Test | Unit + integration tests pass |
| SAST | SonarQube / Semgrep / Bandit critical findings = 0 |
| SCA | Trivy fs / Snyk; Critical CVEs = 0 |
| Build | Reproducible build; non-root user |
| Image scan | Trivy image / ECR enhanced scanning; Critical CVEs = 0 |
| Push | Sign with Cosign; attach SBOM |
| Deploy | Admission control (Kyverno) verifies signature + policy |
| DAST | ZAP baseline scan against deployed app |
| Prod approval | Manual gate; CODEOWNERS-style approval |

## 3. The 80/20 GitLab CI pipeline

```yaml
stages: [test, build, scan, deploy-dev, dast, deploy-prod]

variables:
  IMAGE: ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHORT_SHA}

test:
  stage: test
  image: python:3.13-slim
  script:
    - pip install -r requirements.txt -r requirements-dev.txt
    - pytest --cov

sast:
  stage: test
  include: { template: Jobs/SAST.gitlab-ci.yml }

dep-scan:
  stage: test
  include: { template: Jobs/Dependency-Scanning.gitlab-ci.yml }

build:
  stage: build
  image: gcr.io/kaniko-project/executor:latest
  script:
    - /kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/Dockerfile --destination $IMAGE

container-scan:
  stage: scan
  image: aquasec/trivy
  script:
    - trivy image --severity CRITICAL,HIGH --exit-code 1 $IMAGE

deploy-dev:
  stage: deploy-dev
  environment: { name: dev, url: https://dev.example.com }
  script: kubectl set image deployment/app app=$IMAGE
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

dast:
  stage: dast
  image: owasp/zap2docker-stable
  script:
    - zap-baseline.py -t https://dev.example.com -r dast-report.html
  artifacts:
    paths: [dast-report.html]
  allow_failure: true

deploy-prod:
  stage: deploy-prod
  environment: { name: prod, url: https://example.com }
  script: kubectl set image deployment/app app=$IMAGE
  when: manual
  only: [tags]
```

## 4. ECR — Elastic Container Registry

### Authenticate
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  1234.dkr.ecr.us-east-1.amazonaws.com
```

In CI, use **OIDC + IAM Role** instead of long-lived keys:

```yaml
# GitHub Actions
permissions: { id-token: write, contents: read }
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::1234:role/github-actions-ecr-push
    aws-region: us-east-1
- run: |
    aws ecr get-login-password | docker login --username AWS --password-stdin 1234.dkr.ecr.us-east-1.amazonaws.com
    docker buildx build --push -t 1234.dkr.ecr.us-east-1.amazonaws.com/app:${{ github.sha }} .
```

### ECR features
- **Image scanning (basic, free)** — Clair-based on push
- **Enhanced scanning (Inspector, paid)** — continuous CVE rescans, OS + OSS package coverage
- **Lifecycle policies** — auto-delete old images
- **Replication** — multi-region or cross-account
- **Pull-through cache** — proxy Docker Hub/Quay/GHCR (avoids public rate limits)
- **Repository policies** — IAM-based cross-account access
- **Signing** — supports Notation / Cosign signature artifacts

### Lifecycle policy (essential for cost)
```json
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep last 10 tagged images",
      "selection": {
        "tagStatus": "tagged",
        "tagPrefixList": ["v"],
        "countType": "imageCountMoreThan",
        "countNumber": 10
      },
      "action": { "type": "expire" }
    },
    {
      "rulePriority": 2,
      "description": "Expire untagged after 7 days",
      "selection": {
        "tagStatus": "untagged",
        "countType": "sinceImagePushed",
        "countUnit": "days",
        "countNumber": 7
      },
      "action": { "type": "expire" }
    }
  ]
}
```

## 5. Deploying to EC2 (Nana's bootcamp baseline)

For an EC2 target with Docker, the pattern:
1. SSH from CI to EC2 (or use SSM RunCommand — modern, no inbound 22)
2. Pull new image from ECR
3. Stop + start container
4. Health check

```bash
ssh deploy@$EC2_HOST <<EOF
  aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin $ECR_REGISTRY
  docker pull $ECR_REGISTRY/app:$VERSION
  docker stop app || true
  docker rm app || true
  docker run -d --name app --restart=unless-stopped \
    -p 80:8000 $ECR_REGISTRY/app:$VERSION
EOF
```

Better: SSM RunCommand (Module 26 covers this) avoids inbound SSH.

## 6. Self-managed GitLab Runner on EC2

```bash
# On EC2
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner
useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register
gitlab-runner register --url https://gitlab.com --token <runner-auth-token> \
  --executor docker --docker-image alpine:3.20
```

Considerations:
- Runners on EC2 in a private subnet; pipelines connect outbound to GitLab.com (or to self-hosted GitLab).
- Tag runners by capability (e.g., `aws`, `large-runner`, `gpu`).
- Auto-scaling via AWS Fleet executor.

## 7. Docker caching on self-managed runner

Each build re-runs `docker build` cold = slow. Options:
- **BuildKit local cache mount** — cache between builds on same runner
- **--cache-from / --cache-to** with registry-based cache
- **buildx with `--cache-to type=registry`** — push cache to ECR cache repo

```bash
docker buildx build \
  --cache-from type=registry,ref=$ECR/cache:buildcache \
  --cache-to type=registry,ref=$ECR/cache:buildcache,mode=max \
  -t $IMAGE --push .
```

10x+ build speedup for incremental changes.

## 8. Multi-environment deploys (Dev → Staging → Prod)

The pattern:
```
main branch push → deploy DEV → run DAST → on success → deploy STG → manual approval → deploy PROD
```

Environment-specific config:
- AWS account per environment (Capital One: separate accounts under one Organization)
- Different K8s namespace or whole separate clusters per env
- DB per environment (never shared between envs)
- Secrets per env in Secrets Manager

## 9. Quick self-check

1. What's the difference between Continuous Delivery and Continuous Deployment?
2. Why use OIDC + IAM Role over AWS access keys in CI?
3. What's an ECR lifecycle policy and why is it essential?
4. What's the modern alternative to SSH-from-CI-to-EC2?
5. How does BuildKit registry-cache speed up Docker builds in CI?

(Answers: Delivery = automated to staging + manual prod, Deployment = no manual; short-lived creds, no long-lived secrets to rotate or leak, audited via CloudTrail; auto-deletes old images to control storage cost — ECR is pay-per-GB; SSM RunCommand — no inbound 22, IAM-based auth, fully audited; caches built layers in a registry so subsequent builds pull cached layers instead of rebuilding.)



ewpage


# 24 — Image Scanning — Trivy + Cosign + ECR

## Why this module exists

Your Dockerfile picked `python:3.13-slim` six months ago. Today that base image has 8 unpatched CVEs. Image scanning catches this before deployment. Image signing proves the artifact you deploy is the one you scanned.

## 1. The image-scanning matrix

| Tool | License | Scope |
|---|---|---|
| **Trivy** | Apache-2.0 | OS pkgs + lang deps + secrets + misconfigs + SBOM |
| **Grype** (Anchore) | Apache-2.0 | OS pkgs + lang deps |
| **Syft** (Anchore) | Apache-2.0 | SBOM generator (paired with Grype) |
| **Snyk Container** | Commercial | OS + lang + base-image recommendations |
| **Docker Scout** | Free + paid tiers | Docker Hub-integrated; Docker Inc. |
| **ECR Basic Scanning** | Free | Clair-based; on push |
| **ECR Enhanced Scanning** | Paid (Inspector) | Continuous; OS + OSS + Lambda |
| **GitHub Code Scanning** (Trivy/Container) | GHAS | Built into Actions; SARIF |
| **Anchore Engine / Sysdig Secure** | Commercial | Enterprise platform |

**Trivy is the OSS de-facto winner.** Installed in ~70% of K8s clusters per 2024 CNCF survey.

## 2. Trivy basics

```bash
# Install
brew install trivy

# Scan an image
trivy image python:3.13-slim
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:1.2.3

# Generate SBOM
trivy image --format cyclonedx -o sbom.json myapp:1.2.3
trivy image --format spdx-json -o sbom.spdx myapp:1.2.3

# Scan filesystem (pre-build)
trivy fs --severity HIGH,CRITICAL .

# Scan IaC
trivy config terraform/

# Scan a running K8s cluster
trivy k8s --report=summary cluster
```

### Output formats
- `table` — human-readable
- `json` — machine-readable
- `sarif` — for GitHub Code Scanning
- `cyclonedx` / `spdx-json` — SBOM formats
- `template` + custom templates — flexible

## 3. Trivy in CI

```yaml
# GitHub Actions
- name: Build image
  run: docker build -t app:${{ github.sha }} .

- name: Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: app:${{ github.sha }}
    severity: CRITICAL,HIGH
    exit-code: '1'
    format: sarif
    output: trivy.sarif

- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: trivy.sarif }
```

## 4. Cosign — image signing

```bash
# Install
brew install cosign

# Generate key pair (for traditional key-based; in 2026 prefer keyless)
cosign generate-key-pair
# cosign.pub + cosign.key produced

# Sign with key
cosign sign --key cosign.key 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Verify with public key
cosign verify --key cosign.pub 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Keyless (OIDC-based, the modern way)
cosign sign 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
# Opens browser; auth via OIDC (GitHub, Google, etc.)
# Signature + ephemeral cert from Fulcio + entry in Rekor transparency log

cosign verify \
  --certificate-identity-regexp 'https://github.com/myorg/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
```

### Keyless signing (the 2026 best practice)
- No key management — ephemeral keys per signing
- Identity bound to OIDC subject (GitHub repo, Google account)
- Verifiable in **Rekor** transparency log (immutable append-only)
- Signed by **Fulcio** (CA for short-lived certs)
- Part of the **Sigstore** project (Linux Foundation)

## 5. Attestations — SBOM, provenance, attestations as artifacts

Beyond signatures, Cosign can sign **attestations**:

```bash
# Generate SBOM
syft 1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3 -o cyclonedx-json > sbom.json

# Attach SBOM as attestation
cosign attest --predicate sbom.json --type cyclonedx \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3

# Verify
cosign verify-attestation --type cyclonedx \
  --certificate-identity-regexp 'https://github.com/myorg/' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  1234.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3
```

Attestation types: `cyclonedx` (SBOM), `slsaprovenance` (build provenance per SLSA), `vuln` (scan results), `custom`.

## 6. SLSA — Supply chain Levels for Software Artifacts

SLSA v1.0 (2023) defines 4 levels of build-provenance hygiene:

| Level | What you prove |
|---|---|
| **L1** | Build is automated; provenance generated |
| **L2** | Provenance is signed; build runs on hosted service with audit |
| **L3** | Build runs in isolated env; provenance is non-falsifiable |
| **L4** | Two-party review of all changes; hermetic builds |

GitHub Actions can produce SLSA L3 provenance via the **slsa-github-generator** project.

Capital One internal policy: SLSA L3 minimum for production artifacts.

## 7. Admission control + signature verification at deploy

The deploy gate: K8s admission controller (Kyverno, OPA Gatekeeper, Sigstore Policy Controller) **verifies signatures before allowing pods**.

```yaml
# Kyverno policy: only signed images from your repo
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-signatures
      match: { any: [{ resources: { kinds: [Pod] } }] }
      verifyImages:
        - imageReferences: ["1234.dkr.ecr.us-east-1.amazonaws.com/*"]
          attestors:
            - entries:
              - keyless:
                  subject: "https://github.com/myorg/*"
                  issuer: "https://token.actions.githubusercontent.com"
```

Pod fails admission if image isn't signed by your CI. This **closes the supply-chain loop** — verified at every stage from build to deploy.

## 8. ECR-specific image security

- **Basic scanning (free)** — Clair-based, runs on push only
- **Enhanced scanning** — uses **Amazon Inspector v2**; continuously rescans + alerts on new CVEs in already-pushed images
- **Pricing for Inspector**: ~$0.09 per image scan, ~$0.01 per image scan re-evaluation
- **Cross-account replication** for multi-team setups
- **Image tags immutable** option (toggle on repo) — once tagged, can't overwrite (prevents tag-takeover supply-chain attacks)

```bash
aws ecr put-image-scanning-configuration \
  --repository-name app --image-scanning-configuration scanOnPush=true

aws ecr put-image-tag-mutability \
  --repository-name app --image-tag-mutability IMMUTABLE
```

## 9. Distroless + minimal base images

Smaller base images = smaller attack surface = fewer CVEs to chase.

- **Distroless** (Google) — no shell, no package manager, just the runtime + your app
- **Chainguard Images** — distroless-style, daily-rebuilt, FIPS-validated options
- **Alpine** — small (~5MB) but has musl libc quirks
- **Wolfi** (Chainguard's distroless base) — glibc-based, designed for chainguard images

```dockerfile
# Build with full Python
FROM python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .

# Runtime distroless
FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /root/.local /home/nonroot/.local
COPY --from=builder /app /app
WORKDIR /app
ENV PATH=/home/nonroot/.local/bin:$PATH
CMD ["main.py"]
```

## 10. The end-to-end secure-image pipeline

```
Build (BuildKit, --no-cache-dir, non-root user, immutable tag)
  ↓
Scan with Trivy (HIGH+CRITICAL fail build)
  ↓
Generate SBOM with Syft
  ↓
Sign image with Cosign (keyless via OIDC)
  ↓
Attest SBOM with Cosign
  ↓
Generate SLSA provenance
  ↓
Push to ECR (immutable tags, enhanced scanning on)
  ↓
Deploy via ArgoCD/Flux
  ↓
Kyverno admission verifies signature + SBOM + provenance
  ↓
Falco runtime watches for drift / anomaly
```

This is the **SLSA L3 + verify-at-admission** pattern Capital One implements internally.

## 11. Quick self-check

1. What does Trivy scan beyond just OS package CVEs?
2. What's "keyless signing" with Cosign and what 3 components make it work?
3. What's the difference between an image signature and an attestation?
4. Why use immutable image tags?
5. What's SLSA L3 in one sentence?

(Answers: lang deps, secrets, IaC misconfigs, can also generate SBOM; OIDC-based ephemeral keys — Sigstore = Fulcio (CA) + Rekor (transparency log) + Cosign (CLI); signature proves who built it, attestation provides additional verified statements (SBOM, provenance, scan results); prevents tag-takeover supply-chain attacks where an attacker pushes a different image at the same tag; build runs in isolated env producing non-falsifiable provenance signed by the build platform.)



ewpage


# 25 — AWS Cloud Security Essentials (IAM Deep)

> Cross-link: [Topic 04 Part A (Modules 2-4)](../04_aws_for_ai_ml/) covers IAM, accounts, billing exhaustively. This module is the **DevSecOps subset** — IAM as a security primitive.

## 1. The AWS security model

- **Shared Responsibility**: AWS secures the cloud (hypervisor, datacenters, networking fabric). You secure what's *in* the cloud (your data, your apps, your IAM).
- **Identity is the new perimeter.** In 2026 there is no "trust the VPC"; assume any pod, any function, any user could be compromised. IAM + per-resource policies decide everything.

## 2. Securing the root user

Root user = god mode on the account. Steps you take **once**:
1. Set strong unique password
2. MFA on hardware key (YubiKey/Titan) — not SMS, not authenticator app for root
3. Delete root access keys if any
4. Use root account only for: account-level changes, billing, account closure
5. Set up account contacts (security + billing + operations)
6. Enable **MFA delete** on critical S3 buckets

Lock it in a virtual safe and walk away.

## 3. IAM core concepts

### Principals
- **Users** — long-lived identities (humans); use Identity Center SSO instead
- **Roles** — temporary creds; assumed by services (EC2 role), federated users (SSO), other accounts (cross-account)
- **Groups** — collections of users (not principals themselves)
- **Federated identities** — external (SAML, OIDC) mapped to roles

### Policies
- **Identity-based** — attached to user/role/group; what *they* can do
- **Resource-based** — attached to resource (S3 bucket, KMS key); who can do what to *it*
- **Permission boundaries** — max-permissions cap on a role; useful for delegated admin
- **SCPs (Service Control Policies)** — Organization-level guardrails (deny-by-default at OU)
- **RCPs (Resource Control Policies)** — Org-level on resources (2024 GA)
- **Session policies** — narrow permissions at AssumeRole time

### Permissions evaluation (the precedence)
```
Explicit DENY → wins, always
Else if SCP/RCP doesn't allow → DENY
Else if permission boundary doesn't allow → DENY
Else if identity policy + resource policy don't allow → DENY (implicit)
Else → ALLOW
```

Master this; it answers 80% of "why is X denied?" questions.

## 4. Policy anatomy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowReadS3",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "Bool": { "aws:MultiFactorAuthPresent": "true" },
        "IpAddress": { "aws:SourceIp": "10.0.0.0/8" }
      }
    }
  ]
}
```

`Action` = what (read, write, delete, list). `Resource` = on what. `Condition` = under what circumstances. `Effect` = Allow or Deny.

## 5. The IAM patterns you'll use

### Principle of least privilege
Start narrow; grant only what's needed; expand on demand. Use **IAM Access Analyzer** to detect over-privileged policies and generate policies from CloudTrail history.

### MFA required for sensitive actions
```json
{
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": {
    "BoolIfExists": { "aws:MultiFactorAuthPresent": "false" }
  }
}
```
Apply via SCP or to specific roles.

### IP allowlist for human users
```json
"Condition": {
  "NotIpAddress": { "aws:SourceIp": ["10.0.0.0/8", "1.2.3.4/32"] }
}
```

### Service-linked roles
AWS creates these per service (e.g., AWSServiceRoleForRDS); don't modify, don't delete unless removing the service.

## 6. IAM Identity Center (formerly AWS SSO)

The 2026 recommended way to give humans access:
- SCIM-sync from your IdP (Okta, Entra ID, JumpCloud)
- Permission sets defined centrally; assigned per account
- Short-lived credentials (no long-lived access keys for humans!)
- One sign-in across all member accounts

```
Identity Center → Permission Set "Developer" → applied to account 111111 and 222222
                → Permission Set "Admin" → applied only to admin account
                → Permission Set "ReadOnly" → applied across all accounts for auditors
```

## 7. CI/CD authentication — OIDC + IAM Role

The **2026 standard** (covered Module 29 + Topic 07 Module 46):
- GitHub Actions / GitLab CI / CircleCI publish OIDC tokens
- IAM trust policy on a role: "this role can be assumed by tokens from `https://token.actions.githubusercontent.com` matching org `myorg` and repo `myrepo`"
- No long-lived access keys = nothing to leak or rotate

Trust policy example:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::1234:oidc-provider/token.actions.githubusercontent.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
      "StringLike": { "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:ref:refs/heads/main" }
    }
  }]
}
```

## 8. KMS — encryption keys

- **AWS-managed keys** — created automatically by service (aws/s3, aws/ebs); free
- **Customer-managed keys (CMK)** — you own; ~$1/mo per key + API calls; can rotate, can restrict
- **CloudHSM** — dedicated FIPS-140-2 L3 hardware; expensive; required for some compliance

CMK best practices:
- One CMK per service per account per environment (don't share)
- **Key policy + IAM policy** must both allow (defense in depth)
- **Automatic annual rotation** on
- Use **multi-region keys** for replicated data
- **Key grants** for temporary delegations

## 9. Secrets Manager + Parameter Store

| Feature | Secrets Manager | SSM Parameter Store |
|---|---|---|
| **Cost** | $0.40/secret/mo + $0.05/10k reads | Free standard tier (4KB max), $0.05/10k reads for advanced |
| **Automatic rotation** | Yes (RDS native) | No |
| **Cross-region replication** | Yes | No |
| **Max size** | 64KB | 4KB (std) / 8KB (advanced) |
| **Use case** | DB creds, API keys | Config, env-specific values |

Use SSM Parameter Store for config + free-tier secrets; Secrets Manager when you need rotation or > 4KB.

Both integrate with **External Secrets Operator** for K8s (Module 35).

## 10. Audit baseline (the must-haves)

- **CloudTrail** — every API call; multi-region trail; S3 + CloudWatch destinations
- **Config** — resource configuration history + compliance rules (Module 37)
- **GuardDuty** — threat detection from VPC Flow Logs + DNS logs + CloudTrail
- **Security Hub** — aggregates findings from GuardDuty, Inspector, Macie, Config, IAM Access Analyzer
- **Inspector v2** — vulnerability scanning for EC2, Lambda, ECR
- **Macie** — sensitive-data discovery in S3

Capital One: all of the above, plus **Cloud Custodian** for policy enforcement.

## 11. The IAM mistakes that cause breaches

1. **Wildcard `Resource: *` on `Action: *`** — admin access where dev should have view
2. **Long-lived access keys for humans** — Capital One 2019 root cause adjacent
3. **No MFA on critical roles** — anyone with the access key wins
4. **Trust policy with `Principal: *`** — anyone in the world can assume
5. **IAM role with NetworkPolicy = none** — pod can hit metadata service
6. **Resource policies allowing cross-account without conditions** — supply-chain risk
7. **Sharing keys via Slack/email** — guarantees breach

## 12. Quick self-check

1. What's the precedence order for IAM permission evaluation?
2. What's the difference between SCP and IAM policy?
3. Why use OIDC instead of access keys for CI/CD?
4. When use SSM Parameter Store vs Secrets Manager?
5. What does IAM Access Analyzer do?

(Answers: explicit Deny → SCP → permission boundary → identity policy ∩ resource policy → implicit Deny; SCP is Org-level guardrail (can't grant, only deny), IAM policy is account-level grant; short-lived creds, nothing to leak/rotate, audited; Parameter Store for config + small free secrets, Secrets Manager for rotation + large/cross-region; finds over-privileged policies and generates least-privilege policies from CloudTrail history.)



ewpage


# 26 — Secure CD + DAST with OWASP ZAP

## Why this module exists

SAST scans your source code; SCA scans your deps; image scans look at the built artifact. **DAST (Dynamic Application Security Testing) scans the running app** — finds runtime vulns SAST can't (auth flaws, business logic, configuration issues).

## 1. DAST vs SAST vs IAST

| | SAST | DAST | IAST |
|---|---|---|---|
| **When** | Code-time | Runtime | Runtime, instrumented |
| **Needs** | Source code | Running app | Agent in the app |
| **Finds** | Pattern matches, taint flows | Real exploit attempts | Both |
| **False positives** | High | Lower | Lowest |
| **Speed** | Fast | Slow (full scan: hours) | Real-time |
| **Tooling** | Semgrep, CodeQL, SonarQube, Bandit | OWASP ZAP, Burp Suite, StackHawk | Contrast, Seeker (HCL) |

You want all three (or at least SAST + DAST). Capital One does.

## 2. OWASP ZAP — the OSS DAST leader

ZAP (Zed Attack Proxy) — originally OWASP flagship; since 2023 hosted by **The Software Security Project** (separate non-profit, after OWASP governance changes); still OSS Apache-2.0.

Modes:
- **Baseline scan** — passive, ~2 min; finds low-hanging fruit
- **Full scan** — active, can run hours; sends actual attack payloads
- **API scan** — given an OpenAPI/GraphQL/SOAP spec, tests endpoints

## 3. ZAP baseline scan in CI

```yaml
# GitLab CI
dast-baseline:
  stage: dast
  image: ghcr.io/zaproxy/zaproxy:stable
  script:
    - zap-baseline.py -t https://staging.example.com -r dast-report.html -J dast.json -m 10
  artifacts:
    paths:
      - dast-report.html
      - dast.json
    expire_in: 30 days
  allow_failure: true
```

```yaml
# GitHub Actions
- name: ZAP Baseline Scan
  uses: zaproxy/action-baseline@v0.13.0
  with:
    target: https://staging.example.com
    rules_file_name: '.zap/rules.tsv'
    cmd_options: '-J zap.json'
```

Baseline scan does:
- Spider the site
- Identify forms, headers, cookies
- Check for missing security headers (CSP, HSTS, X-Frame-Options)
- Check cookie attributes (HttpOnly, Secure, SameSite)
- TLS configuration check
- Default credential checks
- **Does NOT send malicious payloads** — safe to run nightly

## 4. ZAP full scan

```bash
docker run -v $(pwd):/zap/wrk -t ghcr.io/zaproxy/zaproxy:stable \
  zap-full-scan.py -t https://staging.example.com -r full-report.html
```

Full scan **does** send active payloads (SQL injection attempts, XSS payloads, command injection). Only run against test environments — never production. Coordinate with WAF teams (will trigger alerts).

## 5. ZAP API scan (for REST/GraphQL APIs)

```bash
zap-api-scan.py -t https://api.example.com/openapi.json \
  -f openapi -r api-report.html
```

ZAP parses the OpenAPI spec; tests every endpoint with auth + edge cases.

## 6. Custom rules + authentication

DAST against authenticated apps requires teaching ZAP to log in:

```yaml
# Authentication config (ZAP automation framework)
env:
  contexts:
    - name: app
      urls: [https://staging.example.com/]
      authentication:
        method: json
        parameters:
          loginUrl: https://staging.example.com/api/login
          loginRequestBody: '{"username":"qa","password":"qa"}'
        verification:
          method: poll
          loggedInRegex: "\\Q\"loggedIn\":true\\E"
      sessionManagement:
        method: cookie
      users:
        - name: qa
          credentials: { username: qa, password: qa }
```

Then `zap-baseline.py -t ... --hook /zap/auth-hook.py`.

## 7. WAF interaction

Your WAF (AWS WAF, Cloudflare, Akamai) will block DAST scans. Options:
- **Whitelist scanner IPs** in WAF for the staging environment
- **Disable WAF on staging** entirely
- **Tag traffic** so WAF logs but doesn't block

Coordinate with security team; don't surprise the SOC with attack traffic at 3am.

## 8. Beyond ZAP — the DAST landscape

| Tool | Note |
|---|---|
| **Burp Suite Community / Pro** | Manual pen-tester favorite; Pro adds scanner ($499/yr/user) |
| **StackHawk** | Commercial; ZAP-engine-based; CI-friendly; per-app pricing |
| **Invicti** / **Acunetix** | Enterprise web app + API |
| **Wallarm** / **42Crunch** | API-specific |
| **Schemathesis** | OSS property-based API testing |

For CI integration: ZAP or StackHawk are the realistic choices. Burp Pro is for manual review.

## 9. API-specific DAST

REST/GraphQL APIs need different testing than full web apps. Tools:
- **Schemathesis** — OSS; property-based from OpenAPI/GraphQL schema
- **42Crunch** — API security platform
- **Wallarm** — API security
- **Postman + Newman** — collection-based functional tests (not security but useful baseline)

```bash
# Schemathesis
schemathesis run https://api.example.com/openapi.json --checks all
```

## 10. Mobile app DAST

For mobile (iOS/Android), DAST means:
- **MobSF** (Mobile Security Framework) — OSS, static + dynamic for mobile binaries
- **NowSecure** — commercial
- **Quark Engine** — Android malware analysis

Less common for back-end engineers; relevant if you ship a mobile app.

## 11. The complete DevSecOps pipeline (where DAST fits)

```
SAST (CI on PR)
  ↓
SCA (CI on PR)
  ↓
Image scan (CI after build)
  ↓
Deploy to staging
  ↓
DAST baseline (post-deploy, on every release)
  ↓
DAST full (nightly, scheduled)
  ↓
DAST API (on schema change)
  ↓
Manual pen test (quarterly)
```

## 12. Quick self-check

1. What's the difference between SAST and DAST?
2. What's the difference between ZAP baseline scan and ZAP full scan?
3. Why can't you run DAST full-scan against production?
4. Why is authenticated DAST significantly harder than unauthenticated?
5. What is Schemathesis and what makes it different from ZAP?

(Answers: SAST scans source code, DAST scans the running app; baseline is passive + safe ~2min, full sends active attack payloads + can run hours; DAST sends real attack payloads that could damage data, trip WAFs, or affect real users; ZAP has to learn login flow + maintain session + re-auth as session expires; OSS property-based API testing from OpenAPI/GraphQL schema — generates test inputs from contract, complementary to ZAP.)



ewpage


# 27 — IaC + GitOps for DevSecOps

## Why this module exists

IaC + GitOps is the structural foundation of DevSecOps. If your infrastructure is in Git: every change is reviewable, every artifact is auditable, every drift is detectable. This module connects Terraform (Module 13) and GitOps practices to the security posture.

## 1. The "Cattle vs Pets" concept

- **Pets** — named, hand-tended, irreplaceable (the legacy server `db01.prod`)
- **Cattle** — numbered, interchangeable, disposable (`autoscaling-group-prod-abc123`)

For DevSecOps: pets are the enemy. They accumulate manual changes, drift from the original config, are impossible to rebuild from source. Cattle are *defined* in code; any instance can be destroyed and rebuilt identically.

## 2. IaC security wins

| Without IaC | With IaC |
|---|---|
| Manual click-ops; un-auditable | Every change in Git history |
| Config drift = compliance gap | Drift detected by `terraform plan` |
| Lost-credential disasters | Reproducible from source |
| "I think it's encrypted" | Encrypted-at-rest enforced by policy |
| Inconsistent tagging | Required tags enforced by policy |
| Open security groups go unnoticed | Policy scan catches `0.0.0.0/0` |

## 3. The IaC security scanner stack

| Tool | Lang | Focus |
|---|---|---|
| **Checkov** (Bridgecrew/Prisma) | Python | Most comprehensive; Terraform + CFN + K8s + Helm + Dockerfile |
| **tfsec** (now part of Trivy) | Go | Terraform-only; merged into Trivy |
| **KICS** (Checkmarx) | Go | Multi-IaC |
| **Terrascan** (Tenable) | Go | Terraform + others |
| **Snyk IaC** | Commercial | Across-the-board |
| **cdk-nag** | TypeScript | AWS CDK specifically |
| **cfn-guard** (AWS) | Rust | CloudFormation |
| **Trivy config** | Go | Multi-IaC |
| **Cloud Custodian** | Python | Runtime AWS policy (Capital One's tool) |

**Recommendation 2026:** Checkov for breadth, plus Trivy config in CI (free + fast), plus Cloud Custodian or AWS Config for runtime drift.

## 4. Checkov in CI

```bash
pip install checkov

# Scan Terraform
checkov -d terraform/ --framework terraform --output cli --output json

# Scan with severity threshold
checkov -d . --check CKV_AWS_*  --hard-fail-on HIGH

# Skip specific checks (with justification)
checkov -d . --skip-check CKV_AWS_18,CKV_AWS_53
```

```yaml
# GitHub Actions
- uses: bridgecrewio/checkov-action@master
  with:
    directory: terraform/
    framework: terraform
    output_format: sarif
    output_file_path: checkov.sarif
- uses: github/codeql-action/upload-sarif@v3
  with: { sarif_file: checkov.sarif }
```

Common Checkov findings:
- `CKV_AWS_18`: S3 bucket without access logging
- `CKV_AWS_21`: S3 bucket versioning disabled
- `CKV_AWS_24`: SG with ingress from 0.0.0.0/0
- `CKV_AWS_53`: S3 bucket public-access-block missing

## 5. Terraform Remote State for DevSecOps

Local state = no audit. Remote state with versioning + locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "tf-state-prod"
    key            = "platform/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "tf-state-lock"
  }
}
```

Why this matters:
- **Encrypted at rest** with KMS
- **Versioning** on the S3 bucket → previous state recoverable
- **DynamoDB lock** prevents concurrent applies
- **CloudTrail logs every read/write** of the state file

## 6. CI/CD for IaC (the GitOps pattern)

```yaml
# .github/workflows/terraform.yml
on:
  pull_request: { paths: ['terraform/**'] }
  push:        { branches: [main], paths: ['terraform/**'] }

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions: { id-token: write, contents: read, pull-requests: write }
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_PLAN_ROLE }}, aws-region: us-east-1 }
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform fmt -check -recursive
      - run: terraform validate
      - uses: bridgecrewio/checkov-action@master
      - run: terraform plan -out=tfplan
      - name: Post plan to PR
        # ... comment with plan output

  apply:
    needs: plan
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production    # requires manual approval per env protection
    permissions: { id-token: write, contents: read }
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with: { role-to-assume: ${{ secrets.AWS_APPLY_ROLE }}, aws-region: us-east-1 }
      - run: terraform apply -auto-approve tfplan
```

The discipline:
- **Plan role** has read + plan permissions only
- **Apply role** has apply permissions; only assumable from `main` branch
- **PR plan visible** as comment for review
- **Apply gated** by GitHub Environment protection (requires approver)

## 7. GitOps for application deploys (preview Module 33)

```
Developer pushes code
  ↓
CI builds + tests + scans + signs image
  ↓
CI pushes image to ECR
  ↓
CI commits "image: app:1.2.3" change to GitOps repo
  ↓
ArgoCD watching GitOps repo notices change
  ↓
ArgoCD pulls + applies to cluster
  ↓
ArgoCD reports sync status
```

Key DevSecOps wins:
- **Pipeline has no cluster credentials** — cluster pulls, doesn't get pushed to
- **Every change is a Git commit** — full audit
- **Drift detection** — ArgoCD compares cluster state to Git, alerts on drift
- **Easy rollback** — revert Git commit, ArgoCD syncs

See Module 33 for the ArgoCD deep dive.

## 8. Policy-as-Code for IaC

**Open Policy Agent (Rego)** can enforce custom Terraform policies pre-apply:

```rego
# policy/terraform.rego
package terraform.s3

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  not resource.change.after.server_side_encryption_configuration
  msg := sprintf("S3 bucket '%s' must have encryption enabled", [resource.address])
}
```

```bash
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
opa eval --data policy/ --input plan.json "data.terraform.s3.deny"
```

Or use **Conftest** (wrapper for OPA on Terraform/K8s manifests):
```bash
conftest test --policy policy/ plan.json
```

## 9. Drift detection

Even with IaC, manual changes happen (incident response, vendor support, accidents). Drift detection catches them.

Options:
- **`terraform plan`** on a schedule against prod state; alert if non-zero plan
- **AWS Config** — resource configuration history; compliance rules
- **Driftctl** (OSS, archived 2023) — successors emerging
- **Snyk Cloud / Wiz CSPM** — commercial
- **Cloud Custodian** — Capital One's open-source tool; broader than drift but covers it

## 10. SBOM for infrastructure?

Yes — there's a movement toward **infra SBOM**:
- What modules + providers + versions are in use across your TF estate
- Drift between TF source and applied state
- Vulnerable modules in use

Tools: **Hashicorp Terraform Cloud's Module Registry insights**, **Stacklet** (commercial Custodian), early-stage offerings from Wiz / Snyk.

## 11. The 12-point IaC security checklist

1. Remote state with encryption + locking
2. IaC scanner (Checkov + Trivy config) in CI
3. Plan on PR; apply only on main + manual approval
4. OIDC + IAM roles; no long-lived keys
5. Provider + module versions pinned (`~> 5.80`)
6. Modules from trusted sources only (private registry preferred)
7. All resources tagged (Environment, Owner, CostCenter, ManagedBy=terraform)
8. Policy-as-Code gates (OPA/Conftest/Sentinel)
9. Scheduled drift detection
10. GitOps for K8s manifests (ArgoCD/Flux)
11. Signing + verification of artifacts at admission (Cosign + Kyverno)
12. Regular IaC code review like any other code

## 12. Quick self-check

1. What's the "cattle vs pets" metaphor and why does it matter for DevSecOps?
2. What does Checkov scan and when in the pipeline do you run it?
3. How does GitOps reduce the attack surface compared to CI-pushes-to-cluster?
4. What's drift detection and what tools enable it?
5. What's the difference between "policy as code" and "compliance as code"?

(Answers: pets are unique manual-tended servers, cattle are interchangeable IaC-defined — cattle are auditable, reproducible, drift-free; Terraform/CFN/K8s/Helm/Dockerfile for security misconfigs, in CI on PR; cluster pulls from Git, pipeline doesn't need cluster credentials, every change is a commit; comparing actual cloud state to IaC source; tools: Cloud Custodian, AWS Config, scheduled terraform plan, Snyk Cloud; PaC enforces design rules pre-apply, CaC enforces continuous compliance against frameworks like CIS/SOC 2 post-deploy.)



ewpage


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



ewpage


# 29 — Kubernetes Security Overview

> Cross-link: [Topic 05 Modules 21-25](../05_docker_kubernetes/21_rbac_serviceaccounts.md) cover K8s security in depth.

## 1. The K8s attack surface

A K8s cluster is a complex system. Attackers target:
- **API server** — anyone with cluster credentials
- **kubelet** — node-level component, can run anything
- **etcd** — has all secrets; full DB access = full cluster
- **Container runtime** — escape from container to host
- **Network** — east-west traffic between pods
- **Cloud control plane** — for managed clusters (EKS/GKE/AKS)
- **Container images** — vulnerable deps in your apps
- **CI/CD pipeline** — supplies the manifests + images
- **DNS** — service-name resolution can be hijacked

## 2. The K8s security layers (4C model)

Google's "4C":
1. **Cloud** — the underlying cloud account (IAM, network)
2. **Cluster** — control plane + nodes
3. **Container** — image + runtime
4. **Code** — your app

Compromise at lower layer cascades upward. Defense-in-depth across all four.

## 3. CIS Kubernetes Benchmark

The community-maintained checklist of K8s hardening. Versions per minor K8s release. **kube-bench** (Aqua Security, OSS) runs it locally:

```bash
docker run --rm --pid=host -v $(pwd):/host \
  aquasec/kube-bench:latest run --targets node,policies
```

Sample findings:
- Use --authorization-mode=Node,RBAC (not AlwaysAllow)
- Ensure kubelet only authorized
- Restrict use of privileged containers
- etcd peer + client TLS

For managed clusters: EKS/GKE/AKS handle the control plane CIS items; you handle node + workload items.

## 4. K8s Security Best Practices (the 20-point checklist)

**Control plane:**
1. K8s version current; auto-upgrade where possible
2. API server audit logs to CloudWatch/SIEM
3. etcd encrypted at rest (default in EKS; explicit on self-managed)
4. RBAC: least privilege; no system:masters bindings
5. ABAC + AlwaysAllow disabled

**Workload:**
6. Pod Security Standards `restricted` profile (PSA enforce on all namespaces)
7. NetworkPolicy default-deny per namespace (Cilium/Calico)
8. ResourceQuotas + LimitRanges per namespace
9. Non-root users in all containers
10. Read-only root filesystem where possible
11. No privileged containers (except specific DaemonSets like CNI)
12. Drop all Linux capabilities; add only needed
13. Pod-level SecurityContext: runAsNonRoot=true, allowPrivilegeEscalation=false

**Image:**
14. Trivy scan; fail Critical+High at build
15. Cosign signed images; verify at admission (Kyverno/OPA)
16. Distroless or minimal base images
17. No latest tags; pin to digest in production

**Secrets:**
18. External Secrets Operator → cloud secrets manager (Module 35)
19. Never base64 unencrypted Secrets committed to Git (use SOPS/Sealed Secrets if storing in Git)

**Network:**
20. mTLS via service mesh (Istio/Linkerd) or app-level TLS

## 5. Pod Security Standards (PSS / PSA)

K8s 1.25 (Aug 2022) removed PodSecurityPolicy and replaced with **Pod Security Admission** (PSA) which enforces **Pod Security Standards (PSS)**.

Three profiles:
- **Privileged** — anything goes (system DaemonSets)
- **Baseline** — minimally restrictive; blocks known dangerous (privileged, hostPID)
- **Restricted** — heavily restricted; required for non-system workloads in 2026

Enable per namespace:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-app
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Restricted profile requirements:**
- runAsNonRoot: true
- allowPrivilegeEscalation: false
- capabilities: drop ["ALL"], add only "NET_BIND_SERVICE" if needed
- seccompProfile: RuntimeDefault
- volumes: limited to safe types
- no host* (hostPath, hostNetwork, hostPID, hostIPC)

## 6. The kubelet attack — and defense

kubelet listens on every node (port 10250). Defenses:
- `--authorization-mode=Webhook` (not AlwaysAllow)
- `--anonymous-auth=false`
- TLS certificates for kubelet (auto-rotated via CSR)
- NetworkPolicy or SG: kubelet port only accessible from control plane

## 7. etcd — the crown jewel

All cluster state including all Secrets lives in etcd. Hardening:
- Encryption at rest (`EncryptionConfiguration` in apiserver)
- TLS for peer + client
- Filesystem permissions: 0600, owned by root
- Backup regularly (etcdctl snapshot save) — see Module 74

EKS/GKE/AKS manage etcd; you don't have direct access (which is good).

## 8. Audit logging

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "clusterroles", "rolebindings", "clusterrolebindings"]
```

EKS: enable via Cluster logging in Console / TF; ships to CloudWatch.
Self-managed: `--audit-policy-file=` + `--audit-log-path=` on apiserver.

What to alert on:
- `kubectl exec` into pods in prod namespace
- Secret reads from unusual ServiceAccount
- ClusterRoleBinding changes
- Privileged pod creation

## 9. Runtime threat detection

After-the-deploy security. Tools:
- **Falco** (Sysdig, CNCF Graduated) — eBPF-based runtime security
- **Tetragon** (Cilium ecosystem) — eBPF-based
- **Sysdig Secure** (commercial)
- **Aqua Security**
- **CrowdStrike Falcon Cloud Workload Protection**

Sample Falco rule:
```yaml
- rule: Shell in Container
  desc: Detect shell exec inside container
  condition: container.id != host and proc.name in (sh, bash, zsh)
  output: "Shell launched in container (user=%user.name container_id=%container.id image=%container.image.repository)"
  priority: WARNING
```

## 10. Provisioning EKS securely (preview Module 32)

The hardening checklist for EKS:
- Latest K8s minor (auto-update)
- API server endpoint private OR strict CIDR allowlist
- Logs to CloudWatch (api, audit, authenticator, controllerManager, scheduler)
- Envelope encryption with KMS for Secrets
- Node groups in private subnets only
- IMDSv2 enforced on nodes (hop-limit=1)
- IRSA / Pod Identity for pod IAM
- Container Insights enabled
- Restrict aws-auth ConfigMap OR use Access Entries

## 11. The K8s security tool matrix

| Layer | Tool |
|---|---|
| **CIS scan** | kube-bench |
| **Image scan** | Trivy |
| **Image signing** | Cosign |
| **Admission control** | Kyverno (preferred), OPA Gatekeeper |
| **Network policy** | Cilium |
| **mTLS** | Istio, Linkerd, Cilium SM |
| **Runtime** | Falco, Tetragon |
| **Secrets** | External Secrets Operator + cloud SM |
| **Audit** | Native API server audit |
| **CSPM** | Wiz, Snyk, Sysdig — multi-cluster posture |

## 12. Quick self-check

1. What's the 4C model and what's at each layer?
2. What replaced PodSecurityPolicy and what are the three profiles?
3. Why is etcd the "crown jewel" of K8s security?
4. What's Falco and what does it use under the hood?
5. Why is `allowPrivilegeEscalation: false` important?

(Answers: Cloud/Cluster/Container/Code — defense in depth across; Pod Security Admission with PSS profiles privileged/baseline/restricted; contains all cluster state including Secrets — full DB access = full cluster compromise; runtime threat detector using eBPF kernel hooks to detect anomalous syscalls; prevents setuid binaries from escalating to root inside the container.)



ewpage


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



ewpage


# 31 — Secure IaC Pipeline — GitLab OIDC to AWS

## Why this module exists

Securing the IaC pipeline means securing the credentials it uses. OIDC is the modern way to give CI short-lived AWS credentials without storing long-lived secrets anywhere. This module covers the GitLab-specific OIDC integration with AWS.

## 1. The OIDC pattern (in one paragraph)

GitLab Runners issue a signed OIDC token per job. AWS IAM trusts GitLab's OIDC provider URL + verifies a signed JWT. The trust policy on a role limits assumption to specific (project, branch, environment) tuples. The runner exchanges its token for short-lived AWS credentials via `sts:AssumeRoleWithWebIdentity`.

Result: no AWS access keys in GitLab CI variables. No long-lived secrets to rotate or leak.

## 2. Register GitLab as OIDC provider in AWS

For GitLab SaaS (gitlab.com):
```bash
aws iam create-open-id-connect-provider \
  --url https://gitlab.com \
  --client-id-list https://gitlab.com \
  --thumbprint-list <gitlab-cert-thumbprint>
```

Or in Terraform:
```hcl
data "tls_certificate" "gitlab" {
  url = "https://gitlab.com"
}

resource "aws_iam_openid_connect_provider" "gitlab" {
  url             = "https://gitlab.com"
  client_id_list  = ["https://gitlab.com"]
  thumbprint_list = [data.tls_certificate.gitlab.certificates[0].sha1_fingerprint]
}
```

For self-hosted GitLab, use your own URL.

## 3. Create an IAM Role with GitLab trust policy

```hcl
resource "aws_iam_role" "gitlab_ci" {
  name = "gitlab-ci-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.gitlab.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "gitlab.com:aud" = "https://gitlab.com"
        }
        StringLike = {
          # Allow only main branch of myorg/myproject
          "gitlab.com:sub" = "project_path:myorg/myproject:ref_type:branch:ref:main"
        }
      }
    }]
  })
}
```

The `sub` claim is the powerful constraint. Examples:
- `project_path:myorg/myrepo:ref_type:branch:ref:main` — only main branch
- `project_path:myorg/myrepo:ref_type:tag:ref:v*` — only version tags
- `project_path:myorg/myrepo:ref_type:branch:ref:*` — any branch (less safe)
- `project_path:myorg/myrepo:environment:production` — only when GitLab env=production

## 4. GitLab CI consumes the OIDC token

```yaml
# .gitlab-ci.yml
deploy:
  stage: deploy
  image: amazon/aws-cli:latest
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.com
  script:
    - >
      export $(printf "AWS_ACCESS_KEY_ID=%s AWS_SECRET_ACCESS_KEY=%s AWS_SESSION_TOKEN=%s"
      $(aws sts assume-role-with-web-identity
      --role-arn arn:aws:iam::1234:role/gitlab-ci-deploy
      --role-session-name "gitlab-${CI_PIPELINE_ID}"
      --web-identity-token "$GITLAB_OIDC_TOKEN"
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text))
    - aws s3 ls
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

The `id_tokens` block tells GitLab to issue an OIDC JWT with the given audience; it's injected as the `GITLAB_OIDC_TOKEN` env var for that job.

## 5. The Terraform IaC pipeline using GitLab OIDC

```yaml
# .gitlab-ci.yml
stages: [validate, plan, apply]

variables:
  AWS_DEFAULT_REGION: us-east-1
  TF_ROOT: terraform/
  TF_STATE_NAME: prod

.assume_role: &assume_role
  before_script:
    - >
      export $(aws sts assume-role-with-web-identity
      --role-arn $AWS_ROLE_ARN
      --role-session-name "tf-${CI_PIPELINE_ID}"
      --web-identity-token "$GITLAB_OIDC_TOKEN"
      --duration-seconds 3600
      --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]'
      --output text | awk '{print "AWS_ACCESS_KEY_ID="$1, "AWS_SECRET_ACCESS_KEY="$2, "AWS_SESSION_TOKEN="$3}')

validate:
  stage: validate
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-plan }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform fmt -check -recursive
    - terraform validate

plan:
  stage: plan
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-plan }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform plan -out=tfplan
  artifacts:
    paths: [$TF_ROOT/tfplan]

apply:
  stage: apply
  image: hashicorp/terraform:1.10
  id_tokens: { GITLAB_OIDC_TOKEN: { aud: https://gitlab.com } }
  variables: { AWS_ROLE_ARN: arn:aws:iam::1234:role/tf-apply }
  <<: *assume_role
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform apply -auto-approve tfplan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

Two roles:
- **tf-plan** — read-only + plan (assumable from any branch)
- **tf-apply** — full apply (trust policy constrains to `ref:main` only)

The two-role split is the **principle of least privilege** at pipeline level.

## 6. Compare to GitHub Actions OIDC

GitHub Actions has equivalent OIDC support. See [Topic 07 Module 29](../07_git_github_devops/29_actions_oidc_aws.md) and [Topic 07 Module 46](../07_git_github_devops/46_aws_oidc_trust_policy_deep.md).

Differences:
- GitHub uses `token.actions.githubusercontent.com` as OIDC provider URL
- `aud` defaults to `sts.amazonaws.com` (or `aws-actions/configure-aws-credentials`)
- `sub` claim format: `repo:owner/repo:ref:refs/heads/main`
- `aws-actions/configure-aws-credentials@v4` action does the assume-role automatically

## 7. Cross-account deploys

Common pattern: GitLab → CI account → cross-account assume → target account.

```hcl
# Target account role (in prod account)
resource "aws_iam_role" "prod_deployer" {
  name = "prod-deployer"
  assume_role_policy = jsonencode({
    Statement = [{
      Effect = "Allow"
      Principal = { AWS = "arn:aws:iam::CI_ACCOUNT_ID:role/gitlab-ci-bridge" }
      Action = "sts:AssumeRole"
      Condition = {
        StringEquals = { "sts:ExternalId" = "shared-external-id-for-mfa" }
      }
    }]
  })
}
```

Pipeline first assumes the CI-account role via OIDC, then chains to target account via cross-account AssumeRole.

## 8. The 12-point secure-pipeline checklist

1. **OIDC + IAM Role** — never long-lived AWS keys in CI vars
2. **Trust policy constrains to specific (project, branch, env)** — `sub` claim wildcards = bad
3. **Two-role split** — plan role read-only, apply role write
4. **Apply only on main + manual approval**
5. **Pipeline runner identity in **CloudTrail** — every API call attributable
6. **Pipeline can't read its own state file** — separate role for state-bucket admin
7. **No `sudo` / no `--privileged` in CI containers**
8. **GitLab Runner on private subnet** — outbound only, no inbound 22
9. **Secrets in GitLab CI Variables only when OIDC isn't possible** — masked + protected
10. **Project Runners over Group Runners** for sensitive projects (avoid noisy-neighbor risk)
11. **`CI_JOB_TOKEN`** for GitLab API access (not personal access tokens)
12. **Scan IaC code with Checkov + tfsec** before plan

## 9. Quick self-check

1. What does the `sub` claim in the GitLab OIDC token contain?
2. Why is splitting "plan role" and "apply role" a security best practice?
3. What's the security benefit of OIDC over AWS access keys in GitLab CI?
4. How does cross-account deploy work with OIDC?
5. Why is `id_tokens` block needed in `.gitlab-ci.yml`?

(Answers: project path + ref type + ref name (e.g., `project_path:myorg/myrepo:ref_type:branch:ref:main`) + optionally environment; least privilege — plan never needs write, so a plan-job compromise can't apply destructive changes; no long-lived secrets to leak/rotate, audited per-job in CloudTrail, scoped to specific (project, branch); first assume CI-account role via OIDC, then chain AssumeRole to target account; tells GitLab to issue an OIDC JWT for that job with the specified audience — required for AWS to verify.)



ewpage


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



ewpage


# 33 — ArgoCD for Application Delivery

## Why this module exists

ArgoCD is the dominant GitOps engine for K8s in 2026. CNCF Graduated 2022; v3.0 GA in 2025-04. Its competitor **Flux v2** is equally capable; both have ~30-40% adoption in K8s shops.

## 1. The GitOps premise

```
Traditional CD:
  CI → kubectl apply → cluster

GitOps:
  CI → commit manifest change → Git
       ↓
  ArgoCD pulls Git → applies to cluster → reconciles
```

Why GitOps wins:
- **Pipeline has no cluster credentials** (cluster pulls from Git)
- **Git history = deploy history** (auditable, revertable)
- **Drift detection** (ArgoCD knows when cluster diverges from Git)
- **Pull model scales** (one Argo per cluster manages many apps; no fan-out from CI)
- **Multi-cluster** is just adding more ArgoCD instances or one ArgoCD with many cluster registrations

## 2. ArgoCD concepts

- **Application** — a CRD pointing at a Git repo+path; represents one deployable
- **AppProject** — a grouping with permissions/restrictions on Applications
- **ApplicationSet** — templating for many Applications from one CRD
- **Sync** — the operation that applies Git state to cluster
- **Auto-sync** — automatic sync on Git change (default off for prod)
- **Self-heal** — re-apply if cluster drifts from Git
- **Sync waves** — order applications/resources

## 3. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f \
  https://raw.githubusercontent.com/argoproj/argo-cd/v3.0.0/manifests/install.yaml

# Or via Helm
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace
```

Access:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

UI at https://localhost:8080 (admin / <password>).

## 4. Define an Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/my-app-manifests
    targetRevision: main
    path: overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: my-app
  syncPolicy:
    automated:
      prune: true        # delete resources removed from Git
      selfHeal: true     # re-apply on cluster drift
    syncOptions:
      - CreateNamespace=true
      - ApplyOutOfSyncOnly=true
```

ArgoCD watches the Git path; when it changes, syncs to the destination cluster + namespace.

## 5. Kustomize + Helm support

ArgoCD natively renders:
- **Plain YAML** — apply as-is
- **Kustomize** — `kustomization.yaml` in the path
- **Helm chart** — `Chart.yaml` in the path
- **Helm chart from repo** — separate field for chart name + values
- **Plugins** (jsonnet, custom) — via configMap config

Kustomize sample:
```
manifests/
├── base/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── overlays/
    ├── dev/
    │   └── kustomization.yaml   # patches replicas=1, image tag
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

## 6. App-of-Apps pattern

```yaml
# root-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/cluster-config
    path: applications/
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```

`applications/` contains more Application manifests. Bootstrap the cluster by `kubectl apply -f root-app.yaml`, and ArgoCD creates everything else.

## 7. ApplicationSet (for multi-cluster, multi-tenant)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: team-apps
  namespace: argocd
spec:
  generators:
  - matrix:
      generators:
      - list:
          elements:
          - { team: team-a }
          - { team: team-b }
          - { team: team-c }
      - clusters: {}    # all registered clusters
  template:
    metadata:
      name: '{{.team}}-{{.cluster.name}}'
    spec:
      project: '{{.team}}'
      source:
        repoURL: https://github.com/myorg/{{.team}}
        targetRevision: main
        path: deploy
      destination:
        server: '{{.cluster.server}}'
        namespace: '{{.team}}'
```

One CRD → many Applications, one per (team × cluster).

## 8. The CI → GitOps repo update pattern

```yaml
# CI pipeline pseudo-code:
build_image()
push_image_to_ecr()

# Update GitOps repo
git clone https://github.com/myorg/cluster-config
cd cluster-config
sed -i "s|image: app:.*|image: $ECR/app:$NEW_TAG|" overlays/prod/deployment.yaml
git commit -am "deploy app $NEW_TAG"
git push

# ArgoCD detects change and syncs
```

Better: use a dedicated tool like **Argo CD Image Updater** or **renovate** that updates manifests automatically when ECR has new tags.

## 9. Progressive delivery — Argo Rollouts

For canary/blue-green deployments beyond simple rolling update:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: { duration: 10m }
      - setWeight: 50
      - pause: { duration: 10m }
      - setWeight: 100
      analysis:
        templates:
        - templateName: success-rate
        startingStep: 2
  selector: { matchLabels: { app: web } }
  template:
    # ... pod spec
```

The analysis template can query Prometheus, Datadog, etc., to auto-rollback on error spike.

## 10. ArgoCD vs Flux

| | ArgoCD | Flux |
|---|---|---|
| **UI** | First-class | Weave Gitops + 3rd party |
| **CLI** | `argocd` | `flux` (lighter) |
| **Multi-tenancy** | Project + RBAC | Tenant CRD |
| **Multi-source app** | Yes (v2.6+) | Native |
| **Helm** | Renders, then applies | Native Helm |
| **Image updater** | Separate project | Native Image Reflector + Image Automation controllers |
| **Notifications** | Notifications Engine | Notification controller |
| **Bootstrapping** | App-of-Apps | `flux bootstrap` |

Picking: ArgoCD has better UX + UI; Flux is more composable + lighter. Capital One uses Flux internally (per Tech blog hints).

## 11. ArgoCD anti-patterns

1. **Manual `kubectl apply` after ArgoCD installed** — drift; ArgoCD will revert
2. **Storing secrets in Git** — use ESO/Vault/Sealed Secrets
3. **Auto-sync in prod** — surprise deploys; gate prod with manual sync
4. **No notifications** — sync failures go unnoticed
5. **Cluster-admin role for ArgoCD** — scope by AppProject; least privilege

## 12. Quick self-check

1. What's the security advantage of GitOps's pull model over CI-push?
2. What's the App-of-Apps pattern?
3. What does ArgoCD self-heal do?
4. What's the difference between ArgoCD and Argo Rollouts?
5. Why might you choose Flux over ArgoCD?

(Answers: pipeline doesn't need cluster credentials, cluster pulls from Git — fewer credentials to leak; one bootstrap Application that creates many others — fully Git-described cluster; if cluster state drifts from Git (manual edit), ArgoCD re-applies Git; ArgoCD does the sync, Rollouts is the progressive delivery engine for canary/blue-green; lighter, more composable, CLI-first, native Helm.)



ewpage


# 34 — OPA Gatekeeper — Policy as Code

## Why this module exists

K8s admission control is your last gate. Pods get created via the API server; admission controllers validate (and mutate) every request. **OPA Gatekeeper** and **Kyverno** are the two policy engines. In 2026, **Kyverno is winning** for simpler use cases (YAML rules) but OPA/Rego still dominates for complex multi-cloud policy.

## 1. Why policy as code

Without policy enforcement: every team can deploy whatever they want — privileged containers, hostPath volumes, latest tags, no resource limits. Eventually one of them tanks the cluster.

With policy as code:
- Rules live in Git, reviewed like any other code
- Enforced at admission (request blocked before it reaches etcd)
- Auditable + dry-runnable (audit mode reports violations without blocking)
- Compliance-by-design

## 2. Admission controllers — how they work

```
kubectl apply → API server → authentication → authorization → mutating webhook(s)
                                                                  ↓
                                                       validating webhook(s) → etcd
```

Mutating webhooks can change the request (inject sidecars, add labels). Validating webhooks accept or reject.

OPA Gatekeeper + Kyverno register themselves as validating (and optionally mutating) webhooks.

## 3. Install OPA Gatekeeper

```bash
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace
```

Verify:
```bash
kubectl get pods -n gatekeeper-system
kubectl get crds | grep gatekeeper
```

## 4. Concepts

- **ConstraintTemplate** — Rego policy code + parameter schema
- **Constraint** — instance of a ConstraintTemplate with specific parameters and target kinds
- **Audit** — periodic re-evaluation against existing resources (not just admission)
- **Mutation** (since Gatekeeper 3.6) — modify requests; less mature than Kyverno mutations

## 5. ConstraintTemplate example

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names: { kind: K8sRequiredLabels }
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items: { type: string }
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        violation[{"msg": msg}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_]}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Missing required labels: %v", [missing])
        }
```

## 6. Apply a Constraint

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: ns-must-have-owner
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Namespace"]
  enforcementAction: deny    # or "warn" or "dryrun"
  parameters:
    labels: ["owner", "cost-center"]
```

Now any Namespace creation/modification without `owner` AND `cost-center` labels gets denied.

## 7. The classic policies

### Reject NodePort Services
```rego
package k8snodeport
violation[{"msg": msg}] {
  input.review.object.kind == "Service"
  input.review.object.spec.type == "NodePort"
  msg := "NodePort Services are not allowed; use ClusterIP + Ingress"
}
```

### Reject privileged containers
```rego
package k8sprivileged
violation[{"msg": msg}] {
  some i
  container := input.review.object.spec.containers[i]
  container.securityContext.privileged == true
  msg := sprintf("Container %v is privileged", [container.name])
}
```

### Restrict image registries
```rego
package k8stregistry
violation[{"msg": msg}] {
  some i
  container := input.review.object.spec.containers[i]
  not startswith(container.image, "1234.dkr.ecr.us-east-1.amazonaws.com/")
  msg := sprintf("Image %v must be from approved registry", [container.image])
}
```

## 8. Kyverno alternative (simpler for most use cases)

Kyverno policies are YAML, not Rego — significantly simpler for the common 80% of policies.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-labels
      match:
        any:
          - resources: { kinds: [Namespace] }
      validate:
        message: "Namespace must have 'owner' and 'cost-center' labels"
        pattern:
          metadata:
            labels:
              owner: "?*"
              cost-center: "?*"
```

```yaml
# Reject privileged
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata: { name: no-privileged }
spec:
  validationFailureAction: Enforce
  rules:
    - name: privileged
      match: { any: [{ resources: { kinds: [Pod] } }] }
      validate:
        message: "Privileged containers are not allowed"
        pattern:
          spec:
            containers:
              - =(securityContext):
                  =(privileged): "false"
```

Kyverno also does mutations (auto-inject sidecars, defaults) cleanly.

## 9. OPA Gatekeeper vs Kyverno (2026)

| | Gatekeeper | Kyverno |
|---|---|---|
| **Lang** | Rego | YAML |
| **Learning curve** | Steep | Mild |
| **Cross-platform** | Yes (Rego + OPA also used for Terraform, Envoy, etc.) | K8s-specific |
| **Mutation** | Mature-ish | Native, full-featured |
| **Generation** | Limited | Native (auto-create resources) |
| **Image signature verify** | Via plugins | Native (verifyImages) |
| **Performance** | OPA engine | Similar |
| **CNCF** | Graduated | Graduated 2024 |
| **Best for** | Multi-tool policy unification | K8s-focused shops |

Picking 2026: Kyverno for simpler policies; OPA when you need cross-tool policy (TF + K8s + Envoy in same Rego library).

## 10. Audit mode + dry-run

Before enforcing in prod, run in **audit** mode (Gatekeeper) / **Audit** action (Kyverno). Violations log without blocking. Then promote to Enforce when zero violations.

```yaml
enforcementAction: dryrun    # Gatekeeper
# or
enforcementAction: warn      # Gatekeeper
# or in Kyverno:
validationFailureAction: Audit
```

## 11. Common policy library

The **OPA Policy Library** (https://github.com/open-policy-agent/library) and **Kyverno Policy Library** (https://kyverno.io/policies/) have 100+ ready-to-use policies:
- Require resources/limits
- Require liveness/readiness probes
- Restrict node selectors
- Force runAsNonRoot
- Block deprecated APIs
- Image registry allowlist
- Pod Security Standards-equivalent

Start with the library; customize as needed.

## 12. Quick self-check

1. What's a Mutating vs Validating webhook?
2. What's a ConstraintTemplate vs Constraint in Gatekeeper?
3. Why is Kyverno winning over Gatekeeper for K8s-only shops in 2026?
4. What's the difference between audit mode and enforce mode?
5. What's the relationship between OPA and Gatekeeper?

(Answers: mutating modifies the request (inject sidecars), validating accepts/rejects; ConstraintTemplate is Rego policy + param schema (reusable), Constraint is an instance with specific params and target kinds; YAML simpler than Rego, native mutation + generation, image signature verify built-in; audit logs violations without blocking — used to roll out new policies safely; OPA is the policy engine, Gatekeeper is K8s admission controller using OPA + adds K8s-specific UX.)



ewpage


# 35 — Secrets Management — Vault + ESO + AWS Secrets Manager

## Why this module exists

K8s Secrets are base64, **not encrypted** at rest by default. Committing them to Git is malpractice. The 2026 stack: cloud-managed secret store (AWS Secrets Manager / Azure Key Vault / GCP Secret Manager / HashiCorp Vault) + **External Secrets Operator (ESO)** to sync them into K8s.

## 1. The K8s Secret problem

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:
  password: c3VwZXItc2VjcmV0  # base64 of "super-secret"
```

Problems:
- `c3VwZXItc2VjcmV0` is **not encrypted**, just encoded — anyone with API access reads it
- Stored unencrypted in etcd by default (EKS encrypts via KMS if configured)
- **You cannot commit this to Git** without exposing the secret
- **You cannot rotate easily** — every consumer needs re-deploy

## 2. The secrets-stack pattern

```
Cloud secret store (Secrets Manager / Vault / Key Vault)
   ↑               ↓
   │ (audit)       │ (ESO sync)
   │               ↓
   │           K8s Secret
   │               ↓
   │           Pod mounts Secret as env or volume
   │               ↓
   └─── App reads value
```

Single source of truth = the cloud store. ESO syncs to K8s; pods consume normally.

## 3. HashiCorp Vault — the cross-cloud option

Vault (HashiCorp, BUSL since 2023; OSS fork **OpenBao** from Linux Foundation) is the long-standing multi-cloud secret store.

Capabilities:
- **KV** secrets engine (static)
- **Database** secrets engine (dynamic DB creds with TTL)
- **AWS / Azure / GCP** secrets engines (dynamic cloud creds)
- **PKI** engine (issue certs on demand)
- **Transit** engine (encryption-as-a-service; never store the key)
- **SSH** engine (SSH cert authority)
- **Identity** engine (entities + groups + aliases)

Auth methods: Kubernetes (use SA tokens), AWS IAM, JWT/OIDC, AppRole, LDAP, Okta, etc.

```bash
# CLI basics
vault server -dev   # dev mode
export VAULT_ADDR=http://127.0.0.1:8200
vault kv put secret/myapp password=super-secret
vault kv get secret/myapp
```

## 4. AWS Secrets Manager — the AWS-native default

```bash
aws secretsmanager create-secret \
  --name myapp/prod/db \
  --secret-string '{"username":"app","password":"super-secret"}'

aws secretsmanager get-secret-value --secret-id myapp/prod/db
```

Features:
- **Automatic rotation** (Lambda-based; RDS rotation built-in)
- **Cross-region replication**
- **KMS-encrypted** at rest
- **Versioning + staging labels** (AWSCURRENT, AWSPREVIOUS, AWSPENDING)
- IAM-controlled access; CloudTrail audit
- Cost: $0.40/secret/mo + $0.05/10k API calls

Alternative: **SSM Parameter Store** — free standard tier (4KB), no rotation; use for config, light secrets.

## 5. External Secrets Operator (ESO)

ESO bridges cloud secret stores → K8s Secrets. CRDs:
- **SecretStore** — connection to a secret backend (per namespace)
- **ClusterSecretStore** — cluster-wide version
- **ExternalSecret** — what to pull and where to put it

```yaml
# SecretStore — connection to AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-sm
  namespace: my-app
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:    # IRSA-based
          serviceAccountRef:
            name: my-app-sa
---
# ExternalSecret — pull a secret into the cluster
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-creds
  namespace: my-app
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-sm
    kind: SecretStore
  target:
    name: db-creds                    # creates K8s Secret with this name
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: myapp/prod/db
        property: username
    - secretKey: password
      remoteRef:
        key: myapp/prod/db
        property: password
```

Result: K8s Secret `db-creds` is auto-created and refreshed every hour from AWS Secrets Manager. Rotate in Secrets Manager → ESO syncs → pods see new value (assuming `restartPodsOnSecretChange` or pod reads at runtime).

## 6. ESO providers

ESO supports 30+ backends:
- AWS Secrets Manager, AWS SSM Parameter Store
- Azure Key Vault, Azure App Configuration
- GCP Secret Manager
- HashiCorp Vault, OpenBao
- 1Password, Doppler, Infisical
- Akeyless, Conjur
- Generic webhook + Kubernetes (cross-cluster)

## 7. Vault with K8s auth

```bash
# Enable K8s auth in Vault
vault auth enable kubernetes
vault write auth/kubernetes/config \
  kubernetes_host="https://kubernetes.default.svc"

# Create policy
vault policy write myapp - <<EOF
path "secret/data/myapp/*" { capabilities = ["read"] }
EOF

# Bind policy to K8s SA
vault write auth/kubernetes/role/myapp \
  bound_service_account_names=myapp-sa \
  bound_service_account_namespaces=my-app \
  policies=myapp \
  ttl=1h
```

Then ESO `SecretStore` references this:
```yaml
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "myapp"
          serviceAccountRef: { name: "myapp-sa" }
```

## 8. Secrets that should never be in K8s Secret

Some patterns that ESO doesn't quite fix:
- **DB credentials with rotation** — better: use IAM auth (RDS IAM auth, Aurora IAM)
- **AWS credentials** — IRSA / Pod Identity (Module 30); no Secret at all
- **TLS certs** — cert-manager; no manual handling
- **Encryption keys for app-layer encryption** — Vault transit engine (encrypt-as-a-service)

The hierarchy: **eliminate the secret > rotate the secret > store the secret well**.

## 9. Sealed Secrets + SOPS (when you want secrets in Git)

When you can't run ESO, but still want Git-stored secrets:

### Sealed Secrets (Bitnami)
- Controller in cluster has a private key
- Encrypt secrets with public key → can commit ciphertext to Git
- Controller decrypts and creates plain K8s Secret

```bash
kubectl create secret generic db-creds --from-literal=password=secret \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > sealed-db-creds.yaml
# Commit sealed-db-creds.yaml
kubectl apply -f sealed-db-creds.yaml
```

### SOPS (Mozilla, now CNCF)
- Encrypt fields in YAML/JSON files with KMS / Vault / age / pgp
- Edit with `sops file.yaml` → opens decrypted in editor → re-encrypts on save
- Works with helm-secrets, sops-secrets-operator, GitOps tools

Both are stepping stones to "secrets in cloud secret store + ESO."

## 10. Rotation strategy

The hardest part of secrets management. Strategies:
- **Dynamic credentials** (Vault DB engine, AWS Secrets Manager rotation) — credentials issued per-use, expire automatically
- **Scheduled rotation** — Lambda updates secret in Secrets Manager every N days; app reads at runtime
- **Manual rotation** — least bad; rotate on incident
- **App-level: rotate on read** — fetch fresh from Secrets Manager every N min; never cache long

## 11. Quick self-check

1. Why are K8s Secrets not actually secret?
2. What does ESO do?
3. What's the difference between AWS Secrets Manager and SSM Parameter Store?
4. What's Sealed Secrets and when use it?
5. Why is IRSA / Pod Identity better than storing AWS credentials in a K8s Secret?

(Answers: base64-encoded only — not encrypted — anyone with API access reads them; syncs cloud secret stores → K8s Secrets with refresh interval; Secrets Manager has rotation + cross-region + larger size, Parameter Store is free standard tier + 4KB max + no rotation; encrypts secrets so you can commit ciphertext to Git, controller in cluster decrypts at apply; no secret at all — pod gets temporary credentials via IAM, no rotation needed, no leak surface.)



ewpage


# 36 — Service Mesh — Istio (mTLS + AuthZ)

## Why this module exists

A service mesh is an infrastructure layer that handles service-to-service communication: mTLS, traffic routing, retries, observability, authorization. Istio is the dominant mesh (CNCF Graduated April 2025). Alternatives: Linkerd (lighter), Cilium Service Mesh (eBPF-based, sidecar-less).

## 1. What problem a mesh solves

Without a mesh, every service has to handle (in code, per language):
- TLS between services
- Retries + timeouts + circuit breaking
- Load balancing
- Authentication (mTLS)
- Authorization (who can call what)
- Tracing instrumentation
- Metrics

A mesh handles all of this in a sidecar (or via eBPF), so apps don't have to.

## 2. Istio architecture

Two flavors:

### Sidecar mode (classic)
Each pod gets an **Envoy sidecar** auto-injected. All traffic in/out passes through Envoy. Control plane (Istiod) configures the sidecars.

### Ambient mode (GA Q4 2024 with 1.24)
**No sidecar.** Per-node ztunnel (L4 + mTLS) + optional per-namespace waypoint proxy (L7). Cheaper, lower latency, but newer.

```
┌─────────────────────────────────────────────────────────┐
│                       Istiod                            │  control plane
│       (PILOT - config, CITADEL - certs, GALLEY - val)   │
└─────────────────────────────────────────────────────────┘
                          │
            xDS APIs      │ configures
                          ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Pod A      │    │   Pod B      │    │   Pod C      │
│  ┌────────┐  │    │  ┌────────┐  │    │  ┌────────┐  │
│  │  app   │  │    │  │  app   │  │    │  │  app   │  │
│  └────────┘  │    │  └────────┘  │    │  └────────┘  │
│  ┌────────┐  │ →  │  ┌────────┐  │ →  │  ┌────────┐  │
│  │ envoy  │──┼────┼─▶│ envoy  │──┼────┼─▶│ envoy  │  │
│  └────────┘  │mTLS│  └────────┘  │mTLS│  └────────┘  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 3. Install (sidecar mode)

```bash
istioctl install --set profile=default -y
kubectl label namespace my-app istio-injection=enabled
# Restart pods → sidecars injected
```

For ambient:
```bash
istioctl install --set profile=ambient -y
kubectl label namespace my-app istio.io/dataplane-mode=ambient
```

## 4. mTLS — the killer feature

Istio gives you **automatic mTLS** between all meshed services. Certs issued by Istiod's built-in CA (or external like cert-manager + SPIRE). Rotation handled automatically.

### Modes
- **STRICT** — only mTLS allowed; non-mTLS rejected
- **PERMISSIVE** — accept both mTLS + plain (transitional default)
- **DISABLE** — no mTLS

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: my-app
spec:
  mtls:
    mode: STRICT
```

This single object enforces mTLS for every pod in `my-app`. Pods that aren't in mesh can't talk to it; mesh pods authenticate each other automatically.

## 5. Traffic Routing

### VirtualService — routing rules
```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
  namespace: my-app
spec:
  hosts: [reviews]
  http:
  - match:
    - headers:
        x-canary: { exact: "true" }
    route:
    - destination: { host: reviews, subset: v2 }
  - route:
    - destination: { host: reviews, subset: v1, weight: 80 }
    - destination: { host: reviews, subset: v2, weight: 20 }
```

### DestinationRule — subsets + load balancing
```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata: { name: reviews, namespace: my-app }
spec:
  host: reviews
  subsets:
  - name: v1
    labels: { version: v1 }
  - name: v2
    labels: { version: v2 }
  trafficPolicy:
    connectionPool:
      tcp: { maxConnections: 100 }
      http: { http1MaxPendingRequests: 1000 }
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
```

This combination = 20% canary + sticky failover routing per service.

## 6. Gateway — ingress for the mesh

```yaml
apiVersion: networking.istio.io/v1
kind: Gateway
metadata: { name: web-gateway }
spec:
  selector: { istio: ingressgateway }
  servers:
  - port: { number: 443, name: https, protocol: HTTPS }
    tls:
      mode: SIMPLE
      credentialName: web-tls-cert
    hosts: ["app.example.com"]
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata: { name: web }
spec:
  hosts: ["app.example.com"]
  gateways: [web-gateway]
  http:
  - route:
    - destination: { host: web, port: { number: 80 } }
```

Istio Gateway is now being superseded by **K8s Gateway API** (vendor-neutral). Istio supports both.

## 7. Authorization Policies

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata: { name: allow-frontend-to-api, namespace: my-app }
spec:
  selector:
    matchLabels: { app: api }
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/my-app/sa/frontend-sa"]
    to:
    - operation:
        methods: [GET, POST]
        paths: ["/api/*"]
    when:
    - key: request.headers[x-tenant]
      values: ["tenant-a", "tenant-b"]
```

`principals` uses **SPIFFE IDs** derived from the K8s ServiceAccount. Authorization at L7 + workload-identity-based — far more granular than NetworkPolicy.

## 8. Istio AuthZ vs K8s NetworkPolicy

| | NetworkPolicy | Istio AuthorizationPolicy |
|---|---|---|
| **Layer** | L3/L4 (IP, port) | L7 (HTTP method, path, headers) |
| **Identity** | Labels / namespaces (IP-based) | SPIFFE / ServiceAccount (cryptographic) |
| **Encryption** | No | mTLS via PeerAuthentication |
| **Granularity** | Pod-to-pod port allow/deny | HTTP-method-and-path level |
| **Deny-all default** | Yes | No (you opt in) |
| **Cost** | Cheap (CNI feature) | Sidecar/ambient overhead |

Use both: NetworkPolicy as broad allow/deny; Istio AuthZ for HTTP-level rules + identity-based.

## 9. Observability for free

Istio out-of-the-box:
- **Metrics** — RED metrics per service via Envoy → Prometheus
- **Tracing** — request spans → Jaeger / Zipkin / Tempo
- **Access logs** — per request → log aggregator
- **Service mesh dashboard** — Kiali (separate, works with Istio)

Install Kiali:
```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.24/samples/addons/kiali.yaml
```

## 10. Linkerd alternative

Linkerd 2.16 (mid-2024) is the simpler alternative:
- Rust-written proxy (vs Envoy in C++)
- Smaller resource footprint
- Simpler config + CLI
- **Buoyant (creator) moved to paid model for stable releases** in 2024 — controversial; some teams forked back

Choose Linkerd if Istio's complexity isn't justified. Linkerd does mTLS + traffic shifting + observability with much less surface area.

## 11. Cilium Service Mesh

Cilium 1.16+ provides service mesh via **eBPF** (kernel-level) instead of sidecars or per-node proxies. Same L4 mTLS + L7 routing. Pros: lowest overhead. Cons: less mature, fewer features than Istio.

If you already run Cilium as CNI (which is the default for new clusters in 2026), Cilium SM is a serious option.

## 12. Service mesh complexity trade-off

The honest question: **do you need a mesh**?

Skip a mesh if:
- < 20 services
- No mTLS requirement
- Simple L3/L4 NetworkPolicy is enough
- No need for L7 routing / canary at mesh layer

Get a mesh if:
- Strict mTLS compliance requirement (PCI-DSS, HIPAA, regulated)
- Many services with complex routing
- Need workload-identity-based AuthZ (zero trust)
- Multi-cluster federation

Capital One: Istio (ambient mode adoption in progress 2026) — required for SR 11-7 + PCI compliance posture.

## 13. Quick self-check

1. What does Istio's PeerAuthentication object do?
2. What's the difference between Istio sidecar mode and ambient mode?
3. What's a SPIFFE ID and why does Istio use them for AuthZ?
4. What's the difference between NetworkPolicy and Istio AuthorizationPolicy?
5. When should you skip a service mesh?

(Answers: configures mTLS mode (STRICT/PERMISSIVE/DISABLE) for pods in scope; sidecar = Envoy per pod, ambient = ztunnel per node + waypoint per namespace — less overhead but newer; cryptographically-secure workload identity derived from ServiceAccount — far stronger than IP/label-based identity; NetworkPolicy is L3/L4 + IP-based + cheap, Istio AuthZ is L7 + identity-based + mTLS — use both layered; small service count + no mTLS need + no L7 routing complexity.)



ewpage


# 37 — Compliance as Code — AWS Config + CIS Benchmarks

## Why this module exists

Compliance frameworks (SOC 2, PCI-DSS, HIPAA, SR 11-7) require **continuous evidence** that controls are in place. Manual screenshots once a year don't scale; you'd spend half your engineering time on audit. **Compliance as code** automates evidence collection and remediation.

## 1. The compliance landscape (regulated finance)

| Framework | Scope | Capital One? |
|---|---|---|
| **SOC 2 Type II** | SaaS controls + 12-month period | Yes |
| **PCI-DSS v4** | Card data | Yes (issuer) |
| **HIPAA** | US health PHI | No (different industry; Optum yes) |
| **GLBA** | US financial services | Yes |
| **SR 11-7** | US bank model risk | Yes |
| **FFIEC** | Federal financial inst. | Yes |
| **ISO 27001** | Global infosec | Yes |
| **NIST CSF** | US infosec voluntary | Yes (mapped) |
| **FedRAMP** | US federal cloud | No (not federal-direct) |
| **GDPR / CCPA** | Privacy | Yes (where data scope) |

## 2. CIS Benchmarks — the operational baseline

CIS (Center for Internet Security) publishes hardening checklists per platform:
- **CIS AWS Foundations Benchmark** v3.0 (Jan 2024) — ~50 checks
- **CIS Kubernetes Benchmark** — per K8s minor version
- **CIS Docker Benchmark**
- **CIS Linux Benchmark** (per distro)
- **CIS Azure / GCP Benchmarks**

These map into SOC 2 / PCI / HIPAA controls. Pass CIS = pass ~80% of compliance controls.

Tools to scan against CIS:
- **AWS Security Hub** — has the CIS standard built in
- **Prowler** — OSS multi-cloud scanner
- **ScoutSuite** — OSS multi-cloud
- **CloudSploit / Aqua Trivy** — multi-cloud
- **kube-bench** — K8s CIS
- **CIS-CAT Pro** — CIS's own tool (paid)
- **OpenSCAP** — Linux SCAP scanner

## 3. AWS Config — resource configuration history + rules

AWS Config:
1. **Records** the configuration of every supported resource (~250+ types)
2. **Stores history** in S3
3. **Evaluates rules** continuously (or on-change)
4. **Triggers remediation** via SSM Automation

```hcl
resource "aws_config_configuration_recorder" "main" {
  name     = "default"
  role_arn = aws_iam_role.config.arn
  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  name           = "default"
  s3_bucket_name = aws_s3_bucket.config.id
  depends_on     = [aws_config_configuration_recorder.main]
}
```

## 4. Config Rules

```hcl
# Managed rule — AWS provides 200+ pre-built
resource "aws_config_config_rule" "s3_public_read" {
  name = "s3-bucket-public-read-prohibited"
  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
  }
}

resource "aws_config_config_rule" "iam_password_policy" {
  name = "iam-password-policy"
  source {
    owner             = "AWS"
    source_identifier = "IAM_PASSWORD_POLICY"
  }
  input_parameters = jsonencode({
    MinimumPasswordLength      = "14"
    RequireSymbols             = "true"
    RequireNumbers             = "true"
    RequireUppercaseCharacters = "true"
    RequireLowercaseCharacters = "true"
    PasswordReusePrevention    = "24"
    MaxPasswordAge             = "90"
  })
}

# Custom Lambda-backed rule
resource "aws_config_config_rule" "custom" {
  name = "my-custom-rule"
  source {
    owner             = "CUSTOM_LAMBDA"
    source_identifier = aws_lambda_function.config_rule.arn
  }
}
```

## 5. Conformance Packs — bundled rules

A conformance pack = many rules + remediation actions, packaged together:

```hcl
resource "aws_config_conformance_pack" "cis_v3" {
  name          = "cis-aws-foundations-v3"
  template_body = file("conformance-packs/cis-aws-foundations-v3.yaml")
}
```

AWS publishes ~30 sample packs (CIS, PCI-DSS, HIPAA, NIST 800-53, FedRAMP, etc.). Apply one, get a hundred rules.

## 6. Auto-Remediation

```hcl
resource "aws_config_remediation_configuration" "sg_open" {
  config_rule_name           = "restricted-ssh"
  target_type                = "SSM_DOCUMENT"
  target_id                  = "AWS-DisablePublicAccessForSecurityGroup"
  automatic                  = true
  maximum_automatic_attempts = 5

  parameter {
    name           = "GroupId"
    resource_value = "RESOURCE_ID"
  }

  parameter {
    name         = "AutomationAssumeRole"
    static_value = aws_iam_role.config_remediation.arn
  }
}
```

When a security group with 0.0.0.0/0 SSH is detected → Config Rule fires NON_COMPLIANT → SSM Automation runs → removes the rule.

Capital One: similar pattern via **Cloud Custodian** which combines policy + remediation in Python.

## 7. Auto-Remediation example for CloudTrail logging

Common: detect when someone disables CloudTrail logging:

```yaml
# CIS rule: ensure CloudTrail logging is enabled
- rule: cloudtrail-enabled
  source: AWS
  identifier: CLOUD_TRAIL_ENABLED
- remediation:
    SSMDocument: AWS-EnableCloudTrail
    automatic: true
```

If anyone disables CloudTrail → Config detects → SSM re-enables. Within minutes, attacker loses their attempt to hide.

## 8. Cloud Custodian — Capital One's tool

Cloud Custodian (YAML-based policy framework, Python under the hood, CNCF Sandbox 2018):

```yaml
policies:
  - name: encrypt-unencrypted-volumes
    resource: ebs
    filters:
      - Encrypted: false
    actions:
      - snapshot
      - delete

  - name: detect-public-s3
    resource: s3
    filters:
      - type: global-grants
    actions:
      - type: remove-statements
        statement_ids: matched
      - type: notify
        to: [security@example.com]
        transport:
          type: sns
          topic: arn:aws:sns:us-east-1:1234:security-alerts

  - name: stop-unused-rds
    resource: rds
    filters:
      - type: metrics
        name: DatabaseConnections
        days: 7
        statistics: Sum
        value: 0
    actions:
      - stop
```

Custodian's strengths:
- **Single YAML covers detection + remediation** (Config separates)
- **Filters compose** declaratively (and/or/not)
- **Pluggable actions** (notify, tag, delete, modify, snapshot, etc.)
- **Multi-cloud** (AWS deepest, Azure + GCP supported)

## 9. Compliance dashboards

| Tool | What |
|---|---|
| **AWS Security Hub** | Aggregates Config + GuardDuty + Inspector + Macie; CIS/PCI/AWS-Foundational standards built in |
| **AWS Audit Manager** | Auto-collects evidence mapped to framework controls; PDF export for auditors |
| **Wiz / Lacework / Orca / Sysdig** | Commercial CSPMs; multi-cloud; better UX than Hub |
| **Drata / Vanta / Secureframe** | Compliance-program platforms — gather evidence across SaaS too |
| **Splunk / Datadog Compliance** | If you already have the SIEM |

## 10. Compliance Rules for AWS EKS

EKS-specific compliance:
- **EKS audit logs enabled** (CW)
- **Public endpoint disabled OR restricted CIDR**
- **Latest K8s minor version**
- **Secrets envelope-encrypted with KMS**
- **Node group security groups restricted**
- **IRSA / Pod Identity used (not long-lived keys)**

Plus K8s-level via kube-bench / Polaris / Trivy K8s.

## 11. The compliance-as-code playbook

1. **Map your obligations** — which frameworks apply, which controls
2. **Pick benchmarks** that satisfy them (CIS AWS, CIS K8s, NIST 800-53)
3. **Implement scanners** that evaluate continuously (Config, Security Hub, Custodian)
4. **Set up auto-remediation** for low-risk findings
5. **Workflow for high-risk findings** — DefectDojo / Jira / Slack
6. **Dashboards + reports** for management + auditors
7. **Drift detection** + alarms (CloudTrail metric filters)
8. **Annual penetration test** + control review

## 12. Quick self-check

1. What does AWS Config do that CloudTrail doesn't?
2. What's a Conformance Pack?
3. What's Cloud Custodian and what Capital One contributed it?
4. Why is auto-remediation valuable beyond just detection?
5. How does CIS map to SOC 2 / PCI compliance?

(Answers: records resource configuration history + evaluates compliance rules — CloudTrail is API-call audit, Config is resource-state audit; bundle of Config Rules + remediations packaged for a framework (CIS, PCI, HIPAA, etc.); declarative Python policy framework for AWS resources — detection + filters + actions in one YAML — Capital One built it, CNCF Sandbox since 2018; closes the window between detection and human response — many findings should be auto-fixed in seconds, not days; CIS Benchmarks define operational hardening that maps to ~80% of SOC 2 / PCI controls — pass CIS, pass most of those.)



ewpage


# 38 — Introducing DevSecOps in Organizations

## Why this module exists

Tools are 20% of DevSecOps; org change is 80%. This module is the people + process layer.

## 1. Why DevSecOps fails to take root

The pattern when DevSecOps fails:
- **Sec team buys tools** → drops them on dev teams → no training, no support → tools ignored
- **Findings flood** → no triage capacity → backlog grows → devs disengage
- **Security team is gate, not partner** → adversarial dynamic → workarounds + shadow IT
- **No exec backing** → feature pressure wins every conflict → security debt accumulates
- **Vendor sprawl** → 20 tools, no normalization → review fatigue

## 2. Cultural change drivers (what actually works)

### Make security visible
Dashboards everyone sees: open findings by team, SLA compliance, time-to-fix. **Public scoreboards drive behavior** (positively or negatively — calibrate carefully).

### Reward fixing, not punish finding
A team that ships features and has zero findings might be hiding them or not scanning. A team with many findings + fast fixes is healthy. The metric should be **MTTR**, not finding count.

### Embed security engineers in product teams
Stop the ivory-tower model. Embed: pair on threat models, write policies together, attend standups. Capital One does this at ~1:30 ratio.

### Run blameless postmortems
When an incident happens, the culture must be "what process gap?" not "who screwed up?" Otherwise people hide problems. (Same SRE principle, applied to security.)

### Champions program
Volunteer "security champions" in each product team — 10% time on security work, regular training. They become the bridge.

## 3. The real-world examples

### Netflix — Paved Road
Security team builds golden paths (Spinnaker, Lemur, BLESS, etc.) that are easier than rolling your own. Teams use the paved road because it's the path of least resistance — not because they're forced.

### Capital One — Cloud Custodian + InnerSource
- Built **Cloud Custodian** in-house; open-sourced 2018; used internally by every team.
- **InnerSource** model: security tools are internal OSS projects; product teams can contribute.
- **Security as a Service** internal — security team operates platforms, product teams consume.
- After 2019 breach: doubled down on least-privilege automation, multi-account architecture, IMDSv2 enforcement.

### Shopify — Security Engineering as Product
- Security tools have product managers + designers + UX research.
- "Security is a product" — measured by developer adoption + NPS, not just findings.

### Stripe — Risk-tiered Security
- Tiered controls by impact (PII service vs marketing site)
- Avoid "every service gets every control" — wasted effort
- High-tier services get more rigor (SAST + DAST + SCA + manual review); low-tier less

## 4. The DevSecOps transformation roadmap (12-month)

### Months 1-2: Baseline
- Inventory: what tools, what scans, what coverage today
- Surveys: how do devs feel about security right now
- Pick 2-3 frameworks to standardize on (SOC 2 + CIS AWS + CIS K8s, e.g.)

### Months 3-4: Foundation
- Stand up DefectDojo (or equivalent)
- Pre-commit hooks rolled out: gitleaks + linters
- SCA + SAST in CI on PRs
- OIDC for CI/CD (kill long-lived keys)

### Months 5-6: Container security
- Trivy in CI; fail Critical
- ECR + Cosign signing
- Pod Security Admission (restricted) on new namespaces

### Months 7-8: Cloud security
- AWS Config + Security Hub
- Cloud Custodian or equivalent
- IAM Access Analyzer
- CloudTrail + alarms

### Months 9-10: K8s + GitOps
- Kyverno admission policies
- ArgoCD/Flux migration
- External Secrets Operator
- Istio mTLS (or simpler — cert-manager + NetworkPolicy)

### Months 11-12: Monitoring + Maturity
- Compliance dashboards
- Auto-remediation for low-risk findings
- Quarterly DR + IR drills
- Re-survey team morale

## 5. DORA-style measurement for DevSecOps

The metrics to track quarterly:
- **% of pipelines with security scans enabled** (target: 100%)
- **Critical CVEs in production** (target: 0)
- **MTTR for security findings, by severity** (target: Critical < 7d, High < 30d)
- **Auto-remediation rate** (target: 50%+ of low-risk findings)
- **Time from alert to ticket** (target: < 5 min — automate)
- **Developer NPS on security tools** (target: positive)

## 6. The Build vs Buy decision

| | Build | Buy |
|---|---|---|
| **Best for** | Unique workflows; org > 5000 engineers | Standard workflows; small team |
| **Time to value** | 6-12 months | Weeks |
| **Customization** | Total | Limited |
| **Ongoing cost** | Engineering + ops | Subscription |
| **Risk** | Internal expertise dependency | Vendor lock-in + supply chain |

Capital One: builds (Cloud Custodian, internal tooling) but also buys (Wiz/Lacework-tier CSPM, Splunk SIEM).

Most teams: buy for everything; build only when scale demands.

## 7. Vendor selection criteria (the boring but essential list)

When evaluating a DevSecOps tool:
- **API-first** — can it integrate with everything you have
- **SAML / SSO + SCIM** — proper enterprise auth
- **CI/CD integration** — GitHub Actions, GitLab CI, Jenkins
- **DefectDojo / Jira ticketing integration**
- **Per-developer vs per-resource pricing** — model your trajectory
- **On-prem option** for regulated shops
- **Support quality** — talk to references
- **Roadmap alignment** — where they're investing
- **Acquisition risk** — vendor stability

## 8. Compliance vs Security (the meta-point)

**Compliance** = passing audits.
**Security** = not getting breached.

They overlap but aren't the same. A team can be compliant and unsecure (security theater). Or secure but non-compliant (mature controls not mapped to a framework).

DevSecOps should aim for **security** with compliance as a side effect. Audit-pass is the floor, not the ceiling.

## 9. The exec sponsor lever

DevSecOps needs:
- **Board / CISO sponsor** — gets time + budget approved
- **Engineering VP sponsor** — gets team buy-in
- **Public commitment** — "we will not ship with Critical CVEs" — credible commitment makes prioritization decisions automatic

Without exec backing, security loses every conflict with feature pressure.

## 10. Quick self-check

1. Why does "buy tools and drop them on devs" fail as a DevSecOps strategy?
2. What's the difference between security and compliance?
3. What's a "security champion" program?
4. Name three DevSecOps maturity metrics you'd track quarterly.
5. Why is "paved road" better than "mandatory policy" for adoption?

(Answers: no training/support/triage → backlog grows → tools get ignored — humans matter more than tools; compliance = pass audit, security = don't get breached — overlap but not the same; volunteer engineers in product teams who allocate 10% to security work + are the bridge to security team; % of pipelines scanned, Critical CVEs in prod, MTTR by severity, auto-remediation rate, developer NPS; humans take the path of least resistance — make secure path easier than insecure path and people use it without being told.)



ewpage


# 39 — GitLab CI/CD vs GitHub Actions vs Jenkins

## Why this module exists

Three CI/CD platforms dominate 2026. Which one to pick for a new project — and why teams have all three — is a real architectural question.

## 1. The market shares (rough, 2026)

| Platform | Share |
|---|---|
| Jenkins (incl. CloudBees CI) | ~40% |
| GitHub Actions | ~35% (and rising) |
| GitLab CI | ~15% |
| CircleCI / Travis / Bitbucket Pipelines / Buildkite / Drone / Tekton / others | ~10% |

Jenkins is declining (slowly) in greenfield; Actions is gaining. GitLab is ~stable. In regulated finance, Jenkins is still dominant due to self-hostability + air-gap support.

## 2. Side-by-side comparison

| Feature | Jenkins | GitHub Actions | GitLab CI |
|---|---|---|---|
| **Hosting** | Self-hosted (CloudBees SaaS exists) | SaaS-first (Enterprise Server on-prem) | SaaS + Self-hosted |
| **Pricing model** | Free OSS / CloudBees license | Per-user + per-minute | Per-user (Free/Premium/Ultimate) |
| **Config language** | Groovy (Jenkinsfile) | YAML | YAML |
| **Plugin ecosystem** | Massive (1800+) | Marketplace, fast-growing | Limited (built-in features instead) |
| **Built-in registry** | Plugin-based | GitHub Packages / GHCR | Built-in container + package registry |
| **Built-in DevSecOps** | Plugins | GHAS (paid; SAST + Secret Scanning) | Ultimate (full SAST + DAST + SCA + Secret + Container) |
| **Self-hosted runners** | Native (agents) | Yes (ARC for K8s) | Yes (well-supported) |
| **Air-gap capable** | Yes | Enterprise Server | Self-managed |
| **Workflow language** | Imperative Groovy | Declarative YAML | Declarative YAML |
| **Learning curve** | Steep (Groovy + plugins) | Mild | Mild |
| **K8s deploy** | Plugins | Actions | GitLab Agent for K8s |
| **Best for** | Regulated / legacy / large orgs | GitHub-native projects | All-in-one DevSecOps |

## 3. When to pick each

### Pick Jenkins when:
- Regulated finance / healthcare (air-gap, on-prem mandates)
- Large existing investment in Groovy + shared libraries
- Need plugin-level customization
- Multi-master, multi-tenant at scale
- Capital One reality

### Pick GitHub Actions when:
- Your code lives on GitHub
- You want the path of least resistance
- You're OK with SaaS (Enterprise Server if you need self-host)
- Strong DevSecOps via GHAS

### Pick GitLab CI when:
- You want one platform for SCM + CI + DevSecOps + registry + IaC + ML registry
- Single-vendor procurement matters
- Strong DevSecOps requirements with budget for Ultimate
- Compliance frameworks built-in

## 4. The "you have all three" reality

Big orgs end up with:
- **Jenkins** for legacy + regulated workloads (Capital One)
- **GitHub Actions** for new microservices + open-source contributions
- **GitLab CI** for teams that want all-in-one

This is fine if you accept the cost: shared libraries don't transfer, runners don't share, observability is split.

## 5. Architectural primitives — vocabulary translation

| Concept | Jenkins | Actions | GitLab |
|---|---|---|---|
| **Pipeline definition** | Jenkinsfile | workflow YAML | .gitlab-ci.yml |
| **Job execution unit** | Stage / Step | Job / Step | Job |
| **Build agent** | Agent | Runner | Runner |
| **Secret storage** | Credentials Store | Secrets | CI/CD Variables |
| **Reusable logic** | Shared Library | Reusable Workflow / Composite Action | CI/CD Component / include |
| **Trigger** | SCM polling / webhook | Event | Push / MR / Schedule |
| **Plugin ecosystem** | Plugins | Marketplace Actions | Limited (built-in) |
| **Environment** | (3rd party) | Environment | Environment |
| **K8s deploy auth** | Plugin / kubeconfig | OIDC + IAM | GitLab Agent |

## 6. Migration paths

### Jenkins → GitLab CI
- Convert Jenkinsfile → .gitlab-ci.yml (Mostly manual; Jenkinsfile Groovy doesn't translate 1:1)
- Migrate shared libraries → CI/CD Components or includes
- Replace plugin functionality with GitLab built-ins
- Re-provision runners as GitLab Runners on EC2/K8s
- Move credentials from Jenkins Credentials → GitLab Variables (or OIDC)

### Jenkins → Actions
- Similar exercise: Jenkinsfile → workflow YAML
- Self-hosted runners as ARC pods on K8s
- Shared libraries → Composite Actions or Reusable Workflows
- See [Topic 07](../07_git_github_devops/) for the Actions deep dive

### Actions → GitLab
- Generally easier than Jenkins → either (YAML to YAML)
- ARC runners → GitLab K8s executor
- Reusable workflows → GitLab includes / Components
- Marketplace Actions → custom job templates (less off-the-shelf in GitLab)

### GitLab → Actions
- YAML → YAML; mostly mechanical
- Use Marketplace Actions for what GitLab built-in did
- For DevSecOps coverage: GHAS replaces GitLab Ultimate scanners

## 7. Cost — the back-of-envelope

### GitHub Actions
- $0.008/min for Linux on Free; included minutes per tier
- Larger runners much more expensive
- Free public repo runners

### GitLab CI SaaS
- 400 free min/mo on Free tier
- 10,000 included min/mo on Premium ($29/user/mo)
- $0.10/min for additional Linux compute units in 2025
- Or self-hosted runners on your infra

### Jenkins
- OSS free; you pay infra + ops
- CloudBees CI: opaque enterprise pricing; ~$5-20/user/mo at scale

For a 50-engineer team:
- Actions: $200-1000/mo (depending on minute usage + GHAS licensing)
- GitLab Ultimate: $4,950/mo (50 × $99) — yikes — but includes everything
- Jenkins OSS: ~$500/mo infra cost (k8s + ec2 agents) + ~1 engineer

## 8. DevSecOps coverage compared

| | Jenkins | Actions | GitLab |
|---|---|---|---|
| **Secret scanning in repo** | Plugins | Free + Push Protection paid via GHAS | Free + Premium for Detection |
| **SAST** | Plugins (Sonar, etc.) | CodeQL via GHAS | Ultimate built-in |
| **SCA** | Plugins | Dependabot free + GHAS | Ultimate built-in |
| **Container scanning** | Plugins | GHAS Container | Ultimate built-in |
| **DAST** | Plugins (ZAP) | 3rd party Actions | Ultimate built-in |
| **License scanning** | Plugins | GHAS | Ultimate built-in |
| **API fuzzing** | Plugins | 3rd party | Ultimate built-in |
| **Vuln tracker** | Plugins (DefectDojo) | Security tab | Built-in Vulnerability Report |

GitLab Ultimate's strength is "everything in one console." The cost is the platform lock-in.

## 9. The CI/CD platform team angle

If you're an AI/ML engineer at Capital One, you'll **consume** Jenkins, not build the platform. Your interview-relevant skills:
- Understand the platform model (controller + agents, runners, etc.)
- Read + write Jenkinsfile / .gitlab-ci.yml / Actions YAML
- Know the security model (OIDC + IAM roles)
- Know how to debug pipeline failures
- Know how to optimize (caching, parallelism, matrix)

You don't need to know "how to install Jenkins from scratch." You need to know "how to add a new pipeline to the existing Jenkins."

## 10. Quick self-check

1. Why is Jenkins dominant in regulated finance?
2. What's the GitLab Ultimate equivalent for GHAS in security coverage?
3. Why might a team end up with all three CI platforms?
4. What's the Composite Action equivalent in GitLab?
5. What does "CI/CD Components" replace in GitLab?

(Answers: self-hostable + air-gap-capable + plugin ecosystem + 20-year track record; GitLab Ultimate scanners (SAST + DAST + SCA + Secret + Container + License + API) all included; legacy on Jenkins, new microservices on Actions because GitHub-native, all-in-one team chooses GitLab; CI/CD Component or `include:` block; CI Templates from the pre-17.0 era.)



ewpage


# 40 — GitLab CI/CD Core Concepts

## 1. The .gitlab-ci.yml file

GitLab CI reads `.gitlab-ci.yml` at the root of your repo. One YAML defines the pipeline.

```yaml
stages: [test, build, deploy]

test:
  stage: test
  image: python:3.13-slim
  script:
    - pip install -r requirements.txt
    - pytest

build:
  stage: build
  image: docker:27-cli
  services: [docker:27-dind]
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: alpine/k8s:1.31
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

## 2. Jobs — the unit of work

A job has:
- **`script`** — what runs (shell commands)
- **`image`** — Docker image the job runs in
- **`stage`** — which stage it belongs to
- **`needs`** — dependency on other jobs (DAG mode)
- **`rules` / `only` / `except`** — when to run
- **`artifacts`** — files to keep
- **`cache`** — files to reuse between runs
- **`before_script` / `after_script`** — setup / teardown

```yaml
unit-tests:
  stage: test
  image: python:3.13-slim
  before_script:
    - pip install -r requirements.txt -r requirements-dev.txt
  script:
    - pytest --cov --junitxml=report.xml
  after_script:
    - echo "done"
  artifacts:
    when: always
    paths: [report.xml, htmlcov/]
    reports:
      junit: report.xml
    expire_in: 30 days
```

## 3. Stages — sequential groups of parallel jobs

```yaml
stages: [lint, test, build, deploy]
```

Jobs in same stage run in parallel; stages run sequentially. A stage waits for all jobs in the previous stage to succeed (unless `allow_failure: true`).

## 4. `needs` — the DAG mode

For granular dependencies, use `needs` to override the stage order:

```yaml
build-frontend:
  stage: build
  script: cd frontend && npm run build

build-backend:
  stage: build
  script: cd backend && go build

test-frontend:
  stage: test
  needs: [build-frontend]   # starts as soon as build-frontend finishes
  script: cd frontend && npm test

test-backend:
  stage: test
  needs: [build-backend]
  script: cd backend && go test ./...
```

`test-frontend` doesn't wait for `build-backend`; it starts as soon as `build-frontend` finishes. DAG mode lets you parallelize aggressively.

## 5. Triggers — `only`, `except`, `rules`, `workflow`

The 2026 way: **`rules`** (the modern syntax; `only`/`except` deprecated for new code).

```yaml
deploy-staging:
  stage: deploy
  script: ./deploy.sh staging
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes: [src/**/*]
      when: on_success

deploy-prod:
  stage: deploy
  script: ./deploy.sh prod
  rules:
    - if: '$CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/'
      when: manual
```

### `workflow:rules` controls whole pipeline
```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'   # MR pipeline
    - if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'        # main branch
    - if: '$CI_COMMIT_TAG'                                  # tag
```

If no rule matches, the pipeline doesn't run.

## 6. Predefined CI/CD Variables

Every job gets dozens of pre-populated env vars:

| Variable | Value |
|---|---|
| `$CI_COMMIT_SHA` | full SHA |
| `$CI_COMMIT_SHORT_SHA` | 8-char prefix |
| `$CI_COMMIT_BRANCH` | branch name |
| `$CI_COMMIT_TAG` | tag if any |
| `$CI_PIPELINE_ID` | unique pipeline ID |
| `$CI_PIPELINE_URL` | URL to view pipeline |
| `$CI_JOB_ID` | unique job ID |
| `$CI_PROJECT_PATH` | namespace/project |
| `$CI_REGISTRY` | host of project's container registry |
| `$CI_REGISTRY_IMAGE` | base image path in registry |
| `$CI_REGISTRY_USER` / `$CI_REGISTRY_PASSWORD` | auth to registry |
| `$CI_JOB_TOKEN` | API token scoped to this job |

Full list: 200+ predefined variables, in GitLab docs.

## 7. Custom variables

### In `.gitlab-ci.yml`
```yaml
variables:
  APP_NAME: my-app
  ENVIRONMENT: dev
```

### In UI (Settings → CI/CD → Variables)
- **Masked** — value hidden in logs
- **Protected** — only available on protected branches/tags
- **Expanded** — variable expansion enabled
- **File type** — value written to a temp file, var contains the path

### Hierarchy (precedence)
1. Inline variables (lowest)
2. `variables:` block
3. Project CI/CD variables (UI)
4. Group CI/CD variables
5. Manual job variables (highest)

## 8. Triggering a pipeline on Merge Request

GitLab MRs auto-trigger pipelines when:
- The MR is opened or commits pushed
- The pipeline source is `merge_request_event`

```yaml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'

# In jobs:
test:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
  script: pytest
```

**Merged-results pipelines** run the pipeline on the *merged* result (target + source merge) — closer to production behavior. **Merge trains** queue MRs to merge one at a time, each running the merged-results pipeline.

## 9. Artifacts + Reports

```yaml
test:
  script: pytest --junitxml=report.xml --cov-report=xml
  artifacts:
    when: always
    paths:
      - report.xml
      - coverage.xml
    reports:
      junit: report.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 30 days
```

GitLab natively understands reports:
- **junit** — test results displayed in MR
- **coverage_report** — coverage in MR
- **sast** — SAST findings in MR
- **dependency_scanning** — SCA findings
- **container_scanning** — image scan
- **dast** — DAST findings
- **secret_detection** — secret scan
- **license_scanning** — license issues
- **terraform** — terraform plan in MR

## 10. Cache vs Artifacts

| | Artifacts | Cache |
|---|---|---|
| **Purpose** | Pass between stages + persist for download | Speed up subsequent runs |
| **Lifetime** | Configurable (default 30 days) | Until manually cleared or evicted |
| **Per-job** | Yes | Shared by key |
| **Compressed + uploaded** | To GitLab server | To shared storage (S3 / GCS / local) |
| **Use case** | Test reports, built binaries | node_modules, pip cache, .terraform |

```yaml
test:
  cache:
    key: $CI_COMMIT_REF_SLUG
    paths:
      - .venv/
      - .pytest_cache/
  script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt
    - .venv/bin/pytest
```

## 11. Inline shell + multiline

```yaml
script:
  - |
    set -euo pipefail
    if [ "$CI_COMMIT_BRANCH" = "main" ]; then
      ./scripts/deploy.sh prod
    else
      ./scripts/deploy.sh staging
    fi
```

The `|` preserves newlines. Bash conditionals work fine.

## 12. Quick self-check

1. What's the difference between `stages` and `needs`?
2. What's the difference between `rules` and the legacy `only`/`except`?
3. What's a "merged-results pipeline" and why use it?
4. What's the difference between artifacts and cache?
5. What's `workflow:rules` vs job-level `rules`?

(Answers: stages = sequential groups, needs = DAG dependencies between jobs that override stage order; rules is the modern flexible syntax with if/changes/exists/when, only/except is legacy + simpler; runs the pipeline on the merged result (target + source merge) — closer to production state; artifacts pass files between jobs + persist for download (junit, coverage), cache speeds up subsequent runs (node_modules, pip cache); workflow:rules controls whether the entire pipeline runs, job-level rules controls whether the specific job runs within an already-running pipeline.)



ewpage


# 41 — GitLab Architecture — Runners + Executors

## 1. The architecture

```
┌────────────────────────────┐
│   GitLab Server            │  (gitlab.com or self-hosted)
│   - SCM, MRs, Pipelines    │
│   - Job queue              │
│   - Artifacts + Registry   │
└────────────────────────────┘
           │
           │ long-poll for jobs
           ▼
┌────────────────────────────┐
│   GitLab Runner (process)  │  (registered to GitLab; runs as service)
│   - Token-authenticated    │
│   - Polls for jobs         │
│   - Dispatches to Executor │
└────────────────────────────┘
           │
           ▼
┌────────────────────────────┐
│       Executor              │  (where the actual job runs)
│   shell / docker / K8s /    │
│   ssh / custom              │
└────────────────────────────┘
```

**Runner** = process that picks up jobs.
**Executor** = where the job actually executes (shell, container, K8s pod).

## 2. Executors

| Executor | When | Job runs in |
|---|---|---|
| **Shell** | Simple; runner's host environment | Same machine as runner, no isolation |
| **Docker** | Most common | Docker container on runner host |
| **Docker-in-Docker (dind)** | Building images | Docker daemon inside a container |
| **Kubernetes** | Production at scale | Auto-spawned K8s pods per job |
| **Docker-Machine** | DEPRECATED — replaced by K8s + Fleet executors |
| **SSH** | Run on existing remote | SSHed to a managed box |
| **Instance / GitLab SaaS** | gitlab.com hosted | AWS/GCP/Azure instances |
| **VirtualBox / Parallels** | macOS / Windows VM-based isolation | Local VM |
| **Custom** | Roll your own | Anywhere via custom driver |

In 2026: **Kubernetes** executor dominates serious GitLab CI deployments. **Docker** for smaller teams. **Instance executor** is the AWS Fleet-style replacement for Docker-Machine.

## 3. Job execution flow

For a Docker-executor job:
1. Runner polls GitLab for a job
2. GitLab assigns: "run this job with these scripts in this image"
3. Runner pulls the image
4. Runner starts a container; clones the repo into it
5. Runs `before_script` + `script` + `after_script`
6. Captures logs + artifacts
7. Uploads artifacts back to GitLab
8. Reports status

## 4. Project Runners vs Group Runners vs Instance Runners

| Type | Scope | Set by |
|---|---|---|
| **Instance Runners** | All projects (admin-configured) | GitLab admin |
| **Group Runners** | All projects in a group | Group owner |
| **Project Runners** | One project only | Project maintainer |

For security: sensitive projects should use **Project Runners** they exclusively control. Shared instance runners run other people's jobs on the same host — risk of supply-chain attacks or noisy neighbors.

## 5. Tags + concurrency

Tag runners by capability:
```bash
gitlab-runner register --tag-list "linux,docker,aws,gpu"
```

Pipeline jobs request runners by tag:
```yaml
job:
  tags: [aws, gpu]
  script: ...
```

`concurrent` setting in `config.toml` defines max parallel jobs per runner. Don't oversaturate: a 4-CPU host running 8 concurrent jobs will be slower than 4.

## 6. Self-hosted runner on EC2

```bash
# Install on Ubuntu
curl -L --output /usr/local/bin/gitlab-runner \
  https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
chmod +x /usr/local/bin/gitlab-runner

# Create user
useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash

# Install service
gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
gitlab-runner start

# Register (new token-based flow since GitLab 16)
gitlab-runner register \
  --url https://gitlab.com \
  --token <authentication-token> \
  --executor docker \
  --docker-image alpine:3.20 \
  --description "ec2-aws-runner-1" \
  --tag-list "aws,docker"
```

Since GitLab 16 (2023), the runner registration uses an **authentication token** (per-runner) instead of the legacy registration token (per-project). The token flow is more secure: each runner has its own credential, revocable independently.

## 7. Kubernetes executor

```toml
# config.toml
[[runners]]
  name = "k8s-runner"
  url = "https://gitlab.com"
  token = "<auth-token>"
  executor = "kubernetes"
  [runners.kubernetes]
    namespace = "gitlab"
    image = "alpine:3.20"
    cpu_request = "500m"
    memory_request = "1Gi"
    service_account = "gitlab-runner"
    privileged = false
```

Each job → fresh K8s pod. Pod terminates after job. **Autoscaling for free** — the cluster's HPA + Karpenter handle node scale.

Image-build pattern: Kaniko or BuildKit (rootless) inside the K8s job, not DinD (DinD requires privileged, which violates Pod Security).

```yaml
build-image:
  image: gcr.io/kaniko-project/executor:debug
  script:
    - /kaniko/executor
        --context $CI_PROJECT_DIR
        --dockerfile $CI_PROJECT_DIR/Dockerfile
        --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
        --cache=true
        --cache-repo $CI_REGISTRY_IMAGE/cache
```

## 8. GitLab SaaS Runners

For gitlab.com users without self-hosted:
- **Linux** (small, medium, large, x-large) — pay per minute beyond included tier
- **Linux GPU** — for ML training
- **macOS** — for iOS builds; $0.08/min in 2025
- **Windows** — for .NET builds
- **z-Linux + s390x** — for mainframe

Pricing (2026, gitlab.com):
- Free: 400 min/mo (Linux only)
- Premium: 10,000 min/mo
- Ultimate: 50,000 min/mo
- Additional units: $5/1000 compute units (varies by runner size)

## 9. Docker Runner on EC2

```toml
[[runners]]
  executor = "docker"
  [runners.docker]
    image = "alpine:3.20"
    privileged = false       # never true unless DinD specifically required
    pull_policy = ["if-not-present", "always"]
    volumes = ["/cache"]
    network_mode = "bridge"
    extra_hosts = []
    helper_image = "registry.gitlab.com/gitlab-org/gitlab-runner/gitlab-runner-helper:x86_64-latest"
```

Mount `/var/run/docker.sock` only when truly needed. Prefer Kaniko/BuildKit for builds.

## 10. Self-Managed GitLab Instance

For air-gap / regulated shops, host your own GitLab:
- Omnibus install (single host) — simplest
- Helm chart on K8s — for HA + scale
- Cloud-Native Helm (CNH) — newer; modular

GitLab.com vs self-managed:
- **Same software, different hosting**
- Self-managed = control + air-gap + custom integrations
- gitlab.com = no ops burden + SLAs

## 11. GitLab Runner versions compatibility

Runner version should match (or be one minor ahead of) GitLab Server version. Older runners may not support new pipeline features.

```bash
gitlab-runner --version
```

Update via package manager or container:
```bash
docker pull gitlab/gitlab-runner:latest
```

## 12. Quick self-check

1. What's the difference between a Runner and an Executor?
2. Why prefer Project Runners over Instance Runners for sensitive projects?
3. What replaced Docker-Machine executor for AWS auto-scaling?
4. Why is Kaniko preferred over DinD for image builds in K8s executor?
5. What changed in runner registration in GitLab 16?

(Answers: Runner is the process polling GitLab + dispatching; Executor is the actual environment (shell, docker, k8s pod) where the job runs; isolation — instance runners share host with other projects' jobs, risk of supply-chain or noisy neighbors; Instance executor (AWS Fleet-style) for auto-scaling on AWS; Kaniko doesn't need privileged pod or daemon socket — runs as rootless user; per-runner authentication tokens replaced per-project registration tokens — each runner now has its own revocable credential.)



ewpage


# 42 — Real Pipeline — Node.js App to Private Registry to DEV

## 1. The scenario

A Node.js app → unit tests → Docker image → push to GitLab Container Registry → deploy to DEV server via SSH + Docker.

## 2. The Node.js project

```
my-node-app/
├── package.json
├── package-lock.json
├── src/
│   └── index.js
├── tests/
│   └── index.test.js
├── Dockerfile
└── .gitlab-ci.yml
```

`Dockerfile`:
```dockerfile
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .

FROM node:24-alpine
RUN addgroup -S app && adduser -S app -G app
WORKDIR /app
COPY --from=builder --chown=app:app /app .
USER app
EXPOSE 3000
CMD ["node", "src/index.js"]
```

## 3. The .gitlab-ci.yml

```yaml
stages: [test, build, deploy]

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  IMAGE_LATEST: $CI_REGISTRY_IMAGE:latest

default:
  image: node:24-alpine
  cache:
    key:
      files: [package-lock.json]
    paths: [node_modules/]

# ─────────────────────────────────────────────────
# Stage: test
# ─────────────────────────────────────────────────
unit-tests:
  stage: test
  script:
    - npm ci
    - npm run lint
    - npm test -- --reporter=junit --output=test-report.xml
  artifacts:
    when: always
    reports:
      junit: test-report.xml
    expire_in: 7 days

# ─────────────────────────────────────────────────
# Stage: build (Docker image + push to GitLab registry)
# ─────────────────────────────────────────────────
build-image:
  stage: build
  image: gcr.io/kaniko-project/executor:v1.23.0-debug
  script:
    - mkdir -p /kaniko/.docker
    - |
      cat > /kaniko/.docker/config.json <<EOF
      {
        "auths": {
          "$CI_REGISTRY": {
            "auth": "$(echo -n "$CI_REGISTRY_USER:$CI_REGISTRY_PASSWORD" | base64 | tr -d '\n')"
          }
        }
      }
      EOF
    - >
      /kaniko/executor
      --context $CI_PROJECT_DIR
      --dockerfile $CI_PROJECT_DIR/Dockerfile
      --destination $IMAGE_TAG
      --destination $IMAGE_LATEST
      --cache=true
      --cache-repo $CI_REGISTRY_IMAGE/cache
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

# ─────────────────────────────────────────────────
# Stage: deploy
# ─────────────────────────────────────────────────
deploy-dev:
  stage: deploy
  image: alpine:3.20
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - ssh-keyscan -H $DEV_SERVER >> ~/.ssh/known_hosts
  script:
    - |
      ssh deploy@$DEV_SERVER <<EOF
      set -euo pipefail
      docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
      docker pull $IMAGE_TAG
      docker stop my-app || true
      docker rm my-app || true
      docker run -d --name my-app --restart=unless-stopped \
        -p 80:3000 \
        $IMAGE_TAG
      EOF
  environment:
    name: dev
    url: http://dev.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

## 4. Variables you set in Settings → CI/CD → Variables

| Variable | Value | Settings |
|---|---|---|
| `SSH_PRIVATE_KEY` | the deploy user's private key | Masked + Protected + File |
| `DEV_SERVER` | dev.example.com | Plain |
| `$CI_REGISTRY_USER` / `$CI_REGISTRY_PASSWORD` | (predefined; GitLab provides automatically) | — |

For SSH key: type **File**, paste private key contents — GitLab writes to temp file and `$SSH_PRIVATE_KEY` contains the path.

## 5. GitLab Environments

```yaml
environment:
  name: dev
  url: http://dev.example.com
```

Creates an entry in **Operate → Environments** with deployment history. Rollback via UI (re-runs the deploy job at an older SHA).

For prod:
```yaml
deploy-prod:
  environment:
    name: production
    url: https://example.com
    deployment_tier: production
  rules:
    - if: '$CI_COMMIT_TAG'
      when: manual
```

`deployment_tier` (production / staging / testing / development / other) gives GitLab semantic awareness for compliance dashboards.

## 6. Test Reports + Coverage in MRs

GitLab parses test reports + coverage:

```yaml
unit-tests:
  script:
    - npm test -- --coverage --coverageReporters=cobertura --reporters=jest-junit
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
```

The `coverage:` regex extracts the percentage from job logs; displays in MR.

## 7. The Container Registry

GitLab's built-in registry is included free. Authentication via:
- `CI_REGISTRY_USER` / `CI_REGISTRY_PASSWORD` (predefined per-job)
- Or `CI_JOB_TOKEN` for short-lived
- Or deploy tokens for cross-project access

```bash
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

For ECR (instead of GitLab registry):
```yaml
build-image:
  before_script:
    - aws ecr get-login-password --region $AWS_REGION | docker login -u AWS --password-stdin $ECR_REGISTRY
  script:
    - docker build -t $ECR_REGISTRY/my-app:$CI_COMMIT_SHORT_SHA .
    - docker push $ECR_REGISTRY/my-app:$CI_COMMIT_SHORT_SHA
```

## 8. Deploying with Docker Compose

Sometimes you want compose, not raw `docker run`:

```yaml
deploy-dev:
  script:
    - |
      ssh deploy@$DEV_SERVER <<EOF
      cd /opt/app
      sed -i "s|image: .*my-app:.*|image: $IMAGE_TAG|" compose.yaml
      docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
      docker compose pull
      docker compose up -d
      EOF
```

The compose file lives on the server; CI updates the tag + pulls.

## 9. The security hardening for this pattern

What's wrong with the above:
- SSH from CI directly = inbound SSH on the server
- Long-lived SSH key in CI vars
- `docker login` with `CI_REGISTRY_PASSWORD` (job token works but is broader scoped than needed)

What to upgrade to:
- **AWS SSM RunCommand** instead of SSH (no inbound; IAM-based auth; CloudTrail audit)
- **OIDC to AWS Role** instead of long-lived SSH key
- **Deploy via K8s + GitOps** instead of raw docker on a VM (eliminates SSH entirely)

This is the Nana-bootcamp pattern; for production at Capital One it's the GitOps + EKS pattern.

## 10. Quick self-check

1. Why use Kaniko instead of `docker build` in this pipeline?
2. What does `$CI_REGISTRY_USER` give you for free?
3. What does GitLab Environments add over just running deploy jobs?
4. Why is SSH from CI to EC2 considered an anti-pattern?
5. What's the difference between `deployment_tier: production` and `name: production`?

(Answers: Kaniko builds images without requiring a privileged Docker daemon — works in unprivileged K8s pods; pre-authenticated credential to the project's container registry — no need to manage; deployment history per env, easy rollback, MR shows latest deploy URL; inbound SSH on prod hosts + long-lived SSH key in CI — SSM RunCommand removes both; tier is the semantic level used by GitLab for compliance dashboards, name is the display label.)



ewpage


# 43 — Optimization — Caching, Multi-Stage, `extends`

## 1. The optimization levers

A slow CI pipeline kills velocity. The four levers:
1. **Parallelization** (DAG mode with `needs`)
2. **Caching** (don't reinstall deps every run)
3. **Smart triggers** (don't run jobs that don't matter)
4. **DRY config** (`extends`, `include`, anchors)

## 2. Dynamic image versioning

Don't push `latest`; use semantic + commit-SHA versioning:

```yaml
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG-$CI_COMMIT_SHORT_SHA

# For tag-driven releases
variables:
  RELEASE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
```

Auto-version from git:
```yaml
build:
  before_script:
    - export APP_VERSION=$(git describe --tags --always --abbrev=7)
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$APP_VERSION .
```

## 3. Caching deeper

```yaml
.cache_template: &python_cache
  cache:
    key:
      files: [requirements.txt]
    paths:
      - .venv/
      - .cache/pip/
    policy: pull-push     # default; alternatives: pull, push, pull-push

test:
  <<: *python_cache
  script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt
    - .venv/bin/pytest
```

`policy: pull` for jobs that only consume; `policy: push` for jobs that produce. Default `pull-push` does both.

### Caching node_modules
```yaml
.node_cache: &node_cache
  cache:
    key:
      files: [package-lock.json]
    paths:
      - node_modules/
      - .npm/

build:
  <<: *node_cache
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run build
```

### Caching Docker layers
For Docker builds, BuildKit + registry cache (Module 23):
```yaml
build-image:
  image: gcr.io/kaniko-project/executor:v1.23.0-debug
  script:
    - /kaniko/executor --cache=true --cache-repo $CI_REGISTRY_IMAGE/cache ...
```

## 4. Speeding up `npm install` etc.

- `npm ci` (not `install`) — fail on lockfile mismatch + skip-update + faster
- `pip install --no-deps -r requirements-locked.txt`
- `uv pip install -r requirements.txt` — 10-100x faster
- `bun install` — even faster for Node

## 5. SAST + DAST as pipeline stages (with security-as-code)

```yaml
include:
  - template: Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/Dependency-Scanning.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml
  - template: Jobs/DAST.gitlab-ci.yml

variables:
  SAST_EXCLUDED_PATHS: "tests/, docs/"
  DS_EXCLUDED_PATHS: "vendor/"
  DAST_WEBSITE: https://staging.example.com
  DAST_FULL_SCAN_ENABLED: "true"
```

GitLab built-in templates (Premium/Ultimate) handle scanner runs + report integration. Free tier: bring your own (Semgrep, Trivy, ZAP).

## 6. Multi-stage deployments — Dev → Staging → Prod

```yaml
stages: [test, build, deploy-dev, deploy-staging, deploy-prod]

.deploy_template: &deploy
  image: alpine/k8s:1.31
  before_script:
    - kubectl config use-context $KUBE_CONTEXT

deploy-dev:
  stage: deploy-dev
  <<: *deploy
  environment: { name: dev, url: https://dev.example.com }
  variables: { KUBE_CONTEXT: dev-cluster, NAMESPACE: app-dev }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy-staging:
  stage: deploy-staging
  <<: *deploy
  environment: { name: staging, url: https://staging.example.com }
  variables: { KUBE_CONTEXT: stg-cluster, NAMESPACE: app-stg }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual

deploy-prod:
  stage: deploy-prod
  <<: *deploy
  environment: { name: production, url: https://example.com }
  variables: { KUBE_CONTEXT: prd-cluster, NAMESPACE: app-prd }
  script: kubectl -n $NAMESPACE set image deployment/app app=$IMAGE_TAG
  rules:
    - if: '$CI_COMMIT_TAG'
      when: manual
```

## 7. Reusing config — `extends`

The cleaner modern syntax over YAML anchors:

```yaml
.test-template:
  image: python:3.13-slim
  cache:
    key:
      files: [requirements.txt]
    paths: [.venv/]
  before_script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt

unit-tests:
  extends: .test-template
  script: .venv/bin/pytest tests/unit

integration-tests:
  extends: .test-template
  script: .venv/bin/pytest tests/integration
  services: [postgres:17]
```

`extends:` is **deep-merged** — child overrides only what it specifies.

## 8. Include — across files + projects

```yaml
include:
  # Local file
  - local: 'ci/build.yml'

  # File from another project
  - project: 'my-org/ci-templates'
    ref: main
    file: '/python/test.yml'

  # Remote URL
  - remote: 'https://example.com/ci/template.yml'

  # GitLab-provided template
  - template: 'Auto-DevOps.gitlab-ci.yml'

  # CI/CD Components (new way, GitLab 17+)
  - component: 'gitlab.com/components/secret-detection/secret-detection@~latest'
```

## 9. Matrix builds

```yaml
test:
  parallel:
    matrix:
      - PYTHON_VERSION: ["3.11", "3.12", "3.13"]
        OS: [linux]
  image: python:$PYTHON_VERSION-slim
  script:
    - pip install -r requirements.txt
    - pytest
```

This generates 3 parallel jobs.

## 10. Skipping unchanged work

`rules:changes` runs the job only when relevant files changed:
```yaml
build-frontend:
  rules:
    - changes: [frontend/**/*]
  script: cd frontend && npm run build

build-backend:
  rules:
    - changes: [backend/**/*]
  script: cd backend && go build
```

Combined with monorepo: only the changed component rebuilds.

## 11. Parallel + needs combo (DAG mode)

```yaml
test-1:
  stage: test
  script: pytest tests/unit_1

test-2:
  stage: test
  script: pytest tests/unit_2

# Aggregator starts as soon as both finish, doesn't wait for whole stage
report:
  stage: test
  needs: [test-1, test-2]
  script: ./aggregate-reports.sh
```

Or run test shards:
```yaml
test:
  parallel: 8
  script: pytest --shard $CI_NODE_INDEX/$CI_NODE_TOTAL
```

## 12. Quick self-check

1. What's the difference between `policy: pull` and `policy: push` in cache config?
2. What's `extends` and how does it compose with anchors?
3. What does `rules:changes` enable for monorepos?
4. How does `parallel:matrix` work?
5. What's the difference between `include:local` and `include:project`?

(Answers: pull only reads cache (don't update), push only writes (don't read first) — useful when only some jobs produce cache; extends is deep-merge of templates — preferred over anchors for readability — child overrides only specified keys; only build the components whose files changed in the commit — huge speedup in monorepos; generates N parallel jobs with cross-product of matrix dimensions, each with a unique combination as env vars; local is files in the same repo, project is files from another project (cross-project sharing).)



ewpage


# 44 — Microservices CI/CD — Monorepo + Polyrepo

## 1. The microservices CI/CD problem

You have 30 services. Options:
- **Polyrepo**: each service its own repo → independent CI/CD; easy to scope ownership; hard to share code/config
- **Monorepo**: one repo with all services → shared code/config easy; complex CI/CD

Both are valid. Pick based on team org + scale.

## 2. Monorepo CI/CD pattern

The challenge: 30 services, one repo. Don't rebuild + retest all 30 on every commit.

### `rules:changes` per service
```yaml
# In services/service-a/ci.yml
service-a:test:
  stage: test
  script: cd services/service-a && npm test
  rules:
    - changes:
        - services/service-a/**/*
        - shared/**/*

service-a:build:
  stage: build
  needs: [service-a:test]
  script: cd services/service-a && docker build -t $CI_REGISTRY_IMAGE/service-a:$CI_COMMIT_SHA .
  rules:
    - changes:
        - services/service-a/**/*

service-a:deploy:
  stage: deploy
  needs: [service-a:build]
  script: kubectl set image deployment/service-a service-a=$CI_REGISTRY_IMAGE/service-a:$CI_COMMIT_SHA
  rules:
    - changes: [services/service-a/**/*]
      if: '$CI_COMMIT_BRANCH == "main"'
```

### Top-level orchestrator
```yaml
include:
  - local: services/service-a/ci.yml
  - local: services/service-b/ci.yml
  - local: services/service-c/ci.yml
  # ... 30 of these
```

Or dynamically:
```yaml
include:
  - local: services/*/ci.yml    # glob since GitLab 16.x
```

## 3. Polyrepo CI/CD pattern

Each service's repo has its own `.gitlab-ci.yml` referring to common templates:

```yaml
# Each service repo:
include:
  - project: 'my-org/ci-templates'
    ref: v2.4
    file: '/python/service.yml'

service:test:
  extends: .python-service-test
  variables:
    SERVICE_NAME: service-a
```

The `ci-templates` project holds the shared logic.

## 4. CI/CD Components (the 2024 way, replacing CI Templates)

GitLab 17.0 (May 2024) GA-d **CI/CD Components** — reusable, versioned bundles published to a Catalog.

A Component lives in its own GitLab project + has a `templates/` dir:

```
ci-templates/
├── templates/
│   ├── docker-build.yml      # Component "docker-build"
│   └── helm-deploy.yml       # Component "helm-deploy"
└── README.md
```

Publish a release tag (e.g., `v1.2`); consumers reference by version:

```yaml
include:
  - component: gitlab.com/my-org/ci-templates/docker-build@v1.2
    inputs:
      image-name: my-app
      build-args: "--build-arg ENV=prod"

  - component: gitlab.com/my-org/ci-templates/helm-deploy@v1.2
    inputs:
      chart-path: ./charts/my-app
      release-name: my-app
      namespace: my-app-prod
```

Components define typed inputs:
```yaml
# In templates/docker-build.yml
spec:
  inputs:
    image-name:
      type: string
      description: Docker image name
    build-args:
      type: string
      default: ""
      description: Extra docker build args
---
docker-build:
  stage: build
  script:
    - docker build $[[ inputs.build-args ]] -t $[[ inputs.image-name ]] .
```

This is **the modern way** for polyrepo orgs to share CI logic.

## 5. Job Templates with `extends:` (the older approach)

For simpler reuse without Component overhead:

```yaml
# in ci-templates/python.yml
.python-test:
  image: python:3.13-slim
  cache:
    paths: [.venv/]
  before_script:
    - python -m venv .venv
    - .venv/bin/pip install -r requirements.txt -r requirements-dev.txt
  script:
    - .venv/bin/pytest --cov

.python-build:
  image: docker:27-cli
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

```yaml
# in service's .gitlab-ci.yml
include:
  - project: my-org/ci-templates
    ref: main
    file: /python.yml

unit-tests:
  extends: .python-test

build:
  extends: .python-build
```

## 6. Multi-project pipelines

A pipeline in one project triggers a pipeline in another:

```yaml
trigger-deploy:
  stage: deploy
  trigger:
    project: my-org/deploy-project
    branch: main
    strategy: depend     # wait for triggered pipeline to finish
```

Useful when you want to keep app code separate from deploy manifests (GitOps).

## 7. Parent-child pipelines

Spawn a child pipeline from a parent:

```yaml
trigger-build:
  stage: build
  trigger:
    include:
      - local: ci/build-pipeline.yml
    strategy: depend
```

Useful for dynamic generation: detect what changed, generate a child pipeline that only builds those.

## 8. Dynamic child pipelines

Generate `.gitlab-ci.yml` at runtime:

```yaml
generate:
  stage: build
  script:
    - python ci/generate.py > dynamic-pipeline.yml
  artifacts:
    paths: [dynamic-pipeline.yml]

trigger:
  stage: deploy
  trigger:
    include:
      - artifact: dynamic-pipeline.yml
        job: generate
    strategy: depend
```

`generate.py` inspects the diff and writes only the relevant build jobs. Combines monorepo + per-service builds elegantly.

## 9. Monorepo vs Polyrepo decision

| | Monorepo | Polyrepo |
|---|---|---|
| **Coordination** | Atomic cross-service commits | Multi-PR dance |
| **Code share** | `shared/` dir easy | Package + version |
| **CI complexity** | Per-service triggers + components | Templates + Components per repo |
| **Build time** | Risk of "build everything" | Isolated |
| **Tooling** | Bazel, Nx, Turborepo help | Standard tooling |
| **Ownership** | CODEOWNERS per path | Repo per team |
| **Scale ceiling** | Soft at 1000+ services | Infinite |

Big tech monorepos: Google, Meta, Twitter. Polyrepo at scale: Netflix, Amazon.

## 10. Build the right thing — affected detection

For monorepos, **affected analysis**:
- Nx, Turborepo, Bazel — language/framework-specific tools that know the dep graph
- Custom: walk dep graph + diff to find affected packages
- Last resort: `git diff --name-only` + heuristic

Skipping unrelated jobs saves money and time at scale.

## 11. Quick self-check

1. What's the modern replacement for CI Templates in GitLab 17+?
2. What's a parent-child pipeline vs a multi-project pipeline?
3. How do `rules:changes` enable smart monorepo CI?
4. What's a dynamic child pipeline?
5. When does polyrepo's "one repo, one CI" beat monorepo for CI complexity?

(Answers: CI/CD Components — versioned, catalog-published, typed inputs; parent-child both inside same project (one spawns the other), multi-project triggers a pipeline in another project; only run jobs for services whose files changed in the commit; pipeline generates more pipeline YAML at runtime — useful when you need to decide what to build based on the diff; small to medium scale + clear service boundaries + no cross-service atomic changes needed.)



ewpage


# 45 — CI/CD Components (the 2024 Templates Replacement)

## 1. Why Components exist

GitLab CI Templates (`include: template:`) and `include: project:` worked but had limits:
- No typed inputs (everything was implicit YAML vars)
- No versioning (you referenced by ref name, no semver guarantees)
- No discoverability (no catalog)
- No tests (templates were tested by their consumers)

**CI/CD Components** (GA in GitLab 17.0, May 2024) add all four.

## 2. Anatomy of a Component

```
my-org/ci-components/
├── templates/
│   ├── docker-build/
│   │   └── template.yml     # the actual job(s)
│   ├── helm-deploy/
│   │   └── template.yml
│   └── trivy-scan/
│       └── template.yml
├── README.md
└── .gitlab-ci.yml            # tests for the components
```

Each subdir in `templates/` is one Component. The directory name is the component name.

## 3. A simple Component

```yaml
# templates/docker-build/template.yml
spec:
  inputs:
    image-name:
      type: string
      description: Image name to build/push
    dockerfile:
      type: string
      default: Dockerfile
      description: Path to Dockerfile
    context:
      type: string
      default: .
    push:
      type: boolean
      default: true
    stage:
      type: string
      default: build
---
docker-build:
  stage: $[[ inputs.stage ]]
  image: docker:27-cli
  services: [docker:27-dind]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker build -f $[[ inputs.dockerfile ]] -t $[[ inputs.image-name ]] $[[ inputs.context ]]
    - if [ "$[[ inputs.push ]]" = "true" ]; then docker push $[[ inputs.image-name ]]; fi
```

## 4. Using a Component

```yaml
# consumer .gitlab-ci.yml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v1.0.0
    inputs:
      image-name: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
      dockerfile: Dockerfile.prod
      context: ./app
```

The `$CI_SERVER_FQDN` predefined variable points to your GitLab instance (gitlab.com or self-hosted).

## 5. Input types

```yaml
spec:
  inputs:
    name:
      type: string
      default: "default-name"
      regex: '^[a-z][a-z0-9-]*$'
    replicas:
      type: number
      default: 3
    debug:
      type: boolean
      default: false
    environments:
      type: array
      default: [dev, staging, prod]
    timeout:
      type: string
      default: "30m"
```

Inputs are validated; bad input fails the pipeline early with a clear message.

## 6. Versioning

Component releases are git tags on the component project. Reference patterns:

```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v1.2.3   # exact version
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@~latest  # latest release
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@main     # main branch (testing only)
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@$CI_COMMIT_SHA  # SHA-pinned
```

For production: **pin to exact semver tag**, like any other dependency.

## 7. CI/CD Catalog

GitLab.com has a public Catalog (https://gitlab.com/explore/catalog) where Components are searchable, tagged, and rated. Self-managed instances have their own internal Catalog.

To publish to Catalog:
1. Project has at least one `templates/<component>/template.yml`
2. Add `description` and `spec.tags` to README
3. Create a release (git tag + GitLab Release object)
4. Mark project as **CI Catalog resource** in Settings

```yaml
# In templates/foo/template.yml
spec:
  description: "Build and push Docker image"
  inputs:
    # ...
```

## 8. The library pattern — your org's component library

```
my-org/ci-components/
├── templates/
│   ├── python-test/template.yml
│   ├── nodejs-test/template.yml
│   ├── docker-build/template.yml
│   ├── helm-deploy/template.yml
│   ├── argocd-sync/template.yml
│   ├── trivy-scan/template.yml
│   ├── cosign-sign/template.yml
│   ├── slack-notify/template.yml
│   └── ...
├── tests/
│   └── ... (verify each component)
└── .gitlab-ci.yml
```

Every service in the org references this:
```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/python-test@v3.1
  - component: $CI_SERVER_FQDN/my-org/ci-components/docker-build@v3.1
    inputs: { image-name: $CI_REGISTRY_IMAGE }
  - component: $CI_SERVER_FQDN/my-org/ci-components/trivy-scan@v3.1
    inputs: { image-name: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA }
  - component: $CI_SERVER_FQDN/my-org/ci-components/helm-deploy@v3.1
    inputs: { chart-path: ./charts/app }
```

One MR to the central components repo updates all consuming projects on next pipeline run.

## 9. Testing a Component

The component's project has its own `.gitlab-ci.yml` that exercises its own components:

```yaml
# Test docker-build component
include:
  - component: $CI_SERVER_FQDN/$CI_PROJECT_PATH/docker-build@$CI_COMMIT_SHA
    inputs:
      image-name: test-image:$CI_COMMIT_SHORT_SHA
      push: false
```

Pipeline runs → if the component breaks, the pipeline fails → block merge.

## 10. Migrating from CI Templates / Includes

Old:
```yaml
include:
  - project: 'my-org/ci-templates'
    ref: main
    file: '/python.yml'

unit-tests:
  extends: .python-test
```

New (Component):
```yaml
include:
  - component: $CI_SERVER_FQDN/my-org/ci-components/python-test@v1.0
    inputs:
      python-version: "3.13"
```

The migration is mechanical but gives:
- Versioning safety
- Typed inputs (no more "did I set the right magic var?")
- Catalog discoverability

## 11. Best practices

1. **One Component per concern** — `docker-build`, not `build-and-deploy`
2. **Typed inputs over implicit variables** — make the contract explicit
3. **Semver versioning** — major bumps for breaking changes
4. **Test in the component's own pipeline** — don't make consumers find your bugs
5. **Pin consumers to exact versions** — `@v1.2.3`, not `@~latest`
6. **Document inputs + outputs** — generate from `spec:` if you can
7. **Avoid hidden side effects** — Component should only do what its name says

## 12. Quick self-check

1. What four things did Components add over CI Templates?
2. What's the input type system give you?
3. How do you reference a Component?
4. Why pin to exact version `@v1.2.3` in production?
5. What's the CI/CD Catalog?

(Answers: typed inputs + versioning + catalog discoverability + testability; runtime validation of inputs with regex/range/enum — bad inputs fail early with clear messages; `include: - component: $CI_SERVER_FQDN/path/to/component-project/component-name@version`; supply-chain safety — `@~latest` could change unexpectedly and break your pipeline; searchable registry of published Components within an instance — public on gitlab.com, private on self-managed.)



ewpage


# 46 — Deploy to Kubernetes from GitLab

## 1. Two ways to deploy to K8s from GitLab

| Method | When |
|---|---|
| **Push from CI (`kubectl set image`)** | Simple; CI has cluster credentials |
| **GitOps via GitLab Agent** | Modern; cluster pulls; better security |

## 2. The legacy push pattern

```yaml
deploy:
  image: alpine/k8s:1.31
  script:
    - mkdir -p ~/.kube
    - echo "$KUBECONFIG_DATA" | base64 -d > ~/.kube/config
    - kubectl set image deployment/app app=$IMAGE_TAG -n my-app
    - kubectl rollout status deployment/app -n my-app --timeout=5m
```

Problems:
- Kubeconfig stored in GitLab CI variables — sensitive credential persistence
- Pipeline has direct write access to the cluster
- Cluster trusts pipeline IPs by NetworkPolicy (or doesn't)

## 3. GitLab Agent for Kubernetes — the modern way

GitLab Agent (formerly KAS = Kubernetes Agent Server) reverses the trust direction:
- **Agent installed in cluster** as a Deployment
- Agent **dials out** to GitLab over WebSocket
- GitLab sends commands through the channel
- No inbound traffic to cluster; no kubeconfig in CI variables

### Install agent
1. GitLab UI → Operate → Kubernetes clusters → Connect → Configure agent
2. Get token + install command
3. Apply Helm chart to cluster:

```bash
helm repo add gitlab https://charts.gitlab.io
helm upgrade --install my-agent gitlab/gitlab-agent \
  --namespace gitlab-agent --create-namespace \
  --set image.tag=v17.10.0 \
  --set config.token=<agent-token> \
  --set config.kasAddress=wss://kas.gitlab.com
```

4. Configure agent in repo: `.gitlab/agents/<agent-name>/config.yaml`:
```yaml
ci_access:
  groups:
    - id: my-group   # Allow this group's pipelines to use the agent
gitops:
  manifest_projects:
    - id: my-group/k8s-manifests
      default_namespace: my-app
      paths:
        - glob: 'overlays/prod/*.yaml'
```

### Use in pipeline
```yaml
deploy:
  image: alpine/k8s:1.31
  script:
    - kubectl config use-context my-group/my-project:my-agent
    - kubectl set image deployment/app app=$IMAGE_TAG -n my-app
```

`kubectl config use-context <group/project>:<agent-name>` — auth handled transparently.

## 4. GitOps mode of the Agent

The Agent can be configured in **GitOps mode**: it watches a manifest repo and applies changes itself. No push-from-CI at all.

```yaml
# .gitlab/agents/my-agent/config.yaml
gitops:
  manifest_projects:
    - id: my-group/k8s-manifests
      default_namespace: my-app
      paths:
        - glob: 'apps/my-app/**.yaml'
      reconcile_timeout: 1m
      dry_run_strategy: server
```

The agent polls the manifest repo + applies changes. Updates to `my-app:1.2.3` in the manifest → agent pulls + applies. Same idea as ArgoCD/Flux but GitLab-native.

## 5. CI updates the manifest repo (the GitOps loop)

```yaml
# In application repo .gitlab-ci.yml
update-manifest:
  image: alpine/git
  before_script:
    - apk add --no-cache git curl yq
  script:
    - git clone https://gitlab-ci-token:$CI_JOB_TOKEN@gitlab.com/my-group/k8s-manifests.git
    - cd k8s-manifests
    - yq -i '.spec.template.spec.containers[0].image = strenv(IMAGE)' apps/my-app/deployment.yaml
    - git config user.email "ci@example.com"
    - git config user.name "CI"
    - git add . && git commit -m "deploy my-app $IMAGE_TAG"
    - git push origin main
  variables:
    IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

The agent's GitOps poller picks up the commit + applies. Pipeline doesn't touch the cluster.

## 6. Create K8s cluster on Linode (LKE) — Nana's bootcamp

For learners + small projects, **Linode Kubernetes Engine (LKE)** is cheap:
- Free control plane
- ~$36/mo for a 3-node small cluster
- DigitalOcean DOKS, Civo, OVHcloud similar

```bash
# Linode CLI
linode-cli lke cluster-create --label test-cluster --region us-east \
  --k8s_version 1.31 --node_pools '[{"type":"g6-standard-2","count":3}]'
```

For real production: EKS / GKE / AKS / managed-K8s (your cloud).

## 7. Creating a GitLab User with restricted K8s permissions

In manifest GitOps mode, the agent uses its ServiceAccount in-cluster. Grant least-privilege:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-agent
  namespace: gitlab-agent
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: gitlab-agent-app
  namespace: my-app
rules:
- apiGroups: ["", "apps", "networking.k8s.io"]
  resources: ["deployments", "services", "configmaps", "ingresses", "pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-agent-app
  namespace: my-app
subjects:
- kind: ServiceAccount
  name: gitlab-agent
  namespace: gitlab-agent
roleRef:
  kind: Role
  name: gitlab-agent-app
  apiGroup: rbac.authorization.k8s.io
```

The agent can manage only the `my-app` namespace. No cluster-admin.

## 8. Deploying to multiple clusters

Register one Agent per cluster; pipelines pick context per environment:

```yaml
deploy-dev:
  script: kubectl config use-context my-group/my-project:dev-agent && kubectl apply -f manifests/dev/

deploy-staging:
  script: kubectl config use-context my-group/my-project:stg-agent && kubectl apply -f manifests/staging/

deploy-prod:
  script: kubectl config use-context my-group/my-project:prd-agent && kubectl apply -f manifests/prod/
  when: manual
```

## 9. Helm deploy from GitLab CI

```yaml
deploy:
  image: alpine/helm:3.16
  script:
    - helm upgrade --install my-app ./charts/my-app \
        --namespace my-app --create-namespace \
        --set image.tag=$CI_COMMIT_SHORT_SHA \
        --wait --timeout 5m
```

For GitLab Agent + Helm: `kubectl config use-context <agent>` then `helm` works.

## 10. Decision: push from CI vs GitOps

| | Push from CI | GitOps (Agent or ArgoCD) |
|---|---|---|
| **Cluster credentials in CI** | Yes (risk) | No |
| **Audit** | CI logs | Git history |
| **Drift detection** | None | Yes (reconciliation) |
| **Multi-cluster** | One credential per cluster in CI | One agent per cluster |
| **Rollback** | Re-run old pipeline | Git revert |
| **Setup complexity** | Lower | Higher upfront |
| **2026 recommendation** | Only for small / experimental | The default |

## 11. Quick self-check

1. What problem does GitLab Agent solve over kubeconfig-in-CI?
2. What's the difference between Agent CI access mode and GitOps mode?
3. Why grant the Agent only namespace-scoped permissions?
4. What does `kubectl config use-context my-group/my-project:my-agent` do?
5. Why is GitOps deploy preferred over push-from-CI in 2026?

(Answers: Agent dials out from cluster to GitLab, no inbound traffic and no kubeconfig stored in CI vars; CI access lets pipelines call kubectl via the agent (push mode), GitOps mode has the agent pull manifests from a repo + apply autonomously; least privilege — Agent compromise → only that namespace at risk, not the whole cluster; sets kubectl context to authenticate via the agent — no kubeconfig file needed; pipeline doesn't need cluster credentials, drift detection, Git-history audit, easy rollback.)



ewpage


# 47 — AI Study Assistants for Engineers

> Nana's "Ultimate IT Fundamentals" course opens with a chapter on using AI to learn faster. For Vatsal (already using Claude Code daily) this is brief — but the curriculum + Socratic patterns + risks are worth surfacing.

## 1. The 2026 landscape

| Tool | Use case |
|---|---|
| **Claude Code (CLI)** | Code-aware tutoring + project building (Vatsal's daily tool) |
| **Claude.ai (chat + projects)** | Long-form reasoning, document analysis |
| **ChatGPT** | Mainstream — broadest knowledge cutoff, native search |
| **Gemini** | Google-integrated; Workspace + Vertex |
| **Perplexity** | Citation-first search |
| **NotebookLM** | "Talk to your sources" — upload PDFs/URLs, ask questions |
| **Cursor / Windsurf** | IDE-integrated coding |
| **Anki + AI** | Spaced repetition + AI-generated cards |
| **Khanmigo** | Math/science tutoring (mostly K-12) |

## 2. The "study assistant" prompting patterns

### Socratic mode
"Don't give me the answer. Ask me questions to help me get there. Stop after each question."

### Feynman technique
"Teach me X like I'm 15. Then teach me X like I'm a senior engineer. Highlight where the two diverge."

### Custom study plan
"I have 8 hours/week, 6 months, and need to learn AWS Sr Lead AI/ML skills. Build me a week-by-week plan with concrete exercises."

### Quiz me
"Ask me 5 questions about Kubernetes scheduling. After my answer, grade (0-10) + explain gaps."

### Exam prep
"You are the CKA exam. Generate a question. Then grade my response. Continue until I pass 10 in a row."

## 3. The do's and don'ts

| Do | Don't |
|---|---|
| Verify factual claims (especially version numbers, pricing) | Trust without checking |
| Use as Socratic tutor | Use as final-answer oracle |
| Combine with primary sources (docs, papers, RFCs) | Replace primary sources |
| Use to generate practice quizzes | Use to grade actual exams |
| Use for first-draft explanations | Use as the only explanation |

## 4. The hallucination problem (still real in 2026)

Even GPT-5 / Claude 4.x hallucinate:
- **Version numbers** — often confidently wrong
- **API signatures** — invented methods
- **CVE numbers / CVSS scores** — wrong details
- **Pricing** — out of date or made up
- **Recent changes** — knowledge cutoff issues

Verify everything that matters. Use docs as ground truth.

## 5. Keeping momentum

Nana's bootcamps last 4-6 months. Maintaining momentum:
- **20-minute daily** beats 4 hours weekly
- **Track in a simple tool** (Notion, Anki, even a text file)
- **Public commitment** — tell your manager or peer; commit to demo
- **Project-based learning** — not just tutorials; build something real
- **Teach what you learn** — blog, brown-bag, Slack thread

## 6. Quick self-check

1. What's the Socratic-mode prompting pattern?
2. Why verify AI-generated version numbers?
3. What does NotebookLM do differently from ChatGPT?
4. Why is 20 min/day better than 4 hr/week?
5. What's a sign you're using AI as oracle instead of tutor?

(Answers: tell it to ask questions back, not give answers; LLMs hallucinate specifics confidently; lets you upload sources and constrains answers to those sources — fewer hallucinations; consistency builds neural pathways, weekend cramming doesn't retain; you can't reproduce the answer from primary sources or explain it without re-asking.)



ewpage


# 48 — Agile + Scrum + Jira (Modern Reality)

## 1. Agile vs Scrum vs SAFe — the 2026 landscape

- **Agile Manifesto** (2001) — values + principles, not a process
- **Scrum** — most-adopted framework; sprints, backlog, ceremonies, roles
- **Kanban** — continuous flow; no sprints; WIP limits
- **Scrumban** — Scrum + Kanban hybrid
- **SAFe** (Scaled Agile Framework) — enterprise-scale; widely hated by practitioners; widely loved by middle managers
- **LeSS** / **Disciplined Agile** / **Spotify Model** — alternatives at scale

## 2. The Scrum cadence (in practice)

- **Sprint** — 1-4 weeks (2 most common)
- **Product Backlog** — prioritized list of work
- **Sprint Backlog** — work committed for the current sprint
- **Daily Standup** — 15min; what I did, what I'll do, blockers
- **Sprint Review** — demo at end
- **Sprint Retro** — what worked, what didn't, what to change
- **Sprint Planning** — pick from backlog for next sprint

Roles:
- **Product Owner** — prioritizes backlog, owns the "what"
- **Scrum Master** — facilitates ceremonies, removes blockers (often disappearing in 2026)
- **Dev Team** — builds it

## 3. The senior-engineer reality check

In 2026, mature orgs are dropping Scrum ceremonies. The trends:
- **Async standups** in Slack — no daily meeting
- **Continuous flow** (Kanban) instead of sprints
- **Story points abandoned** — measure cycle time + throughput instead
- **Retros every 2 weeks**, not every sprint
- **Demo days** monthly, not at end of every sprint

The Scrum-Master role is increasingly an EM responsibility, not a separate hire.

## 4. Jira essentials

Atlassian Jira Cloud is the dominant tool. Key concepts:
- **Project** — container of issues
- **Issue** — task (story, bug, epic, sub-task)
- **Board** — visualization (Scrum or Kanban)
- **Backlog** — prioritized list (Scrum)
- **Epic** → Stories → Sub-tasks hierarchy
- **Workflow** — issue state machine (To Do → In Progress → Done)
- **Sprint** — timeboxed iteration
- **Velocity** — story points completed per sprint (problematic metric)

## 5. The 2026 alternatives

| Tool | Why pick |
|---|---|
| **Linear** | Best DX, modern, opinionated, no setup |
| **Shortcut** (formerly Clubhouse) | Lightweight Jira |
| **Asana** | Cross-functional teams; non-tech projects too |
| **Monday.com** | Visual; project management beyond engineering |
| **Notion** | All-in-one workspace; lightweight project tracking |
| **GitHub Projects** | Tight GitHub integration |
| **Jira Product Discovery** | Atlassian's PM tool (separate from Jira Software) |

Engineering-tool-focused teams in 2026 increasingly leave Jira for Linear. Enterprise stays on Jira (Atlassian's lock-in via JSM, Confluence, ecosystem).

## 6. Backlog grooming + estimation

- **Story points** — relative sizing (Fibonacci: 1, 2, 3, 5, 8, 13). Increasingly debated.
- **T-shirt sizing** — XS/S/M/L/XL. Cheaper to apply.
- **Cycle time** — hours/days from "In Progress" to "Done". The metric that actually predicts.
- **Throughput** — items/sprint completed. Better than velocity.

The DORA-derived insight: cycle time is more honest than velocity. Velocity is gamed; cycle time is harder to fake.

## 7. Agile for AI/ML teams (the special case)

Standard Scrum struggles with AI/ML work because:
- Research has unpredictable timelines
- Experiments can fail (the result is "we learned X, no shippable artifact")
- Deliverables are model versions, not user stories
- "Done" is fuzzy (95% accuracy = ship? 98% = ship?)

Patterns that work:
- **Two-track agile** — discovery track (research) + delivery track (shippable improvements)
- **OKRs** for research goals; Kanban for ML platform/eng work
- **Demo every other week** of either: working model OR negative result
- **Time-box research** explicitly (e.g., "2 weeks to evaluate, then decide")

## 8. The Scrum anti-patterns

1. **Velocity as KPI** — gameable; encourages estimate inflation
2. **No retro action items** — retros become rituals with no improvement
3. **Story-point-poker as decision-making** — disagreement on point estimates means specification gap, not estimate gap
4. **Daily standup as status report** — should be coordination, not reporting
5. **No definition of done** — "done" varies per PR, leading to half-shipped work
6. **Sprint goal = "complete all stories"** — should be an outcome, not a list

## 9. Quick self-check

1. What's the difference between Scrum and Kanban?
2. Why is cycle time a better metric than velocity?
3. What's two-track agile and when use it?
4. Why are senior orgs dropping story points?
5. Name one Scrum anti-pattern.

(Answers: Scrum = timeboxed sprints with ceremonies, Kanban = continuous flow with WIP limits; cycle time is harder to game and directly measures throughput, velocity inflates with practice; one track for discovery/research, another for shippable delivery — fits AI/ML work; gameable, time-consuming, doesn't predict better than t-shirt sizes or just splitting work; velocity-as-KPI, story-poker as decision-making, no retro action items, daily-standup-as-status-report, no DoD, sprint-goal-as-list.)



ewpage


# 49 — Web Fundamentals — HTML / CSS / JS in 2026

> Skim module. Vatsal isn't pivoting to frontend, but knowing modern HTML/CSS/JS basics fills a context gap when reviewing frontend PRs from team members.

## 1. How the web works (the 30-second model)

```
Browser → DNS → resolves domain → IP
         → TCP/TLS handshake → connection
         → HTTP/2 or HTTP/3 → request
         → server response (HTML + assets)
         → browser parses + renders
         → JS executes → can fetch more data
```

Key protocols:
- **HTTP/1.1** — text-based, one request per connection
- **HTTP/2** (2015) — binary, multiplexed, server push
- **HTTP/3** (2022) — over QUIC (UDP), no head-of-line blocking
- **WebSockets** — bidirectional persistent connection
- **Server-Sent Events** — one-way streaming from server
- **WebTransport** (emerging) — HTTP/3-based, replaces WebSockets in some use cases

## 2. HTML5 semantic elements

Use semantic tags, not div soup:
```html
<header>, <nav>, <main>, <article>, <aside>, <footer>
<section>, <figure>, <figcaption>, <details>, <summary>
<dialog> for modals
```

Accessibility:
- ARIA roles + labels
- WCAG 2.2 (2023) — current accessibility standard
- Screen readers parse semantic HTML naturally

## 3. Modern CSS (massive evolution since 2020)

### Layout
- **Flexbox** — 1D layouts
- **Grid** — 2D layouts; replaces Bootstrap-style grid frameworks
- **Container queries** (2023) — responsive based on parent size, not viewport
- **Subgrid** (2023) — grid children inherit grid lines

### Features
- **`:has()`** — parent selector (2023 GA in all browsers)
- **CSS Nesting** — like SCSS, native
- **Cascade Layers** (`@layer`) — explicit specificity buckets
- **`@scope`** — limit selectors to a subtree
- **CSS Custom Properties (variables)** — `--main-color: blue;`
- **`color-mix()`** + `color()` — advanced color math
- **`clamp()`, `min()`, `max()`** — fluid sizing

### Why this matters
2026 CSS can do 80% of what required JS in 2015. The "no-JS-needed" frontier keeps expanding.

## 4. JavaScript ES2024+

Recent additions:
- `Array.prototype.toSorted/toReversed/toSpliced` — immutable variants (2023)
- `Object.groupBy` (2024)
- `Promise.withResolvers` (2024)
- `Set` set operations (`union`, `intersection`) (2024-2025)
- `Iterator helpers` (2024-2025)
- **Decorators** — finally stable (2023+)
- **Records & Tuples** — immutable primitives (proposal stage)
- **Pipeline operator** (`|>`) — still proposal

## 5. TypeScript dominance

TypeScript ~90% of new web projects (2026). Why:
- Catches type errors at compile time
- IDE autocomplete is dramatically better
- Documentation via types
- Ecosystem libraries ship `.d.ts` automatically

Modern alternatives:
- **JSDoc with type checking** (`@ts-check`) — gradual TS without rewrite
- **Deno's built-in TS support**
- **Bun's built-in TS support**

## 6. Variables, conditionals, loops (the basics)

```javascript
const name = "world";  // immutable binding
let count = 0;          // mutable
var unused = 1;          // legacy — don't use

// Conditionals
if (x === y) { /* ... */ } else if (x > y) { /* ... */ }
const result = x > 0 ? "pos" : "neg";

// Loops
for (const item of items) { /* ... */ }
for (const [i, item] of items.entries()) { /* ... */ }
items.forEach((item, i) => { /* ... */ });
const doubled = items.map(x => x * 2);
const evens = items.filter(x => x % 2 === 0);
const sum = items.reduce((acc, x) => acc + x, 0);
```

## 7. Objects + arrays + destructuring

```javascript
const user = { name: "Alice", age: 30 };
const { name, age } = user;
const updated = { ...user, age: 31 };

const arr = [1, 2, 3, 4];
const [first, ...rest] = arr;
const doubled = arr.map(x => x * 2);
```

## 8. Functions

```javascript
// Function declaration
function add(a, b) { return a + b; }

// Arrow functions (most common)
const add = (a, b) => a + b;

// Default + rest params
const greet = (name = "world", ...others) => `Hello ${name}, ${others.join(", ")}`;

// Async/await
const fetchUser = async (id) => {
  const r = await fetch(`/api/users/${id}`);
  return await r.json();
};
```

## 9. Built-in functions

```javascript
JSON.parse(str);
JSON.stringify(obj);
Object.keys(obj);
Object.values(obj);
Object.entries(obj);
Array.from(iter);
Array.isArray(x);
parseInt(str, 10);
parseFloat(str);
Number.isNaN(x);
fetch(url, options).then(r => r.json());
```

## 10. Browser DevTools (the muscle memory)

Open: F12 / Cmd+Option+I. Key tabs:
- **Elements** — DOM + CSS inspection
- **Console** — JS REPL + logs
- **Sources** — debugger, breakpoints
- **Network** — HTTP requests, timing
- **Performance** — flame charts
- **Lighthouse** — performance + a11y + SEO audit
- **Application** — storage, cookies, service workers

`document.querySelector('button')` to grab elements in Console.

## 11. Quick self-check

1. What's the difference between HTTP/2 and HTTP/3 at protocol level?
2. What's `:has()` and why is it useful?
3. What's the difference between `let` and `const`?
4. What's TypeScript adoption percentage in new web projects in 2026?
5. Why is `Array.prototype.toSorted()` an improvement over `sort()`?

(Answers: HTTP/2 over TCP with multiplexing, HTTP/3 over QUIC (UDP) eliminating head-of-line blocking; parent selector — can style based on what a child contains; let is mutable binding, const is immutable binding; ~90%; toSorted returns a new array (immutable), sort mutates in place — toSorted matches functional programming style + avoids subtle bugs.)



ewpage


# 50 — Frontend Framework Landscape

## 1. The 2026 frontend framework market

| Framework | Share | Notable |
|---|---|---|
| **React** | ~40% (still dominant) | React 19 RSC; meta-frameworks: Next.js, Remix |
| **Vue** | ~12% | Vue 3 only (Vue 2 EOL); Nuxt for SSR |
| **Angular** | ~10% (mostly legacy + enterprise) | v18+ with signals + standalone components |
| **Svelte** | ~8% (growing) | Svelte 5 with runes; SvelteKit |
| **Solid** | ~3% (small but loved) | Fine-grained reactivity; SolidStart |
| **Qwik** | ~2% (niche) | Resumability concept; meta-framework Qwik City |
| **HTMX + Alpine** | rising | Server-rendered + small JS |
| **Lit / Web Components** | <5% | Standards-based |

## 2. The mental model differences

| Framework | Reactivity model |
|---|---|
| **React** | Re-render component on state change; VDOM diff |
| **Vue** | Reactive refs; templated; small VDOM |
| **Angular** | Zone.js change detection (legacy) → Signals (modern) |
| **Svelte** | Compile away — no runtime VDOM |
| **Solid** | Fine-grained — only the DOM nodes that depend on changed state re-render |

The 2026 trend: **fine-grained reactivity** (Solid, Svelte runes, Vue Composition API + Vapor mode, Angular signals) — fewer wasted renders.

## 3. React in 2026

- **React 19** (Dec 2024) — actions, useOptimistic, useFormStatus, RSC stable
- **Next.js 15** (Oct 2024) — App Router + RSC + Turbopack default
- **Remix → React Router 7** (Nov 2024) — merged
- **Vite-based React** — for SPAs without SSR

Server Components (RSC): components run server-side; only client components hydrate; smaller JS bundle. Game-changer for data-heavy apps.

## 4. Vue in 2026 — preview

Vue 3 only (Vue 2 EOL Dec 2023). Defaults:
- **Composition API** (`setup()` / `<script setup>`)
- **Pinia** for state (replaced Vuex)
- **Vue Router 4**
- **Nuxt 3 / 4** for SSR meta-framework
- **Vapor Mode** — Vue 3.x emerging; compile-to-no-VDOM like Svelte

See Module 51 for the deep dive.

## 5. Svelte 5 (2024) — runes

```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  $effect(() => {
    console.log(`count is ${count}`);
  });
</script>

<button onclick={() => count++}>+</button>
<p>{count} → {doubled}</p>
```

Runes (`$state`, `$derived`, `$effect`) are explicit reactivity — replaces Svelte 4's implicit assignment-based reactivity.

## 6. Angular (Google) — what changed

Angular 18+ (2024) modernized:
- **Standalone components** — no NgModule
- **Signals** — fine-grained reactivity (replacing Zone.js)
- **Built-in control flow** (`@if`, `@for`)
- **Hydration** improvements

Mostly used in enterprise (Capital One frontend has Angular pockets).

## 7. The meta-framework era

| Meta-framework | Wraps | Adds |
|---|---|---|
| **Next.js** | React | SSR, RSC, routing, image opt |
| **Remix / React Router 7** | React | SSR, data loaders/actions |
| **Nuxt** | Vue | SSR, file-routing |
| **SvelteKit** | Svelte | SSR, file-routing |
| **SolidStart** | Solid | SSR, file-routing |
| **Astro** | Any (islands) | MPA-first, Markdown content |
| **Qwik City** | Qwik | Resumability |

Astro deserves special mention — uses any framework, but only ships the framework's JS for interactive islands. Massive perf win for content sites.

## 8. Build tools (the 2026 reality)

- **Vite** dominant for dev + SPAs
- **Turbopack** (Next.js bundled; Rust)
- **Rspack** (Webpack-compatible, Rust)
- **esbuild** (Go) — Vite's underlying minifier
- **swc** (Rust) — Babel replacement
- **Webpack** — legacy maintenance mode
- **Rollup** — library bundling
- **Bun** — JS runtime + bundler in one

Vite + esbuild + swc handle ~90% of new projects.

## 9. State management

| Tool | Framework |
|---|---|
| **Zustand, Jotai** | React |
| **Redux Toolkit** | React (legacy-pattern but still used) |
| **TanStack Query** | All |
| **SWR** | React |
| **Pinia** | Vue |
| **NgRx, NGXS, Signal Store** | Angular |
| **XState** | Any (state machines) |
| **Nanostores** | Any |

The 2026 default: **TanStack Query for server state**, **Zustand / Jotai / Pinia for client state**. Redux is legacy.

## 10. Pick a framework — decision frame

| Goal | Pick |
|---|---|
| **Career safety + hiring pool** | React (Next.js) |
| **Most enjoyable DX (subjective)** | Svelte or Vue |
| **Enterprise / Google ecosystem** | Angular |
| **Performance ceiling** | Solid or Qwik |
| **Content-heavy (blog, docs, marketing)** | Astro |
| **Minimal JS server-rendered** | HTMX + tiny Alpine.js |

For Vatsal: if you ever need a side project, **Next.js (React)** for safest career signal + AI tools (Cursor, Claude Code) work best with it.

## 11. Quick self-check

1. What are React Server Components and what problem do they solve?
2. What's "fine-grained reactivity" and which frameworks implement it?
3. What's Vue 3's preferred state management library?
4. What's Astro's island architecture?
5. Why is Webpack in maintenance mode?

(Answers: components run server-side and stream HTML, only client components hydrate — smaller JS bundle, faster TTI for data-heavy apps; only DOM nodes that depend on changed state re-render, vs whole-component re-render — Solid, Svelte 5, Vue Vapor, Angular signals; Pinia replaced Vuex; only ships JS for interactive components, rest is static HTML — massive perf win for content sites; Vite + esbuild + swc are ~10x faster and Webpack's perf can't catch up.)



ewpage


# 51 — VueJS 3 Deep

> Nana's IT Fundamentals course uses Vue 3 for the demo "Teamable" frontend. Vue 2 has been EOL since Dec 2023; everything here is Vue 3.

## 1. The Vue 3 mental model

```
<template> — declarative HTML with directives + bindings
<script setup> — reactive state + functions
<style scoped> — CSS scoped to this component
```

Vue is **template-first**; React is **JS-first**. Vue compiles templates to render functions.

## 2. The minimal Vue 3 component

```vue
<script setup>
import { ref, computed, onMounted } from 'vue'

const count = ref(0)
const doubled = computed(() => count.value * 2)

function increment() {
  count.value++
}

onMounted(() => {
  console.log('mounted; count is', count.value)
})
</script>

<template>
  <button @click="increment">Click me</button>
  <p>Count: {{ count }}, Doubled: {{ doubled }}</p>
</template>

<style scoped>
button { background: blue; color: white; }
</style>
```

`ref` creates a reactive value. Inside `<script>`, access via `.value`. Inside `<template>`, just use the name (Vue unwraps).

## 3. Composition API vs Options API

### Composition API (`<script setup>`) — modern, preferred
```vue
<script setup>
import { ref, computed } from 'vue'
const count = ref(0)
const doubled = computed(() => count.value * 2)
</script>
```

### Options API — legacy but still works
```vue
<script>
export default {
  data() { return { count: 0 } },
  computed: { doubled() { return this.count * 2 } },
}
</script>
```

**Use Composition API for new code.** Composition handles complex logic better (reusability via composables; better TypeScript).

## 4. Reactivity primitives

```javascript
import { ref, reactive, computed, watch, watchEffect } from 'vue'

// ref — wraps any value
const count = ref(0)
count.value = 1   // .value to access

// reactive — for objects/arrays (proxy-based)
const user = reactive({ name: 'Alice', age: 30 })
user.age = 31    // no .value

// computed — derived value, cached
const fullName = computed(() => `${user.name} (${user.age})`)

// watch — react to specific changes
watch(count, (newVal, oldVal) => {
  console.log(`count: ${oldVal} → ${newVal}`)
})

// watchEffect — runs immediately + tracks deps automatically
watchEffect(() => {
  console.log('count is', count.value)
})
```

## 5. Directives

```vue
<template>
  <!-- text -->
  <p>{{ message }}</p>
  <p v-text="message"></p>

  <!-- HTML (sanitize first!) -->
  <p v-html="trustedHTML"></p>

  <!-- attribute binding -->
  <img :src="imageUrl" :alt="caption" />

  <!-- event handlers -->
  <button @click="handleClick">Click</button>
  <input @input="onInput" />

  <!-- two-way binding -->
  <input v-model="searchText" />

  <!-- conditional -->
  <p v-if="loggedIn">Welcome</p>
  <p v-else-if="loading">Loading...</p>
  <p v-else>Please log in</p>

  <!-- list rendering -->
  <ul>
    <li v-for="(item, i) in items" :key="item.id">{{ i }} - {{ item.name }}</li>
  </ul>

  <!-- show/hide (toggle display) -->
  <div v-show="visible">...</div>
</template>
```

`v-if` removes/adds to DOM; `v-show` toggles CSS `display`. Use `v-show` when toggling frequently.

## 6. Props + Emits (parent → child → parent)

```vue
<!-- Child.vue -->
<script setup>
const props = defineProps({
  message: { type: String, required: true },
  count: { type: Number, default: 0 },
})

const emit = defineEmits(['update', 'close'])

function handle() {
  emit('update', { newValue: 42 })
}
</script>

<template>
  <p>{{ message }} - {{ count }}</p>
  <button @click="handle">Update</button>
  <button @click="emit('close')">Close</button>
</template>
```

```vue
<!-- Parent.vue -->
<Child :message="hello" :count="5" @update="onUpdate" @close="onClose" />
```

## 7. Slots (component composition)

```vue
<!-- Card.vue -->
<template>
  <div class="card">
    <header><slot name="header" /></header>
    <main><slot /></main>
    <footer><slot name="footer" /></footer>
  </div>
</template>

<!-- Parent -->
<Card>
  <template #header><h2>Title</h2></template>
  <p>Main content</p>
  <template #footer><button>OK</button></template>
</Card>
```

## 8. Composables (the React-hooks equivalent)

```javascript
// composables/useFetch.js
import { ref, onMounted } from 'vue'

export function useFetch(url) {
  const data = ref(null)
  const loading = ref(true)
  const error = ref(null)

  onMounted(async () => {
    try {
      const r = await fetch(url)
      data.value = await r.json()
    } catch (e) {
      error.value = e
    } finally {
      loading.value = false
    }
  })

  return { data, loading, error }
}
```

```vue
<script setup>
import { useFetch } from '@/composables/useFetch'
const { data, loading, error } = useFetch('/api/users')
</script>
```

## 9. Pinia — state management

```javascript
// stores/counter.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubled = computed(() => count.value * 2)
  function increment() { count.value++ }
  return { count, doubled, increment }
})
```

```vue
<script setup>
import { useCounterStore } from '@/stores/counter'
const counter = useCounterStore()
</script>

<template>
  <p>{{ counter.count }} (doubled: {{ counter.doubled }})</p>
  <button @click="counter.increment">+</button>
</template>
```

Pinia replaced Vuex as official state management in 2022.

## 10. Vue Router 4

```javascript
// router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/users/:id', component: () => import('@/views/UserView.vue') },
  ],
})
export default router
```

```vue
<template>
  <RouterLink to="/">Home</RouterLink>
  <RouterView />
</template>
```

## 11. Nuxt 3 / Nuxt 4 (SSR + meta-framework)

Nuxt is to Vue what Next.js is to React. File-based routing, SSR, auto-imports, modules:

```bash
npx nuxi@latest init my-app
cd my-app
npm install
npm run dev
```

`pages/` directory becomes routes. `composables/` auto-imported. `server/api/` for backend endpoints.

## 12. Quick self-check

1. What's the difference between `ref` and `reactive` in Vue 3?
2. When use `v-if` vs `v-show`?
3. What does `<script setup>` give you over a regular `<script>`?
4. What replaced Vuex as official state management?
5. What does Nuxt add over plain Vue?

(Answers: ref wraps any value (use .value), reactive is proxy-based for objects/arrays (direct access); v-if adds/removes from DOM (use for rare toggles), v-show toggles CSS display (use for frequent toggles); concise syntax, no `return`, auto-exposes top-level bindings to template, better TypeScript; Pinia (official since 2022); SSR, file-based routing, auto-imports, server API, module system.)



ewpage


# 52 — NodeJS Backend

## 1. Node.js in 2026

- **Node 22 LTS** (Oct 2024, EOL Apr 2027)
- **Node 24** (current, LTS Oct 2025)
- **Node 26 LTS** (Oct 2026 expected)
- Even-numbered = LTS; odd = current/short-lived

Key recent additions:
- Built-in `--watch` (no nodemon needed)
- Built-in `fetch()` (no node-fetch)
- Built-in test runner (`node:test`)
- WebStreams, WebCrypto
- Native TypeScript stripping (Node 22.6+) — run `.ts` files without compile

## 2. The framework landscape

| Framework | When |
|---|---|
| **Express 4/5** | Still dominant; legacy + simple APIs |
| **Fastify** | Faster than Express; schema-validated; modern |
| **Hono** | Web-standards based; runs anywhere (Bun/Deno/Workers/Node); rising fast |
| **NestJS** | Angular-inspired DI + decorators; enterprise; opinionated |
| **Koa** | Lightweight Express successor (Express team) |
| **tRPC** | Type-safe RPC (TS-only); meta-pattern not framework |
| **GraphQL Yoga / Apollo** | GraphQL servers |

Picking: **Hono** for new projects in 2026; **Fastify** for serious production APIs; **Express** for compatibility with old ecosystem; **NestJS** if you like Java-style DI.

## 3. Minimal Express server

```javascript
import express from 'express'

const app = express()
app.use(express.json())

app.get('/api/users', async (req, res) => {
  res.json({ users: ['Alice', 'Bob'] })
})

app.post('/api/users', async (req, res) => {
  const { name } = req.body
  res.status(201).json({ id: 1, name })
})

app.use((err, req, res, next) => {
  console.error(err)
  res.status(500).json({ error: 'internal' })
})

app.listen(3000, () => console.log('listening on 3000'))
```

## 4. Hono — the modern choice

```javascript
import { Hono } from 'hono'
import { logger } from 'hono/logger'

const app = new Hono()

app.use(logger())

app.get('/api/users', (c) => c.json({ users: ['Alice'] }))

app.post('/api/users', async (c) => {
  const body = await c.req.json()
  return c.json({ id: 1, ...body }, 201)
})

export default app   // works on Node, Bun, Deno, Cloudflare Workers
```

Hono is portable — same code runs on Node, Bun, Deno, Cloudflare Workers, Lambda, edge. That portability is the killer feature.

## 5. HTTP basics every backend dev needs

### Methods
- GET — retrieve (idempotent, cacheable)
- POST — create (not idempotent)
- PUT — replace entirely (idempotent)
- PATCH — partial update (not necessarily idempotent)
- DELETE — remove
- HEAD, OPTIONS, TRACE, CONNECT (rarely)

### Status codes
- 2xx — success (200 OK, 201 Created, 204 No Content)
- 3xx — redirect (301 permanent, 302 found, 304 not modified)
- 4xx — client error (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity, 429 Too Many)
- 5xx — server error (500 Internal, 502 Bad Gateway, 503 Service Unavailable, 504 Gateway Timeout)

### Headers
- `Authorization: Bearer <token>` — JWT/OAuth
- `Content-Type: application/json` — request body type
- `Accept: application/json` — response wanted
- `Cache-Control: no-cache, max-age=0`
- `X-Forwarded-For`, `X-Real-IP` — client IP through proxy
- `Strict-Transport-Security` — HSTS
- `Content-Security-Policy` — CSP

## 6. URL + IP basics

- **URL anatomy**: `https://user:pass@host.example.com:8443/path/to/page?query=value#fragment`
- **IPv4**: 4 octets (1.2.3.4); 2^32 = 4.3B addresses (exhausted)
- **IPv6**: 8 groups of 4 hex (`2001:db8::1`); 2^128 ≈ unlimited
- **Private ranges (RFC1918)**: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- **localhost**: 127.0.0.1 / ::1
- **CIDR**: notation like `10.0.0.0/24` (256 addresses)

## 7. JSON

```javascript
const obj = { name: "Alice", roles: ["admin", "user"], active: true }
const str = JSON.stringify(obj, null, 2)
const parsed = JSON.parse(str)
```

JSON limits:
- No comments
- No trailing commas
- No undefined values (becomes `null` or omitted)
- No `Date` (becomes ISO string)
- No `BigInt`, `Map`, `Set` natively

For richer serialization: MessagePack, Protobuf, CBOR.

## 8. Data exchange between frontend and backend

Patterns:
- **REST** — resource-oriented; HTTP verbs + JSON
- **GraphQL** — query language; one endpoint
- **tRPC** — type-safe RPC for TS apps
- **WebSocket** — bidirectional, real-time
- **SSE** — server → client streaming (LLM-style)
- **gRPC** — internal services; binary; HTTP/2

For new public-facing APIs in 2026: REST + OpenAPI spec, optionally GraphQL for internal-flexibility tools.

## 9. Sample REST endpoint with validation (Zod)

```javascript
import { Hono } from 'hono'
import { zValidator } from '@hono/zod-validator'
import { z } from 'zod'

const app = new Hono()

const createUserSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
})

app.post('/api/users', zValidator('json', createUserSchema), async (c) => {
  const body = c.req.valid('json')
  // body is typed!
  const user = await db.users.create(body)
  return c.json(user, 201)
})
```

Zod schemas validate at runtime + generate TS types automatically.

## 10. Connecting to MongoDB (preview for Module 53)

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient(process.env.MONGO_URL)
await client.connect()
const db = client.db('teamable')

const users = await db.collection('users').find().toArray()
await db.collection('users').insertOne({ name: 'Alice', createdAt: new Date() })
```

## 11. Bun + Deno alternatives

- **Bun** (v1.0 Sept 2023, v1.2 in 2025) — Node-compatible runtime, 3-4x faster start, built-in test runner, bundler, package manager. Use for new projects where you control deployment.
- **Deno** (v1 in 2020, v2 Oct 2024 "Node-compatible") — Secure-by-default, TypeScript-first, built-in tools. Use for security-sensitive isolated scripts.

## 12. Quick self-check

1. What's the current Node.js LTS version?
2. What's Hono's killer feature?
3. What's the difference between PUT and PATCH?
4. What does Zod give you?
5. Why might you choose Bun over Node for a new project?

(Answers: Node 22 (until Apr 2027); portability — same code runs on Node, Bun, Deno, Workers, Lambda, edge; PUT replaces entirely (idempotent), PATCH does partial update; runtime validation + auto-generated TypeScript types from the same schema; 3-4x faster startup, built-in bundler/test/package-manager, less ops overhead.)



ewpage


# 53 — MongoDB + SQL vs NoSQL

## 1. SQL vs NoSQL — the decision framework

| | SQL (relational) | NoSQL |
|---|---|---|
| **Schema** | Strict; defined upfront | Flexible; per-document |
| **Joins** | Native, optimized | Manual; better to denormalize |
| **Transactions** | ACID, native | Limited (improved in 2020s) |
| **Scaling** | Vertical first; horizontal hard | Horizontal-native |
| **Query lang** | Standardized (SQL) | Per-DB |
| **Use case** | Most apps; default 2026 | Specific patterns (event sourcing, sharded scale, flexible schema) |

In 2026: **default is Postgres** for OLTP. NoSQL where Postgres genuinely doesn't fit.

## 2. NoSQL categories

| Category | DBs | Pattern |
|---|---|---|
| **Document** | MongoDB, CouchDB, DynamoDB, Firestore | JSON docs in collections |
| **Key-value** | Redis, DynamoDB, Memcached | Hash table |
| **Wide-column** | Cassandra, ScyllaDB, BigTable, Keyspaces | Row keys + column families |
| **Graph** | Neo4j, Neptune, ArangoDB | Nodes + edges |
| **Time-series** | InfluxDB, TimescaleDB, VictoriaMetrics | Timestamped data |
| **Vector** | Pinecone, Weaviate, Qdrant, Milvus, pgvector | Embeddings + ANN |
| **Search** | Elasticsearch, OpenSearch, Algolia | Full-text + faceting |

## 3. MongoDB at a glance

- **Document database** — stores BSON (binary JSON)
- **Schema-flexible** — documents in a collection can differ
- **Aggregation pipeline** — powerful query language
- **Sharding** native — horizontal scale by shard key
- **Replica sets** for HA
- **Atlas** — managed cloud offering (dominant 2026)
- **Vector Search** built-in (since 2023)

Versions: MongoDB 7.0 (2023), 8.0 (Oct 2024). Atlas runs 7.0+/8.0.

## 4. Basic MongoDB operations

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient('mongodb://localhost:27017')
const db = client.db('teamable')
const users = db.collection('users')

// Create
await users.insertOne({ name: 'Alice', age: 30, roles: ['admin'] })
await users.insertMany([
  { name: 'Bob', age: 25 },
  { name: 'Carol', age: 28 },
])

// Read
const alice = await users.findOne({ name: 'Alice' })
const admins = await users.find({ roles: 'admin' }).toArray()
const adults = await users.find({ age: { $gte: 18 } })
  .sort({ age: -1 }).limit(10).toArray()

// Update
await users.updateOne({ name: 'Alice' }, { $set: { age: 31 } })
await users.updateMany({ active: false }, { $set: { archived: true } })

// Delete
await users.deleteOne({ name: 'Alice' })
await users.deleteMany({ archived: true })

// Aggregation
const pipeline = [
  { $match: { active: true } },
  { $group: { _id: '$department', count: { $sum: 1 }, avgAge: { $avg: '$age' } } },
  { $sort: { count: -1 } },
]
const stats = await users.aggregate(pipeline).toArray()
```

## 5. ACID transactions (since MongoDB 4.0, 2018)

```javascript
const session = client.startSession()
try {
  session.startTransaction()
  await db.collection('accounts').updateOne(
    { _id: from }, { $inc: { balance: -amount } }, { session }
  )
  await db.collection('accounts').updateOne(
    { _id: to }, { $inc: { balance: amount } }, { session }
  )
  await session.commitTransaction()
} catch (e) {
  await session.abortTransaction()
  throw e
} finally {
  session.endSession()
}
```

## 6. Indexes — the performance lever

```javascript
await users.createIndex({ email: 1 }, { unique: true })
await users.createIndex({ createdAt: -1 })
await users.createIndex({ name: 'text' })   // text search
await users.createIndex({ location: '2dsphere' })  // geo
await users.createIndex({ embedding: 'vector', numDimensions: 1536, similarity: 'cosine' })  // vector
```

Without indexes, queries do collection scans → slow.

`explain()` shows the query plan:
```javascript
await users.find({ email: 'alice@example.com' }).explain('executionStats')
```

## 7. Install MongoDB locally

```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
mongosh

# Docker
docker run -d -p 27017:27017 --name mongo mongo:8
mongosh
```

For production: **MongoDB Atlas** (managed cloud) — most teams skip self-hosting entirely.

## 8. Schema design — the doc-store mindset

SQL: normalize. NoSQL: **denormalize where you read**. Example:

### SQL (normalized)
```sql
CREATE TABLE posts (id, user_id, title, body);
CREATE TABLE comments (id, post_id, user_id, body);
CREATE TABLE users (id, name, email);
-- Join 3 tables to render a post page
```

### MongoDB (embedded)
```javascript
{
  _id: ObjectId('...'),
  title: 'Hello',
  body: 'World',
  author: { id: 'u1', name: 'Alice' },          // embedded user
  comments: [                                     // embedded comments
    { author: 'Bob', body: 'Nice', createdAt: ... },
    { author: 'Carol', body: 'Cool', createdAt: ... },
  ],
}
```

Render post page = 1 query. Trade-off: updating Alice's name updates many docs.

Patterns:
- **Embed** when child can't exist without parent + read together
- **Reference** when child is shared / large / changes often
- **Extended reference** — embed some fields, reference for the rest

## 9. SQL vs NoSQL — when each wins

### Postgres wins for:
- Anything with relations + joins
- Strong consistency needs
- Mature transactional workloads
- Reporting / OLAP-lite via partial indexes + materialized views
- **Default for new projects** in 2026

### MongoDB wins for:
- Flexible schema where rows really vary
- Event sourcing
- Real-time data + change streams
- Geospatial heavy
- Time-series within Atlas (TS Collections)

### DynamoDB wins for:
- Massive scale predictable access patterns
- Serverless (pay-per-request)
- Single-digit-ms latency at any scale
- AWS-native

### Redis wins for:
- Cache
- Rate limiting
- Session store
- Pub/sub
- Real-time leaderboards

### Postgres + extensions (the 2026 swiss army):
- pgvector for vector search
- TimescaleDB for time-series
- PostGIS for geo
- Citus for sharding
- JSONB for flexible schema

Postgres-with-extensions covers ~80% of what people used to need NoSQL for.

## 10. Connecting from Node (Teamable backend pattern)

```javascript
import { MongoClient } from 'mongodb'

const client = new MongoClient(process.env.MONGO_URL, {
  serverApi: { version: '1', strict: true, deprecationErrors: true },
})

let dbConnection

export async function connect() {
  if (!dbConnection) {
    await client.connect()
    dbConnection = client.db(process.env.MONGO_DB)
  }
  return dbConnection
}
```

For ORMs: **Mongoose** (Node), **Prisma** (multi-DB), **Drizzle** (TS-first, multi-DB).

## 11. Quick self-check

1. Why is Postgres often the 2026 default for OLTP?
2. What replaced Vuex / Redux-style state in MongoDB's "denormalize where you read" principle?
3. What's an Atlas Vector Search index used for?
4. When use DynamoDB over MongoDB?
5. What's the difference between embedding and referencing in MongoDB schema?

(Answers: relational + ACID + ecosystem + JSONB for flexible schema + pgvector for vector + battle-tested; embed data needed together in one document — read in one query at cost of denormalization; semantic search via embeddings — RAG, recommendations, similar items; massive predictable-access scale + serverless billing model + AWS-native + need for single-digit-ms latency; embed = child stored inside parent (read together, hard to share), reference = child stored separately and parent points to it (share easily, multiple reads).)



ewpage


# 54 — Test Automation — Jest + Vitest + Playwright

## 1. The test pyramid (and its critics)

```
        /\
       /  \    E2E (slow, fragile)        ← 5-10%
      /────\
     /      \  Integration (medium)        ← 20-30%
    /────────\
   /          \ Unit tests (fast, many)    ← 60-70%
  /────────────\
```

Modern critique (Kent C. Dodds: **Testing Trophy**):
```
   Static (TS, eslint)
   ─────────────────
   Unit
   ─────────────────
   Integration   ← most value
   ─────────────────
   E2E
```

The lesson: lots of unit + heavy on integration + a few E2E + lean on static analysis.

## 2. JavaScript testing landscape

| Tool | Use |
|---|---|
| **Jest** | Most-installed; mature; slow startup |
| **Vitest** | Vite-aligned; faster; Jest-compatible API; **dominant for new projects 2026** |
| **Mocha + Chai** | Legacy + composable |
| **Node's built-in `node:test`** | Zero-dep; for simple needs |
| **Bun's built-in test** | Fast; Bun projects only |
| **Playwright** | E2E browser automation |
| **Cypress** | E2E (Playwright is winning the war in 2026) |
| **Testing Library** | DOM testing helpers (works with Jest/Vitest) |
| **MSW** (Mock Service Worker) | HTTP mocking for tests |

## 3. Jest essentials

```javascript
// math.test.js
import { add, multiply } from './math'

describe('add', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })

  test('handles negatives', () => {
    expect(add(-1, 1)).toBe(0)
  })
})

describe('multiply', () => {
  test.each([
    [2, 3, 6],
    [0, 5, 0],
    [-2, 3, -6],
  ])('multiply(%i, %i) = %i', (a, b, expected) => {
    expect(multiply(a, b)).toBe(expected)
  })
})
```

```bash
npx jest
npx jest --coverage
npx jest --watch
```

## 4. Vitest — the modern Jest

```typescript
// math.test.ts
import { describe, test, expect } from 'vitest'
import { add } from './math'

describe('add', () => {
  test('adds two numbers', () => {
    expect(add(2, 3)).toBe(5)
  })
})
```

```bash
npx vitest
npx vitest --coverage
npx vitest --watch    # default — watch mode is the default!
```

Vitest perks:
- Native ESM + TypeScript (no Babel/SWC setup)
- Reuses Vite config (same plugins)
- Browser mode (run tests in real browser)
- UI mode (`vitest --ui`)
- ~2-5x faster than Jest

## 5. Integration tests example (Express + Supertest)

```javascript
import request from 'supertest'
import { describe, test, expect, beforeAll, afterAll } from 'vitest'
import { app, startServer, stopServer } from './app'

describe('GET /api/users', () => {
  beforeAll(() => startServer())
  afterAll(() => stopServer())

  test('returns users list', async () => {
    const res = await request(app).get('/api/users')
    expect(res.status).toBe(200)
    expect(res.body.users).toBeInstanceOf(Array)
  })
})
```

## 6. Mocking HTTP with MSW

```javascript
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { beforeAll, afterAll, afterEach, test, expect } from 'vitest'

const server = setupServer(
  http.get('https://api.example.com/users', () => {
    return HttpResponse.json([{ id: 1, name: 'Alice' }])
  }),
  http.post('https://api.example.com/users', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({ id: 2, ...body }, { status: 201 })
  })
)

beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

test('fetches users', async () => {
  const r = await fetch('https://api.example.com/users')
  const users = await r.json()
  expect(users).toHaveLength(1)
})
```

## 7. E2E with Playwright

```typescript
import { test, expect } from '@playwright/test'

test('user can log in', async ({ page }) => {
  await page.goto('http://localhost:3000/login')
  await page.getByLabel('Email').fill('alice@example.com')
  await page.getByLabel('Password').fill('password')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL('/dashboard')
  await expect(page.getByText('Welcome, Alice')).toBeVisible()
})
```

```bash
npx playwright test
npx playwright test --ui          # interactive
npx playwright test --headed      # show browser
npx playwright codegen            # record interactions to generate test
```

Playwright supports Chromium, Firefox, WebKit. Cross-browser by default.

## 8. Component testing (React/Vue)

```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { test, expect } from 'vitest'
import Counter from './Counter'

test('increments on click', async () => {
  render(<Counter />)
  const button = screen.getByRole('button', { name: '+' })
  await userEvent.click(button)
  await userEvent.click(button)
  expect(screen.getByText('Count: 2')).toBeInTheDocument()
})
```

Testing Library philosophy: test as a user would (find by role/text, not by class name).

## 9. Coverage — meaningful numbers

```bash
npx vitest --coverage
```

Output:
```
File         | % Stmts | % Branch | % Funcs | % Lines
-------------|---------|----------|---------|--------
src/math.ts  |   95.45 |    83.33 |   100.0 |   95.45
src/auth.ts  |   72.00 |    66.67 |   75.00 |   72.00
```

**70-80% is the sweet spot.** Below 60% = inadequate. Above 90% = diminishing returns and brittle tests. Don't chase 100% — it leads to testing implementation details.

## 10. Snapshot testing — caution

```javascript
test('renders correctly', () => {
  const tree = renderer.create(<MyComponent />).toJSON()
  expect(tree).toMatchSnapshot()
})
```

Anti-pattern when overused: snapshots become a wall of un-reviewed text. Use for:
- Stable API responses
- Generated config files
- Visual regression sparingly

Don't use for whole component trees — review fatigue → blind "update snapshots" without reading.

## 11. Property-based testing

```javascript
import { fc, test } from '@fast-check/vitest'

test.prop([fc.integer(), fc.integer()])('add is commutative', (a, b) => {
  expect(add(a, b)).toBe(add(b, a))
})
```

`fast-check` (JS) / `Hypothesis` (Python) — generate random inputs that satisfy a property. Finds edge cases humans miss.

## 12. Quick self-check

1. What's the "Testing Trophy" and how does it differ from the test pyramid?
2. Why is Vitest displacing Jest in 2026?
3. What does MSW do?
4. Why is 100% coverage usually a bad goal?
5. What does property-based testing find that example-based doesn't?

(Answers: heavy on integration + static analysis, lighter on unit/E2E than the pyramid suggests; native ESM + TS, faster, reuses Vite config, browser mode, watch by default; mocks HTTP at the service-worker layer — your fetch calls hit the mock without code changes; leads to testing implementation details and brittle tests with diminishing returns; edge cases generated by random inputs that humans wouldn't have written as examples.)



ewpage


# 55 — Packaging Applications

## 1. What "packaging" means

Producing a deployable artifact:
- **JS/TS app** → bundled JS files + assets (dist/ directory)
- **Python** → wheel (.whl) or container
- **Java** → jar or war
- **Go** → static binary
- **Container** → Docker image (multi-stage)

## 2. JS/TS packaging — Vite

For SPAs:
```bash
npm run build
# produces dist/ — minified, hashed-filename bundles
```

`vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'utils': ['lodash-es', 'date-fns'],
        },
      },
    },
  },
})
```

Output is static files; deploy to any CDN (CloudFront, Cloudflare, Vercel, Netlify).

## 3. NodeJS app packaging

For backend Node apps:
- **Direct deploy** — copy source + `node_modules` to server
- **Docker image** — `npm ci --omit=dev` in builder, copy to slim runtime stage
- **Bundle to single file** — esbuild / ncc; reduces files but rarely necessary
- **Native binary** — `pkg` (deprecated) / `nexe` / `bun build --compile`

The 2026 pattern: container image.

```dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist
USER node
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

## 4. Python packaging

For a library: build a wheel.
For an app: build a container image.

```toml
# pyproject.toml
[project]
name = "my-tool"
version = "1.2.3"
dependencies = ["click>=8.0", "requests>=2.30"]

[project.scripts]
my-tool = "my_tool.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

```bash
uv build         # produces dist/my_tool-1.2.3-py3-none-any.whl
uv publish       # to PyPI / private registry
```

For app: container with `uv` in the build stage.

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
USER 10001
CMD ["python", "-m", "my_app"]
```

## 5. Container image best practices (recap from Module 8)

1. Multi-stage build
2. Pin versions (digest in production)
3. Non-root user
4. `.dockerignore`
5. Cache deps before app code (layer order)
6. Minimal base (distroless / alpine / chainguard)
7. Health check
8. Single concern per container
9. Sign with Cosign
10. Scan with Trivy

## 6. Distroless / Chainguard for security

```dockerfile
FROM python:3.13-slim AS builder
# ... build ...

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /app /app
COPY --from=builder /root/.local /home/nonroot/.local
WORKDIR /app
ENV PATH=/home/nonroot/.local/bin:$PATH
CMD ["main.py"]
```

Or Chainguard images:
```dockerfile
FROM cgr.dev/chainguard/python:latest-dev AS builder
# ... build ...
FROM cgr.dev/chainguard/python:latest
COPY --from=builder /app /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["main.py"]
```

Chainguard images: daily-rebuilt, signed, SBOM-included, mostly CVE-free.

## 7. Running an application from a package

### Node
```bash
node dist/index.js
# Or as a service:
pm2 start dist/index.js --name my-app
# Or as systemd unit:
systemctl start my-app
```

### Python
```bash
python -m my_app
# Or installed CLI:
my-tool --help
```

### Container
```bash
docker run -d --name my-app --restart=unless-stopped \
  -p 80:3000 \
  -e DATABASE_URL=... \
  my-app:1.2.3
```

### Kubernetes
```bash
kubectl set image deployment/my-app app=my-app:1.2.3
```

## 8. Semantic Versioning (semver)

`MAJOR.MINOR.PATCH`:
- **MAJOR** — breaking change
- **MINOR** — new feature, backward-compatible
- **PATCH** — bug fix, backward-compatible

Pre-release: `1.2.3-rc.1`, `2.0.0-alpha.5`
Build metadata: `1.2.3+sha.deadbeef`

In CI:
```bash
VERSION=$(git describe --tags --abbrev=7 --always)
# e.g., v1.2.3 or v1.2.3-5-g0a1b2c3 if commits since tag
```

## 9. Conventional Commits + automated releases

Conventional Commits (https://conventionalcommits.org):
```
feat: add user dashboard
fix: handle null pointer in auth
docs: update README
chore: bump dependencies
feat!: change API contract (breaking)
```

Tools that read these:
- **release-please** (Google) — auto-creates release PRs with bumped versions + changelogs
- **semantic-release** — fully automated; tags + publishes on every merge
- **changesets** (Atlassian) — monorepo-friendly

The pattern: commit → CI parses commit message → determines version bump → creates release.

## 10. SBOM as part of packaging

Generate SBOM during build:
```bash
syft dir:. -o cyclonedx-json > sbom.json
trivy sbom sbom.json   # scan
```

Attach SBOM to release / image:
```bash
cosign attest --predicate sbom.json --type cyclonedx myimage:1.2.3
```

## 11. Quick self-check

1. What does `npm run build` produce in a Vite project?
2. Why use multi-stage Dockerfile?
3. What's the difference between Distroless and Chainguard images?
4. What's a `feat!:` commit in Conventional Commits?
5. Why generate an SBOM as part of the package step?

(Answers: minified hashed-filename bundles in dist/; smaller runtime image, no build tools in deployed image, faster pulls; Distroless is Google project (debian-based, no shell/pkg-mgr), Chainguard is commercial daily-rebuilt distroless-style with SBOM/signing; breaking change — bumps major version under release-please/semantic-release; supply-chain transparency, required for SLSA, evidence for security audits.)



ewpage


# 56 — Linux Server Deployment

## 1. The "deploy to a single VM" reality check

In 2026 most production traffic runs on K8s, but **single-VM deploys are still common** for:
- Small projects / side projects
- Internal tools
- Legacy apps
- Learning + skill-building

The skills you learn here transfer to: Bastion hosts, GitLab runners, monitoring agents, AI training VMs, etc.

## 2. Provisioning Ubuntu 24.04 on cloud

```bash
# AWS
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.small \
  --key-name my-key \
  --security-group-ids sg-0abc \
  --user-data file://bootstrap.sh

# DigitalOcean
doctl compute droplet create my-server \
  --region nyc3 --size s-1vcpu-2gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys 12345

# Linode
linode-cli linodes create --label my-server \
  --image linode/ubuntu24.04 --type g6-nanode-1 --region us-east
```

Ubuntu 24.04 "Noble Numbat" — current LTS, EOL Apr 2029.

## 3. SSH into the server

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<ip>
```

On macOS:
```bash
ssh root@<ip>       # DO uses root
ssh ubuntu@<ip>     # AWS Ubuntu AMI uses ubuntu
ssh ec2-user@<ip>   # AWS Amazon Linux
```

On Windows: use Windows Terminal + OpenSSH (built into Windows 10+).

## 4. Initial hardening (the 8-point checklist)

```bash
# 1. Update everything
sudo apt update && sudo apt upgrade -y

# 2. Create non-root user
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo cp -r ~/.ssh /home/deploy/
sudo chown -R deploy:deploy /home/deploy/.ssh

# 3. Disable root SSH + password auth
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 4. Firewall — UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 5. Unattended security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 6. fail2ban for brute-force protection
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban

# 7. Set timezone
sudo timedatectl set-timezone UTC

# 8. Set hostname
sudo hostnamectl set-hostname my-server.example.com
```

## 5. Reverse proxy — Caddy (the easiest TLS)

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

`/etc/caddy/Caddyfile`:
```
app.example.com {
  reverse_proxy localhost:3000
}

api.example.com {
  reverse_proxy localhost:8000
  encode gzip
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options nosniff
    Referrer-Policy strict-origin-when-cross-origin
  }
}
```

```bash
sudo systemctl reload caddy
```

**Caddy's killer feature: automatic Let's Encrypt TLS.** Add a domain to the Caddyfile + point DNS at the server — TLS just works.

## 6. Reverse proxy — Nginx (more traditional)

```bash
sudo apt install -y nginx
```

`/etc/nginx/sites-available/app`:
```nginx
server {
  listen 80;
  server_name app.example.com;
  location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

For TLS: install `certbot`:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d app.example.com
```

## 7. Run app as systemd service

`/etc/systemd/system/my-app.service`:
```ini
[Unit]
Description=My App
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/my-app
Environment=NODE_ENV=production
EnvironmentFile=/etc/my-app/env
ExecStart=/usr/bin/node /opt/my-app/dist/index.js
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/my-app/data
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now my-app
sudo systemctl status my-app
journalctl -u my-app -f
```

## 8. Docker on Ubuntu (simpler alternative)

```bash
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker deploy
```

Run app:
```bash
docker compose up -d
```

For rootless Docker (better security):
```bash
curl -fsSL https://get.docker.com/rootless | sh
```

## 9. Multi-app deployment patterns

For multiple apps on one VM:
- **Docker Compose** — preferred; isolation + reproducibility
- **Systemd units** — each app a unit
- **Nginx/Caddy** routing to different ports
- **HAProxy** for advanced routing

Discipline: keep apps in `/opt/<app>` with own user; logs to journald; secrets in `/etc/<app>/env` mode 600.

## 10. The "deploy to single VM" vs "deploy to K8s" debate

**VM wins when:**
- < 5 services
- < 100 req/s
- Solo / small team
- No need for autoscaling
- Cost matters (< $50/mo budget)
- Simple, predictable workloads

**K8s wins when:**
- > 10 services
- Autoscaling needed
- Multi-team org
- Compliance/audit requirements
- Already have K8s expertise
- > $200/mo budget anyway

For learning: do both. VM for fundamentals; K8s for scale.

## 11. Modern PaaS alternatives

Skip Linux entirely:
- **Fly.io** — global edge deploy
- **Railway** — Heroku-style PaaS
- **Render** — Heroku-style
- **Vercel** / **Netlify** — frontends + serverless
- **Cloudflare Workers** — edge functions
- **AWS App Runner** — managed container PaaS

For Vatsal's side projects: Fly.io or Railway eliminates 80% of the Linux skills below — but the Linux skills still apply when you SSH into Jenkins agents or AWS instances at work.

## 12. Quick self-check

1. Why disable root SSH login?
2. What's Caddy's killer feature over Nginx?
3. What does systemd's `ProtectSystem=strict` do?
4. What's the difference between Docker and rootless Docker?
5. When does a single VM deploy beat K8s?

(Answers: prevents brute-force on the default username + forces named-user accountability + audit trail; automatic Let's Encrypt TLS just by adding a domain; mounts /usr and /boot read-only for the service — limits attack-driven file modification; rootless runs the daemon as a non-root user — escape from container doesn't give root on host; small service count, predictable load, solo/small team, cost-constrained.)



ewpage


# 57 — Multi-environment Configuration + Secrets

## 1. The 12-factor app principle (Heroku, 2011)

The relevant factors for config:
- **Factor III: Config** — strict separation of config from code. Config in env vars, not files in repo.
- **Factor X: Dev/prod parity** — keep dev, staging, prod as similar as possible.

## 2. Three categories of config

| Category | Examples | Where it lives |
|---|---|---|
| **Non-secret, env-specific** | `LOG_LEVEL=debug`, `DATABASE_URL=...` | Env vars, configmaps |
| **Secret, env-specific** | DB password, API keys | Secrets Manager / Vault |
| **Constants / app config** | feature flags, app version | Config file in repo OR feature-flag service |

## 3. The `.env` file pattern

Local development:
```bash
# .env.local — gitignored
DATABASE_URL=postgresql://localhost/myapp_dev
API_KEY=dev-fake-key
LOG_LEVEL=debug
```

```javascript
// load with dotenv
import 'dotenv/config'
console.log(process.env.DATABASE_URL)
```

```python
# load with python-dotenv
from dotenv import load_dotenv
load_dotenv()
os.environ.get("DATABASE_URL")
```

**Never commit `.env` to Git.** Use `.env.example` with placeholder values to document what's needed:
```
# .env.example — committed
DATABASE_URL=
API_KEY=
LOG_LEVEL=info
```

## 4. Multi-env file pattern (Vite / Next.js)

```
.env                  # all envs (committed if non-secret)
.env.local            # local override (gitignored)
.env.development      # dev only
.env.production       # prod only
.env.production.local # prod local override (gitignored)
```

Precedence (highest wins): `.env.<mode>.local > .env.local > .env.<mode> > .env`.

## 5. Production: env vars from the runtime

| Platform | How env vars get into the app |
|---|---|
| **systemd** | `EnvironmentFile=/etc/app/env` (file mode 600) |
| **Docker Compose** | `environment:` block or `env_file:` in compose.yaml |
| **K8s** | `env:` block in container spec, often from ConfigMap/Secret |
| **AWS Lambda** | Function environment variables |
| **Fly.io / Railway / Render** | Web UI or CLI |
| **GitHub Actions** | `env:` block + `secrets.X` |
| **Jenkins** | Credentials + `withCredentials` |
| **GitLab CI** | CI/CD Variables |

## 6. Secrets backends (recap from Module 35)

In 2026:
1. **AWS Secrets Manager / Azure Key Vault / GCP Secret Manager** — cloud-native
2. **HashiCorp Vault / OpenBao** — multi-cloud
3. **External Secrets Operator** — sync them into K8s
4. **Doppler / Infisical / 1Password Secrets Automation** — developer-friendly SaaS
5. **SOPS** — encrypt-in-repo (when ESO not available)

Anti-patterns:
- `.env` committed to Git ❌
- Secrets in Jenkins job config ❌
- Long-lived API keys ❌
- Same DB password across dev/staging/prod ❌

## 7. Securing MongoDB access (Nana's bootcamp example)

```javascript
// app.js
import { MongoClient } from 'mongodb'

const uri = process.env.MONGO_URL  // mongodb://user:pass@host:port/db
const client = new MongoClient(uri, {
  tls: true,
  tlsCAFile: '/etc/ssl/mongo-ca.pem',
})
```

- Dev: local MongoDB or Atlas free tier with weak creds
- Prod: Atlas + IP allowlist + DB user with **least-privilege role** (`readWrite` on app DB only, not `dbAdmin` or `clusterAdmin`)
- Connection string in Secrets Manager; injected as env var

## 8. Environment-aware code

```javascript
// config.js
const config = {
  database: {
    url: process.env.DATABASE_URL,
    poolSize: parseInt(process.env.DB_POOL_SIZE ?? '10'),
  },
  logging: {
    level: process.env.LOG_LEVEL ?? 'info',
    json: process.env.NODE_ENV === 'production',
  },
  features: {
    newDashboard: process.env.FEATURE_NEW_DASHBOARD === 'true',
  },
}

// validate at startup
if (!config.database.url) {
  throw new Error('DATABASE_URL is required')
}

export default config
```

Validate config at startup; fail fast, not at request time.

## 9. Feature flags (config you want to flip without redeploy)

Tools:
- **LaunchDarkly** — commercial, enterprise default
- **Statsig** — commercial, A/B + flags
- **GrowthBook** — OSS
- **Unleash** — OSS, self-host
- **PostHog** — OSS, includes flags + analytics
- **OpenFeature** — vendor-neutral spec

```javascript
import { ldClient } from './ld'

if (await ldClient.boolVariation('new-checkout', user)) {
  // show new checkout
} else {
  // old checkout
}
```

Flags decouple deploy from release. Critical for trunk-based development at scale.

## 10. Configuration in Kubernetes

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config, namespace: my-app }
data:
  LOG_LEVEL: info
  DB_POOL_SIZE: "20"
  API_BASE_URL: https://api.example.com
---
apiVersion: v1
kind: Secret
metadata: { name: app-secrets, namespace: my-app }
type: Opaque
stringData:
  DATABASE_URL: postgresql://...
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: app, namespace: my-app }
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
          - configMapRef: { name: app-config }
          - secretRef: { name: app-secrets }
```

Secret should come from ESO → cloud Secret Manager, not be committed directly.

## 11. Completing the Sprint (Nana's Jira link)

Wrap-up:
- Mark stories Done when feature shipped + observed in prod
- Run sprint retro
- Update env-config docs if anything changed
- Audit secrets: anything leaked? anything not rotated in 90+ days?

## 12. Quick self-check

1. Why are env vars preferred over config files in repo?
2. Why never commit `.env`?
3. What's the precedence order for Vite's `.env*` files?
4. What's a feature flag and why does it decouple deploy from release?
5. Where should K8s Secrets actually come from in production?

(Answers: 12-factor — config varies between envs but code doesn't — env vars give clean separation + no risk of accidental commit; secrets leak if pushed; `.env.<mode>.local > .env.local > .env.<mode> > .env`; runtime config that can be flipped without code change — feature visible only when flag on so you can deploy code without releasing the feature to users; from cloud Secret Manager via External Secrets Operator — never base64'd into Git.)



ewpage


# 58 — Git for Application Teams

> Cross-link: [Topic 07 — Git, GitHub & DevOps (57 modules)](../07_git_github_devops/) is exhaustive. This module is the **beginner-level Git refresher** Nana includes in her IT Fundamentals course.

## 1. The 10-minute Git mental model

```
Working tree → git add → Staging area → git commit → Local repo → git push → Remote
                                                                       ← git pull ←
```

- **Working tree** — your files on disk
- **Staging area** — what's queued for the next commit
- **Local repo** — commits on your machine
- **Remote** — origin (GitHub/GitLab/etc.)

## 2. Setting up Git for the first time

```bash
git config --global user.name "Vatsal Raicha"
git config --global user.email "vatsal.raicha@gmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase true        # rebase instead of merge on pull
git config --global core.editor "code --wait"

# SSH key for GitHub/GitLab
ssh-keygen -t ed25519 -C "vatsal@laptop"
# Copy public key to GitHub: Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub
```

## 3. Cloning + initializing

```bash
# Clone existing
git clone git@github.com:org/repo.git

# Initialize new
mkdir my-app && cd my-app
git init
git remote add origin git@github.com:org/my-app.git
echo "# my-app" > README.md
git add README.md
git commit -m "initial commit"
git push -u origin main
```

## 4. The daily Git loop

```bash
# Check status
git status

# Pull latest from main
git checkout main
git pull

# Create feature branch
git checkout -b feat/add-login

# Make changes, then:
git add src/login.js
git status         # confirm what's staged
git diff --cached  # review staged diff
git commit -m "feat: add login page"

# Push
git push -u origin feat/add-login

# Open PR on GitHub/GitLab in browser
```

## 5. `.gitignore` (essentials)

```
# Node
node_modules/
dist/
build/
*.log

# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
.DS_Store

# Env / secrets
.env
.env.local
*.pem

# OS
Thumbs.db
```

Use https://gitignore.io to generate one for your stack.

## 6. Resolving merge conflicts

You pull, conflict reported:
```bash
$ git pull
Auto-merging src/auth.js
CONFLICT (content): Merge conflict in src/auth.js
```

Open the conflicted file; you'll see:
```
<<<<<<< HEAD
const apiKey = process.env.API_KEY_NEW
=======
const apiKey = process.env.API_KEY
>>>>>>> origin/main
```

Edit to resolve (pick one, both, or neither), remove the markers, then:
```bash
git add src/auth.js
git commit          # or git rebase --continue if rebasing
```

Use VS Code's built-in merge editor or a dedicated tool (Meld, Beyond Compare).

## 7. Commit message style (Conventional Commits)

```
feat: add user dashboard
fix: handle null email in login
docs: update README
refactor: extract auth helper
test: add user controller tests
chore: bump deps
feat!: change API contract (breaking)
```

The `<type>:` prefix makes commits scannable + parseable by release automation.

## 8. Branching strategies recap

| Strategy | When |
|---|---|
| **GitHub Flow** | Web apps, SaaS, continuous deploy |
| **Trunk-based** | High-velocity teams; feature flags |
| **Git Flow** | Versioned products (declining for SaaS) |

Most modern teams in 2026: GitHub Flow or Trunk-based.

## 9. Pulling changes

```bash
git pull                  # fetch + merge
git pull --rebase         # fetch + rebase (cleaner history)
git fetch origin          # download but don't merge
git fetch --all --prune   # update all + remove deleted branches
```

Set rebase default:
```bash
git config --global pull.rebase true
```

## 10. Branches

```bash
git branch                    # list local
git branch -a                 # list all incl. remote
git checkout -b feat/x        # create + switch
git switch feat/x             # switch (modern)
git switch -c feat/x          # create + switch (modern)
git push -u origin feat/x     # push and track
git branch -d feat/x          # delete local (safe — refuses if unmerged)
git branch -D feat/x          # delete local (force)
git push origin --delete feat/x   # delete remote
```

## 11. Merge Requests / Pull Requests

The MR/PR is the **collaboration unit**. Workflow:
1. Push feature branch
2. Open MR/PR
3. CI runs (tests, lint, security scans)
4. Reviewer comments
5. Address comments; push more commits
6. Approver clicks "Merge" (often with squash)
7. Delete branch

## 12. Deleting branches after merge

```bash
git checkout main
git pull
git branch -d feat/x          # local
# GitHub/GitLab usually auto-deletes remote branch after merge
```

For batch cleanup of merged branches:
```bash
git branch --merged main | grep -v '^\*\|main' | xargs git branch -d
```

## 13. Recovering from mistakes

```bash
# Undo last commit but keep changes staged
git reset --soft HEAD~1

# Undo last commit and changes (DESTRUCTIVE)
git reset --hard HEAD~1

# Reset to a remote state
git reset --hard origin/main

# Recover something from reflog (the safety net)
git reflog
git reset --hard HEAD@{5}
```

Reflog keeps everything for ~90 days — even "lost" commits.

## 14. Quick self-check

1. What's the difference between `git pull` and `git fetch`?
2. What does `git switch` give you over `git checkout`?
3. What's the Conventional Commits format?
4. What's the difference between `-d` and `-D` when deleting a branch?
5. Where's the safety net when you `git reset --hard` by accident?

(Answers: pull = fetch + merge/rebase, fetch only downloads (read-only); clearer intent — switch is for branches, restore is for files (vs checkout doing both confusingly); `<type>(scope)?: subject` with feat/fix/docs/refactor/test/chore types; `-d` refuses to delete unmerged branches, `-D` forces; `git reflog` — keeps every HEAD movement for ~90 days, can `git reset --hard HEAD@{n}` to recover.)



ewpage


# 59 — AI Tools for Engineers in 2026

## 1. The landscape

| Tool | Strength |
|---|---|
| **GitHub Copilot** | Default; broadest install; in-IDE autocomplete; agentic mode (Workspace) |
| **Cursor** | Standalone editor (VS Code fork); fast autocomplete + chat |
| **Windsurf** | Cursor competitor; agentic-first |
| **Claude Code (CLI)** | Vatsal's tool; project-aware coding agent |
| **Claude.ai** | Long-form reasoning + Projects + Skills |
| **Aider** | OSS terminal coding agent |
| **Cline** | OSS VS Code extension agent |
| **Continue** | OSS extension; bring-your-own-model |
| **Replit Agent** | Cloud IDE + agent |
| **Cody** (Sourcegraph) | Code search + AI in big repos |
| **Tabnine** | Privacy-focused autocomplete |

## 2. The three usage modes

### Autocomplete mode (Copilot, Cursor Tab)
Ghost-text completion as you type. Accept with Tab. Best for boilerplate, obvious patterns.

### Chat mode (Cursor Chat, Claude.ai, ChatGPT)
Conversation about code. Best for: "explain this function", "refactor to do X", brainstorming.

### Agentic mode (Claude Code, Cursor Composer, Aider, Cline)
You give a task; the agent reads files, edits, runs commands, iterates. Best for: multi-file changes, prototype generation, refactors.

## 3. GitHub Copilot in 2026

- ~15M paid users (early 2026)
- **Copilot Free** — limited usage
- **Copilot Pro** — $10/mo individual
- **Copilot Business** — $19/user/mo (org)
- **Copilot Enterprise** — $39/user/mo (custom models on org code)
- **Usage-based billing** moving in June 2026 ("AI Credits")

Features:
- Code completions (in-line)
- Chat (in-IDE)
- Copilot Workspace (agentic; web-based)
- Autofix for CodeQL
- PR summaries
- CLI assistance

## 4. Claude Code (Vatsal's daily tool)

Claude Code is the CLI agent:
```bash
claude
# Opens an interactive session in current directory
# Read files, edit, run shell commands, iterate
```

Strengths:
- Full project awareness via `CLAUDE.md`
- Strong reasoning + planning
- Skills + Plugins ecosystem
- Web UI (claude.ai/code) in 2026
- Enterprise GA early 2026

## 5. Cursor — the rising VS Code fork

- ~$20/mo Pro tier
- Built on VS Code; familiar UI
- Built-in chat + agent ("Composer") + Tab completion
- Multi-file edits
- Codebase-wide context (vector-indexed)

The 2026 wave: ~30% of new engineers default to Cursor over VS Code + Copilot.

## 6. The "prompt the agent well" patterns

### Be specific
Bad: "Add login"
Good: "Add a /login route that accepts email + password, validates against the users table, sets a session cookie, redirects to /dashboard on success. Use the existing auth helper in src/lib/auth.ts."

### Reference files
"Look at src/lib/db.ts for the connection pattern; apply the same to src/lib/redis.ts."

### Constrain
"Don't add new dependencies. Don't change the public API. Don't touch tests."

### Verify
"After making changes, run `npm test` and report the output."

### Iterate
Long sessions: break the task into chunks. Ask the agent to plan before executing.

## 7. Generating tests

```
Generate unit tests for src/lib/auth.ts using Vitest.
- Cover login, logout, refreshToken
- Include edge cases: expired token, invalid signature, missing email
- Use MSW to mock the API
- Aim for 80% line coverage
```

AI-generated tests need review:
- Verify they actually test the intended behavior
- Don't accept tests that just snapshot whatever the function returns
- Run them; confirm they fail when you break the code

## 8. Generating documentation

```
Read src/lib/auth.ts. Generate a README section explaining:
- The auth flow (3 sentences)
- How to use the public functions
- Common errors and how to handle them
Match the style of existing READMEs in this repo.
```

## 9. Troubleshooting + debugging

```
This test is failing intermittently. Look at the test output + the function. What hypotheses do you have? Don't fix yet — list the top 3 candidates.
```

Force the agent to enumerate hypotheses before committing to a fix. Reduces "I think I fixed it" without root cause.

## 10. Generating automation scripts

Great use case:
```
Write a Python script that:
- Reads all .yaml files in ./manifests/
- Sets `resources.requests.cpu` to "100m" if missing
- Writes the files back
- Reports a summary of changes
```

Or:
```
Write a bash script that runs Trivy on every Docker image in our registry and posts results to DefectDojo.
```

These tasks are well-bounded; AI gets them mostly right + you review.

## 11. Limits + risks

**Verify everything**:
- API signatures (Copilot will invent methods)
- Library versions
- Security-sensitive code (auth, crypto, file ops)
- Anything where wrong-without-knowing is costly

**Don't paste secrets into chat models** — even though many vendors say "we don't train on your data," operationally treat the chat surface as untrusted. Use enterprise tiers with data residency / no-train clauses for sensitive work.

**Atrophy risk** — relying entirely on autocomplete can erode fundamentals. Periodically write code from scratch without AI to stay sharp.

## 12. Governance for AI tools (enterprise angle)

For Capital One / regulated finance:
- **Approved vendor list** — only enterprise tiers with DPA + no-train guarantees
- **Air-gap / private deployment** for sensitive repos (Copilot Enterprise + custom models, Claude Code Enterprise)
- **Data classification** — what can be sent to AI tools (no PII, no card data, no SR 11-7 model code)
- **Audit logs** of AI tool usage (prompts + outputs in regulated repos)
- **Code review** by humans for AI-generated security-critical code

See [Topic 07 Module 55](../07_git_github_devops/55_ai_governance_privacy.md) for the deep dive.

## 13. Quick self-check

1. What's the difference between autocomplete, chat, and agentic AI modes?
2. Why is Cursor a serious challenger to VS Code + Copilot?
3. Why force the agent to enumerate hypotheses before fixing a bug?
4. What's the atrophy risk with AI tools?
5. What enterprise governance applies to AI dev tools in regulated finance?

(Answers: autocomplete = ghost-text inline, chat = conversation about code, agentic = give task and AI executes multi-step with file edits + shell; built on VS Code so familiar + tight integration of Tab + Chat + Composer + codebase-wide context; reduces premature fixes that look right but miss root cause; relying on autocomplete erodes fundamentals — periodically write code without AI; approved vendor list, enterprise tiers with no-train, data classification, audit logs, human review of AI-generated security code.)



ewpage


# 60 — CKA Exam — Logistics, Domain Weights, 2025 Changes

## 1. The CKA exam (current as of 2026-05)

| Property | Value |
|---|---|
| **Vendor** | CNCF + Linux Foundation; delivered via PSI |
| **Cost** | $445 USD (was $395 for years; raised 2024) |
| **Format** | Browser-based hands-on, 2 hours |
| **Tasks** | 15-20 hands-on K8s tasks |
| **Passing score** | 66% |
| **Retake** | 1 free retake included with voucher |
| **Voucher validity** | 12 months from purchase |
| **Cert validity** | 24 months |
| **K8s version** | v1.30+ (tracks GA Kubernetes releases) |

## 2. The 2024-2025 redesign

Sept 2024: CKA exam refresh. Key changes:
- Killer.sh simulator updated
- Allowed docs: kubernetes.io (full) + kubernetes.io/blog + github.com/kubernetes
- More multi-cluster tasks
- More CRI/CNI troubleshooting
- Less "from scratch" cluster builds (more pre-built scenarios you debug)

## 3. Domain weights (2025)

| Domain | Weight | What it tests |
|---|---|---|
| **Storage** | **10%** | PV/PVC/SC, volume types, access modes |
| **Troubleshooting** | **30%** | The biggest single domain — node failures, pod failures, networking, kubectl/kubelet issues |
| **Workloads and Scheduling** | **15%** | Deployments, scheduling, ConfigMap/Secret, scaling, rolling update |
| **Cluster Architecture, Installation, and Configuration** | **25%** | kubeadm, RBAC, HA, upgrades, etcd backup |
| **Services and Networking** | **20%** | Services, Ingress, NetworkPolicy, DNS, CoreDNS |

**Strategy implication:** Troubleshooting + Install/Config = 55%. Master kubectl debugging + kubeadm + etcd + RBAC. Storage is the smallest (10%) — don't over-invest.

## 4. The exam environment

- Provided browser terminal (GNOME Terminal + Firefox + xdotool)
- Six pre-existing clusters; you switch between them per task
- Each task tells you: "use cluster `k8s` and run on `controlplane01`"
- `kubectl` configured; `kubectl-config` to switch contexts
- Allowed: kubernetes.io tabs in Firefox

## 5. The 2-hour time pressure

15-20 tasks in 120 minutes = **~6-7 min/task average**. Discipline:
- **Skip tasks > 10 min** — flag for return; don't get stuck
- **Imperative kubectl** for speed — `kubectl run`, `kubectl create`, `kubectl expose`
- **`--dry-run=client -o yaml`** to scaffold then customize
- **Aliases + completion** set in shell:
  ```bash
  alias k=kubectl
  source <(kubectl completion bash)
  complete -F __start_kubectl k
  export do='--dry-run=client -o yaml'
  ```
- **Trust the kubernetes.io docs** — find what you need fast; don't try to remember everything

## 6. The 8-week prep plan

### Weeks 1-2: Core concepts
- Watch Mumshad Mannambeth's CKA course (Udemy) or KodeKloud
- Topics 5 modules 16-25 + this Part 5
- Build a kind/minikube cluster locally
- Drill kubectl basics

### Weeks 3-4: Storage, Networking, RBAC
- PV/PVC/SC walkthroughs
- NetworkPolicy practice
- RBAC scenarios (create user → role → binding → test)
- CoreDNS troubleshooting

### Weeks 5-6: Cluster lifecycle
- kubeadm from scratch (3 VMs on cloud)
- etcd backup + restore drills (do 10+)
- Cluster upgrade drill
- Certificate renewal

### Weeks 7-8: Mock exams + speed
- **Killer.sh** (2 free sessions with voucher) — harder than real exam
- **KillerCoda** scenarios (free, in-browser)
- **KodeKloud labs** if you have access
- Re-do mocks until consistently > 80%
- Practice imperative kubectl + `dry-run=client -o yaml`

## 7. Free resources

- **kubernetes.io docs** — your friend during the exam
- **KillerCoda** (https://killercoda.com) — free interactive scenarios
- **KodeKloud** (free tier; paid for full labs)
- **CNCF tutorials**
- **K8s the Hard Way** (Kelsey Hightower) — too deep for CKA but solid foundation
- **Mumshad Mannambeth's Udemy course** — gold standard, ~$15 on sale

## 8. Paid resources

- **KodeKloud Pro** (~$25-40/mo) — labs aligned with CKA
- **Killer.sh extra sessions** — $40 each beyond the 2 free
- **A Cloud Guru CKA** — comparable to KodeKloud
- **Linux Foundation LFS258** (course bundled with cert often) — $499

## 9. Differences between CKA, CKAD, CKS

| | CKA | CKAD | CKS |
|---|---|---|---|
| **Audience** | Cluster admin | App developer | Security engineer |
| **Prereq** | None | None | CKA |
| **Cost** | $445 | $445 | $445 |
| **Focus** | Build + manage cluster | Build + deploy apps | Hardening + threat detection |
| **Order** | Take first | Take alongside CKA | Take last (after CKA) |

For Vatsal (AI/ML eng at Capital One): **CKA first**. CKAD overlaps too much with day-job; CKS is the natural next step after CKA + 6mo.

## 10. Exam-day strategy

1. **Read every task fully** before starting work on it
2. **Confirm context**: `kubectl config use-context <name>`
3. **Confirm namespace**: `--namespace=<ns>` or `kubens <ns>`
4. **Start imperative**: `kubectl create ... --dry-run=client -o yaml | kubectl apply -f -`
5. **Verify**: `kubectl get ... -o wide` after each task
6. **Flag + skip** if > 10 min stuck
7. **Return to flagged tasks** in last 20 min
8. **Save snapshots**: many tasks build on prior tasks; commit changes
9. **Read the task description carefully** — the wording usually reveals the expected approach

## 11. The morning before

- Hydrate, eat carbs, no caffeine excess
- Test webcam + browser + room scan
- Have ID ready (passport preferred)
- Quiet room, clear desk, no notes
- Charge laptop + backup power

## 12. Quick self-check

1. What's the CKA passing score?
2. Which domain is the biggest weight on the CKA?
3. What two free Killer.sh sessions come with the voucher?
4. What's the prerequisite for CKS?
5. Which alias should you set first when you open the exam terminal?

(Answers: 66%; Troubleshooting at 30%; the simulator sessions — harder than real exam by design; CKA must be passed first; `alias k=kubectl` + completion + `export do='--dry-run=client -o yaml'`.)



ewpage


# 61 — K8s Core Concepts (CKA Refresher)

> Cross-link: [Topic 05 Module 16 — K8s architecture](../05_docker_kubernetes/16_k8s_architecture.md) and [Module 11](11_k8s_overview.md) of this topic. This module is the **CKA-exam-shaped refresher** of the essentials.

## 1. The architecture (control plane + nodes)

```
Control Plane (manage cluster state):
- kube-apiserver — REST API (only thing talking to etcd)
- etcd — distributed KV store; the source of truth
- kube-scheduler — assigns pods to nodes
- kube-controller-manager — runs controllers (deployment, replicaset, etc.)
- cloud-controller-manager (cloud) — talks to cloud APIs

Worker Node (run pods):
- kubelet — node agent; receives pod specs; tells runtime to start containers
- container runtime — containerd / CRI-O
- kube-proxy — implements Service IPs via iptables/IPVS/nftables
```

## 2. The objects (and what tests them)

| Object | CKA tasks |
|---|---|
| Pod | scheduling, troubleshooting |
| Deployment | rolling update, rollback, scale |
| StatefulSet | ordered start, stable identity |
| DaemonSet | one-pod-per-node tasks |
| Job / CronJob | run-to-completion |
| Service | networking, ClusterIP/NodePort/LoadBalancer |
| Ingress | host/path routing, TLS |
| ConfigMap / Secret | env + volume injection |
| PV / PVC / StorageClass | storage tasks |
| RBAC (Role/ClusterRole/RoleBinding) | access control |
| ServiceAccount | identity inside cluster |
| NetworkPolicy | pod-level firewall |
| Namespace | isolation |

## 3. kubectl + config file

```bash
# Where kubectl looks
echo $KUBECONFIG          # if set, this path
# else
~/.kube/config

# View config
kubectl config view
kubectl config get-contexts
kubectl config current-context
kubectl config use-context my-cluster
```

The kubeconfig has 3 sections:
- **clusters** — cluster endpoints + CA certs
- **users** — credentials (cert / token / exec)
- **contexts** — combinations of (cluster, user, namespace)

## 4. The minimal K8s YAML object

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:1.27-alpine
```

Every object has:
- `apiVersion` — group/version (e.g., `v1`, `apps/v1`, `networking.k8s.io/v1`)
- `kind` — type
- `metadata` — name, namespace, labels, annotations
- `spec` — desired state
- `status` — current state (set by controllers, you don't write this)

## 5. YAML basics for the exam

```yaml
# Scalars
name: nginx
count: 3
ready: true
note: "quoted string"

# Lists (block + flow)
items:
  - a
  - b
items: [a, b, c]

# Maps (block + flow)
labels:
  app: web
  tier: frontend
labels: {app: web, tier: frontend}

# Multiline string
script: |
  set -e
  echo "hello"
  date

# Folded
description: >
  This is a
  long sentence on
  one line
```

For exam: master indentation discipline (2 spaces, consistent). YAML errors waste minutes.

## 6. The kubectl shortcuts the exam expects you to know

```bash
k get pods                           # list
k get pods -o wide                   # more
k get pods -A                        # all namespaces
k get pods -o yaml                   # YAML output
k get pods -o json                   # JSON
k get pods -o jsonpath='{.items[*].metadata.name}'
k describe pod <name>                # events + spec
k logs <pod>                         # logs
k logs -f <pod> -c <container>       # follow
k exec -it <pod> -- bash             # shell
k run debug --rm -it --image=alpine -- sh   # ephemeral debug pod

# Imperative create + dry-run scaffold
k create deployment web --image=nginx --replicas=3 --dry-run=client -o yaml > web.yaml
k create service clusterip web --tcp=80:80 --dry-run=client -o yaml
k create role app-reader --verb=get,list --resource=pods --dry-run=client -o yaml
k create rolebinding app-reader-binding --role=app-reader --serviceaccount=default:default --dry-run=client -o yaml
k create configmap app-config --from-literal=LOG_LEVEL=info --dry-run=client -o yaml
k create secret generic db-creds --from-literal=password=secret --dry-run=client -o yaml
k create cronjob hello --image=busybox --schedule="*/1 * * * *" -- /bin/sh -c "date"

# Edit live
k edit deployment web                # opens YAML in $EDITOR; live-applies on save
k scale deployment web --replicas=5
k rollout status deployment web
k rollout history deployment web
k rollout undo deployment web --to-revision=2

# Apply / delete
k apply -f file.yaml
k apply -f directory/
k delete -f file.yaml
k delete pod <name> --grace-period=0 --force      # force delete stuck pod

# Find things
k get pods --selector app=web                     # by label
k get pods -l app=web,tier=frontend
k get pods --field-selector status.phase=Running

# Resource inspection
k api-resources                                    # all resource kinds
k explain pod.spec.containers.livenessProbe       # docs
```

## 7. Labels + selectors

```yaml
metadata:
  labels:
    app: web
    tier: frontend
    version: v1
```

```bash
kubectl get pods -l app=web                       # equality
kubectl get pods -l 'tier in (frontend,backend)'  # set
kubectl get pods -l 'app=web,!cache'              # not
```

Labels drive: Deployment → ReplicaSet → Pod selection, Service → Pod selection, NetworkPolicy targets.

## 8. Namespaces

```bash
k get namespaces
k get ns
k create ns my-app
k delete ns my-app                                # deletes everything in ns

# Set default namespace for kubectl
k config set-context --current --namespace=my-app
```

Built-in namespaces:
- `default` — everything you don't specify
- `kube-system` — control plane components
- `kube-public` — readable by all (rarely used)
- `kube-node-lease` — node heartbeat data

## 9. Common Pod fields

```yaml
spec:
  containers:
  - name: app
    image: my-app:1.2.3
    imagePullPolicy: IfNotPresent          # Always | IfNotPresent | Never
    command: ["python"]
    args: ["-m", "my_app"]
    ports:
    - containerPort: 8000
    env:
    - name: DATABASE_URL
      value: postgresql://...
    - name: API_KEY
      valueFrom:
        secretKeyRef: { name: secrets, key: api-key }
    resources:
      requests: { cpu: "100m", memory: "128Mi" }
      limits:   { cpu: "500m", memory: "256Mi" }
    livenessProbe:
      httpGet: { path: /healthz, port: 8000 }
      initialDelaySeconds: 30
    readinessProbe:
      httpGet: { path: /readyz, port: 8000 }
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    emptyDir: {}
  restartPolicy: Always
  serviceAccountName: my-app-sa
```

## 10. The "show me what's in there" workflow

When you don't remember the syntax:
```bash
k explain deployment.spec.template.spec.containers
k explain pod.spec.containers.lifecycle
k explain ingress.spec.rules
k api-resources                # all resource short names + groups
k api-versions                 # available API versions
```

Use this constantly during the exam.

## 11. Quick self-check

1. What's the only component that talks to etcd?
2. What's the difference between `apiVersion: v1` and `apiVersion: apps/v1`?
3. What does `kubectl config use-context` do?
4. What's `kubectl explain pod.spec.containers.livenessProbe` for?
5. What's the difference between `imagePullPolicy: Always` and `IfNotPresent`?

(Answers: kube-apiserver — all other components go through it; v1 is the core API group, apps/v1 is the apps group (Deployment, StatefulSet, etc.); switches the active context — which cluster + user + default namespace kubectl uses; offline help — shows the schema for any nested field; Always re-pulls every time even if cached, IfNotPresent only pulls if image not local — use IfNotPresent for stable tags, Always when using `latest` (which you shouldn't in production).)



ewpage


# 62 — Build K8s Cluster from Scratch (kubeadm + containerd + Cilium)

## 1. Why this matters for CKA

Building a cluster from scratch is **the** Cluster Architecture + Install + Configuration exam topic (25% of the exam). You won't build a full cluster on exam day, but you will:
- Initialize a control plane with kubeadm
- Join worker nodes
- Configure CRI (containerd)
- Install a CNI (Cilium / Calico / Flannel)
- Troubleshoot when any step fails

## 2. The provisioning prerequisites

For a 3-node lab (1 control + 2 workers):
- 3 VMs (Ubuntu 24.04, ≥ 2 vCPU, ≥ 2GB RAM)
- Network connectivity between them
- Unique hostnames
- Swap disabled (kubelet requires)
- Kernel modules + sysctls configured

## 3. AWS quick provisioning (3 EC2 instances)

```bash
# Create SG allowing K8s ports
aws ec2 create-security-group --group-name k8s-lab --description "K8s lab"
aws ec2 authorize-security-group-ingress --group-name k8s-lab --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name k8s-lab --protocol -1 --source-group k8s-lab

# Launch 3 instances
aws ec2 run-instances --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium --count 3 \
  --key-name my-key --security-groups k8s-lab \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=k8s-lab}]'
```

Cost trick: **stop instances when not learning** ($0/hour stopped; only pay for EBS storage ~$3/mo per disk).

## 4. Prepare each node (run on ALL 3)

```bash
# Disable swap permanently
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl for K8s networking
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system
```

## 5. Install containerd (CRI)

```bash
sudo apt update
sudo apt install -y containerd

sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Use systemd cgroup driver (matches kubelet)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd
```

## 6. Install kubeadm + kubelet + kubectl

```bash
# Add Kubernetes apt repo (v1.31 example — match exam version)
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gpg

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
  https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl   # prevent auto-upgrade

# Enable kubelet
sudo systemctl enable kubelet
```

## 7. Initialize control plane (on controlplane01)

```bash
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=<control-plane-ip>
```

Output ends with:
```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join <ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

Run the user-config commands. Verify:
```bash
kubectl get nodes
# control-plane01   NotReady   control-plane   2m   v1.31.x
# (NotReady is correct — no CNI yet)
```

## 8. Install CNI (Cilium recommended)

```bash
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
curl -L --fail --remote-name-all "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}"
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

cilium install --version 1.16.0
cilium status --wait
```

Alternative: **Calico** (still widely used):
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

Or **Flannel** (simpler, for labs):
```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

After CNI install, node should become Ready:
```bash
kubectl get nodes
# control-plane01   Ready   control-plane   5m   v1.31.x
```

## 9. Join worker nodes

On each worker, run the `kubeadm join` command from step 7. If you lost it:
```bash
# On control plane
kubeadm token create --print-join-command
```

After joining, on control plane:
```bash
kubectl get nodes
# control-plane01   Ready   control-plane   10m   v1.31.x
# worker01          Ready   <none>          1m    v1.31.x
# worker02          Ready   <none>          1m    v1.31.x
```

## 10. Common gotchas

- **Swap not disabled** → kubelet won't start
- **`net.bridge.bridge-nf-call-iptables` not set** → pod networking broken
- **Mismatched containerd cgroup driver** → kubelet errors; both must be `systemd`
- **kubeadm join fails** → token expired (24hr default); regenerate
- **Pods stuck Pending** → no CNI installed yet (Ready won't happen)
- **CoreDNS Pending** → no CNI; install one

## 11. The `kube-system` namespace (what's running)

```bash
kubectl get pods -n kube-system
# coredns-...               2/2 Running
# etcd-controlplane01       1/1 Running
# kube-apiserver-...        1/1 Running
# kube-controller-mgr-...   1/1 Running
# kube-proxy-...            1/1 Running (DaemonSet)
# kube-scheduler-...        1/1 Running
# cilium-...                1/1 Running (DaemonSet)
# cilium-operator-...       1/1 Running
```

These are **static pods** for the control plane (managed by kubelet directly via `/etc/kubernetes/manifests/`) + the CNI pods.

## 12. Networking in K8s — the conceptual model

K8s requires:
1. Every pod gets a unique IP (no NAT between pods)
2. Pods on same node can communicate
3. Pods on different nodes can communicate (no NAT)
4. Pods see themselves at the same IP others see

The CNI plugin implements this. Pod CIDR (`10.244.0.0/16` above) is the address space. Each node gets a /24 from this, allocates /32s to pods.

## 13. Quick self-check

1. Why must swap be disabled before installing kubeadm?
2. What does `kubeadm init` write to `/etc/kubernetes/`?
3. Why does the control-plane node show NotReady right after init?
4. Why must containerd cgroup driver match kubelet?
5. What does the CNI plugin provide that kubeadm doesn't?

(Answers: kubelet refuses to start with swap on because of QoS guarantees + scheduling assumptions; admin.conf (kubeconfig), pki/ (certs), manifests/ (static pod manifests for control plane); no CNI = no pod networking = node not Ready; cgroups inconsistency → kubelet can't manage containers correctly; pod networking — IPAM + routing across nodes — kubeadm doesn't include this.)



ewpage


# 63 — Deployments, Services & DNS

## 1. Deploying nginx (the canonical exam example)

```bash
# Imperative
k create deployment nginx --image=nginx:1.27-alpine --replicas=3

# Or scaffold YAML + edit
k create deployment nginx --image=nginx:1.27-alpine --replicas=3 \
  --dry-run=client -o yaml > nginx-deploy.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: nginx }
spec:
  replicas: 3
  selector: { matchLabels: { app: nginx } }
  template:
    metadata: { labels: { app: nginx } }
    spec:
      containers:
      - name: nginx
        image: nginx:1.27-alpine
        ports: [{ containerPort: 80 }]
        resources:
          requests: { cpu: "50m", memory: "32Mi" }
          limits:   { cpu: "200m", memory: "128Mi" }
```

```bash
k apply -f nginx-deploy.yaml
k get deploy,rs,pods                # Deployment + ReplicaSet + Pods
```

## 2. The Deployment → ReplicaSet → Pod hierarchy

```
Deployment (rolling-update controller)
   └── ReplicaSet (maintains N replicas)
        └── Pod (× N)
```

Deployment manages multiple ReplicaSets during rolling updates (old + new versions coexist briefly).

## 3. Creating an nginx Service

```bash
k expose deployment nginx --port=80 --target-port=80 --name=nginx-svc
# Creates ClusterIP Service
```

```yaml
apiVersion: v1
kind: Service
metadata: { name: nginx-svc }
spec:
  selector: { app: nginx }
  ports:
  - port: 80          # Service port
    targetPort: 80    # Container port
    protocol: TCP
  type: ClusterIP     # internal-only
```

Service types:
- **ClusterIP** (default) — internal only
- **NodePort** — exposes on every node at port 30000-32767
- **LoadBalancer** — provisions cloud LB
- **ExternalName** — DNS CNAME alias

## 4. Labels — the glue

Service selects Pods by label:
```yaml
spec:
  selector:
    app: nginx     # matches Pods with `metadata.labels.app: nginx`
```

If labels don't match, Service has no endpoints:
```bash
k get endpoints nginx-svc
# nginx-svc   <none>   <none>      # zero endpoints — selector mismatch
```

Debug:
```bash
k get pods --show-labels
k get svc nginx-svc -o yaml | grep -A 3 selector
```

## 5. Scaling Deployments

```bash
k scale deployment nginx --replicas=5
k get deploy nginx                  # READY 5/5

# Auto-scaling (HPA)
k autoscale deployment nginx --min=3 --max=10 --cpu-percent=70
k get hpa
```

HPA requires metrics-server installed.

## 6. Recording commands (legacy `--record` is deprecated)

To track which command made which rollout:
```bash
# Old (deprecated)
k set image deployment/nginx nginx=nginx:1.28-alpine --record

# Modern (use annotations)
k annotate deployment/nginx \
  kubernetes.io/change-cause="upgrade to 1.28" --overwrite
k set image deployment/nginx nginx=nginx:1.28-alpine
```

View history:
```bash
k rollout history deployment nginx
k rollout history deployment nginx --revision=2
```

## 7. Connecting to a Pod

```bash
# Exec into running pod
k exec -it <pod-name> -- bash

# Port forward (local 8080 → pod 80)
k port-forward pod/<pod-name> 8080:80
# Or to Service
k port-forward svc/nginx-svc 8080:80
# Browse http://localhost:8080

# Run an ephemeral debug pod
k run debug --rm -it --image=alpine -- sh

# From inside the cluster (debug pod)
apk add curl
curl http://nginx-svc:80
curl http://nginx-svc.default.svc.cluster.local:80
```

## 8. DNS basics in Kubernetes

K8s has built-in DNS (CoreDNS in kube-system). The naming convention:
```
<service>.<namespace>.svc.cluster.local
```

Resolution patterns:
- Same namespace: `nginx-svc` (short form)
- Cross-namespace: `nginx-svc.production` (mid form)
- Fully qualified: `nginx-svc.production.svc.cluster.local`

For pods (with stable hostname via subdomain):
```
<pod-hostname>.<service>.<namespace>.svc.cluster.local
```

This is how StatefulSets get stable network identity per replica.

## 9. CoreDNS

```bash
k get pods -n kube-system | grep coredns
# coredns-...   Running

# CoreDNS config
k get configmap coredns -n kube-system -o yaml
```

The default Corefile:
```
.:53 {
    errors
    health { lameduck 5s }
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
    }
    prometheus :9153
    forward . /etc/resolv.conf {
        max_concurrent 1000
    }
    cache 30
    loop
    reload
    loadbalance
}
```

Common exam task: a pod can't resolve `nginx-svc.production`. Debug:
```bash
k exec -it debug-pod -- nslookup nginx-svc.production
k get svc -n production           # confirm svc exists
k get endpoints -n production nginx-svc   # confirm has endpoints (labels match?)
k get pods -n kube-system -l k8s-app=kube-dns   # CoreDNS running?
k logs -n kube-system -l k8s-app=kube-dns       # CoreDNS errors?
```

## 10. Configuring Service IP address (ClusterIP range)

The control plane allocates ClusterIPs from `--service-cluster-ip-range` (default `10.96.0.0/12`). Configured via kubeadm config.

You can also set a specific IP per Service:
```yaml
spec:
  clusterIP: 10.96.0.100
```

Useful only for static-IP services with external dependencies. Otherwise let K8s allocate.

## 11. kubectl pro tips (exam-time speedups)

```bash
# Output format options
k get pods -o wide
k get pods -o yaml
k get pods -o jsonpath='{.items[*].metadata.name}'
k get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase
k get pods --sort-by=.metadata.creationTimestamp

# Field selectors (not selectors on labels — different namespace)
k get pods --field-selector=status.phase=Running
k get pods --field-selector=spec.nodeName=worker01

# Multiple resources
k get deployments,services,pods

# Watch
k get pods --watch
k get pods -w

# All namespaces
k get pods -A

# Show resource quotas + limits
k describe ns my-app
k get resourcequotas -A
k get limitranges -A

# Save bash history
history > ~/exam-history.txt
```

## 12. Quick self-check

1. What's the Deployment → ReplicaSet → Pod hierarchy and what does each do?
2. What's a Service selector and what makes a Service have zero endpoints?
3. What's the FQDN format for a K8s Service?
4. What ConfigMap holds CoreDNS configuration?
5. What's the difference between `--selector` and `--field-selector` in kubectl?

(Answers: Deployment manages rolling updates, ReplicaSet maintains N replicas, Pod is the actual unit; label-based query that picks Pods to forward traffic to — zero endpoints when selector labels don't match any pod's labels; `<service>.<namespace>.svc.cluster.local`; coredns ConfigMap in kube-system namespace; --selector matches `metadata.labels`, --field-selector matches built-in fields like `status.phase` or `spec.nodeName`.)



ewpage


# 64 — External Services — NodePort, LoadBalancer, Ingress

## 1. Three ways to expose a Service externally

| Type | How | When |
|---|---|---|
| **NodePort** | Opens port 30000-32767 on every node | Dev/test; not for production |
| **LoadBalancer** | Cloud provisions external LB | Cloud K8s; one LB per Service |
| **Ingress** | HTTP/L7 routing via Ingress Controller | Many services share one LB; host/path routing |

## 2. NodePort

```yaml
apiVersion: v1
kind: Service
metadata: { name: web }
spec:
  selector: { app: web }
  type: NodePort
  ports:
  - port: 80           # ClusterIP port
    targetPort: 80     # Container port
    nodePort: 30080    # Optional; auto-allocated 30000-32767 if omitted
```

Access from outside: `http://<any-node-ip>:30080`.

Drawbacks:
- Limited port range
- Direct node IPs exposed
- No L7 routing
- Cumbersome at scale

## 3. LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata: { name: web }
spec:
  selector: { app: web }
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
```

On cloud K8s (EKS/GKE/AKS): provisions a cloud LB (NLB/ALB on AWS, GCP LB on GCP). On bare-metal K8s: stuck in Pending unless you install **MetalLB**.

Get the assigned IP:
```bash
k get svc web
# NAME   TYPE          CLUSTER-IP    EXTERNAL-IP     PORT(S)
# web    LoadBalancer  10.96.0.42    1.2.3.4         80:30123/TCP
```

Cost reality: one cloud LB per Service. 30 Services = 30 LBs = $$$. Hence Ingress.

## 4. Ingress + Ingress Controller

Ingress is an *abstract* HTTP routing rule. An **Ingress Controller** (Nginx, Traefik, HAProxy, AWS ALB Controller, GCP GLBC) implements it.

### Install Nginx Ingress Controller
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace
```

This creates a single LoadBalancer Service for the controller; all your Ingress rules share it.

### Ingress object
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port: { number: 80 }
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port: { number: 8000 }
  tls:
  - hosts: [app.example.com]
    secretName: app-tls
```

## 5. The Ingress → Service → Pod chain

```
Client → DNS → cloud LB (Ingress Controller) → routes by host/path → Service (ClusterIP) → Pods
```

## 6. cert-manager — automatic TLS

```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

Configure a ClusterIssuer:
```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef: { name: letsencrypt-prod-pk }
    solvers:
    - http01:
        ingress: { ingressClassName: nginx }
```

Annotate Ingress:
```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts: [app.example.com]
    secretName: app-tls           # cert-manager will create this Secret
```

cert-manager issues + renews automatically.

## 7. Gateway API — the Ingress replacement (GA 2024)

K8s Gateway API (https://gateway-api.sigs.k8s.io) is the **modern replacement for Ingress**, GA in K8s 1.31 (Aug 2024).

Three CRDs:
- **Gateway** — listener (port + TLS); replaces "Ingress + LB Service"
- **HTTPRoute / GRPCRoute / TCPRoute / TLSRoute / UDPRoute** — routing rules
- **GatewayClass** — controller (like IngressClass)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata: { name: web-gateway }
spec:
  gatewayClassName: nginx
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - { name: web-tls }
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata: { name: web }
spec:
  parentRefs: [{ name: web-gateway }]
  hostnames: [app.example.com]
  rules:
  - matches:
    - path: { type: PathPrefix, value: / }
    backendRefs:
    - { name: web, port: 80 }
```

Most exam content still uses Ingress (since CKA exam tracks K8s versions but slowly).

## 8. Path-based vs host-based routing

```yaml
# Host-based: different hosts → different services
rules:
- host: api.example.com
  http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: api, port: { number: 8000 }}}}] }
- host: web.example.com
  http: { paths: [{ path: /, pathType: Prefix, backend: { service: { name: web, port: { number: 80 }}}}] }

# Path-based: same host, different paths
rules:
- host: example.com
  http:
    paths:
    - path: /api
      pathType: Prefix
      backend: { service: { name: api, port: { number: 8000 }}}
    - path: /
      pathType: Prefix
      backend: { service: { name: web, port: { number: 80 }}}
```

## 9. ingressClassName matters

Multiple Ingress controllers can coexist in a cluster. `ingressClassName` selects which:
```yaml
spec:
  ingressClassName: nginx     # or "traefik" or "alb"
```

For exam: usually just `nginx`.

## 10. Common CKA Ingress tasks

```bash
# Create Ingress
k create ingress web --rule="app.example.com/*=web:80" --class=nginx

# View
k get ingress
k describe ingress web

# Debug: pods can't be reached through Ingress
k get ingress web -o yaml          # spec correct?
k get svc web                       # service exists?
k get endpoints web                 # has endpoints? (selector matching pods?)
k get pods -n ingress-nginx         # controller running?
k logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx   # controller errors?
```

## 11. Quick self-check

1. Why is one LoadBalancer Service per app a cost problem at scale?
2. What's the relationship between an Ingress object and an Ingress Controller?
3. What does `ingressClassName` do?
4. What's Gateway API replacing and when did it GA?
5. What does cert-manager add to an Ingress setup?

(Answers: each is a cloud LB charge ~$15-25/mo on AWS + ENIs + IPs; Ingress is the abstract routing spec, Controller is the actual proxy implementation (nginx, traefik, ALB controller); selects which Ingress Controller in a multi-controller cluster handles this Ingress; replacing Ingress with Gateway + HTTPRoute + GatewayClass — GA in K8s 1.31 Aug 2024; automatic Let's Encrypt TLS — issues + renews certs into K8s Secrets that Ingress mounts.)



ewpage


# 65 — RBAC + ServiceAccounts + Certificates API

## 1. The K8s authorization layers

```
Request → API Server → Authentication → Authorization → Admission → etcd
                          ↓                ↓                ↓
                       who you are    can you do this   should you do this
                       (cert/token)   (RBAC/ABAC/Node)  (validating webhooks)
```

## 2. Authentication mechanisms

- **X.509 client certs** — most common for human admins
- **Bearer tokens** — ServiceAccount tokens (pods)
- **OIDC** — via Identity Center / Okta / etc.
- **Webhook** — custom (EKS uses this for aws-auth)
- **ServiceAccount tokens** — JWT bearer tokens

## 3. Authorization modes

| Mode | What |
|---|---|
| **RBAC** | Roles + Bindings; the default + recommended |
| **Node** | Built-in: kubelets get permissions only on their own node's resources |
| **ABAC** | Attribute-based, JSON policy file; rarely used |
| **AlwaysAllow / AlwaysDeny** | Don't use; AlwaysAllow is gaping security hole |
| **Webhook** | External authorization (rare) |

API server runs with `--authorization-mode=Node,RBAC` typically.

## 4. RBAC objects

| Object | Scope |
|---|---|
| **Role** | Permissions within a namespace |
| **ClusterRole** | Cluster-wide permissions OR a Role template usable in multiple namespaces |
| **RoleBinding** | Grants a Role to a subject (User/Group/SA) within a namespace |
| **ClusterRoleBinding** | Grants a ClusterRole to a subject cluster-wide |

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: pod-reader, namespace: my-app }
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: alice-reader, namespace: my-app }
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Verbs: `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection`.

## 5. ServiceAccounts

Every pod runs as a ServiceAccount (default: `default` SA in its namespace).

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: my-app-sa, namespace: my-app }
automountServiceAccountToken: false   # don't mount unless pod needs K8s API
```

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      serviceAccountName: my-app-sa
      containers: [...]
```

## 6. Bind a Role to a ServiceAccount

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: my-app-pod-reader, namespace: my-app }
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: my-app
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

The pod, when calling the K8s API, gets `pod-reader` permissions.

## 7. The `kubectl auth can-i` check (exam-critical)

```bash
# As current user
kubectl auth can-i list pods --namespace=my-app
# yes / no

# Impersonate (admin only)
kubectl auth can-i create deployments --as=alice --namespace=my-app
kubectl auth can-i list pods --as=system:serviceaccount:my-app:my-app-sa --namespace=my-app
```

Use this constantly during RBAC exam tasks to verify your bindings worked.

## 8. Certificates in Kubernetes

K8s uses PKI everywhere:
- **API server cert** — TLS for API
- **etcd certs** — peer + client TLS
- **kubelet certs** — auth between kubelet ↔ API server
- **front-proxy** certs — aggregation API
- **Client certs** — for human admins, e.g., kubeadm-generated admin.conf

All under `/etc/kubernetes/pki/` on control plane nodes.

## 9. Certificates API (creating user certs)

For a new human user, you need a client cert. The flow:

```bash
# 1. Generate private key + CSR
openssl genrsa -out alice.key 2048
openssl req -new -key alice.key -out alice.csr -subj "/CN=alice/O=dev"

# 2. Create K8s CertificateSigningRequest
cat <<EOF | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata: { name: alice }
spec:
  request: $(cat alice.csr | base64 | tr -d '\n')
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400      # 24 hours
  usages: [client auth]
EOF

# 3. Approve
kubectl certificate approve alice

# 4. Retrieve signed cert
kubectl get csr alice -o jsonpath='{.status.certificate}' | base64 -d > alice.crt

# 5. Add to kubeconfig
kubectl config set-credentials alice --client-certificate=alice.crt --client-key=alice.key
kubectl config set-context alice-context --cluster=<cluster> --user=alice --namespace=my-app

# 6. Test
kubectl --context=alice-context get pods -n my-app
# error: alice has no permissions yet — bind a role
```

## 10. Creating a User Account end-to-end

```bash
# Above flow + bind a role
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n my-app
kubectl create rolebinding alice-reader --role=pod-reader --user=alice -n my-app

# Test
kubectl --context=alice-context auth can-i list pods -n my-app    # yes
kubectl --context=alice-context auth can-i delete pods -n my-app  # no
```

## 11. Connecting to Cluster with a User

```bash
# Set context (alias for cluster+user+namespace)
kubectl config use-context alice-context

# Or explicit
kubectl --context=alice-context get pods -n my-app
```

In the kubeconfig:
```yaml
contexts:
- name: alice-context
  context:
    cluster: kubernetes
    user: alice
    namespace: my-app
users:
- name: alice
  user:
    client-certificate: /home/alice/alice.crt
    client-key: /home/alice/alice.key
```

## 12. Giving User permissions (ClusterRole + binding)

For cross-namespace: use ClusterRole + RoleBinding (per namespace) — grants ClusterRole's permissions but scoped to the namespace.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: alice-view, namespace: my-app }
subjects:
- { kind: User, name: alice, apiGroup: rbac.authorization.k8s.io }
roleRef:
  kind: ClusterRole       # using built-in `view` ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

Built-in ClusterRoles: `cluster-admin`, `admin`, `edit`, `view`.

## 13. ServiceAccount + Permissions creation

Common exam task: create SA, role, and binding in one go.

```bash
# All in one
kubectl create sa pipeline -n my-app
kubectl create role deployer -n my-app \
  --verb=get,list,create,update,patch,delete \
  --resource=deployments,services,configmaps,secrets
kubectl create rolebinding pipeline-deployer -n my-app \
  --role=deployer --serviceaccount=my-app:pipeline

# Verify
kubectl auth can-i create deployments \
  --as=system:serviceaccount:my-app:pipeline -n my-app
```

## 14. Quick self-check

1. What's the difference between Authentication and Authorization?
2. What's the difference between Role and ClusterRole?
3. What's `kubectl auth can-i` for and when use it?
4. What's the CSR + approve + retrieve flow for creating a new user cert?
5. What's the canonical SA + Role + Binding triplet for least-privilege pod access to K8s API?

(Answers: AuthN verifies who, AuthZ checks what they can do; Role is namespace-scoped, ClusterRole is cluster-wide OR used cross-namespace via RoleBinding; verify whether the current (or impersonated) identity can do an action without actually trying it — fast check during RBAC exam tasks; create K8s CSR with CSR data → approve → retrieve signed cert → add to kubeconfig; ServiceAccount in app namespace + Role with narrow verbs/resources + RoleBinding tying them together — pod uses serviceAccountName.)



ewpage


# 66 — Troubleshooting Applications (30% of CKA Exam)

## 1. The troubleshooting tier — top to bottom

When a pod isn't working:
```
1. Pod status (Pending? CrashLoopBackOff? ImagePullBackOff?)
2. Pod events (kubectl describe)
3. Pod logs (kubectl logs, --previous)
4. Service / endpoints (label match?)
5. NetworkPolicy (blocking traffic?)
6. DNS (CoreDNS healthy?)
7. Node (cordoned? out of resources?)
8. Control plane components (kube-system pods running?)
9. CNI (pods getting IPs?)
```

## 2. Pod statuses

| Status | Means |
|---|---|
| **Pending** | Not scheduled yet (no matching node, taint, resources unavailable) |
| **Running** | Scheduled + container started |
| **Succeeded** | All containers exited 0 |
| **Failed** | All containers exited non-zero |
| **Unknown** | Node communication lost |
| **CrashLoopBackOff** | Container keeps crashing; restart-backed-off |
| **ImagePullBackOff** | Can't pull image |
| **ErrImagePull** | Image pull error |
| **ContainerCreating** | Starting; usually < 30s; if longer = volume / image / network issue |

## 3. The diagnostic workflow

```bash
# Pod-level diagnosis
k get pods                              # see status
k describe pod <name>                   # events at bottom!
k logs <name>                           # current logs
k logs <name> --previous                # logs from previous (crashed) container
k logs <name> -c <container>            # specific container
k logs <name> -f --tail=100             # follow last 100

# Node-level
k get nodes                             # Ready?
k describe node <name>                  # conditions + capacity + taints
k top nodes                             # resource usage (needs metrics-server)
k top pods -A

# Cluster-level
k get componentstatuses                 # legacy but useful
k get events --sort-by=.lastTimestamp -A
k get all -A                            # everything
```

## 4. Pod stuck in Pending

```bash
k describe pod <name>
# Events:
#   FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu
# OR
#   FailedScheduling: 0/3 nodes are available: 3 node(s) had untolerated taint
```

Causes:
- **Insufficient resources** — bump resources.requests down, or add nodes
- **Untolerated taint** — pod doesn't tolerate node taint
- **No node matches nodeSelector** — wrong label
- **PVC unbound** — no matching PV

## 5. Pod stuck in ImagePullBackOff

```bash
k describe pod <name>
# Events:
#   Failed to pull image "myimage:bad": rpc error
#   Failed to pull image "myimage:bad": ErrImagePull
```

Causes:
- Image doesn't exist (typo, never pushed)
- Private registry without imagePullSecrets
- Wrong tag
- Network issue from node to registry
- Image is for wrong architecture (arm64 image on amd64 node)

Fix:
```bash
# For private registry
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user --docker-password=pass

# Reference in pod spec
spec:
  imagePullSecrets:
  - name: regcred
  containers: [...]
```

## 6. Pod stuck in CrashLoopBackOff

```bash
k logs <name> --previous
# Shows logs from the crashed container
```

Causes:
- Application error on startup (env var missing, can't connect to DB)
- Wrong command/args
- Missing config / secrets mount
- OOMKilled (exit 137)
- Health check killed it before ready

Check resource events:
```bash
k describe pod <name> | grep -A 5 "Last State"
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
```

OOM means memory limit too low or memory leak.

## 7. Service has no endpoints

```bash
k get endpoints <svc>
# NAME    ENDPOINTS    AGE
# my-svc  <none>       5m         ← no endpoints!
```

Causes:
- Service selector doesn't match any pod labels
- Pods are not Ready (failing readiness probe)
- Pods are in a different namespace

```bash
k get pods --show-labels                          # what labels do pods have?
k get svc my-svc -o jsonpath='{.spec.selector}'   # what does svc select?
```

## 8. DNS not resolving

```bash
# In a debug pod
k run debug --rm -it --image=alpine -- sh
apk add bind-tools
nslookup kubernetes.default
nslookup my-svc.my-app
nslookup my-svc.my-app.svc.cluster.local
```

If resolution fails:
- CoreDNS pods in kube-system not running?
- CoreDNS ConfigMap broken?
- NetworkPolicy blocking DNS traffic?

```bash
k get pods -n kube-system -l k8s-app=kube-dns
k logs -n kube-system -l k8s-app=kube-dns
k get configmap coredns -n kube-system -o yaml
```

## 9. Debugging with temporary pods

The exam's go-to:
```bash
# Network debugging
k run debug --rm -it --image=nicolaka/netshoot -- bash

# Inside:
curl -v http://my-svc:80
nslookup my-svc.my-app
nc -zv my-svc 80
traceroute my-svc

# Single-shot
k run curl --rm -it --image=curlimages/curl -- curl -v http://my-svc

# Test from a specific node
k run debug --rm -it --image=alpine \
  --overrides='{"spec":{"nodeName":"worker01"}}' -- sh
```

## 10. `kubectl debug` (newer; ephemeral containers)

```bash
# Attach ephemeral debug container to running pod
k debug -it <pod-name> --image=nicolaka/netshoot --target=<container-name>

# Copy a pod with image swap (debug crash-looping pod with shell-based image)
k debug <pod-name> -it --image=alpine --copy-to=debug-pod --share-processes
```

This avoids "I need to debug this prod pod but can't `exec` into a crashed container."

## 11. `kubectl` format output

```bash
k get pod my-pod -o yaml
k get pod my-pod -o json
k get pod my-pod -o jsonpath='{.status.phase}'
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
k get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
k get pods --sort-by=.metadata.creationTimestamp
k get pods --selector=app=web -o name | xargs -I{} kubectl logs {}
```

For exam: practice jsonpath + custom-columns. Faster than `-o yaml | grep`.

## 12. Kubelet + kubectl issues

### Kubelet not starting (on a node)
```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 100
# Common causes:
# - swap not disabled
# - CRI not running (containerd down?)
# - Wrong cgroup driver mismatch
# - Cert expired (kubelet client cert)
```

### kubectl can't connect
```bash
kubectl cluster-info dump | head
# Check:
# - $KUBECONFIG env var?
# - ~/.kube/config exists + has correct cluster endpoint?
# - API server cert expired?
# - API server pod healthy?

k get pods -n kube-system | grep apiserver
ssh control-plane "sudo crictl ps | grep apiserver"
```

### API server not running
```bash
ssh control-plane
ls /etc/kubernetes/manifests/
# kube-apiserver.yaml should be there; if you accidentally moved it, the static pod stopped
# Restore + kubelet will start it again within seconds
```

## 13. Quick self-check

1. What's the difference between `k logs` and `k logs --previous`?
2. What does exit code 137 mean?
3. Why might `k get endpoints my-svc` return `<none>`?
4. What's `kubectl debug` used for?
5. Where do static control plane pod manifests live?

(Answers: --previous shows logs from the container before the current restart (the crashed one); OOMKilled — process was killed by Linux OOM killer (memory limit exceeded); selector doesn't match any pod's labels, or pods aren't Ready (failing readiness probe); attaching ephemeral debug containers or making a copy of a pod with image swap — for debugging crash-looping pods you can't exec into; /etc/kubernetes/manifests/ on control plane nodes — kubelet watches this directory.)



ewpage


# 67 — Multi-container Pods — Sidecar + Init

## 1. The 3 multi-container patterns

| Pattern | When |
|---|---|
| **Sidecar** | Helper alongside main container (log shipper, proxy) |
| **Init container** | Runs to completion BEFORE main containers start |
| **Adapter** | Transforms output of main container (normalizes metrics format) |
| **Ambassador** | Proxies main container's outbound traffic |

## 2. Init containers

Init containers run sequentially before main containers. Each must complete (exit 0) before the next starts. Used for:
- Wait for a dependency to be ready
- Run a migration / seed data
- Generate config files
- Pre-warm cache

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  initContainers:
  - name: wait-for-db
    image: busybox
    command: ['sh', '-c', 'until nslookup db; do echo waiting; sleep 2; done']
  - name: migrate
    image: my-app:1.2.3
    command: ['python', '-m', 'app.migrate']
  containers:
  - name: app
    image: my-app:1.2.3
    command: ['python', '-m', 'app.main']
```

Sequence:
1. `wait-for-db` runs until DB DNS resolves
2. `migrate` runs migrations and exits
3. `app` starts (main container)

If any init container fails, pod restarts (re-runs from init container 1).

## 3. Sidecar containers (the K8s 1.28+ way)

Pre-1.28: a sidecar was just "another container in `containers:`". This had problems:
- No ordering — main + sidecar started at same time
- Pod ready when *all* containers ready (sidecar startup delayed main readiness)
- No graceful shutdown ordering

K8s 1.28 added **first-class sidecar containers** — init containers with `restartPolicy: Always`:

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  initContainers:
  - name: log-shipper            # sidecar (init container with restartPolicy: Always)
    image: fluent-bit:3
    restartPolicy: Always         # ← makes it a sidecar
    volumeMounts:
    - { name: logs, mountPath: /var/log }
  containers:
  - name: app
    image: my-app:1.2.3
    volumeMounts:
    - { name: logs, mountPath: /app/logs }
  volumes:
  - { name: logs, emptyDir: {} }
```

Sidecar:
- Starts before main containers
- Pod is ready when main containers are ready (sidecar doesn't gate readiness)
- Sidecar lives for the pod's lifetime
- On pod shutdown: main container terminates first, then sidecar

## 4. Common sidecar use cases

### Log shipping
```yaml
- name: fluent-bit
  image: fluent/fluent-bit:3
  restartPolicy: Always
  volumeMounts:
  - { name: logs, mountPath: /var/log }
  - { name: fluent-config, mountPath: /fluent-bit/etc }
```

### Service mesh proxy (Istio sidecar)
Istio in sidecar mode auto-injects an Envoy sidecar into every pod (`istio-injection=enabled` namespace label).

### Reverse proxy / cache
```yaml
- name: nginx
  image: nginx:1.27-alpine
  ports: [{ containerPort: 80 }]
  volumeMounts:
  - { name: app-cache, mountPath: /cache }
- name: app
  image: my-app:1.2.3
  ports: [{ containerPort: 8000 }]    # only accessed via sidecar
```

### Secrets refresher / cert renewer
A sidecar polls Vault and refreshes mounted credentials.

## 5. Containers share what?

In one pod:
- **Same network namespace** — they share IP + can talk via localhost
- **Same volume mounts** (if specified) — share filesystem state via emptyDir
- **Same lifecycle** — start/stop together (with sidecar ordering for K8s 1.28+)
- **Same IPC** — by default share IPC namespace
- **Independent process namespace** by default; `shareProcessNamespace: true` to share

```yaml
spec:
  shareProcessNamespace: true   # both containers see each other's processes
```

## 6. Exposing Pod Information — Downward API

Containers can read pod metadata via env vars or volumes:

```yaml
containers:
- name: app
  image: my-app
  env:
  - name: POD_NAME
    valueFrom: { fieldRef: { fieldPath: metadata.name } }
  - name: POD_IP
    valueFrom: { fieldRef: { fieldPath: status.podIP } }
  - name: NODE_NAME
    valueFrom: { fieldRef: { fieldPath: spec.nodeName } }
  - name: POD_CPU_REQUEST
    valueFrom: { resourceFieldRef: { containerName: app, resource: requests.cpu } }
  volumeMounts:
  - { name: podinfo, mountPath: /etc/podinfo }
volumes:
- name: podinfo
  downwardAPI:
    items:
    - { path: labels, fieldRef: { fieldPath: metadata.labels } }
    - { path: annotations, fieldRef: { fieldPath: metadata.annotations } }
```

Use case: app logs include POD_NAME, structured logging can include node + pod IP without app-level config.

## 7. Inter-container communication patterns

### Same pod: localhost
```python
# app container connects to sidecar nginx on same pod:
requests.get("http://localhost:80")
```

### Same pod: shared file system (emptyDir)
```yaml
volumes:
- { name: shared, emptyDir: {} }
containers:
- name: producer
  volumeMounts: [{ name: shared, mountPath: /out }]
  command: ['sh', '-c', 'while true; do date >> /out/log; sleep 5; done']
- name: consumer
  volumeMounts: [{ name: shared, mountPath: /in }]
  command: ['sh', '-c', 'tail -f /in/log']
```

### Across pods: through Service
Use a Service; not direct pod-to-pod.

## 8. The `kubectl exec` with multi-container pods

```bash
# Default: first container
k exec -it my-pod -- bash

# Specific container
k exec -it my-pod -c sidecar -- bash

# Logs of specific container
k logs my-pod -c app
k logs my-pod -c app --previous
```

## 9. Init containers vs sidecar containers — exam questions

```yaml
spec:
  initContainers:
  - name: setup
    image: alpine
    command: ['sh', '-c', 'echo ready']      # exits → main containers can start
  - name: telegraf
    image: telegraf
    restartPolicy: Always                     # ← sidecar in K8s 1.28+
  containers:
  - name: app
    image: my-app
```

The `restartPolicy: Always` on an init container is the discriminator.

## 10. Common pitfalls

- **Sidecar not starting before main** — use restartPolicy: Always on init container (K8s 1.28+) or accept legacy parallel startup
- **Init container failure loop** — pod restarts everything; check init container logs
- **Resources counted per pod** — sum of all containers' requests/limits; large pods schedule less easily
- **One bad container in `containers:` doesn't fail others** — but pod isn't Ready unless all are Ready

## 11. Quick self-check

1. What's the difference between an init container and a sidecar?
2. What changed in K8s 1.28 about sidecars?
3. How do containers in the same pod communicate?
4. What does the Downward API expose?
5. Why does `restartPolicy: Always` on an init container make it a sidecar?

(Answers: init runs to completion before main starts, sidecar runs alongside main for pod lifetime; first-class sidecar via init container with restartPolicy: Always — gets ordering, doesn't gate pod readiness, graceful shutdown; via localhost (same network ns) or via emptyDir volumes (shared filesystem); pod metadata (name, IP, namespace, labels, annotations) + container resource limits — exposed as env vars or volume files; init container with always-restart becomes long-running but still has init-ordering semantics — that's the sidecar contract.)



ewpage


# 68 — Volumes — PV / PVC / SC + HostPath + emptyDir

## 1. The K8s storage layer

```
StorageClass (SC) — "how to provision a PV when asked"
  ↓ (defines provisioner)
PersistentVolume (PV) — "an actual chunk of storage backed by something real"
  ↓ (bound to)
PersistentVolumeClaim (PVC) — "user's request for storage"
  ↓ (mounted by)
Pod
```

## 2. emptyDir — ephemeral pod-scoped

Lives for pod's lifetime. Lost on pod deletion. Used for:
- Sidecar ↔ main container shared scratch
- Cache that survives container restart but not pod restart
- Stream buffer

```yaml
volumes:
- name: cache
  emptyDir:
    sizeLimit: 1Gi              # K8s 1.27+ accounts against ephemeral storage
    medium: Memory              # tmpfs — faster, counts against memory limit
```

## 3. HostPath — mount a host path

Maps a directory from the node into the pod. Dangerous: pod escape risk, breaks if pod moves to another node.

```yaml
volumes:
- name: data
  hostPath:
    path: /data/myapp
    type: DirectoryOrCreate
```

Used for:
- Logging agents reading `/var/log/`
- Monitoring agents reading `/proc/` or `/sys/`
- Local development (Minikube)

For CKA tasks: know how to mount it. For production: avoid.

## 4. PV / PVC — persistent storage

```yaml
# Admin creates a PV
apiVersion: v1
kind: PersistentVolume
metadata: { name: pv-1 }
spec:
  capacity: { storage: 10Gi }
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: standard
  hostPath: { path: /mnt/data }       # backing storage
```

```yaml
# User creates a PVC requesting storage
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: data, namespace: my-app }
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard
  resources:
    requests: { storage: 5Gi }
```

```yaml
# Pod mounts the PVC
spec:
  containers:
  - name: app
    image: my-app
    volumeMounts:
    - { name: data, mountPath: /var/lib/app }
  volumes:
  - name: data
    persistentVolumeClaim: { claimName: data }
```

K8s binds the PVC to a PV that matches (size + accessMode + storageClass).

## 5. Access modes

| Mode | Means |
|---|---|
| **ReadWriteOnce (RWO)** | One node can mount RW (multiple pods on that node OK) |
| **ReadOnlyMany (ROX)** | Many nodes can mount RO |
| **ReadWriteMany (RWX)** | Many nodes can mount RW (NFS / EFS / CephFS, not EBS) |
| **ReadWriteOncePod (RWOP)** | Only one pod can mount (K8s 1.27+ GA) |

Cloud reality:
- EBS = RWO only
- EFS / FSx for Lustre = RWX
- GCS Fuse / Azure Files = RWX
- Local SSD = RWO

## 6. StorageClass — dynamic provisioning

Without SC: admin pre-creates PVs manually.
With SC: PVC requests storage; SC's provisioner creates a PV automatically.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: gp3 }
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer    # delay binding until pod scheduled
reclaimPolicy: Delete
allowVolumeExpansion: true
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  fsType: ext4
  encrypted: "true"
```

```yaml
# PVC uses SC
spec:
  storageClassName: gp3          # default SC used if omitted (and one marked default)
```

`WaitForFirstConsumer` binding mode: don't provision until a pod actually needs it (lets scheduler pick a node first, then provision EBS in that AZ).

## 7. CSI drivers (the modern storage layer)

In-tree drivers (kubernetes/kubernetes repo) are deprecated. **CSI (Container Storage Interface)** drivers run as separate controllers + DaemonSets.

Cloud CSI drivers:
- **AWS EBS CSI** (ebs.csi.aws.com) — for EBS volumes
- **AWS EFS CSI** (efs.csi.aws.com) — for EFS file systems
- **GCE PD CSI** (pd.csi.storage.gke.io) — for GCP persistent disks
- **Azure Disk CSI**
- **Azure File CSI**

Multi-cloud / on-prem:
- **Rook-Ceph** — full Ceph cluster on K8s
- **Longhorn** — Rancher's distributed block storage
- **Portworx** — commercial
- **NetApp Trident** — for NetApp ONTAP

## 8. Configuring HostPath Volume (CKA exam-style)

```yaml
apiVersion: v1
kind: Pod
metadata: { name: hostpath-pod }
spec:
  containers:
  - name: app
    image: nginx
    volumeMounts:
    - name: data
      mountPath: /usr/share/nginx/html
  volumes:
  - name: data
    hostPath:
      path: /tmp/web-data
      type: DirectoryOrCreate
```

`type:`
- `DirectoryOrCreate` — create if missing
- `Directory` — must already exist as directory
- `FileOrCreate` — create file if missing
- `File` — must exist as file
- `Socket`, `CharDevice`, `BlockDevice`

## 9. Configuring emptyDir Volume

```yaml
apiVersion: v1
kind: Pod
metadata: { name: scratch }
spec:
  containers:
  - name: writer
    image: alpine
    command: ['sh', '-c', 'while true; do date >> /data/log.txt; sleep 5; done']
    volumeMounts: [{ name: shared, mountPath: /data }]
  - name: reader
    image: alpine
    command: ['sh', '-c', 'tail -f /data/log.txt']
    volumeMounts: [{ name: shared, mountPath: /data }]
  volumes:
  - name: shared
    emptyDir: {}
```

## 10. PVC binding lifecycle

```
Pending → Bound → (PV/PVC bound) → Mounted → (in use)
                                              ↓
                                          Released (PVC deleted)
                                              ↓
                                Reclaim Policy:
                                  - Delete → PV deleted (and backing storage gone)
                                  - Retain → PV kept (manual cleanup)
                                  - Recycle → DEPRECATED
```

Common task: PVC stuck Pending.
- No StorageClass + no matching PV → manually create PV
- StorageClass exists but provisioner fails → check CSI controller logs
- accessMode mismatch → PVC wants RWX, only RWO PVs available

```bash
k get pvc
k describe pvc my-data
k get pv
k describe pv pv-1
k get sc
k get pods -n kube-system | grep csi
```

## 11. Volume expansion

```bash
# Patch PVC to request more storage
k patch pvc my-data -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
# SC must have allowVolumeExpansion: true
# Online expansion (no pod restart) supported by EBS, EFS, etc.
```

## 12. ConfigMap + Secret as volumes (preview Module 69)

```yaml
volumes:
- name: config
  configMap:
    name: app-config
- name: secrets
  secret:
    secretName: app-secrets
    defaultMode: 0400
```

Each ConfigMap/Secret key becomes a file in the volume.

## 13. Quick self-check

1. What's the difference between emptyDir and a PVC?
2. What's the difference between ReadWriteOnce and ReadWriteMany?
3. What does `volumeBindingMode: WaitForFirstConsumer` do and when use it?
4. What's a CSI driver vs in-tree driver?
5. What's the reclaim policy and what are the two options that aren't deprecated?

(Answers: emptyDir lives for pod lifetime + lost on pod delete, PVC is persistent + survives pod restarts/recreations; RWO = one node mounts (EBS-style), RWX = many nodes mount simultaneously (EFS/NFS-style); delays PV provisioning until a pod is scheduled — lets scheduler pick the node first, then provision storage in that AZ — essential for zonal storage like EBS; CSI is out-of-tree pluggable storage driver, in-tree was baked into K8s source — CSI is the modern path, in-tree is being removed; Delete (PV deleted with backing storage when PVC deleted) and Retain (PV kept, manual cleanup needed).)



ewpage


# 69 — ConfigMap + Secret (env + volume)

## 1. ConfigMap basics

```bash
# Create from literals
k create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=ENV=prod

# From a file
k create configmap nginx-conf --from-file=nginx.conf

# From a directory
k create configmap config-files --from-file=./configs/

# From an env file
k create configmap envs --from-env-file=.env

# Scaffold YAML
k create configmap app-config --from-literal=X=1 --dry-run=client -o yaml
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config, namespace: my-app }
data:
  LOG_LEVEL: info
  ENV: prod
  app.conf: |
    server {
      listen 80;
      server_name example.com;
    }
binaryData:
  cert.bin: <base64>
```

## 2. Secret basics

```bash
# Generic (Opaque)
k create secret generic db-creds \
  --from-literal=username=app \
  --from-literal=password=super-secret

# TLS cert/key
k create secret tls web-tls \
  --cert=path/to/tls.crt --key=path/to/tls.key

# Docker registry creds
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user --docker-password=pass

# Scaffold
k create secret generic db-creds --from-literal=password=x --dry-run=client -o yaml
```

```yaml
apiVersion: v1
kind: Secret
metadata: { name: db-creds }
type: Opaque
data:                              # base64-encoded values
  username: YXBw
  password: c3VwZXItc2VjcmV0
# Or use stringData for plain values
stringData:
  username: app
  password: super-secret
```

**Secrets are base64-encoded, NOT encrypted.** See Module 35 for proper secrets management.

Secret types:
- `Opaque` — generic
- `kubernetes.io/service-account-token` — auto-created for SAs
- `kubernetes.io/dockerconfigjson` — registry creds
- `kubernetes.io/tls` — TLS cert + key
- `kubernetes.io/basic-auth`, `kubernetes.io/ssh-auth`

## 3. Passing as Environment Variables

```yaml
containers:
- name: app
  image: my-app
  env:
  # From literal
  - name: APP_NAME
    value: my-app
  # From ConfigMap
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: LOG_LEVEL
  # From Secret
  - name: DATABASE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: db-creds
        key: password
  # All keys from a ConfigMap as env vars
  envFrom:
  - configMapRef: { name: app-config }
  - secretRef: { name: db-creds }
  # With a prefix
  - configMapRef: { name: app-config }
    prefix: CONFIG_
```

`envFrom` is the bulk way: every key in the ConfigMap becomes an env var.

## 4. Passing as Volumes

```yaml
spec:
  containers:
  - name: nginx
    image: nginx
    volumeMounts:
    - name: nginx-config
      mountPath: /etc/nginx/conf.d
      readOnly: true
    - name: tls-cert
      mountPath: /etc/nginx/tls
      readOnly: true
  volumes:
  - name: nginx-config
    configMap:
      name: nginx-conf
      defaultMode: 0644
      items:
      - { key: nginx.conf, path: default.conf }   # rename key→path
  - name: tls-cert
    secret:
      secretName: web-tls
      defaultMode: 0400
```

Each key in the ConfigMap/Secret becomes a file under the mount path.

## 5. Volume vs env — when to use which

| | Env vars | Volumes |
|---|---|---|
| **Visibility** | `env` in process; logged sometimes | Filesystem; explicit reads |
| **Update without restart** | No (env baked at start) | Yes (K8s syncs the volume) |
| **Multi-line values** | Awkward | Natural (`app.conf` file) |
| **Binary data** | No | Yes |
| **Security** | Often logged accidentally | Better (don't appear in process env) |

For secrets: prefer **volume mounts**. Env vars get logged.

## 6. Updating ConfigMaps / Secrets

```bash
k edit configmap app-config
# Modify, save
```

Behavior:
- **Env-var consumers**: don't see the update until pod restart
- **Volume consumers**: K8s syncs the volume (~minutes); app must re-read

To force pod restart on ConfigMap change:
- **kustomize**: configMapGenerator + hash suffix
- **Helm**: checksum annotation on Deployment
- **Reloader** (CNCF): watches ConfigMaps + restarts dependent Deployments

## 7. Immutable ConfigMaps + Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: app-config }
immutable: true                  # locked; can't be modified
data: { ... }
```

Immutable benefits:
- Performance (kubelet doesn't watch for changes)
- Stability (no accidental modification)
- Use kustomize or helm-style hash-suffixed names for "updates" (create new immutable one, swap reference)

## 8. CKA exam tasks

Common asks:
- Create a ConfigMap from a literal
- Create a Secret from a file
- Make a Pod read a ConfigMap key as an env var
- Make a Pod mount a Secret as a volume
- Use a registry Secret for image pull

```bash
# Quick scaffold
k create cm app-config --from-literal=LOG=debug --dry-run=client -o yaml > cm.yaml
k create secret generic db-creds --from-literal=pw=secret --dry-run=client -o yaml > sec.yaml
k apply -f cm.yaml -f sec.yaml

# Pod consuming both
cat <<EOF | k apply -f -
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  containers:
  - name: web
    image: nginx
    envFrom:
    - configMapRef: { name: app-config }
    - secretRef: { name: db-creds }
EOF

# Verify
k exec web -- env | grep -E "LOG|pw"
```

## 9. Encryption at rest for Secrets

Default: Secrets stored in etcd unencrypted (just base64). Better:
- **Envelope encryption with KMS** — etcd encrypts Secret values with a key from KMS
- Configure via `--encryption-provider-config` on apiserver

EKS: enable in cluster creation:
```hcl
cluster_encryption_config = {
  provider_key_arn = aws_kms_key.eks.arn
  resources        = ["secrets"]
}
```

## 10. Quick self-check

1. Why is `secret` base64 not encryption?
2. What's the difference between `env` and `envFrom`?
3. What happens to a pod's env vars when the source ConfigMap is updated?
4. Why prefer volume mounts over env vars for Secrets?
5. What does `immutable: true` give you on a ConfigMap?

(Answers: encoding is reversible without a key — anyone with API access can decode; env picks specific keys, envFrom imports all keys from a ConfigMap/Secret as env vars at once; nothing — env vars baked at pod start; restart needed to pick up changes; env vars are easier to accidentally log + show up in process listings, volumes require explicit reads; performance (no watch) + stability (can't modify) — must create new and swap reference for updates.)



ewpage


# 70 — Resource Requests + Limits

## 1. Why requests + limits matter

K8s uses these to:
- **Schedule** pods (request = guaranteed reservation; needs enough free)
- **Cap usage** (limit = max; CPU throttled; memory exceeded → OOMKilled)
- **Determine QoS class** (BestEffort / Burstable / Guaranteed)

## 2. The syntax

```yaml
resources:
  requests:
    cpu: 100m           # 0.1 vCPU
    memory: 128Mi       # 128 mebibytes
    ephemeral-storage: 1Gi
  limits:
    cpu: 500m           # 0.5 vCPU
    memory: 256Mi
    ephemeral-storage: 2Gi
```

### CPU units
- `1` = 1 vCPU (1 core)
- `100m` = 100 millicores = 0.1 vCPU
- `1500m` = 1.5 vCPU
- Fractions allowed: `0.5` = `500m`

### Memory units
- `Mi` = mebibytes (2^20 bytes) — preferred
- `Gi` = gibibytes
- `M` = megabytes (10^6 bytes, less common)
- `Ki`, `Pi`, `Ti` — kibibytes, pebibytes, tebibytes

## 3. QoS classes (derived from requests + limits)

| QoS | Condition |
|---|---|
| **Guaranteed** | Every container has equal requests = limits for CPU AND memory |
| **Burstable** | At least one container has requests OR limits set, but not Guaranteed |
| **BestEffort** | No requests or limits set at all |

Eviction order under pressure: BestEffort first, then Burstable, then Guaranteed last. Set Guaranteed for the most critical workloads.

## 4. CPU vs Memory limits — different behavior

| | CPU | Memory |
|---|---|---|
| **Over-limit** | Throttled (slow) | OOMKilled (exit 137) |
| **Compressible** | Yes | No |
| **Burstable** | Can use unused CPU briefly | No memory bursting |

This asymmetry matters:
- CPU limit slightly low → app slow but alive
- Memory limit slightly low → app killed → restarts → may CrashLoopBackOff

**Many practitioners drop CPU limits** (keep requests) and only set memory limits. Argument: CPU throttling causes worse outcomes than letting bursts happen.

## 5. Setting per-namespace defaults — LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata: { name: defaults, namespace: my-app }
spec:
  limits:
  - type: Container
    default:                # used when pod doesn't specify a limit
      cpu: "500m"
      memory: "256Mi"
    defaultRequest:         # used when pod doesn't specify a request
      cpu: "50m"
      memory: "64Mi"
    max:                    # caps pod-specified limits
      cpu: "2"
      memory: "2Gi"
    min:                    # floor on pod-specified requests
      cpu: "10m"
      memory: "16Mi"
```

Now pods in `my-app` namespace without explicit resources get sane defaults.

## 6. Namespace capacity — ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata: { name: my-app-quota, namespace: my-app }
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
    secrets: "20"
```

Pods that exceed the quota fail to create. Use ResourceQuota to bound namespace usage in shared clusters.

```bash
k describe ns my-app             # shows quotas + usage
k get resourcequotas -A
```

## 7. Reading resource usage — metrics-server

```bash
# Install metrics-server (one-time per cluster)
k apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Now you can use top
k top nodes
k top pods
k top pods -A
k top pod my-pod --containers
```

## 8. Right-sizing — the discipline

The pattern:
1. Deploy with conservative requests (low) + memory limit (slightly above expected peak)
2. Observe for 1-2 weeks via Prometheus / `kubectl top`
3. Use **Vertical Pod Autoscaler (VPA)** in recommendation mode:
   ```bash
   k apply -f https://github.com/kubernetes/autoscaler/raw/master/vertical-pod-autoscaler/deploy/vpa-v1-crd.yaml
   ```
4. Look at p95 / p99 actual usage
5. Set request ≈ p95 typical; limit ≈ p99 + headroom

## 9. Horizontal Pod Autoscaler (HPA)

```bash
k autoscale deployment web --min=3 --max=20 --cpu-percent=70
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target: { type: Utilization, averageUtilization: 70 }
  - type: Resource
    resource:
      name: memory
      target: { type: Utilization, averageUtilization: 80 }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - { type: Percent, value: 50, periodSeconds: 60 }
```

HPA requires:
- metrics-server installed
- Pods have `resources.requests` set (HPA computes utilization relative to requests)

## 10. The 4 autoscalers

| Scaler | Scales |
|---|---|
| **HPA** | Replicas (horizontal) |
| **VPA** | Pod resource requests (vertical) |
| **CA / Karpenter** | Nodes |
| **KEDA** | Replicas based on custom metrics (queue depth, etc.) |

VPA + HPA conflict — don't use both for the same metric.

## 11. Capacity planning + headroom

Practical rule: keep node CPU utilization < 70% average, memory < 80%, to absorb spikes. K8s scheduler will refuse to schedule pods if their requests would exceed node capacity even if actual usage is fine — keep enough headroom.

## 12. Quick self-check

1. What does QoS class Guaranteed require?
2. Why is CPU limit considered controversial?
3. What's the difference between LimitRange and ResourceQuota?
4. Why does HPA require pods to have `resources.requests` set?
5. What's the exit code for OOMKilled?

(Answers: every container has requests = limits for CPU AND memory; CPU throttling causes hard-to-diagnose perf issues — many practitioners only set memory limits and CPU requests; LimitRange sets defaults + min/max for pods within a namespace, ResourceQuota caps total resources usable within a namespace; HPA computes utilization as actual_usage / requested — without requests it has no denominator; 137.)



ewpage


# 71 — Scheduling — NodeSelector, Affinity, Taints, Tolerations

## 1. How the K8s scheduler decides

When a pod is unscheduled, kube-scheduler:
1. **Filter** — drop nodes that don't meet hard constraints (resources, nodeSelector, taints without tolerations, PV zone)
2. **Score** — rank remaining by soft preferences (affinity, balanced resource use, image locality)
3. **Pick** the highest-scoring node
4. **Bind** the pod to it

## 2. NodeName (force a node)

```yaml
spec:
  nodeName: worker-3
  containers: [...]
```

Bypasses scheduler entirely. Use sparingly — pod won't move if node fails.

## 3. NodeSelector (match by label)

```yaml
spec:
  nodeSelector:
    disktype: ssd
    region: us-east-1a
  containers: [...]
```

Only nodes with matching labels are candidates. Simple, but `equality only`.

Label nodes:
```bash
k label node worker-1 disktype=ssd
k get nodes --show-labels
```

## 4. Node Affinity (richer matching)

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:      # hard
        nodeSelectorTerms:
        - matchExpressions:
          - { key: disktype, operator: In, values: [ssd] }
          - { key: zone, operator: In, values: [us-east-1a, us-east-1b] }
      preferredDuringSchedulingIgnoredDuringExecution:     # soft
      - weight: 100
        preference:
          matchExpressions:
          - { key: instance-type, operator: In, values: [m5.xlarge] }
```

Operators: `In`, `NotIn`, `Exists`, `DoesNotExist`, `Gt`, `Lt`.

Note: `IgnoredDuringExecution` means after scheduling, if labels change, pod stays put.

## 5. Inter-Pod Affinity / Anti-Affinity

```yaml
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels: { app: web }
        topologyKey: kubernetes.io/hostname        # don't put 2 web pods on same node
```

Common use cases:
- **Anti-affinity**: spread replicas across nodes/zones for HA
- **Affinity**: co-locate pods that communicate heavily (rarely useful in K8s)

`topologyKey` defines the topology level: `kubernetes.io/hostname`, `topology.kubernetes.io/zone`, `topology.kubernetes.io/region`.

## 6. Pod Topology Spread Constraints (the modern replacement)

```yaml
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels: { app: web }
```

Forces pods to be spread evenly across zones (max skew = 1 pod difference between any two zones). Replaces awkward pod-anti-affinity for spread use cases.

## 7. Taints + Tolerations

**Taint a node** = no pods land there unless they explicitly tolerate it.

```bash
# Taint
k taint nodes worker-1 dedicated=ml-training:NoSchedule

# Remove
k taint nodes worker-1 dedicated-

# View
k describe node worker-1 | grep Taints
```

Effects:
- `NoSchedule` — won't schedule new pods (existing stay)
- `PreferNoSchedule` — soft "avoid"
- `NoExecute` — evict existing pods that don't tolerate, won't schedule new

```yaml
# Pod with toleration
spec:
  tolerations:
  - key: dedicated
    operator: Equal
    value: ml-training
    effect: NoSchedule
  containers: [...]
```

Common taints:
- Control plane nodes auto-tainted with `node-role.kubernetes.io/control-plane:NoSchedule`
- Spot instances tagged `karpenter.sh/disruption=...`
- GPU nodes often tainted to prevent non-GPU workloads landing there

## 8. The NodeSelector / Affinity / Taint matrix

| Question | Use |
|---|---|
| "Only put workload X here" | Taints on node + tolerations on pod |
| "Prefer to put workload X here" | nodeAffinity preferred |
| "Pod must run on nodes with label L" | nodeSelector or required affinity |
| "Spread pods across zones" | Pod Topology Spread Constraints |
| "Avoid co-locating these pods" | podAntiAffinity |

Taint-based isolation is **the strongest**: even if a pod has matching node selector but no toleration, it won't land on tainted nodes.

## 9. Common scheduling exam tasks

### Schedule on a specific node
```yaml
spec:
  nodeName: worker-1
```
Or:
```yaml
spec:
  nodeSelector: { kubernetes.io/hostname: worker-1 }
```

### Taint + toleration
```bash
k taint node worker-1 env=prod:NoSchedule
```
```yaml
spec:
  tolerations:
  - { key: env, operator: Equal, value: prod, effect: NoSchedule }
```

### Schedule on a labeled set of nodes
```bash
k label node worker-1 gpu=true
k label node worker-2 gpu=true
```
```yaml
spec:
  nodeSelector: { gpu: "true" }
```

### Require pod to run on amd64 nodes only
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - { key: kubernetes.io/arch, operator: In, values: [amd64] }
```

## 10. Cordon + Drain (operator's tools)

```bash
# Cordon — mark node unschedulable (existing pods stay, no new pods)
k cordon worker-1

# Drain — cordon + evict pods (for maintenance)
k drain worker-1 --ignore-daemonsets --delete-emptydir-data

# Uncordon — make schedulable again
k uncordon worker-1
```

Common workflow: node maintenance / upgrade:
```bash
k drain node-x --ignore-daemonsets --delete-emptydir-data
# ... do maintenance ...
k uncordon node-x
```

## 11. PodDisruptionBudget (PDB)

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: web-pdb, namespace: my-app }
spec:
  minAvailable: 2          # always keep 2 healthy
  # OR
  maxUnavailable: 1        # max 1 down at a time
  selector:
    matchLabels: { app: web }
```

PDB blocks voluntary disruptions (drains, upgrades) that would violate the budget. Critical for HA workloads during cluster ops.

## 12. Quick self-check

1. What's the difference between nodeSelector and nodeAffinity?
2. What's the difference between a taint with effect `NoSchedule` and `NoExecute`?
3. What's the modern replacement for pod-anti-affinity for spreading pods across zones?
4. What's a PodDisruptionBudget for?
5. What's the command to evict pods from a node for maintenance?

(Answers: nodeSelector is equality-only label match, nodeAffinity supports In/NotIn/Exists/operators + required vs preferred; NoSchedule prevents new pods landing, NoExecute also evicts existing pods that don't tolerate; Pod Topology Spread Constraints; blocks voluntary disruptions like drains/upgrades that would violate minAvailable / maxUnavailable; `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data`.)



ewpage


# 72 — Liveness + Readiness Probes

## 1. Three kinds of probes

| Probe | Question | What if it fails |
|---|---|---|
| **Startup** | "Is the container ready to start receiving liveness/readiness probes?" | Container not killed yet — liveness deferred |
| **Liveness** | "Is the container still alive (not deadlocked)?" | Container restarted |
| **Readiness** | "Is the container ready to serve traffic?" | Pod removed from Service endpoints |

## 2. Probe types — HTTP, TCP, exec, gRPC

```yaml
# HTTP probe
livenessProbe:
  httpGet:
    path: /healthz
    port: 8000
    httpHeaders:
    - { name: X-Probe, value: liveness }
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 2
  successThreshold: 1
  failureThreshold: 3

# TCP probe (port open?)
livenessProbe:
  tcpSocket: { port: 5432 }
  initialDelaySeconds: 5

# Exec probe (command exit 0?)
livenessProbe:
  exec:
    command: [cat, /tmp/healthy]
  initialDelaySeconds: 5

# gRPC probe (K8s 1.24+)
livenessProbe:
  grpc:
    port: 50051
    service: my-service
```

## 3. Tuning probe parameters

- `initialDelaySeconds` — wait this long after container start before first probe
- `periodSeconds` — how often (default 10)
- `timeoutSeconds` — how long before probe times out (default 1)
- `successThreshold` — consecutive successes to consider healthy (default 1)
- `failureThreshold` — consecutive failures to declare unhealthy (default 3)

Common bug: `initialDelaySeconds: 0` + slow-starting app → liveness fails before app boots → restart loop.

## 4. Startup probes (the slow-start fix)

For apps that take 30s-5min to start (Java apps, complex initialization):
```yaml
startupProbe:
  httpGet: { path: /healthz, port: 8000 }
  failureThreshold: 30          # 30 × 10s = 5min max startup time
  periodSeconds: 10

livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  periodSeconds: 10              # only runs after startupProbe succeeds
```

Startup probe gives long startup window without making liveness probe wait that long every time.

## 5. Liveness vs Readiness — when each matters

- **Liveness fails** → container restarted (the K8s self-heal)
- **Readiness fails** → traffic stops being sent to pod (Service endpoint removed) but pod stays alive

**Common mistake**: same endpoint for both. Then:
- Liveness fails because DB is slow → container restarted (which doesn't fix the DB)
- Cascading restarts hide the real issue

**Better pattern**:
- **Liveness** = "am I deadlocked / unable to serve at all" (rare check, simple)
- **Readiness** = "can I serve a request right now (DB connected, etc.)"

```yaml
livenessProbe:
  httpGet: { path: /liveness, port: 8000 }   # /liveness only checks the app's own process
readinessProbe:
  httpGet: { path: /readiness, port: 8000 }  # /readiness checks DB, cache, dependencies
```

## 6. The "no liveness probe" school

Some teams argue: don't use liveness probes at all. Reasoning:
- Restarts mask the real issue
- Better to alert + investigate than to silently restart
- Crash + actual unrecoverable state → app should `exit(1)` itself, then K8s restarts

Use liveness probe only when you know a real deadlock condition exists that restart fixes.

## 7. Health endpoint patterns

```python
# Python Flask example
@app.route('/liveness')
def liveness():
    return jsonify({"status": "ok"}), 200

@app.route('/readiness')
def readiness():
    try:
        db.execute("SELECT 1")
        cache.ping()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503
```

Or use a library like `py-healthcheck`. Frameworks (FastAPI, NestJS, Spring Boot) have built-in.

## 8. Service traffic + readiness

K8s Service routes only to **Ready** endpoints:
```bash
k get endpoints my-svc
# NAME    ENDPOINTS              AGE
# my-svc  10.244.0.5:80,...      5m

# Endpoints with NotReady (failing readiness)
k get endpointslices -A
```

A pod stuck NotReady = no traffic; safe to investigate without user impact.

## 9. PreStop hooks (graceful shutdown)

```yaml
lifecycle:
  preStop:
    exec:
      command: ['sh', '-c', 'sleep 15 && /app/graceful-shutdown.sh']
```

Sequence on pod shutdown:
1. Pod marked Terminating
2. **Removed from Service endpoints** (no more new traffic)
3. PreStop hook runs
4. SIGTERM sent to PID 1
5. `terminationGracePeriodSeconds` (default 30) countdown
6. If still running, SIGKILL

For LB latency (~5-10s for SG → endpoint update propagation), a `sleep 10` in preStop avoids dropping in-flight requests.

## 10. CKA exam: configuring probes

```yaml
apiVersion: v1
kind: Pod
metadata: { name: web }
spec:
  containers:
  - name: web
    image: nginx
    ports: [{ containerPort: 80 }]
    livenessProbe:
      httpGet: { path: /, port: 80 }
      initialDelaySeconds: 5
      periodSeconds: 5
    readinessProbe:
      httpGet: { path: /, port: 80 }
      initialDelaySeconds: 2
      periodSeconds: 5
```

Quick imperative-edit pattern:
```bash
k run web --image=nginx --dry-run=client -o yaml > web.yaml
# Edit web.yaml to add probes
k apply -f web.yaml
```

Verify:
```bash
k get pod web                     # READY column should be 1/1
k describe pod web | grep -i liveness
```

## 11. Probes + autoscaling interaction

HPA scales based on metrics. Without readiness probes:
- New pods join Service endpoints immediately
- New pods get traffic before they're warm
- Latency spike on each scale-up

With readiness probes: new pods get traffic only when actually ready. **Always configure readiness for autoscaled workloads.**

## 12. Quick self-check

1. What happens when a liveness probe fails?
2. What happens when a readiness probe fails?
3. Why is using the same endpoint for both probes an anti-pattern?
4. What problem do startup probes solve?
5. What does the preStop hook give you?

(Answers: container is restarted; pod is removed from Service endpoints (no traffic) but stays alive; liveness check failing because DB slow causes restart that doesn't fix DB — cascading restarts hide root cause; gives long startup window without making liveness probe wait that long every interval — for slow-starting apps; chance to gracefully drain in-flight work before SIGTERM — typically a sleep to wait for LB to stop routing traffic + the actual shutdown.)



ewpage


# 73 — Deployment Strategies — Rolling Update + ReplicaSet

## 1. The Deployment object — what it gives you

- **Declarative scale** (`replicas: N`)
- **Rolling updates** — gradually replace old pods with new
- **Rollback** — revert to a previous revision
- **History** — track which version is which

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: web }
spec:
  replicas: 5
  revisionHistoryLimit: 10
  selector: { matchLabels: { app: web } }
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%          # up to 25% extra pods during update
      maxUnavailable: 25%    # up to 25% can be unavailable
  template:
    metadata: { labels: { app: web } }
    spec:
      containers:
      - { name: web, image: my-app:1.2.3 }
```

## 2. ReplicaSet — managed by Deployment

You almost never create ReplicaSets directly. Deployment creates them:
```bash
k get deploy,rs,pods
# deployment.apps/web   5/5   5   5   2m
# replicaset.apps/web-abc   5   5   5   2m       (current)
# replicaset.apps/web-xyz   0   0   0   10m      (previous; kept for rollback)
```

When you update the Deployment's template:
1. Deployment creates a new ReplicaSet
2. New RS scales up, old RS scales down (rolling)
3. Old RS kept (at 0 replicas) for rollback up to `revisionHistoryLimit`

## 3. Deployment strategies

### RollingUpdate (default)
Gradually replace old pods with new. Configurable via `maxSurge` + `maxUnavailable`.

### Recreate
Delete all old pods first, then create new. Causes downtime.
```yaml
spec:
  strategy:
    type: Recreate
```
Use when:
- App can't run multiple versions simultaneously (e.g., schema migration that breaks old version)
- Single-replica apps where downtime is acceptable

## 4. Beyond Deployments — Argo Rollouts (Module 33)

For more advanced strategies (canary, blue-green, A/B):
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: web }
spec:
  strategy:
    canary:
      steps:
      - { setWeight: 20 }
      - { pause: { duration: 5m } }
      - { setWeight: 50 }
      - { pause: {} }     # wait for manual continue
      - { setWeight: 100 }
```

Or blue-green:
```yaml
spec:
  strategy:
    blueGreen:
      activeService: web-active
      previewService: web-preview
      autoPromotionEnabled: false
```

## 5. Performing an update

```bash
# Imperative (quick)
k set image deployment/web web=my-app:1.2.4

# Declarative
# (edit YAML, then)
k apply -f web.yaml

# Wait for rollout
k rollout status deployment/web --timeout=5m

# Watch
k rollout status deployment/web --watch
```

## 6. Rollback

```bash
# View history
k rollout history deployment/web

# Check a specific revision's spec
k rollout history deployment/web --revision=3

# Rollback to previous
k rollout undo deployment/web

# Rollback to specific revision
k rollout undo deployment/web --to-revision=3

# Pause / resume (useful for multi-step changes)
k rollout pause deployment/web
# Make multiple changes
k rollout resume deployment/web
```

## 7. The change-cause annotation

```bash
k annotate deployment web kubernetes.io/change-cause="upgrade to 1.2.4" --overwrite
k set image deployment/web web=my-app:1.2.4
```

The change-cause shows in `rollout history`:
```
REVISION  CHANGE-CAUSE
1         <none>
2         upgrade to 1.2.4
```

## 8. RollingUpdate parameters in depth

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%           # extra pods during update
    maxUnavailable: 25%     # how many can be unavailable
```

With 8 replicas:
- `maxSurge: 25%` → up to 2 extra pods (10 max during update)
- `maxUnavailable: 25%` → up to 2 fewer pods (6 min during update)

Tuning:
- **High velocity, no downtime tolerated**: `maxSurge: 50%, maxUnavailable: 0`
- **Limited capacity**: `maxSurge: 0, maxUnavailable: 25%`
- **Default**: `maxSurge: 25%, maxUnavailable: 25%`

## 9. Scaling

```bash
# Imperative
k scale deployment web --replicas=10

# Declarative (in YAML)
spec:
  replicas: 10

# Autoscaling (HPA — Module 70)
k autoscale deployment web --min=3 --max=20 --cpu-percent=70
```

If HPA is set, don't fight it in the YAML (HPA wins; manual scale only takes effect transiently).

## 10. DaemonSet — one pod per node

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata: { name: fluent-bit, namespace: logging }
spec:
  selector: { matchLabels: { app: fluent-bit } }
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
  template:
    metadata: { labels: { app: fluent-bit } }
    spec:
      tolerations:
      - { operator: Exists, effect: NoSchedule }      # run on tainted nodes too
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:3
```

DaemonSets are how you run "one pod per node": logging agents, metrics agents, CSI drivers, CNI components.

## 11. StatefulSet — ordered, stable

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: postgres }
spec:
  serviceName: postgres-headless
  replicas: 3
  selector: { matchLabels: { app: postgres } }
  template:
    metadata: { labels: { app: postgres } }
    spec:
      containers:
      - { name: postgres, image: postgres:17 }
  volumeClaimTemplates:
  - metadata: { name: data }
    spec:
      accessModes: [ReadWriteOnce]
      resources: { requests: { storage: 10Gi } }
```

StatefulSet guarantees:
- Pods named `postgres-0`, `postgres-1`, `postgres-2` (stable)
- Ordered startup (0 → 1 → 2)
- Ordered shutdown (2 → 1 → 0)
- Stable DNS: `postgres-0.postgres-headless.<ns>.svc.cluster.local`
- Per-pod PVC (templated)

For databases + anything requiring stable identity.

## 12. CKA Exam tasks

Common rolling-update tasks:
1. Create a Deployment with N replicas
2. Update image
3. Roll back
4. Set maxSurge / maxUnavailable
5. Pause / resume

Practice the imperative + declarative flows until both are muscle memory.

## 13. Quick self-check

1. What's the difference between a Deployment and a ReplicaSet?
2. What's the difference between RollingUpdate and Recreate strategy?
3. What does `revisionHistoryLimit: 10` give you?
4. When would you use a DaemonSet?
5. What does StatefulSet guarantee that Deployment doesn't?

(Answers: Deployment manages rolling updates by creating multiple ReplicaSets; ReplicaSet maintains N replicas of a pod template; RollingUpdate gradually replaces old with new (no downtime), Recreate deletes all old then creates new (downtime, but safe for incompatible versions); keeps last 10 old ReplicaSets at 0 replicas so you can roll back to any of them; one pod per node — for agents like logging/metrics/CSI/CNI; stable network identity per replica + ordered start/stop + per-pod PVC.)



ewpage


# 74 — etcd Backup + Restore

## Why this module is high-stakes

**etcd backup + restore is the highest-anxiety CKA exam task.** It tests Linux + certs + binary tools + careful steps. ~1-2 tasks per exam attempt. Practice this 10+ times until it's muscle memory.

## 1. What etcd stores

Everything K8s knows:
- All resource objects (Pods, Deployments, Services, ConfigMaps, Secrets, etc.)
- RBAC rules
- Custom resources
- Events (recent)

If etcd dies + you have no backup: **the cluster's data is gone**. Workloads might still run (pods on nodes), but the control plane has no memory of them.

## 2. The etcd architecture on a kubeadm cluster

- etcd runs as a **static pod** on the control plane node
- Manifest at `/etc/kubernetes/manifests/etcd.yaml`
- Data dir: `/var/lib/etcd/`
- TLS certs: `/etc/kubernetes/pki/etcd/`

## 3. etcdctl + endpoint setup

`etcdctl` (the etcd CLI) talks to etcd via mTLS. You need 4 things:
- Endpoint URL (`https://127.0.0.1:2379`)
- CA cert (`/etc/kubernetes/pki/etcd/ca.crt`)
- Client cert (`/etc/kubernetes/pki/etcd/server.crt`)
- Client key (`/etc/kubernetes/pki/etcd/server.key`)

Set env vars for convenience:
```bash
export ETCDCTL_API=3
export ETCDCTL_ENDPOINTS=https://127.0.0.1:2379
export ETCDCTL_CACERT=/etc/kubernetes/pki/etcd/ca.crt
export ETCDCTL_CERT=/etc/kubernetes/pki/etcd/server.crt
export ETCDCTL_KEY=/etc/kubernetes/pki/etcd/server.key
```

## 4. Verify connection

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health
# https://127.0.0.1:2379 is healthy: ...

# Member list
sudo etcdctl member list -w table
```

## 5. Backup — `snapshot save`

```bash
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup-$(date +%F-%H%M).db
```

Verify:
```bash
sudo etcdctl --write-out=table snapshot status /tmp/etcd-backup-*.db
# Hash, Revision, Total Keys, Total Size shown
```

## 6. Restore — `snapshot restore`

Restoring is involved because etcd must be **stopped** while you restore + the apiserver must restart.

### Steps

```bash
# 1. Stop kube-apiserver + etcd by moving their static pod manifests aside
sudo mv /etc/kubernetes/manifests/etcd.yaml /etc/kubernetes/manifests-bak/
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests-bak/

# Wait for pods to disappear
sudo crictl ps | grep -E 'etcd|apiserver'

# 2. Move existing data dir aside
sudo mv /var/lib/etcd /var/lib/etcd-bak

# 3. Restore from snapshot
sudo ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd

# 4. Fix permissions
sudo chown -R etcd:etcd /var/lib/etcd       # if etcd user exists; else stay root

# 5. Restore static pod manifests
sudo mv /etc/kubernetes/manifests-bak/etcd.yaml /etc/kubernetes/manifests/
sudo mv /etc/kubernetes/manifests-bak/kube-apiserver.yaml /etc/kubernetes/manifests/

# kubelet detects + restarts the pods
# 6. Verify
sudo crictl ps | grep -E 'etcd|apiserver'
k get nodes
k get pods -A
```

## 7. Exam shortcut: restore to a different path

The exam often asks you to restore the snapshot to a specific path, perhaps with a different etcd cluster config. If `--data-dir=/var/lib/etcd-restored`, then **edit the static pod manifest** (`/etc/kubernetes/manifests/etcd.yaml`) to point at the new dir:

```yaml
# In etcd.yaml — change hostPath:
volumes:
- name: etcd-data
  hostPath:
    path: /var/lib/etcd-restored        # ← updated
```

kubelet reapplies the static pod with the new mount.

## 8. Backup automation

Production: backup every N hours via cron + write to S3:

```bash
#!/bin/bash
set -euo pipefail
TS=$(date +%F-%H%M)
sudo ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-snapshot-$TS.db

aws s3 cp /tmp/etcd-snapshot-$TS.db s3://my-etcd-backups/$TS.db --sse aws:kms
rm /tmp/etcd-snapshot-$TS.db
```

Cron entry:
```
0 */6 * * * /usr/local/bin/etcd-backup.sh >> /var/log/etcd-backup.log 2>&1
```

## 9. EKS / GKE / AKS — managed etcd

For managed K8s services, **AWS/GCP/Azure manage etcd backup automatically**. You don't run `etcdctl snapshot save`. EKS retains the cluster state and disaster recovery is on AWS.

CKA exam still tests etcd backup/restore (on self-managed kubeadm clusters). It's required knowledge even if your job uses EKS.

## 10. Alternatives to managing etcd

- **EKS / GKE / AKS** — managed (don't think about etcd)
- **kOps** — Kubernetes Operations; manages etcd via the etcd-manager
- **Rancher / RKE2** — opinionated etcd setup with backup
- **k3s** — uses SQLite by default (single-node) or external etcd / Postgres / MySQL

## 11. Restoring etcd — exam-task pseudocode

A typical exam task:
> "Take a backup of etcd to `/tmp/etcd-backup.db`. Restore it to a new data dir `/var/lib/etcd-from-backup` and configure etcd to use this new dir."

```bash
# Backup (assume env vars set)
sudo etcdctl snapshot save /tmp/etcd-backup.db

# Restore
sudo etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-from-backup

# Edit /etc/kubernetes/manifests/etcd.yaml to use new data dir
# Find:
#   --data-dir=/var/lib/etcd
# Change to:
#   --data-dir=/var/lib/etcd-from-backup
# And the volume hostPath similarly

# kubelet reapplies; check
sudo crictl ps | grep etcd
k get nodes
```

## 12. Quick self-check

1. Where do etcd's TLS certs live on a kubeadm cluster?
2. What three flags must you pass to etcdctl to authenticate (besides endpoint)?
3. What environment variable selects etcdctl API v3?
4. Why must kube-apiserver be stopped during restore?
5. What's the difference between EKS-managed etcd and kubeadm-managed etcd?

(Answers: `/etc/kubernetes/pki/etcd/`; `--cacert`, `--cert`, `--key`; `ETCDCTL_API=3`; apiserver would write to old etcd while you're restoring → corruption / data inconsistency; EKS = AWS handles backup/restore/HA, kubeadm = you do it via etcdctl + cron + manifests/.)



ewpage


# 75 — Kubernetes REST API

## 1. Everything is a REST call

`kubectl` is a CLI wrapper around HTTP REST calls to `kube-apiserver`. Knowing this:
- Lets you debug "kubectl says X" by inspecting the raw API
- Lets you write tools in any language
- Lets you understand watch streams, paging, server-side apply

## 2. The API tree

```
/api/v1/...                       # core API group (Pods, Services, etc.)
/apis/apps/v1/...                 # apps group (Deployment, StatefulSet)
/apis/networking.k8s.io/v1/...    # networking
/apis/rbac.authorization.k8s.io/v1/...
/apis/batch/v1/...
/apis/storage.k8s.io/v1/...
/apis/policy/v1/...
/apis/<group>/<version>/...       # custom resources via CRDs
```

```bash
k api-resources                   # all resources + their groups
k api-versions                    # all group/versions enabled
```

## 3. URL structure

```
GET  /api/v1/namespaces/my-app/pods
GET  /api/v1/namespaces/my-app/pods/my-pod
GET  /apis/apps/v1/namespaces/my-app/deployments
GET  /apis/apps/v1/namespaces/my-app/deployments/my-deploy
POST /api/v1/namespaces/my-app/pods        # body = pod spec
DELETE /api/v1/namespaces/my-app/pods/my-pod
PATCH  /api/v1/namespaces/my-app/pods/my-pod
```

## 4. Accessing API with `kubectl proxy`

The easiest way (handles auth for you):
```bash
k proxy &
# Starts a local proxy at http://127.0.0.1:8001

curl http://127.0.0.1:8001/api/v1/namespaces/default/pods
curl http://127.0.0.1:8001/apis/apps/v1/namespaces/default/deployments
```

Use this for ad-hoc exploration or scripts running on the same host as kubectl.

## 5. Direct access (without proxy)

```bash
APISERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
TOKEN=$(kubectl create token default --namespace=my-app)

curl -X GET "$APISERVER/api/v1/namespaces/my-app/pods" \
  -H "Authorization: Bearer $TOKEN" \
  --cacert /path/to/ca.crt
```

For ServiceAccount in a pod (the typical case):
```bash
# Inside a pod
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

curl --cacert $CACERT \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/pods
```

## 6. Verbs (HTTP methods)

| HTTP | K8s verb |
|---|---|
| GET (collection) | list |
| GET (single) | get |
| GET ?watch=1 | watch |
| POST | create |
| PUT | update (full replace) |
| PATCH (merge / strategic) | patch |
| DELETE | delete |
| DELETE (collection) | deletecollection |

## 7. Listing + filtering

```bash
# All pods cluster-wide
curl http://127.0.0.1:8001/api/v1/pods

# Pods in namespace
curl http://127.0.0.1:8001/api/v1/namespaces/my-app/pods

# Filter by label
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?labelSelector=app=web"

# Filter by field
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?fieldSelector=status.phase=Running"

# Page through large collections
curl "http://127.0.0.1:8001/api/v1/pods?limit=500&continue=<continueToken>"
```

## 8. Watch streams

```bash
# Long-poll for changes
curl "http://127.0.0.1:8001/api/v1/namespaces/my-app/pods?watch=1"
# Stream emits ADDED / MODIFIED / DELETED events
```

This is how controllers + operators stay synchronized with cluster state.

## 9. The `kubectl --v=N` debug

Add verbosity to see HTTP calls kubectl is making:
```bash
k get pods --v=8
# Shows the actual HTTP request + response

k get pods --v=10
# Shows even more (request body for POSTs)
```

Useful for "what is kubectl actually sending?" debugging.

## 10. Creating resources via API

```bash
cat <<EOF | curl -X POST \
  -H "Content-Type: application/yaml" \
  --data-binary @- \
  http://127.0.0.1:8001/api/v1/namespaces/default/pods
apiVersion: v1
kind: Pod
metadata: { name: api-created-pod }
spec:
  containers:
  - { name: nginx, image: nginx:1.27-alpine }
EOF
```

Or JSON:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"v1","kind":"Pod","metadata":{"name":"x"},"spec":{"containers":[{"name":"n","image":"nginx"}]}}' \
  http://127.0.0.1:8001/api/v1/namespaces/default/pods
```

## 11. Patches

Three patch types:
- **Strategic Merge Patch** (default; K8s-aware, smart on arrays)
- **JSON Merge Patch** (RFC 7396; simple object merge)
- **JSON Patch** (RFC 6902; operations: add/remove/replace)

```bash
k patch deployment web -p '{"spec":{"replicas":10}}'

k patch deployment web --type=json -p='[{"op": "replace", "path": "/spec/replicas", "value": 10}]'

k patch deployment web --type=merge -p '{"spec":{"replicas":10}}'
```

## 12. Server-Side Apply

The modern way to apply changes:
```bash
k apply -f deployment.yaml --server-side
```

Each "manager" (user or controller) owns specific fields. K8s tracks ownership; conflicts surface explicitly. Better for GitOps + multi-controller scenarios.

## 13. CRDs — extending the API

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata: { name: backups.acme.io }
spec:
  group: acme.io
  versions:
  - name: v1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              schedule: { type: string }
              retention: { type: integer }
  scope: Namespaced
  names:
    plural: backups
    singular: backup
    kind: Backup
    shortNames: [bkp]
```

Once applied: `kubectl get backups`, `kubectl create -f backup.yaml`. CRDs are how operators extend K8s.

## 14. Quick self-check

1. What does `kubectl proxy` do?
2. How do you authenticate from a pod to the K8s API?
3. What's the difference between Strategic Merge Patch and JSON Patch?
4. What does `kubectl --v=8` show you?
5. What's a CRD and what does it enable?

(Answers: starts a local HTTP proxy that handles auth — you can curl http://localhost:8001 without managing tokens/certs; mount ServiceAccount token + ca.crt + namespace at /var/run/secrets/kubernetes.io/serviceaccount/ + use bearer token; Strategic is K8s-aware (knows arrays are lists vs sets), JSON Patch is operation-based (add/remove/replace at paths); the actual HTTP request kubectl makes to the API — useful for debugging; Custom Resource Definition — extends the API with new resource kinds — what operators use.)



ewpage


# 76 — Cluster Upgrade with kubeadm

## 1. Why upgrades matter

- K8s ships 3 minor versions/year (Apr / Aug / Dec)
- Each version supported ~14 months
- Falling behind = unsupported (no security patches) + can't take advantage of new features
- Compliance requires current minor for many regulated workloads

## 2. The upgrade rule

**Upgrade one minor at a time.** v1.30 → v1.31 → v1.32. Never skip (e.g., v1.30 → v1.32 directly).

Patches within a minor (v1.31.0 → v1.31.5) are safe to do in one shot.

## 3. Upgrade order on a kubeadm cluster

```
1. Drain + upgrade FIRST control-plane node
2. Drain + upgrade REMAINING control-plane nodes (if HA)
3. Drain + upgrade WORKER nodes (one at a time)
4. Update kubeconfig clients on your workstation
```

The control plane upgrades before workers. **Kubelet on workers must not be newer than the control plane** (skew policy: control-plane >= node).

## 4. Pre-upgrade checks

```bash
# Current versions
k get nodes -o wide
k version

# Check workloads health
k get pods -A | grep -v Running

# Backup etcd (Module 74)
sudo etcdctl snapshot save /tmp/pre-upgrade.db

# Check for deprecated APIs
kubectl api-resources --verbs=list --namespaced -o name | \
  xargs -n 1 kubectl get --show-kind --ignore-not-found -A
```

Tools for deprecation scanning:
- **kubent** (`kubent` / `kube-no-trouble`) — scans manifests + cluster for deprecated APIs
- **pluto** (Fairwinds) — same idea

## 5. Upgrade first control-plane node

```bash
# 1. Update kubeadm to target version
sudo apt-mark unhold kubeadm
sudo apt-get update
sudo apt-cache madison kubeadm | head -10        # see versions available
sudo apt-get install -y kubeadm=1.31.3-1.1
sudo apt-mark hold kubeadm

# 2. Verify
kubeadm version

# 3. Plan the upgrade
sudo kubeadm upgrade plan

# 4. Drain the node
kubectl drain <cp-node> --ignore-daemonsets

# 5. Apply
sudo kubeadm upgrade apply v1.31.3

# 6. Uncordon
kubectl uncordon <cp-node>

# 7. Update kubelet + kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet=1.31.3-1.1 kubectl=1.31.3-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

## 6. Upgrade remaining control-plane nodes (HA)

Same as above EXCEPT use `kubeadm upgrade node` (not `apply`):
```bash
sudo kubeadm upgrade node
```

## 7. Upgrade worker nodes

For each worker:
```bash
# 1. Drain (from any control-plane node)
kubectl drain <worker> --ignore-daemonsets --delete-emptydir-data

# 2. SSH into worker

# 3. Update kubeadm
sudo apt-mark unhold kubeadm
sudo apt-get install -y kubeadm=1.31.3-1.1
sudo apt-mark hold kubeadm

# 4. Upgrade kubelet config
sudo kubeadm upgrade node

# 5. Update kubelet + kubectl
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet=1.31.3-1.1 kubectl=1.31.3-1.1
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet

# 6. Uncordon
kubectl uncordon <worker>
```

## 8. Verify

```bash
k get nodes
# All should show new version
# control-plane01   Ready   1.31.3
# worker01          Ready   1.31.3
# worker02          Ready   1.31.3

k version
k get pods -A | grep -v Running     # everything healthy?
```

## 9. Common upgrade pitfalls

- **Skipping minor versions** — supported skew is +1 minor only; v1.30 → v1.32 will fail
- **Forgetting to drain** — pods on the node get killed unpredictably
- **CNI conflicts** — some CNI plugins require their own upgrade in concert
- **Deprecated APIs in manifests** — `pluto` / `kubent` to check before
- **kubelet hold** — if you don't `apt-mark hold`, an unrelated `apt upgrade` can break the cluster
- **DaemonSet pods not draining** — must use `--ignore-daemonsets`
- **Stateful workloads with `emptyDir`** — `--delete-emptydir-data` for drain to proceed

## 10. EKS upgrade (the easier path)

EKS:
- Control plane: AWS upgrades; you click "upgrade" in console / Terraform
- Node groups: AWS upgrades; rolling update of EC2 instances
- Add-ons: separately versioned (VPC CNI, CoreDNS, kube-proxy) — upgrade alongside

```bash
aws eks update-cluster-version --name my-cluster --kubernetes-version 1.31

# For managed node groups
aws eks update-nodegroup-version --cluster-name my-cluster --nodegroup-name workers

# For Karpenter-managed nodes
# Update Karpenter NodePool's image; Karpenter rolls nodes
```

EKS supports skipping minor versions in some cases — but follow the AWS guide carefully.

## 11. CKA exam — upgrade tasks

Typical exam task:
> "Upgrade the cluster's control plane and nodes from v1.30 to v1.31. Make sure to drain the nodes before upgrading and uncordon them after."

Run the 10 commands above. Don't forget:
- `kubeadm` → upgrade plan → upgrade apply / upgrade node
- `kubelet` + `kubectl` packages
- `systemctl daemon-reload` + restart kubelet
- `drain` before, `uncordon` after

## 12. Quick self-check

1. What's the version skew policy between control plane and nodes?
2. Why use `kubeadm upgrade apply` on first CP node vs `upgrade node` on others?
3. What tools detect deprecated API usage before an upgrade?
4. Why `apt-mark hold kubelet kubeadm kubectl`?
5. What's different about an EKS upgrade vs kubeadm?

(Answers: control plane >= node, max 1 minor version skew; first CP defines the new control plane state, subsequent CPs and workers just sync; pluto, kubent (kube-no-trouble); prevents `apt upgrade` from accidentally updating these to incompatible versions; EKS = AWS handles control plane upgrade in place, you only roll node groups + add-ons.)



ewpage


# 77 — Kube Contexts (Multi-Cluster)

## 1. The kubeconfig file

`~/.kube/config` (or `$KUBECONFIG` if set). Three top-level sections:

```yaml
apiVersion: v1
kind: Config

clusters:
- name: prod
  cluster:
    server: https://prod.example.com:6443
    certificate-authority: /home/vatsal/.kube/prod-ca.crt
- name: dev
  cluster:
    server: https://dev.example.com:6443
    insecure-skip-tls-verify: true

users:
- name: alice
  user:
    client-certificate: /home/vatsal/.kube/alice.crt
    client-key: /home/vatsal/.kube/alice.key
- name: bob
  user:
    token: eyJhbGciOiJSUzI1NiIs...

contexts:
- name: prod-as-alice
  context:
    cluster: prod
    user: alice
    namespace: my-app
- name: dev-as-bob
  context:
    cluster: dev
    user: bob
    namespace: testing

current-context: prod-as-alice
```

A **context** binds (cluster, user, namespace) into a name.

## 2. The kubectl config commands

```bash
# View
k config view                                 # full config
k config view --minify                        # just current
k config view --minify -o jsonpath='{.contexts[0].context.namespace}'

# Contexts
k config get-contexts                         # list all
k config current-context                      # show active
k config use-context dev-as-bob               # switch

# Add a cluster
k config set-cluster prod \
  --server=https://prod:6443 \
  --certificate-authority=/path/ca.crt

# Add a user (cert-based)
k config set-credentials alice \
  --client-certificate=/path/alice.crt \
  --client-key=/path/alice.key

# Add a user (token-based)
k config set-credentials bob --token=<jwt>

# Add a context
k config set-context prod-as-alice \
  --cluster=prod --user=alice --namespace=my-app

# Set namespace in current context
k config set-context --current --namespace=my-app

# Delete things
k config delete-context dev-as-bob
k config delete-cluster dev
k config unset users.bob
```

## 3. Multiple kubeconfig files

```bash
export KUBECONFIG=~/.kube/config:~/.kube/eks-prod.yaml:~/.kube/eks-dev.yaml
k config get-contexts             # merges all 3 files
```

Merging is in-memory; doesn't write. Use this when you have separate config files from different sources.

## 4. Helper tools

### kubectx + kubens
The killer multi-cluster productivity tools (https://github.com/ahmetb/kubectx):

```bash
brew install kubectx              # installs kubectx + kubens

kubectx                           # list contexts
kubectx dev-as-bob                # switch
kubectx -                         # switch to previous

kubens                            # list namespaces
kubens my-app                     # set current namespace
kubens -                          # previous
```

### k9s
TUI for cluster management — `brew install k9s`. Visual replacement for many kubectl commands.

### kubie
Like kubectx but spawns a subshell per context — prevents accidental context drift.

## 5. Multi-context workflow patterns

### Pattern 1: one context per cluster, switch via kubectx
```bash
kubectx prod        # work in prod
kubectx staging     # switch to staging
```

Risk: accidental prod ops. Mitigate with shell prompt showing current context.

### Pattern 2: one terminal per cluster
```bash
# Terminal 1
export KUBECONFIG=~/.kube/prod.yaml

# Terminal 2
export KUBECONFIG=~/.kube/staging.yaml
```

Less ambiguous.

### Pattern 3: kubie (subshell per context)
```bash
kubie ctx prod          # opens a subshell with prod context
# work, then exit
```

## 6. Shell prompt that shows context

Add to `~/.bashrc` or `~/.zshrc`:
```bash
function kctx() {
  k config current-context 2>/dev/null
}
PS1='[$(kctx)] \w \$ '

# Or for zsh:
PROMPT='[$(kctx)] %~ %# '
```

Or use **starship** prompt with the `kubernetes` module:
```toml
[kubernetes]
disabled = false
detect_files = ['k8s.yaml']
```

## 7. EKS update-kubeconfig

```bash
aws eks update-kubeconfig --name my-cluster --region us-east-1 \
  --alias my-cluster-prod
```

This:
- Adds a cluster entry pointing at EKS API
- Adds a user entry that uses `aws eks get-token` for auth (refreshing every ~15 min)
- Adds a context binding them, named via `--alias`
- Switches `current-context` to it

```bash
# For different role
aws eks update-kubeconfig --name my-cluster --profile prod-admin --alias prod-admin
```

## 8. Switching role + cluster via context

```bash
# Configure once
aws eks update-kubeconfig --name dev --profile dev --alias dev-readonly
aws eks update-kubeconfig --name dev --profile dev-admin --alias dev-admin
aws eks update-kubeconfig --name prod --profile prod-readonly --alias prod-readonly
aws eks update-kubeconfig --name prod --profile prod-admin --alias prod-admin

# Then daily
kubectx dev-readonly
# ... work safely ...
kubectx prod-admin
# ... privileged ops in prod ...
```

## 9. The "wrong context" footgun + mitigations

You ran `kubectl delete pod x` in prod thinking it was dev. The classic mistake.

Mitigations:
- **Prompt shows context** (kctx in PS1)
- **Different terminal colors per context** (e.g., red for prod, green for dev)
- **kubie subshell** isolates context
- **kube-ps1** plugin (oh-my-zsh)
- **Confirmation for destructive ops in prod** — alias `kdelete-prod` with confirm prompt
- **RBAC** — readonly role on prod for daily work; assume admin only when needed

## 10. CKA exam — context tasks

Typical exam task:
> "Switch to context `kubernetes-admin@cluster2`. Find the pod named `important-pod` in namespace `tools`."

```bash
k config use-context kubernetes-admin@cluster2
k get pod important-pod -n tools
```

Easy if you remember to use `use-context` (not `set-context`).

## 11. Quick self-check

1. What 3 things does a context bind?
2. How do you merge multiple kubeconfig files?
3. What does `aws eks update-kubeconfig` actually write to your kubeconfig?
4. What's `kubectx` and `kubens`?
5. How do you set the current namespace without typing `-n` every command?

(Answers: cluster + user + namespace; `KUBECONFIG=file1:file2:file3` — kubectl reads all and merges in memory; cluster entry + user entry (using aws eks get-token for auth) + context binding them; CLI helpers for switching contexts and namespaces faster than typing `kubectl config use-context`; `k config set-context --current --namespace=my-ns`.)



ewpage


# 78 — Certificate Management + Renewal

## 1. The K8s PKI

K8s uses PKI everywhere:

```
/etc/kubernetes/pki/
├── ca.crt + ca.key                 # cluster root CA
├── apiserver.crt + apiserver.key
├── apiserver-kubelet-client.crt + .key
├── front-proxy-ca.crt + .key
├── front-proxy-client.crt + .key
├── sa.key + sa.pub                 # ServiceAccount signing
└── etcd/
    ├── ca.crt + ca.key
    ├── server.crt + .key
    ├── peer.crt + .key
    └── healthcheck-client.crt + .key
```

Plus per-kubelet certs in `/var/lib/kubelet/pki/`.

## 2. Default cert expiry

- **kubeadm-generated certs**: 1 year (365 days)
- **Cluster CA**: 10 years (rebuilt rarely)
- **kubelet client cert**: auto-rotated by default

Year-old self-managed clusters: this is the #1 cause of "cluster suddenly broken" — certs expired.

## 3. Checking certificate expiration

```bash
sudo kubeadm certs check-expiration

CERTIFICATE                EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
admin.conf                 Mar 15, 2026 12:34 UTC   285d            no
apiserver                  Mar 15, 2026 12:34 UTC   285d            no
apiserver-kubelet-client   Mar 15, 2026 12:34 UTC   285d            no
controller-manager.conf    Mar 15, 2026 12:34 UTC   285d            no
etcd-healthcheck-client    Mar 15, 2026 12:34 UTC   285d            no
etcd-peer                  Mar 15, 2026 12:34 UTC   285d            no
etcd-server                Mar 15, 2026 12:34 UTC   285d            no
front-proxy-client         Mar 15, 2026 12:34 UTC   285d            no
scheduler.conf             Mar 15, 2026 12:34 UTC   285d            no

CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
ca                      Jul 14, 2034 12:34 UTC   3000d           no
etcd-ca                 Jul 14, 2034 12:34 UTC   3000d           no
front-proxy-ca          Jul 14, 2034 12:34 UTC   3000d           no
```

## 4. Manual cert renewal

```bash
# Renew all certs (apiserver, kubelet-client, controller-mgr, scheduler, etcd, etc.)
sudo kubeadm certs renew all

# Or specific cert
sudo kubeadm certs renew apiserver
sudo kubeadm certs renew kubelet-client
sudo kubeadm certs renew etcd-server

# Verify
sudo kubeadm certs check-expiration
```

After renewal, **restart control plane components** (they don't pick up new certs automatically):

```bash
# Restart by moving + restoring static pod manifests (kubelet detects + restarts)
sudo mv /etc/kubernetes/manifests/*.yaml /tmp/
sleep 15
sudo mv /tmp/*.yaml /etc/kubernetes/manifests/
```

Or restart kubelet itself which restarts static pods:
```bash
sudo systemctl restart kubelet
```

## 5. Inspecting a cert manually

```bash
# What's in the file
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout

# Just expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate

# Decode the kubeconfig admin cert
k config view --raw -o jsonpath='{.users[?(@.name=="kubernetes-admin")].user.client-certificate-data}' | \
  base64 -d | openssl x509 -text -noout | grep -E "Not Before|Not After|Subject:"
```

## 6. kubelet client cert auto-rotation

The kubelet client cert (for kubelet → apiserver) auto-rotates **if** these flags are set on kubelet:
- `--rotate-certificates=true`
- `--rotate-server-certificates=true` (for kubelet's server cert)

Check on a node:
```bash
sudo grep -E "rotate" /var/lib/kubelet/config.yaml
# rotateCertificates: true
# serverTLSBootstrap: true
```

kubeadm enables these by default since v1.17. Older clusters may not have them.

When a rotation happens, kubelet:
1. Generates a new key
2. Submits a CSR
3. Controller approves (if signer is configured for auto-approval) or you manually approve
4. Picks up the new cert

## 7. Manually approving kubelet CSRs

```bash
# Pending CSRs
k get csr

# Approve
k certificate approve <csr-name>

# Deny
k certificate deny <csr-name>
```

## 8. cert-manager — for application-level certs

Different from K8s internal PKI: **cert-manager** issues TLS certs for your Ingress endpoints.

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef: { name: letsencrypt-prod }
    solvers:
    - http01: { ingress: { ingressClassName: nginx } }
```

```yaml
# Ingress requests a cert via annotation
metadata:
  annotations: { cert-manager.io/cluster-issuer: letsencrypt-prod }
spec:
  tls:
  - hosts: [app.example.com]
    secretName: app-tls
```

cert-manager talks to Let's Encrypt, gets a cert, stores in a K8s Secret. Renews automatically.

## 9. The CKA exam — certificate tasks

Typical task:
> "The apiserver-kubelet-client certificate expires in 30 days. Renew it. Verify the new cert is in use."

```bash
sudo kubeadm certs check-expiration | grep apiserver-kubelet-client
sudo kubeadm certs renew apiserver-kubelet-client
# Restart static pods (move manifests)
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
sleep 15
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
# Verify
sudo kubeadm certs check-expiration | grep apiserver-kubelet-client
```

## 10. EKS / GKE / AKS — managed certs

EKS:
- Cluster control plane certs: AWS manages
- Cluster CA: AWS manages
- kubelet client cert: auto-rotated (or AWS-managed for new nodes)
- Anything else (workload TLS): cert-manager

You almost never touch EKS internal certs. The CKA still tests it because the exam is on kubeadm clusters.

## 11. Common cert-related cluster failures

| Symptom | Likely cause |
|---|---|
| `Unable to connect to the server: x509: certificate has expired` | API server cert expired |
| `Unable to authenticate the request due to an error: invalid bearer token` | SA token signing cert issue |
| kubelet logs `failed to renew bootstrap certificate` | CSR approval not happening; check controller-manager |
| etcd peers can't talk: `tls: bad certificate` | etcd peer certs expired |
| Webhook calls fail: `x509: certificate has expired` | webhook cert (e.g., from cert-manager) expired |

## 12. Quick self-check

1. What's the default expiration for kubeadm-generated certs?
2. What command checks all K8s cert expirations?
3. After renewing certs, why do you need to restart control plane components?
4. What's the difference between kubeadm-managed certs and cert-manager?
5. Why does the kubelet client cert auto-rotate by default in modern clusters?

(Answers: 1 year (365 days); `sudo kubeadm certs check-expiration`; static pods cache the old cert in memory — moving the manifest forces kubelet to restart them with the new cert; kubeadm manages K8s internal PKI (apiserver, kubelet, etcd, etc.), cert-manager manages TLS for application Ingresses; flags `--rotate-certificates=true` enable kubelet to submit CSRs and pick up new cert before old one expires — kubeadm sets this by default since v1.17.)



ewpage


# 79 — NetworkPolicy Deep

## 1. What NetworkPolicy is

Pod-level firewall rules. By default, K8s pods can talk to any other pod. NetworkPolicy lets you restrict traffic.

**Requires a CNI plugin that implements NetworkPolicy** — Calico, Cilium, Weave do; some CNI plugins don't (flannel for example, unless paired with Calico).

## 2. The default state

Without any NetworkPolicy:
- All pods can reach all other pods
- All pods can reach all Services
- Pods can reach external internet (subject to node-level routing)

**NetworkPolicy adds restrictions, never grants.** Once one NP applies to a pod, only what's explicitly allowed is allowed.

## 3. The basic structure

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: my-policy
  namespace: my-app
spec:
  podSelector:                        # which pods this applies to (empty = all in namespace)
    matchLabels: { app: web }
  policyTypes: [Ingress, Egress]      # which directions
  ingress:                            # rules for inbound
  - from:
    - podSelector:
        matchLabels: { app: frontend }
    ports:
    - protocol: TCP
      port: 80
  egress:                             # rules for outbound
  - to:
    - podSelector:
        matchLabels: { app: db }
    ports:
    - protocol: TCP
      port: 5432
```

## 4. Default-deny (the recommended baseline)

```yaml
# Deny ALL ingress + egress to all pods in namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: my-app }
spec:
  podSelector: {}                     # all pods
  policyTypes: [Ingress, Egress]
  # no ingress or egress rules = deny everything
```

Then add explicit allows for traffic you want.

## 5. Allow DNS (always needed)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: my-app }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector:
        matchLabels: { kubernetes.io/metadata.name: kube-system }
      podSelector:
        matchLabels: { k8s-app: kube-dns }
    ports:
    - { protocol: UDP, port: 53 }
    - { protocol: TCP, port: 53 }
```

Without DNS allowed, pods can't resolve any name. First thing to add after default-deny.

## 6. Allow internal app traffic

```yaml
# Allow frontend → backend on port 8000
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: frontend-to-backend, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: backend }
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector:
        matchLabels: { app: frontend }
    ports:
    - { protocol: TCP, port: 8000 }
```

## 7. Allow Ingress controller traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-ingress-controller, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: web }
  policyTypes: [Ingress]
  ingress:
  - from:
    - namespaceSelector:
        matchLabels: { kubernetes.io/metadata.name: ingress-nginx }
    ports:
    - { protocol: TCP, port: 80 }
```

## 8. Egress to external service

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-egress-to-postgres, namespace: my-app }
spec:
  podSelector:
    matchLabels: { app: backend }
  policyTypes: [Egress]
  egress:
  - to:
    - ipBlock:
        cidr: 10.0.5.0/24       # RDS subnet
        except: [10.0.5.42/32]  # except this IP
    ports:
    - { protocol: TCP, port: 5432 }
```

## 9. Cross-namespace allow

```yaml
ingress:
- from:
  - namespaceSelector:
      matchLabels: { team: frontend }
    podSelector:
      matchLabels: { app: web }
```

This allows pods labeled `app=web` in any namespace labeled `team=frontend`. Combined namespace + pod selector = AND. Multiple `from:` entries = OR.

## 10. Cilium NetworkPolicy (richer, L7)

Cilium extends NetworkPolicy with **L7 rules** (HTTP method/path-based):

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata: { name: api-l7, namespace: my-app }
spec:
  endpointSelector:
    matchLabels: { app: api }
  ingress:
  - fromEndpoints:
    - matchLabels: { app: frontend }
    toPorts:
    - ports: [{ port: "8000", protocol: TCP }]
      rules:
        http:
        - method: "GET"
          path: "/api/users/.*"
        - method: "POST"
          path: "/api/login"
```

The standard K8s NP is L3/L4 only; Cilium NP can do L7. The K8s upstream is adding L7 features in 2025-2026.

## 11. Debugging NetworkPolicy

```bash
# Confirm CNI supports it
k get pods -A | grep -E "cilium|calico|weave"

# List policies
k get networkpolicy -A
k describe netpol my-policy

# Test connectivity from a debug pod
k run debug --rm -it --image=nicolaka/netshoot -n my-app -- bash
nc -zv backend 8000      # OK or denied?
curl -v http://backend:8000

# Cilium-specific: Hubble for observability
hubble observe --pod my-app/frontend-abc --to-pod my-app/backend-xyz
```

## 12. CKA exam — NetworkPolicy tasks

Common task:
> "Create a NetworkPolicy in namespace `my-app` that allows traffic from pods labeled `app=frontend` to pods labeled `app=backend` on TCP port 8000. Block all other ingress to backend pods."

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-frontend-to-backend, namespace: my-app }
spec:
  podSelector: { matchLabels: { app: backend } }
  policyTypes: [Ingress]
  ingress:
  - from:
    - podSelector: { matchLabels: { app: frontend } }
    ports:
    - { protocol: TCP, port: 8000 }
```

When you apply this NP, it implicitly denies all other ingress to backend pods (because once any NP selects a pod for Ingress, only allowed traffic is permitted).

## 13. The model — once a NP applies, default-deny

A pod's traffic is **default-allow** UNTIL any NP selects it. Then:
- Pod is **default-deny** for that direction
- Only traffic explicitly allowed by all applying NPs is allowed
- Multiple NPs are **additive** (OR)

This is a common point of confusion: adding one restrictive NP doesn't deny the pod — it denies what's NOT covered by *any* NP rule on the pod.

## 14. Quick self-check

1. What's the default pod-to-pod connectivity in K8s?
2. What happens to a pod once any NetworkPolicy selects it?
3. Why must you allow DNS explicitly after a default-deny?
4. What's the difference between K8s NetworkPolicy and Cilium NetworkPolicy?
5. What CNI plugins implement NetworkPolicy?

(Answers: all pods can reach all other pods + Services + external (subject to host routes); pod becomes default-deny for the direction(s) the NP covers — only explicitly allowed traffic permitted; without DNS pod can't resolve any names — first allow after default-deny; K8s NP is L3/L4 (IP + port), Cilium NP adds L7 (HTTP method/path/header); Calico, Cilium, Weave, Antrea — Flannel does NOT alone (needs Calico for NP).)



ewpage


# 80 — CKA Exam Tips + 12-Week Study Plan

## 1. The exam-day mindset

- **Time pressure is the enemy.** 15-20 tasks in 120 minutes = ~6-7 min/task.
- **Don't get stuck.** Skip and return; partial credit > zero on a different task.
- **Trust the docs.** kubernetes.io is open in a tab; use it.
- **Imperative > YAML-from-scratch** for any single-step task. Dry-run-to-YAML for complex.
- **Verify each task** before moving on (`k get -o wide`, `k describe`).
- **Save bash history** for the last 20-min review.

## 2. The 12-week study plan

### Weeks 1-2: Foundations
- Watch Mumshad's CKA course Sections 1-3 (or KodeKloud equivalent)
- Read Topic 05 Modules 1-25 (K8s + Docker fundamentals)
- Read Topic 08 Part 5 Modules 60-65 (this guide)
- Set up local kind/minikube + practice basics
- Drill kubectl get/describe/exec/logs daily

### Weeks 3-4: kubeadm + Networking + Storage
- Build a 3-node cluster on AWS / GCP / Linode with kubeadm (Module 62)
- Practice etcd backup/restore 10 times (Module 74)
- Cilium / Calico NetworkPolicy walkthroughs (Module 79)
- PV/PVC/SC scenarios (Module 68)
- Sidecar + init container patterns (Module 67)

### Weeks 5-6: RBAC + Scheduling + Workloads
- Create users with certs (CSR API, Module 65)
- 5 RBAC tasks: create role + binding for different SAs
- Taints + tolerations + node affinity scenarios (Module 71)
- DaemonSet + StatefulSet labs
- HPA + VPA setup

### Weeks 7-8: Troubleshooting
- **Spend a LOT of time here.** 30% of the exam.
- Practice the diagnostic ladder (Module 66) on broken clusters
- Killer.sh "Killercoda" CKA scenarios (free, in-browser)
- Cluster + Worker troubleshooting scenarios:
  - Pod stuck Pending → fix
  - Pod CrashLoopBackOff → fix
  - Service has no endpoints → fix
  - kubelet down → fix
  - DNS resolution broken → fix
  - Certificate expired → fix

### Weeks 9-10: Cluster Lifecycle
- kubeadm upgrade drill 5 times (Module 76)
- Certificate renewal drill 5 times (Module 78)
- Multi-cluster context switching (Module 77)
- Backup + restore drills

### Weeks 11: Mock exams
- **Killer.sh** (2 free with voucher) — your most valuable practice
- **KodeKloud mock exams** if you have access
- After each mock: review every wrong answer + redo it
- Target: 70%+ on first attempt, 85%+ on second

### Week 12: Polish + register exam
- Re-do Killer.sh attempts you weren't fast on
- Review FACTS.md (this topic) + Topic 05 FACTS for version-specific notes
- Read CKA candidate handbook front-to-back
- Test webcam + browser + room setup
- Schedule exam for a low-stress morning

## 3. The non-negotiable skill drills

By exam day, these must be muscle memory:
1. **kubectl create + --dry-run=client -o yaml** — for every resource type
2. **kubectl explain** — for any field you forget
3. **kubectl describe** — to find events
4. **kubectl logs --previous** — to see crashed container logs
5. **etcdctl snapshot save + restore** — exact command sequence
6. **kubeadm token create + join** — cluster join
7. **kubeadm upgrade plan + apply + node** — upgrade flow
8. **kubeadm certs check-expiration + renew** — cert flow
9. **Drain + uncordon** — maintenance
10. **JSONPath + custom-columns** — for fast filtering

## 4. JSONPath patterns to memorize

```bash
# Pod names
k get pods -o jsonpath='{.items[*].metadata.name}'

# Pod IPs
k get pods -o jsonpath='{.items[*].status.podIP}'

# Pods sorted by name
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# Nodes with version
k get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.nodeInfo.kubeletVersion}{"\n"}{end}'

# Containers in a pod
k get pod my-pod -o jsonpath='{.spec.containers[*].name}'

# Find pods using a specific image
k get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | grep nginx

# Service IPs
k get svc -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.clusterIP}{"\n"}{end}'
```

## 5. Exam-time shell setup (the first 60 seconds)

```bash
# Aliases
alias k=kubectl
source <(kubectl completion bash)
complete -F __start_kubectl k

# Dry-run helper
export do='--dry-run=client -o yaml'
export now='--force --grace-period 0'

# Set vim defaults
cat > ~/.vimrc <<EOF
set ts=2 sts=2 sw=2 et ai nu
EOF

# Tmux setup if available
```

Spend 30 seconds setting these. Saves minutes over 2 hours.

## 6. The "skip and return" discipline

When stuck:
- 5 min in, no progress → flag + skip
- Come back in the last 20 min
- Some tasks have setup that takes longer than the task itself
- Don't sink 25 min into one task when you have 14 others

## 7. Reading tasks carefully

Common parse failures:
- "Add a new container called X to pod Y" → it's a multi-container edit, not a new pod
- "In namespace Z" → forgetting to set namespace
- "Use cluster Y" → forgetting to `use-context`
- "Resources should be requested" → you need both requests AND limits in some cases
- "Without using kubectl edit" → must use `kubectl patch` or `kubectl apply`

Read 2-3 times before starting work.

## 8. The "I'll come back to this" notebook

The exam terminal has a notepad. Use it for:
- Tasks you flagged
- Commands you want to re-use
- A running tally of what's done

## 9. Saving your work

After each task:
```bash
k get -o yaml > /tmp/last-state.yaml      # snapshot what you built
```

Many tasks reset on context switch. Save aggressively if a later task references earlier work.

## 10. Common mistakes that cost points

- Wrong namespace (forgot `-n` flag, or wrong namespace flag)
- Typo in label / selector
- Missed a deliverable in a multi-part task ("Create a Deployment AND expose it AND scale it" — did all three?)
- YAML indentation broken — fix early
- Used `kubectl create` for resource you should have applied YAML

## 11. After the exam

- Results: typically within 24 hours (PSI emails)
- If pass: cert PDF available immediately; LinkedIn add
- If fail: 1 free retake within 12 months of original voucher
- Either way: **continue practicing** — CKA pass is the floor, not the ceiling

## 12. After CKA — what's next

| Cert | Audience | Timing |
|---|---|---|
| **CKAD** | App developer focus | 3 months after CKA (overlap; not strictly necessary) |
| **CKS** | Security | 6+ months after CKA (CKA is prereq; pivot to DevSecOps) |
| **KCSA** | Security associate-level | optional intermediate |
| **CISSP / CCSP** | Security CISSP | different track, multi-year |

For Vatsal at Capital One: **CKA → CKS** is the natural path. CKAD overlaps too much with CKA + day-job.

## 13. Quick self-check

1. What's the exam pass threshold?
2. What's the time budget per task?
3. Which domain has the highest weight?
4. What two free practice runs come with the voucher?
5. After CKA, what's the recommended next cert for a security-focused engineer?

(Answers: 66%; ~6-7 min/task with 15-20 tasks in 2 hours; Troubleshooting at 30%; Killer.sh sessions — harder than real exam; CKS — but CKA must be passed first, and ideally 6+ months of K8s ops experience between.)



ewpage

# Part Quizzes




ewpage

# Quiz — Part 1 (DevOps Bootcamp: Modules 1-17)

Self-assessment quiz covering the DevOps Bootcamp fundamentals. Answer first, expand the answer block, score yourself.

## Section A — Core DevOps + Linux + Git

**Q1.** Name DORA's four (now five) key DevOps metrics.

<details><summary>Answer</summary>

Deployment Frequency, Lead Time for Changes, MTTR, Change Failure Rate, plus **Reliability** added in 2024 (SLO attainment).
</details>

**Q2.** What's `set -euo pipefail` for in a bash script?

<details><summary>Answer</summary>

`-e` = exit on first error, `-u` = error on undefined variable, `-o pipefail` = fail if any command in a pipeline fails (not just the last). Together: scripts that catch errors instead of silently continuing.
</details>

**Q3.** Why generate ed25519 SSH keys instead of RSA in 2026?

<details><summary>Answer</summary>

Smaller (256-bit), faster, equivalent security to RSA-4096. Default modern recommendation.
</details>

**Q4.** What's the difference between `git pull` and `git fetch`?

<details><summary>Answer</summary>

`fetch` downloads remote changes (read-only). `pull` = `fetch` + `merge` (or `rebase`).
</details>

**Q5.** How do you recover a commit you `git reset --hard`'d away?

<details><summary>Answer</summary>

`git reflog` shows every HEAD movement (kept ~90 days). Then `git reset --hard HEAD@{n}` to the desired state.
</details>

## Section B — Build tools + Cloud + Nexus + Docker

**Q6.** What replaced Poetry as the modern Python default in 2025-2026 and why?

<details><summary>Answer</summary>

**uv** (from Astral, Rust). Single binary, ~10-100x faster than pip, lockfile-first, manages Python versions too.
</details>

**Q7.** Why is `docker-compose` (v1) replaced by `docker compose` (v2)?

<details><summary>Answer</summary>

v1 was Python-based and unmaintained. v2 is Go-written, a plugin to the Docker CLI, actively developed.
</details>

**Q8.** Name three Nexus alternatives and when you'd pick each.

<details><summary>Answer</summary>

- **AWS CodeArtifact** for AWS-native shops
- **GitHub Packages** for GitHub-native shops
- **JFrog Artifactory** for regulated finance (Cap One uses this)
- **GitLab Package Registry** for GitLab-native shops
</details>

**Q9.** What's the difference between a Docker image and a container?

<details><summary>Answer</summary>

Image = immutable, layered blueprint. Container = running instance of an image with its own writable layer + isolated process namespaces.
</details>

**Q10.** Why is multi-stage Docker build a best practice?

<details><summary>Answer</summary>

Builder stage has build tools + source; runtime stage has only the artifact + runtime deps. Smaller final image, smaller attack surface, faster pulls.
</details>

## Section C — Jenkins + AWS + K8s

**Q11.** What's a Multibranch Pipeline and what does it auto-discover?

<details><summary>Answer</summary>

Jenkins job type that scans a Git repo for branches with `Jenkinsfile`s, creates sub-jobs per branch (and per PR with the GitHub source plugin). Each branch's Jenkinsfile runs that branch's pipeline.
</details>

**Q12.** Why use OIDC + IAM Role over AWS access keys in CI/CD?

<details><summary>Answer</summary>

Short-lived credentials, nothing to leak or rotate, audited per-job in CloudTrail, scoped via trust policy to specific (project, branch).
</details>

**Q13.** Name three things a fresh `eksctl create cluster` does NOT give you.

<details><summary>Answer</summary>

CSI driver, autoscaler (Karpenter or CAS), ingress controller, cert-manager, monitoring stack, GitOps controller, policy engine. EKS Blueprints fills this gap.
</details>

**Q14.** What's the difference between IRSA and EKS Pod Identity?

<details><summary>Answer</summary>

IRSA uses OIDC provider + trust policy on the SA name in the role. Pod Identity uses Pod Identity Agent DaemonSet + EKS API association — simpler trust policy + simpler ops.
</details>

## Section D — Terraform + Python + Ansible + Prometheus

**Q15.** What's the difference between Terraform and OpenTofu?

<details><summary>Answer</summary>

OpenTofu is the OSS fork after HashiCorp's BUSL relicense (Aug 2023). Same HCL, MPL 2.0, Linux Foundation governance. Matters for OSS-purity shops and avoiding vendor lock-in.
</details>

**Q16.** When use Boto3 over Terraform?

<details><summary>Answer</summary>

Boto3 for: runtime/operations (backup, cleanup), ad-hoc scripts, things needing logic (if-then), bulk ops across accounts. Terraform for static infra.
</details>

**Q17.** Why is Ansible-to-K8s an anti-pattern in 2026?

<details><summary>Answer</summary>

K8s has native declarative tooling (Helm, Kustomize, ArgoCD/Flux). Ansible's imperative push model doesn't match K8s's pull-based reconciliation.
</details>

**Q18.** What's a Prometheus ServiceMonitor and what does it enable?

<details><summary>Answer</summary>

CRD from Prometheus Operator that selects K8s Services to scrape. Replaces hand-editing `prometheus.yml` — declarative scrape targets via labels.
</details>

**Q19.** What's the four-golden-signals SRE framework?

<details><summary>Answer</summary>

Latency, Traffic, Errors, Saturation. From Google's SRE book.
</details>

**Q20.** Why is cardinality explosion a Prometheus problem and how to avoid it?

<details><summary>Answer</summary>

High-cardinality labels (user_id, URL with path params) blow up the index. Use endpoint templates (`/users/:id` not `/users/12345`) and finite label values.
</details>

---

**Scoring**: 18-20 correct → solid command of DevOps Bootcamp. 14-17 → revisit weak areas. < 14 → re-read corresponding modules.


ewpage

# Quiz — Part 2 (DevSecOps Bootcamp: Modules 18-38)

## Section A — Security Fundamentals + Scanning

**Q1.** What was the root cause of the Capital One 2019 breach and which OWASP item is it?

<details><summary>Answer</summary>

SSRF + over-permissive IAM role + IMDSv1 — OWASP A10. IMDSv2 hop-limit=1 mitigates the specific attack vector.
</details>

**Q2.** What problem does the pre-commit framework solve?

<details><summary>Answer</summary>

Orchestrates many hooks (gitleaks, lint, format, secret detect) from a single declarative `.pre-commit-config.yaml` + version-pins each.
</details>

**Q3.** Why must CI also scan for secrets if pre-commit catches them?

<details><summary>Answer</summary>

Developers can bypass pre-commit with `git commit --no-verify`. CI is the enforcement layer that can't be bypassed.
</details>

**Q4.** What's the difference between SAST, DAST, and IAST?

<details><summary>Answer</summary>

SAST scans source code, DAST scans the running app, IAST instruments the running app (agent inside). False positives: SAST high → IAST low.
</details>

**Q5.** What problem does DefectDojo solve that running scanners individually doesn't?

<details><summary>Answer</summary>

Normalizes findings from many scanners into one trackable backlog with dedup + SLA + CWE mapping + risk-accept workflow + reporting.
</details>

**Q6.** What's EPSS and why is it more actionable than CVSS alone?

<details><summary>Answer</summary>

Exploit Prediction Scoring System — probability of exploitation in next 30 days. CVSS only measures theoretical severity; EPSS measures actual risk.
</details>

## Section B — Container Security + GitOps

**Q7.** What is "keyless signing" with Cosign and what 3 Sigstore components make it work?

<details><summary>Answer</summary>

OIDC-based ephemeral keys with no long-term key management. Components: Fulcio (CA for short-lived certs), Rekor (transparency log), Cosign (CLI).
</details>

**Q8.** What's SLSA L3 in one sentence?

<details><summary>Answer</summary>

Build runs in isolated environment producing non-falsifiable provenance signed by the build platform.
</details>

**Q9.** What's the security advantage of GitOps's pull model over CI-push?

<details><summary>Answer</summary>

Pipeline doesn't need cluster credentials; cluster pulls from Git. Fewer credentials to leak. Plus Git-history audit, drift detection.
</details>

**Q10.** Why is Kyverno winning over OPA Gatekeeper for K8s-only shops in 2026?

<details><summary>Answer</summary>

YAML policies (simpler than Rego), native mutation + generation, image signature verify built-in. K8s-focused — no need for Rego's cross-tool flexibility.
</details>

## Section C — AWS + K8s Security

**Q11.** What's the IAM permission evaluation precedence order?

<details><summary>Answer</summary>

Explicit Deny → SCP/RCP → Permission Boundary → Identity Policy ∩ Resource Policy → implicit Deny.
</details>

**Q12.** Why does the legacy aws-auth ConfigMap pose risks compared to EKS Access Entries?

<details><summary>Answer</summary>

Bad edit can lock you out of cluster. No IAM controls on its modification. Only K8s-audit (no CloudTrail). Access Entries fix all three.
</details>

**Q13.** What replaced PodSecurityPolicy in K8s 1.25+ and what are the three profiles?

<details><summary>Answer</summary>

Pod Security Admission (PSA) enforcing Pod Security Standards. Profiles: Privileged, Baseline, Restricted.
</details>

**Q14.** Why is automounting the ServiceAccount token to a pod that doesn't need K8s API a risk?

<details><summary>Answer</summary>

The token is a credential. Compromised pod → attacker has K8s API access scoped to that SA. Set `automountServiceAccountToken: false` for pods that don't need the API.
</details>

## Section D — Secrets, Mesh, Compliance

**Q15.** Why are K8s Secrets not actually secret?

<details><summary>Answer</summary>

Base64-encoded only — not encrypted. Anyone with API access can decode them. Use envelope encryption with KMS + External Secrets Operator + cloud secret manager.
</details>

**Q16.** What does Istio's PeerAuthentication object do?

<details><summary>Answer</summary>

Configures mTLS mode (STRICT / PERMISSIVE / DISABLE) for pods in scope. STRICT = only mTLS allowed; PERMISSIVE = accepts both during migration.
</details>

**Q17.** What's the difference between NetworkPolicy and Istio AuthorizationPolicy?

<details><summary>Answer</summary>

NetworkPolicy is L3/L4 + IP/label-based + cheap. Istio AuthZ is L7 + SPIFFE-identity-based + mTLS-required. Use both layered.
</details>

**Q18.** What's Cloud Custodian and who built it?

<details><summary>Answer</summary>

Declarative Python policy-as-code framework for AWS resources — detection + filters + actions in one YAML. Capital One built it, CNCF Sandbox since 2018.
</details>

**Q19.** Why is auto-remediation valuable beyond just detection?

<details><summary>Answer</summary>

Closes the window between detection and human response — many findings should be auto-fixed in seconds, not days. Defense-in-depth at machine speed.
</details>

**Q20.** Why does "buy tools and drop them on devs" fail as a DevSecOps strategy?

<details><summary>Answer</summary>

No training, no support, no triage capacity → backlog grows → tools get ignored. Humans + process + paved-road > tools alone.
</details>

---

**Scoring**: 18+ → DevSecOps-ready conversation. 14-17 → solid working knowledge. < 14 → revisit critical modules.


ewpage

# Quiz — Part 3 (GitLab CI/CD: Modules 39-46)

**Q1.** When pick GitLab over GitHub Actions vs Jenkins?

<details><summary>Answer</summary>

- **Jenkins**: regulated finance, air-gap requirements, large existing Groovy investment
- **GitHub Actions**: code on GitHub, simplest path, GitHub-native ecosystem
- **GitLab**: all-in-one DevSecOps (Ultimate tier), single-vendor procurement, compliance frameworks built in
</details>

**Q2.** What's the difference between `stages:` and `needs:` in `.gitlab-ci.yml`?

<details><summary>Answer</summary>

Stages = sequential groups (a stage waits for all previous-stage jobs). `needs:` = explicit DAG dependencies between jobs — a job starts as soon as listed dependencies finish, regardless of stage boundary.
</details>

**Q3.** What replaced legacy `only`/`except` in modern GitLab CI?

<details><summary>Answer</summary>

`rules:` — more flexible, supports `if`/`changes`/`exists`/`when`, composable.
</details>

**Q4.** What's a merged-results pipeline?

<details><summary>Answer</summary>

Pipeline runs on the *merged* result (source branch + target merged in memory) — closer to what production will see after merge. Catches conflicts that don't exist in source alone.
</details>

**Q5.** What's the difference between a Runner and an Executor?

<details><summary>Answer</summary>

**Runner** = the process polling GitLab + dispatching jobs. **Executor** = the actual environment where the job runs (shell, docker, k8s pod, ssh).
</details>

**Q6.** Why is Project Runners preferred over Instance Runners for sensitive projects?

<details><summary>Answer</summary>

Isolation — Instance Runners share host with other projects' jobs; risk of supply-chain attack or noisy neighbors. Project Runners run only your team's jobs.
</details>

**Q7.** Why use Kaniko instead of `docker build` in a K8s GitLab runner?

<details><summary>Answer</summary>

Kaniko builds images without a privileged Docker daemon or `docker.sock` mount — works in unprivileged K8s pods, respecting Pod Security Standards.
</details>

**Q8.** What does GitLab Environments add over just deploy jobs?

<details><summary>Answer</summary>

Deployment history per env, easy rollback, MR shows latest deploy URL, dashboards for compliance.
</details>

**Q9.** What replaced "CI Templates" in GitLab 17+?

<details><summary>Answer</summary>

**CI/CD Components** — versioned, catalog-published, typed inputs, dedicated test pipeline.
</details>

**Q10.** What's the difference between `include: project:` and `include: component:`?

<details><summary>Answer</summary>

`include: project:` is older — includes a YAML file from another project by path + ref. `include: component:` is newer — references a CI/CD Component with typed inputs + semver versioning + catalog discoverability.
</details>

**Q11.** Why pin Components to exact version (`@v1.2.3`) in production?

<details><summary>Answer</summary>

Supply-chain safety — `@~latest` could change unexpectedly and break your pipeline. Treat Components like dependencies.
</details>

**Q12.** What problem does GitLab Agent for Kubernetes solve over kubeconfig-in-CI?

<details><summary>Answer</summary>

Agent dials out from cluster to GitLab (no inbound traffic to cluster). No kubeconfig stored in CI vars. Audit by Git history (GitOps mode).
</details>

**Q13.** What's the difference between Agent CI access mode and GitOps mode?

<details><summary>Answer</summary>

**CI access mode**: pipelines use `kubectl` via the Agent (push). **GitOps mode**: Agent pulls manifests from a Git repo + applies autonomously (no CI involvement after manifest commit).
</details>

**Q14.** Why does `id_tokens:` block matter in `.gitlab-ci.yml` for AWS OIDC?

<details><summary>Answer</summary>

Tells GitLab to issue an OIDC JWT for that job with the specified audience — required for AWS to verify the token in `AssumeRoleWithWebIdentity`.
</details>

**Q15.** Why split CI roles into "plan" and "apply" for Terraform?

<details><summary>Answer</summary>

Least privilege — plan never needs write permissions, so a compromise in a plan job can't apply destructive changes. Apply role only assumable on protected branches.
</details>

---

**Scoring**: 13+ → GitLab CI competent. 9-12 → solid baseline. < 9 → revisit modules 39-46.


ewpage

# Quiz — Part 4 (IT Fundamentals: Modules 47-59)

**Q1.** What's the Socratic-mode AI study assistant prompting pattern?

<details><summary>Answer</summary>

Tell it to ask questions back, not give answers. "Don't give me the answer. Ask me questions to help me get there. Stop after each question."
</details>

**Q2.** Why is cycle time a better metric than velocity?

<details><summary>Answer</summary>

Cycle time is harder to game and directly measures throughput. Velocity inflates with practice as teams pad estimates.
</details>

**Q3.** Why are senior orgs dropping story-point estimation?

<details><summary>Answer</summary>

Gameable, time-consuming, doesn't predict better than t-shirt sizes or just breaking work into similar-sized pieces.
</details>

**Q4.** What is "fine-grained reactivity" in modern frontend frameworks?

<details><summary>Answer</summary>

Only DOM nodes that depend on changed state re-render — vs whole-component re-render. Implemented by Solid, Svelte 5, Vue Vapor, Angular signals.
</details>

**Q5.** What replaced Vuex as Vue's official state management?

<details><summary>Answer</summary>

Pinia (since 2022).
</details>

**Q6.** When use `v-if` vs `v-show` in Vue?

<details><summary>Answer</summary>

`v-if` adds/removes from DOM (use for rare toggles). `v-show` toggles CSS `display` (use for frequent toggles — cheaper).
</details>

**Q7.** What's the killer feature of Hono over Express/Fastify?

<details><summary>Answer</summary>

Portability — same code runs on Node, Bun, Deno, Cloudflare Workers, AWS Lambda, edge runtimes.
</details>

**Q8.** Why is Postgres often the 2026 default for OLTP over MongoDB/DynamoDB?

<details><summary>Answer</summary>

Relational + ACID + huge ecosystem + JSONB for flexible schema + pgvector for vector search + battle-tested. Postgres-with-extensions covers ~80% of what people used to need NoSQL for.
</details>

**Q9.** What's the difference between Vitest and Jest?

<details><summary>Answer</summary>

Vitest: native ESM + TypeScript, faster startup, reuses Vite config, browser mode, watch by default. Jest-compatible API but much modernized.
</details>

**Q10.** Why is 100% test coverage typically a bad goal?

<details><summary>Answer</summary>

Leads to testing implementation details + brittle tests with diminishing returns. 70-80% is the sweet spot.
</details>

**Q11.** Why is Caddy's automatic Let's Encrypt TLS a killer feature?

<details><summary>Answer</summary>

Just add the domain to the Caddyfile + point DNS — TLS just works. No certbot dance, no renewal cron, no manual cert mgmt.
</details>

**Q12.** Why never commit `.env` to Git?

<details><summary>Answer</summary>

Secrets in env files get leaked. Even if "secret" in name, repo history is forever. Use `.env.example` for the template + cloud secrets manager for actual values.
</details>

**Q13.** Where should K8s Secrets actually come from in production?

<details><summary>Answer</summary>

From cloud Secret Manager (AWS Secrets Manager / Azure Key Vault / GCP SM / Vault) via External Secrets Operator — never base64'd into Git.
</details>

**Q14.** What's the difference between AI tool autocomplete, chat, and agentic modes?

<details><summary>Answer</summary>

- **Autocomplete**: ghost-text inline as you type (Copilot Tab, Cursor Tab)
- **Chat**: conversation about code (Cursor Chat, Claude.ai)
- **Agentic**: give task, AI executes multi-step with file edits + shell (Claude Code, Cursor Composer, Aider)
</details>

**Q15.** Why is "atrophy risk" with AI tools real, and how to mitigate?

<details><summary>Answer</summary>

Relying on autocomplete erodes fundamentals. Mitigation: periodically write code without AI to stay sharp. Use AI for boilerplate, but synthesize the architecture yourself.
</details>

---

**Scoring**: 13+ → strong cross-stack literacy. 9-12 → solid. < 9 → revisit modules where you missed.


ewpage

# Quiz — Part 5 (CKA: Modules 60-80)

The high-stakes exam quiz. Take this until you score 18+/20 consistently before scheduling the real CKA.

## Section A — Logistics + Concepts

**Q1.** What's the CKA passing score, and what's the largest domain weight?

<details><summary>Answer</summary>

66%. Largest domain = Troubleshooting at 30%.
</details>

**Q2.** What's the only K8s component that talks to etcd directly?

<details><summary>Answer</summary>

kube-apiserver. All other components go through the API server.
</details>

**Q3.** What's the version skew policy between control plane and nodes?

<details><summary>Answer</summary>

Control plane >= node, max 1 minor version skew. Upgrades follow this order: control plane → workers.
</details>

## Section B — Build + Networking + Storage

**Q4.** Why must swap be disabled before kubeadm init?

<details><summary>Answer</summary>

kubelet refuses to start with swap on. QoS + scheduling assumptions depend on memory accounting that swap breaks.
</details>

**Q5.** Why does a node show NotReady right after kubeadm init?

<details><summary>Answer</summary>

No CNI installed yet — no pod networking → node not Ready. Install Cilium/Calico/Flannel.
</details>

**Q6.** What's the FQDN format for a K8s Service?

<details><summary>Answer</summary>

`<service>.<namespace>.svc.cluster.local`
</details>

**Q7.** Why does `kubectl get endpoints my-svc` return `<none>`?

<details><summary>Answer</summary>

Selector doesn't match any pod's labels, OR pods exist but aren't Ready (failing readiness probe).
</details>

**Q8.** What's the difference between ReadWriteOnce and ReadWriteMany access modes?

<details><summary>Answer</summary>

RWO = one node can mount RW (EBS-style). RWX = many nodes can mount simultaneously (EFS / NFS / CephFS / Azure Files).
</details>

**Q9.** What does `volumeBindingMode: WaitForFirstConsumer` do and when use it?

<details><summary>Answer</summary>

Delays PV provisioning until a pod is scheduled — so the scheduler picks a node first, then storage provisions in that AZ. Essential for zonal storage like EBS.
</details>

## Section C — RBAC + Scheduling + Probes

**Q10.** What command verifies if a user can perform a specific action?

<details><summary>Answer</summary>

`kubectl auth can-i <verb> <resource> --as=<user-or-sa> -n <ns>`. Use during exam to confirm RBAC bindings worked.
</details>

**Q11.** What's the difference between a taint effect `NoSchedule` and `NoExecute`?

<details><summary>Answer</summary>

NoSchedule = no new pods land on the node (existing stay). NoExecute = also evicts existing pods that don't tolerate.
</details>

**Q12.** What problem do startup probes solve?

<details><summary>Answer</summary>

Apps that take 30s-5min to start. Startup probe gives long startup window without making liveness probe wait that long every interval after startup.
</details>

**Q13.** Why is using the same endpoint for liveness + readiness an anti-pattern?

<details><summary>Answer</summary>

Liveness failing because (e.g.) DB is slow → container restart (doesn't fix DB). Cascading restarts hide root cause. Liveness should check the process itself; readiness should check dependencies.
</details>

## Section D — etcd + Upgrade + Certs

**Q14.** What 4 things do you need to authenticate with etcdctl?

<details><summary>Answer</summary>

Endpoint URL, `--cacert`, `--cert`, `--key`. Plus `ETCDCTL_API=3` env var.
</details>

**Q15.** Why must kube-apiserver be stopped during etcd restore?

<details><summary>Answer</summary>

API server would write to old etcd while you're restoring → data inconsistency / corruption. Move both apiserver + etcd static pod manifests aside before restore.
</details>

**Q16.** What's the kubeadm upgrade order on an HA cluster?

<details><summary>Answer</summary>

First control plane node with `kubeadm upgrade apply` → remaining CP nodes with `kubeadm upgrade node` → workers one at a time with `kubeadm upgrade node`. Drain before each, uncordon after.
</details>

**Q17.** What's the default expiration for kubeadm-generated certs and how do you renew them?

<details><summary>Answer</summary>

1 year (365 days). Renew: `sudo kubeadm certs renew all` + restart control plane components by moving + restoring static pod manifests.
</details>

## Section E — NetworkPolicy + REST API + Contexts

**Q18.** What's the default pod-to-pod connectivity, and what changes when any NP applies?

<details><summary>Answer</summary>

Default: all pods can reach all pods + Services. Once any NP selects a pod (for a given direction), that pod becomes default-deny for that direction — only explicitly allowed traffic permitted.
</details>

**Q19.** What does `kubectl proxy` give you for API access?

<details><summary>Answer</summary>

Starts a local HTTP proxy that handles auth — you can `curl http://localhost:8001` without managing tokens/certs. Useful for ad-hoc exploration.
</details>

**Q20.** What 3 things does a kubectl context bind?

<details><summary>Answer</summary>

Cluster + User + Namespace. Switch with `kubectl config use-context <name>`.
</details>

---

**Scoring**: 18+ → ready for CKA. 14-17 → more drills (KillerCoda + Killer.sh). < 14 → return to Part 5 modules.



ewpage


# CAPITAL_ONE.md — Topic 08 Interview-Ready Dossier

> Curated mapping from Topic 08 modules → Capital One Sr Lead AI/ML role conversations. Use this for the final week before an interview to refresh signal-dense points.

## The Capital One DevOps stack (public knowledge as of 2026-05)

| Layer | Tool |
|---|---|
| **SCM** | GitHub Enterprise Cloud (not GitLab) |
| **CI** | Jenkins (CloudBees CI Enterprise); ~500k pipelines, ~50k builds/day |
| **CD** | Internal pattern: Jenkins → ECR → EKS via custom IDP |
| **IaC** | Terraform + Cloud Custodian (their OSS) |
| **K8s** | EKS-dominant; Critical Stack (homegrown) deprecated ~2020 |
| **Model serving** | KServe on EKS (self-hosted; not SageMaker for inference) |
| **Service mesh** | Istio (ambient adoption in progress) |
| **Secrets** | AWS Secrets Manager + ESO |
| **Monitoring** | AMP + AMG + Datadog + X-Ray + rubicon-ml |
| **Governance** | Cloud Custodian (AWS API layer) + Kyverno (K8s API layer) |
| **Compliance** | SOC 2, PCI-DSS v4, SR 11-7, GLBA, FFIEC |

Reference: Topic 04 (AWS) Module 49 + 52-56 for the deep AWS-side dossier.

## Signal-dense talking points (10 things to say)

1. **"I know SR 11-7 model-risk compliance requires immutable audit trails for every model version + decision."** → Topic 07 Module 37 + this Topic Module 18.

2. **"Capital One built Cloud Custodian — Python declarative policy-as-code for AWS — and donated to CNCF in 2018."** → Module 37.

3. **"Their 2019 breach was SSRF + over-permissive IAM + IMDSv1. The fix path that became industry default: IMDSv2 hop-limit=1 + GuardDuty credential-exfiltration detection + Inspector v2."** → Module 18 + 25.

4. **"For K8s admission control they use Kyverno's YAML-policy model — simpler than OPA Gatekeeper for K8s-specific use cases. OPA still wins for cross-tool (TF + K8s + Envoy) Rego libraries."** → Module 34.

5. **"Their model serving runs on EKS via KServe, not SageMaker, because they need control of the serving stack for SR 11-7 audit + cost at scale."** → Module 12 + Topic 04 Module 54.

6. **"They use Jenkins on CloudBees CI Enterprise, not GitLab — air-gap support + the plugin ecosystem + 20-year track record. ~500k pipelines × ~50k builds/day."** → Module 9.

7. **"Their CI/CD uses GitHub Enterprise Cloud as SCM + Jenkins as the engine + OIDC + IAM Role chained to per-account IAM Roles in target accounts for deploy."** → Module 25 + 31.

8. **"For compliance: they pair AWS Config + Conformance Packs (CIS AWS, PCI-DSS) with Cloud Custodian for auto-remediation of low-risk findings."** → Module 37.

9. **"Their MLOps spine: SageMaker for some training, Glue/EMR for ETL, Step Functions for orchestration, EKS+KServe for serving, MLflow + rubicon-ml for tracking + lineage."** → Topic 04 Module 52-54.

10. **"They've been all-AWS since ~2015; closed last datacenter in 2020. Multi-account architecture via Organizations + Control Tower + SCPs at OU level."** → Module 10 + 25.

## Likely interview questions + framing

### "How would you secure a K8s model-serving cluster?"

Layered defense (Module 29):
- **Cloud layer**: VPC private subnets only; IAM least-privilege; KMS envelope encryption
- **Cluster layer**: EKS latest minor; control plane private endpoint; audit logs to CloudWatch
- **Workload layer**: Pod Security Standards `restricted`; NetworkPolicy default-deny per namespace; Kyverno policies enforced at admission
- **Image layer**: Trivy scans in CI, Cosign signed at build, Kyverno verifies signatures at admission
- **Identity layer**: IRSA or Pod Identity for pod IAM; ESO + AWS Secrets Manager
- **Mesh layer**: Istio STRICT mTLS; AuthorizationPolicy per workload-identity
- **Runtime layer**: Falco for anomaly detection; Container Insights
- **Compliance layer**: AWS Config + CIS K8s benchmark + Cloud Custodian remediation

### "Walk me through a model deploy pipeline at Capital One scale"

- Data engineer commits SQL to GHE → Jenkins → Glue ETL job updated
- ML engineer commits training code to GHE → Jenkins job → SageMaker training → MLflow registry
- Model evaluator (rubicon-ml) signs off → manual gate
- ML engineer commits inference container Dockerfile + Helm chart updates
- Jenkins → Trivy scan + Cosign sign → push to ECR
- Jenkins → GitOps repo update (image tag)
- ArgoCD (or KServe operator) syncs → KServe InferenceService updated → progressive canary via Argo Rollouts
- CloudWatch + AMP + Datadog → SLO monitoring → auto-rollback if error spike

### "How do you handle K8s secrets at scale?"

- AWS Secrets Manager as source of truth — single source, automatic rotation for DB creds
- External Secrets Operator in K8s syncs Secrets Manager → K8s Secrets (refresh every hour)
- ESO authenticates via IRSA — no long-lived credentials in cluster
- K8s Secrets use envelope encryption via KMS in EKS config
- Application reads from K8s Secret as env var or volume; rotates via pod restart or hot-reload

### "Tell me about a time you debugged a production K8s issue"

Walk through the diagnostic ladder (Module 66):
1. Pod status (Pending? CrashLoopBackOff? ImagePullBackOff?)
2. `kubectl describe` events
3. `kubectl logs --previous`
4. Service endpoints (selector match?)
5. NetworkPolicy (blocking traffic?)
6. DNS (CoreDNS healthy?)
7. Node (cordoned? resources?)
8. Control plane (apiserver healthy?)
9. CNI (pods getting IPs?)

Have a specific story ready. The framework is what matters.

## Certifications mapped to the role

- **CKA** — operational K8s competence. Required signal for "I can run a cluster, not just kubectl."
- **AWS SAA-C03** → **MLA-C01** (AI/ML Specialty) → **DEA-C01** (Data Engineering) → **SCS-C02** (Security) → **AIP** (AI Practitioner) — the AWS ladder. See Topic 04 Module 57.
- **CKS** — Kubernetes Security — natural follow-up after CKA + 6 months ops experience.
- **Optional**: PMP if pivoting toward EM track.

## What NOT to lead with

- Vague Agile certifications (PSM, CSM, etc.) — Cap One won't care
- HashiCorp certifications (Terraform, Vault) — nice-to-have, not signal
- Kubernetes Application Developer (CKAD) — too overlapping with day-job, weaker signal than CKA
- Cloud Foundation certifications without role-relevance

## After the interview

- LinkedIn add the panelists
- Send specific thank-you notes (not generic) within 24 hours
- Reference one specific topic from each conversation
- If pinged for additional rounds, brush up on the panelist's stated specialty (their LinkedIn)

---

This dossier pairs with Topic 04's CAPITAL_ONE.md and Topic 07's CAPITAL_ONE.md. Together they form the complete interview prep set.
