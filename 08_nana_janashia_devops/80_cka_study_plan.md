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
