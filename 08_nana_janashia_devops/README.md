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
