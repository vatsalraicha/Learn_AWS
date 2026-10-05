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
