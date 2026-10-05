# 27 — GKE deep: Workload Identity Federation, GCS Fuse CSI, Filestore CSI, Secret Manager CSI, BinAuth, Autopilot

## Why this module exists

GKE is the K8s with the cleanest identity story (Workload Identity Federation by default) and the most opinionated managed flavor (Autopilot). For a Sr Lead candidate, understanding GKE's primitives sharpens the EKS view by contrast.

---

## 1. Identity — Workload Identity Federation for GKE

Each pod's KSA maps to a GCP service account via annotation:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: infer-server
  namespace: ml-serving
  annotations:
    iam.gke.io/gcp-service-account: infer-server@my-proj.iam.gserviceaccount.com
```

Then bind:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  infer-server@my-proj.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:my-proj.svc.id.goog[ml-serving/infer-server]"
```

Pod's `DefaultCredentials` uses the GKE metadata server (`metadata.google.internal`); the GKE-side workload identity component intercepts and trades the K8s token for a GCP access token via the GSA. No JSON keys. Period.

For new clusters (mid-2024+), enable **Workload Identity Federation for GKE in its new mode** (the "GKE Identity Federation"), which is cleaner under the hood. Old "Workload Identity for GKE" is the same model architecturally.

### 1.1 Org policy: ban JSON keys

```yaml
constraint: constraints/iam.disableServiceAccountKeyCreation
booleanPolicy: { enforced: true }
```

Apply at the organization level. Eliminates a whole class of credential leaks.

---

## 2. PD CSI — block storage

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: ssd-cmek }
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  disk-encryption-kms-key: projects/my-proj/locations/us-central1/keyRings/my-kr/cryptoKeys/my-key
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
reclaimPolicy: Retain
```

Hyperdisk variants (Balanced, Throughput, Extreme) for tier separation. CMEK via Cloud KMS key reference.

For training checkpoints / vector indices / databases: `pd-ssd` is the default; Hyperdisk Balanced for cost.

---

## 3. GCS Fuse CSI driver — S3-equivalent mounted into pods

GA late 2023. Sidecar architecture: the driver injects a `gcs-fuse-sidecar` per pod that runs `gcsfuse` and presents the GCS bucket as a volume to the main container.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: train
  namespace: ml-training
  annotations:
    gke-gcsfuse/volumes: "true"
    gke-gcsfuse/cpu-limit: "500m"
    gke-gcsfuse/memory-limit: 1Gi
spec:
  serviceAccountName: train-sa
  containers:
    - name: train
      image: nvcr.io/nvidia/pytorch:24.06-py3
      volumeMounts:
        - { name: training-data, mountPath: /data, readOnly: true }
  volumes:
    - name: training-data
      csi:
        driver: gcsfuse.csi.storage.gke.io
        readOnly: true
        volumeAttributes:
          bucketName: myorg-training-2026q2
          mountOptions: "implicit-dirs,file-cache-max-size-mb=10000"
```

The KSA `train-sa` is WIF-bound to a GSA with `roles/storage.objectViewer` on the bucket. Pods now have a read-only S3-equivalent at `/data`.

For ML training: this is the cleanest "read training data from object storage" pattern. Better than s3fs on AWS by quite a margin.

---

## 4. Filestore CSI — managed NFS

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata: { name: filestore-enterprise }
provisioner: filestore.csi.storage.gke.io
parameters:
  tier: enterprise
  network: my-vpc
  reserved-ipv4-cidr: 10.10.0.0/29
allowVolumeExpansion: true
```

RWX NFS for "many pods read the same data" patterns. Enterprise tier for HA. Comparable to AWS EFS or Azure Files.

---

## 5. Parallelstore — GCP's Lustre answer (2024)

For 1000+ GPU training, Parallelstore (GA mid-2024) is GCP's high-perf parallel FS. Mounts via CSI. Comparable to FSx for Lustre on AWS.

---

## 6. Secret Manager CSI provider

[secrets-store-csi-driver-provider-gcp](https://github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp):

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: db-creds, namespace: ml-serving }
spec:
  provider: gcp
  parameters:
    secrets: |
      - resourceName: "projects/my-proj/secrets/db-password/versions/latest"
        fileName: "db_password"
```

Pod's KSA (WIF-bound) needs `roles/secretmanager.secretAccessor` on the secret. Mount appears at the volume path.

ESO with GCP backend is the alternative if you want a K8s Secret object.

---

## 7. Binary Authorization — image attestations enforced

Already covered in module 24. GKE has the deepest cloud-native integration:

- Attestation notes stored in Grafeas (Container Analysis).
- Policy applied per cluster.
- Break-glass via deploy-time label, audited.

For regulated GKE clusters: BinAuth + signed images + CMEK. Standard.

---

## 8. GKE Autopilot — opinionated managed mode

GA Feb 2021. Differences from Standard:

- Node pools managed entirely by Google.
- You pay per pod resources (vCPU·hr, GB·hr) rather than per node-hour — predictable.
- Restrictions: no privileged pods, no hostPath, no hostNetwork, no `nodeSelector` for arbitrary labels, no DaemonSets except whitelisted, limited preempt.
- Default security: PSA-restricted, Workload Identity required.

For ML serving: Autopilot is fine and removes node ops. For ML training with GPUs and fine-grained tuning: Standard.

---

## 9. Confidential GKE Nodes

Confidential GKE runs nodes on **AMD SEV** (and **Intel TDX**, depending on region) — VM memory encrypted with a per-VM key. Useful for processing PII in containers where you don't want even Google operators to read memory.

```bash
gcloud container clusters create prod --enable-confidential-nodes
```

Same model as Azure Confidential containers. For regulated finance, this is the strongest hardware boundary.

---

## 10. Dataplane V2 — Cilium under the hood

GKE Dataplane V2 (default for new clusters since 2021) replaces kube-proxy + the legacy CNI with **Cilium**. Implications:

- L7 visibility (Hubble equivalent via gcloud CLI / Cloud Console).
- NetworkPolicy enforcement is built-in.
- BPF-based, low overhead at scale.

If you've been on Dataplane V2 for years, you're getting Cilium without knowing it.

---

## 11. The reference GKE+KServe architecture (for the curious)

Same idea as the EKS reference, with substitutions:

| Layer | EKS | GKE |
|---|---|---|
| Identity per pod | IRSA / Pod Identity | Workload Identity Federation |
| Block CSI | EBS CSI | PD CSI |
| File RWX CSI | EFS CSI | Filestore CSI |
| HPC | FSx for Lustre CSI | Parallelstore CSI |
| Object | Mountpoint-S3 CSI | GCS Fuse CSI |
| Secrets | ASCP / ESO | Secret Manager CSI / ESO |
| Image signing admission | Kyverno + Cosign | Binary Authorization |
| Dataplane | VPC CNI / Cilium | Dataplane V2 (Cilium) |
| Autoscaling | Karpenter | Cluster Autoscaler / Autopilot |

---

## Sanity check

1. Why does GCP's `iam.disableServiceAccountKeyCreation` org policy eliminate a whole class of credential leaks?
2. GCS Fuse CSI runs as a sidecar per pod, not as a node-level mount. What's the trade-off?
3. GKE Autopilot disallows hostPath. Why does that block some workloads, and which ones?
4. Confidential GKE Nodes — what specifically do they protect against?
5. GKE Dataplane V2 — what does it replace, and what does that give you?
6. Map: AWS EFS → GCP ?, AWS FSx-Lustre → GCP ?, AWS Secrets Manager → GCP ?

---

## Sources

- [Workload Identity Federation for GKE](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [GCS Fuse CSI Driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/cloud-storage-fuse-csi-driver)
- [Filestore CSI](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver)
- [Parallelstore](https://cloud.google.com/parallelstore/docs)
- [Secret Manager CSI Provider for GCP](https://github.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp)
- [Binary Authorization](https://cloud.google.com/binary-authorization)
- [GKE Autopilot](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Confidential GKE Nodes](https://cloud.google.com/confidential-computing/confidential-gke-nodes)
- [GKE Dataplane V2](https://cloud.google.com/kubernetes-engine/docs/concepts/dataplane-v2)

→ Next: [28 — **AKS deep — Entra Workload ID, Azure Files/Disk/Blob CSI, Key Vault CSI**](28_aks_data_exposure.md)
