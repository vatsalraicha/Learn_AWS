# Topic 05 — Table of Contents

> Master index. Use this to navigate; use [`README.md`](README.md) for the why-and-how-to-read-this overview.

## Part A — Container fundamentals
1. [Linux primitives: namespaces, cgroups, capabilities, seccomp, LSMs](01_linux_primitives.md)
2. [Docker architecture & runtime: dockerd → containerd → runc → OCI](02_docker_architecture.md)
3. [Dockerfile & image layers — building production images](03_dockerfile_images.md)
4. [Image security: scanning, SBOM, signing, supply chain](04_image_security.md)
5. [Container registries: ECR, GAR, ACR, Harbor, JFrog](05_registries.md)

## Part B — Docker networking & storage
6. [Docker networking — bridge, host, overlay, macvlan, port publishing](06_docker_networking.md)
7. [Docker storage — bind mounts, volumes, tmpfs, volume drivers](07_docker_storage.md)
8. [Secrets in Docker — BuildKit secrets, Swarm secrets, runtime patterns](08_docker_secrets.md)
9. [Docker Compose & local development](09_docker_compose.md)

## Part C — Container security & hardening
10. [Container hardening checklist](10_hardening_checklist.md)
11. [CIS Docker Benchmark + common CVEs](11_cis_cves.md)

## Part D — Exposing data IN/OUT of containers, per cloud
12. [**Data exposure — on-premise**](12_data_exposure_onprem.md)
13. [**Data exposure — AWS**](13_data_exposure_aws.md)
14. [**Data exposure — GCP**](14_data_exposure_gcp.md)
15. [**Data exposure — Azure**](15_data_exposure_azure.md)

## Part E — Kubernetes fundamentals
16. [K8s architecture — control plane, kubelet, kube-proxy, etcd, CRDs](16_k8s_architecture.md)
17. [Workload objects — Pod, Deployment, StatefulSet, DaemonSet, Job, CronJob](17_workload_objects.md)
18. [Services & networking — Ingress, Gateway API, NetworkPolicy, CNI](18_k8s_networking.md)
19. [Storage in K8s — PV, PVC, StorageClass, CSI, ephemeral, projected](19_k8s_storage.md)
20. [ConfigMaps & Secrets — etcd encryption-at-rest, sealed-secrets, external-secrets](20_configmap_secrets.md)

## Part F — Kubernetes security
21. [RBAC & ServiceAccounts](21_rbac_serviceaccounts.md)
22. [Pod Security — PSA, SecurityContext, runtime classes](22_pod_security.md)
23. [Admission control — OPA Gatekeeper, Kyverno](23_admission_control.md)
24. [Supply chain on K8s — image signing admission, SBOM, BinAuth](24_k8s_supply_chain.md)
25. [Observability & runtime security — Prom, OTel, Falco, Hubble](25_observability_runtime.md)

## Part G — Exposing data in K8s, per cloud
26. [**EKS deep — IRSA, Pod Identity, EFS/FSx/S3 CSI, ASCP, KMS**](26_eks_data_exposure.md)
27. [**GKE deep — Workload Identity Federation, GCS Fuse CSI, BinAuth**](27_gke_data_exposure.md)
28. [**AKS deep — Entra Workload ID, Azure Files/Disk/Blob CSI, Key Vault CSI**](28_aks_data_exposure.md)
29. [**On-prem K8s — Rook-Ceph, Longhorn, Velero, Vault, MetalLB, air-gap**](29_onprem_k8s_data.md)

## Part H — AI/ML on Kubernetes
30. [Model serving on K8s — KServe, Seldon, BentoML, Triton, vLLM, Ray Serve](30_model_serving_k8s.md)
31. [Training on K8s — Training Operator, Volcano, GPU Operator, Karpenter](31_training_k8s.md)
32. [Service mesh & zero-trust — Istio, Linkerd, Cilium, SPIFFE/SPIRE](32_service_mesh.md)

## Part I — Certifications & roadmap
33. [Certification roadmap — KCNA, KCSA, CKAD, CKA, CKS](33_cert_roadmap.md)

## Companion files
- [README.md](README.md) — topic overview and how to use this corpus
- [FACTS.md](FACTS.md) — atomic citable facts with last-verified dates
- [quizzes/](quizzes/) — per-part quizzes
- [code/](code/) — Dockerfiles, K8s manifests, Helm fragments, Terraform per cloud
