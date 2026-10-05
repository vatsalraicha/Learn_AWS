# 33 — Certification roadmap: KCNA, KCSA, CKAD, CKA, CKS — plus AWS/GCP/Azure K8s certs

> *"For a Sr Lead AI/ML interview at Capital One: CKA + CKS is the credibility multiplier. KCNA is noise."*

## Why this module exists

The user has explicitly asked to add K8s certs to the resume. This module gives a buy/skip verdict per cert tailored to "Sr AI/ML Engineer targeting Sr Lead AI/ML at Capital One" — a regulated-finance, AWS-only, EKS+KServe shop.

---

## 1. The CNCF / Linux Foundation cert ladder

| Cert | Level | Cost | Format | Time | Validity |
|---|---|---:|---|---|---|
| **KCNA** (Kubernetes & Cloud Native Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **KCSA** (Kubernetes Security Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **CKAD** (Certified Kubernetes App Developer) | Associate | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **CKA** (Certified Kubernetes Administrator) | Associate | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **CKS** (Certified Kubernetes Security Specialist) | Specialty (requires active CKA) | $445 | Hands-on, 2 hr | 2 hr | 2 yr |
| **PCA** (Prometheus Certified Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |
| **ICA** (Istio Certified Associate) | Foundational | $250 | MCQ, 90 min, 60 q | 90 min | 2 yr |

[Source: training.linuxfoundation.org] — all hands-on exams allow `kubectl` autocomplete and access to kubernetes.io docs in a sandboxed browser.

### 1.1 Bundle discounts

- CKA + CKAD + CKS bundle commonly available at $1,135 (vs $1,335 separate).
- KubeCon weeks: extra 30-40% off.
- Linux Foundation Black Friday: ~50% off all certs.

**Buy during a discount window.** No certs are urgent enough to pay full price.

---

## 2. Verdict per cert for "Sr AI/ML Engineer → Sr Lead AI/ML at Capital One"

| Cert | Verdict | Why |
|---|---|---|
| **KCNA** | **Skip** | Too elementary for a Sr engineer; no ROI on resume |
| **KCSA** | **Skip-or-bundle** | Useful for someone explicitly targeting security roles; otherwise covered by CKS |
| **CKAD** | **Buy** | Validates "you can build K8s-native apps"; required muscle memory; ~2 weeks of prep |
| **CKA** | **Buy** | The credibility-pillar K8s cert; required for CKS; ~4 weeks of prep |
| **CKS** | **Buy** | Security-spec; the Capital One-aligned cert; ~6 weeks of prep after CKA |
| **PCA** | **Maybe** | Useful if you'll own production observability; otherwise low-priority |
| **ICA** | **Skip-or-later** | Service mesh is niche; only buy if you become the mesh owner |
| **AWS DOP-C02** (DevOps Engineer Pro) | **Maybe** | Covers EKS extensively; complements CKA on AWS. Buy after CKS. |
| **AWS Specialty: Adv. Networking ANS-C01** | **Skip for this role** | Network depth more than the AI role demands |

---

## 3. Recommended sequence + 18-month plan (at 3 hr/week)

| Month | Cert | Hours | Notes |
|---|---|---|---|
| 1-2 | **CKAD** | ~30 | Get the muscle memory for `kubectl`; YAML reflexes |
| 3-5 | **CKA** | ~50 | Operator-level depth; etcd backup; cluster troubleshooting |
| 6-9 | **CKS** | ~60 | Security focus; CIS K8s benchmark; Falco; admission; supply chain |
| 10-12 | Break / production work / Topic 06 study | | |
| 13-15 | **AWS DOP-C02** | ~50 | EKS + CI/CD on AWS; complements CKS |
| 16-18 | **AWS MLA-C01** (covered Topic 04) or **AWS AIP-C01** | ~50 | Top off the AI specialization |

Cap at 3 certs per year. Sustainability over speed.

---

## 4. CKA / CKAD / CKS exam mechanics

- **Hands-on only.** No MCQ. You SSH into K8s clusters and `kubectl` your way through tasks.
- **Allowed tools in exam environment**: terminal, `kubectl` (with autocomplete), `kubernetes.io/docs` in a sandboxed browser, `kubectl` cheat sheet bookmark.
- **Time pressure is real.** ~120 minutes for 15-20 questions; budget ~6-8 min each.
- **Cluster context switching**: every task gives you `kubectl config use-context <name>` — execute it immediately. Wrong cluster = 0 points.
- **Saved snippets**: practice alias setups (`alias k=kubectl; export do='--dry-run=client -o yaml'`).

---

## 5. CKAD curriculum highlights

- Define + apply pods, deployments, services.
- Multi-container pods (sidecar, init).
- ConfigMaps + Secrets injection.
- Probes (liveness, readiness, startup).
- Jobs + CronJobs.
- Resource limits + QoS.
- Updating workloads (rolling update + rollback).
- Helm charts.
- NetworkPolicy basics.

Approx 30 hours of focused practice. Killer.sh has the official practice exam.

---

## 6. CKA curriculum highlights (2025+)

- Cluster architecture, installation, configuration (25%).
- Workloads + scheduling (15%).
- Services + networking (20%).
- Storage (10%).
- Troubleshooting (30%) — the big one; cluster + node + pod + log debugging.

Approx 50 hours.

---

## 7. CKS curriculum highlights

- Cluster setup (10%): network policies, CIS benchmarks, ingress TLS, NSG hardening.
- Cluster hardening (15%): RBAC, ServiceAccounts, K8s upgrades.
- System hardening (15%): kernel, IAM, network restrictions.
- Microservice vulnerabilities (20%): managing K8s Secrets, container runtime sandboxes (gVisor, Kata), mTLS.
- Supply chain security (20%): image scanning, signing, admission control.
- Monitoring, logging, runtime security (20%): Falco, syscall tracing, audit logs.

Approx 60 hours. Heavy on hands-on **Falco** rule writing and **AppArmor/seccomp** profile authoring — practice on a local cluster.

---

## 8. Study resources

| Resource | Cost | Notes |
|---|---|---|
| **Killer.sh practice exam** | $25 (often included with cert purchase) | The closest simulator |
| **KodeKloud CKA/CKS courses** | $30/mo | Best video course; hands-on labs |
| **Linux Academy / A Cloud Guru** | $40/mo | Decent but less hands-on |
| **Pluralsight** | $30/mo | More breadth, less depth |
| **Free official curriculum** | Free | training.linuxfoundation.org |
| **Sander van Vugt CKA/CKS books** | $50 | Solid textbooks |
| **CNCF KCNA/KCSA free path** | Free | If you want to do those |
| **YouTube: Tech World with Nana, KubeCraft, TechWorld with Vatsal Kohli** | Free | Concept reinforcement |

For the user's context: **KodeKloud + Killer.sh** is the standard combo.

---

## 9. The role-relevance argument

For a Capital One interview, the order of impressiveness on a resume:

1. **CKS** — "I know K8s security at the depth of regulated finance."
2. **CKA** — "I know cluster operations."
3. **AWS DOP-C02** — "I know EKS + CI/CD on AWS."
4. **AWS MLA-C01** — "I know the ML platform on AWS."
5. **CKAD** — "I can build K8s apps."
6. KCNA / KCSA — barely registers.

For interviewing, certs are the foot in the door. **The "Lead Machine Learning Engineer (MLOps, KServe)" job posting language signals that hands-on K8s + KServe wins over alphabet soup.** Pair cert prep with real KServe deployment in a personal lab.

---

## 10. The personal-lab build that pairs with certs

Spin up a Kind / Minikube cluster on your laptop, or a small EKS cluster in your own AWS account ($50-100/month budget). Practice:

- Install Cilium, Karpenter, GPU Operator (if GPU laptop), KServe, Prometheus, Falco, Kyverno, ESO.
- Deploy a sentiment model via KServe with IRSA.
- Sign images with Cosign keyless via GitHub Actions OIDC; verify with Kyverno.
- Configure Falco rules; trigger one yourself and watch the alert flow.
- Velero backup; restore drill.

This personal lab is the **single most useful** interview-prep asset. Talks about it score more points than any cert.

---

## Sanity check

1. Which 3 certs are the "buy" list for the Capital One target?
2. CKS requires what prerequisite?
3. Why is KCNA likely noise for a Sr engineer's resume?
4. What's allowed in the CKA/CKS exam environment that catches new test-takers off guard?
5. The 18-month plan caps at how many certs per year, and why?

---

## Sources

- [Linux Foundation Training](https://training.linuxfoundation.org/)
- [CNCF Certifications](https://www.cncf.io/training/certification/)
- [Killer.sh](https://killer.sh/)
- [KodeKloud](https://kodekloud.com/)
- [CKA Curriculum PDF](https://github.com/cncf/curriculum)
- [AWS DOP-C02](https://aws.amazon.com/certification/certified-devops-engineer-professional/)

→ End of Topic 05.
