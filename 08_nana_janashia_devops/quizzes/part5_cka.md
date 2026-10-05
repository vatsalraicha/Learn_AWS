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
