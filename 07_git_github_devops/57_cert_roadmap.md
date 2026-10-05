# 57 — Certification roadmap (GH-900, GH-200, GH-500, GH-300, CJE)

> *"Certifications are credibility signals to recruiters and hiring managers. The four GitHub certs + Jenkins map cleanly to this role."*

## Why this module exists

Closing Topic 07 with the cert ladder. None of these are required to do the job; all of them help in a competitive market for the Sr Lead seat. Costs, durations, contents, and recommended sequence below.

---

## 1. The ladder

| Order | Cert | Code | Duration | Cost | Vendor |
|---|---|---|---|---|---|
| 1 | GitHub Foundations | GH-900 | 120 min | $99 (often -50%) | Microsoft Learn |
| 2 | GitHub Actions | GH-200 | 100 min | $99 | Microsoft Learn |
| 3 | GitHub Advanced Security | GH-500 | 100 min | $99 | Microsoft Learn |
| 4 | GitHub Administration | GH-300 | 100 min | $99 | Microsoft Learn |
| 5 | CloudBees Certified Jenkins Engineer | CJE | 90 min | ~$300 | CloudBees |
| 6 | (Optional) GitHub Copilot | GH-CP-CHK (recently added) | — | $99 | Microsoft Learn |

All GitHub certs administered via Microsoft Learn (Pearson VUE proctored). Pass = 70%. Valid 2 years.

---

## 2. GitHub Foundations (GH-900)

**Target**: entry-level understanding of GitHub.

**Topics**: repos, branches, PRs, Issues, Projects, GitHub Actions intro, GitHub Pages, security basics, account/billing, Markdown.

**Why take it**: easy entry, builds discipline on terminology + features you may not have used (Discussions, Pages, Projects v2). 75 scored + 10-15 unscored questions in 120 min.

**Prep**: official study guide on Microsoft Learn; ~2 weeks at 1h/day with hands-on. Free practice tests on OpenExamPrep and similar.

**Decision**: yes, take it. Cheap signal, fast win.

---

## 3. GitHub Actions (GH-200)

**Target**: workflow authoring, runners, secrets, events, deployment automation.

**Topics**: workflow syntax, jobs/steps, runners (hosted + self-hosted), events + triggers, expressions/contexts, env/secrets/vars, matrix, caching, artifacts, reusable workflows, composite actions, GITHUB_TOKEN, environments + protection rules, OIDC, security best practices.

**Why take it**: highest-ROI cert for this role. Hiring managers actively look for it. Aligns directly with Topic 07 Parts E + F.

**Prep**: official study guide updated Jan 2026 (covers 2026 features); cross-reference Topic 07 modules 20-31; hands-on building reusable workflows in your own repo. 2-3 weeks at 1h/day.

**Decision**: yes — this is THE cert for Sr Lead with CI/CD focus.

---

## 4. GitHub Advanced Security (GH-500)

**Target**: security professionals + developers responsible for code/dep/secret scanning.

**Topics**: CodeQL (default + advanced setup, custom queries), Copilot Autofix, secret scanning + push protection, Dependabot (alerts + security updates + version updates), dependency review, security advisories, SBOM, Artifact Attestations, SLSA, supply-chain security.

**Why take it**: bank-grade signal. Capital One operates GHAS at scale; this cert proves you understand the stack. Aligns with Topic 07 Parts G + H.

**Prep**: 2-3 weeks if you're already familiar with the topic. CodeQL custom queries are the hardest section (need to write QL).

**Decision**: yes if targeting bank/regulated roles. For non-regulated SaaS, lower priority.

---

## 5. GitHub Administration (GH-300)

**Target**: GitHub Enterprise Cloud / Enterprise Server administrators.

**Topics**: org/team/enterprise hierarchy, SAML SSO, SCIM, IP allow lists, policies, audit logs, custom roles, GHES install + upgrade, runner administration, Apps + OAuth, license management.

**Why take it**: if you'll be on the platform team. As an ML Sr Lead, you're more "user" than "admin" — but knowing how the platform layer works distinguishes you.

**Decision**: defer until specifically needed. Optional for ML Sr Lead.

---

## 6. CloudBees Certified Jenkins Engineer (CJE)

**Target**: Jenkins users + administrators.

**Topics**: Pipeline syntax (declarative + scripted), Jenkinsfile, multibranch, shared libraries, plugins, Blue Ocean, credentials, agents (incl. K8s), security, admin (controller setup, backup, upgrade), troubleshooting.

**Why take it**: Capital One uses Jenkins extensively. CJE is widely-recognized in the Jenkins community. Worth $300.

**Prep**: 3-4 weeks. Hands-on with Jenkinsfile + shared library required.

**Decision**: yes if targeting Capital One specifically (or any large enterprise heavily using Jenkins). Otherwise optional.

---

## 7. The supporting cert ecosystem

Adjacent certs relevant to this role:

| Cert | Why |
|---|---|
| **AWS Certified Solutions Architect Associate** | Foundational AWS — see Topic 04 cert roadmap |
| **AWS Certified Machine Learning Specialty** | ML on AWS — see Topic 04 cert roadmap |
| **AWS Certified DevOps Engineer Professional** | CI/CD + ops on AWS |
| **CKA (Certified Kubernetes Administrator)** | K8s — see Topic 05 |
| **HashiCorp Certified: Terraform Associate** | If using Terraform |

For Capital One Sr Lead AI/ML Engineer, the cert priority order:
1. AWS SA Associate (table stakes)
2. AWS ML Specialty (role fit)
3. GitHub Actions (CI/CD)
4. GitHub Advanced Security (bank-relevant)
5. AWS DevOps Engineer Professional (ML-Eng + CI/CD bridge)
6. CKA (if doing EKS-KServe heavily)
7. Jenkins CJE (Capital One specific)
8. GitHub Foundations (easy win)

---

## 8. Practice resources

- **Microsoft Learn** — free study guides for all GH certs
- **OpenExamPrep** — free practice tests
- **Udemy** — paid practice exams (Lazaro Diaz and others have prep courses)
- **YouTube** — Stephane Maarek for AWS, varied for GitHub
- **GitHub Docs** — the authoritative source for everything GH
- **Hands-on**: build a repo that exercises every topic (reusable workflows, OIDC, CodeQL custom queries, ARC on a local K8s, etc.)

---

## 9. The "should I really take the cert?" thinking

Certs are NOT a substitute for doing the work. Hiring managers know this. A cert helps when:
- You're entering a new domain and need to signal "I've at least covered the basics."
- You're competing against candidates who have certs and you don't.
- You're a contractor / consultant where credentials matter for vetting.
- You're new to a tool (cert provides structured learning path).

A cert HURTS when:
- You list it but can't speak to depth in an interview.
- It crowds out actually building things.

For Sr Lead at Capital One: the certs above are bonuses to a strong portfolio. Your *Topic 04 + 05 + 06 + 07 modules + projects* are the real signal. Certs validate.

---

## 10. The 90-day prep plan (suggested)

Assuming you have AWS SA Associate already.

- **Weeks 1–3**: GitHub Foundations (GH-900). Light study + take exam.
- **Weeks 4–7**: GitHub Actions (GH-200). Hands-on building reusable workflows. Take exam.
- **Weeks 8–11**: GitHub Advanced Security (GH-500). Practice with CodeQL custom queries. Take exam.
- **Weeks 12–13**: Jenkins CJE (if pursuing). Build a Jenkinsfile + shared library. Take exam.

Spread out further if life gets in the way. 3 GitHub certs + 1 Jenkins cert in 3 months is aggressive but achievable.

---

## 11. The closing thought

Topic 07 was 57 modules deep. The certs validate the surface; the modules + your project portfolio prove the depth. Use the certs as forcing functions to systematize what you've learned — not as the goal.

For the Capital One conversation:
- "I've certified GitHub Actions, GHAS, and Jenkins; I've built [your project here] that exercises OIDC + reusable workflows + ARC + Jenkins shared libraries"
- > "I've certified GitHub Actions, GHAS, and Jenkins" alone

The cert opens the door. The portfolio + the conversation walk you through it.

---

## 12. Cross-references

- The complete Topic 07 syllabus → [`README.md`](README.md) and [`00_Table_Of_Contents.md`](00_Table_Of_Contents.md).
- Companion dossier for Capital One specifically → [`CAPITAL_ONE.md`](CAPITAL_ONE.md).
- Topic 04 cert roadmap (AWS-side) → topic 04 module 57.
- Topic 05 cert roadmap (Docker/K8s side) → topic 05 module 32 (or similar).
- Topic 06 cert roadmap (Airflow side) → topic 06 module 32.
