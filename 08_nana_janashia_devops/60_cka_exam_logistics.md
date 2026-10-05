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
