# 12 — Data exposure for containers — on-premise patterns

> *"On-prem doesn't mean 'less security' — it means **you** own every layer of the trust boundary, with no AWS / GCP / Azure to lean on. Get the storage right and the rest follows."*

## Why this module exists

This is the first of four cloud-targeted deep dives requested by the user: "Cover all possible scenarios on how people use and expose data within Docker containers safely and securely. Cover this for on-premise, AWS, GCP, Azure."

On-prem is where the storage ecosystem is most diverse — NFS, CIFS, iSCSI, Ceph, GlusterFS, MinIO, Portworx, Longhorn, NetApp, Dell EMC PowerScale (Isilon), Pure FlashBlade. Each is a different trust model and a different way to fail. This module walks the full landscape, plus the cross-cutting concerns: encryption at rest, encryption in transit, key management without KMS, backups, air-gap, registries, and the regulated-finance posture.

We cover **Docker-on-host** here; on-prem Kubernetes is covered in module 29.

---

## 1. The storage taxonomy on-prem

### 1.1 File vs Block vs Object

| Kind | Protocols | Example backends | Container exposure pattern |
|---|---|---|---|
| **File (shared)** | NFSv3/v4, SMB/CIFS | NetApp, Isilon, GlusterFS, CephFS | Mount via Docker `local` driver with NFS opts, or `volume-driver` (legacy) |
| **Block** | iSCSI, FC, FCoE, NVMe-oF | NetApp SAN, Pure FlashArray, Dell PowerStore, Ceph RBD | Map iSCSI LUN to host, mkfs, bind-mount or volume |
| **Object** | S3 API, Swift | MinIO, Ceph RGW, Cloudian, Hitachi HCP | Pull/push via SDK; or mount via FUSE (s3fs, goofys) — slow, lossy |

### 1.2 Why this matters for containers

Containers prefer **file** or **object** storage. Block storage requires host-level mkfs + mount before bind-mounting into a container, which couples container lifecycle to host state — fragile.

For ML, the dominant pattern on-prem is **NFS to all training nodes**, with object storage (MinIO/Ceph RGW) holding model artifacts and large dataset archives. Spark/Iceberg/Delta workloads talk **S3 protocol** to MinIO or Ceph RGW.

---

## 2. NFS — the universal on-prem default

### 2.1 NFS volume in Docker

```bash
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=10.0.10.50,rw,vers=4.1,sec=sys,nconnect=8 \
  --opt device=:/exports/ml-data \
  ml-data

docker run -v ml-data:/data -e DATA_DIR=/data myorg/train:1.0
```

Critical options:

| Option | Default | Production setting | Why |
|---|---|---|---|
| `vers=` | varies | `4.1` (or `4.2`) | Modern stateful ACL support, parallel I/O via pNFS |
| `sec=` | `sys` | `krb5p` for sensitive data | `sys` is UID-trust on the wire (easily spoofed); `krb5p` is Kerberos + integrity + privacy |
| `nconnect=` | 1 | 4–16 | Multiple TCP connections per mount; massive throughput win for large reads |
| `hard,intr` | hard | `hard,intr` | Hang waiting on server (not silent corruption) on outages |
| `noatime` | off | `noatime` | Avoid update-on-read metadata storms |
| `rsize/wsize` | 1MB | 1MB or 4MB depending on backend | Larger reads, fewer round trips |

### 2.2 NFS auth — the AUTH_SYS trap

Default `sec=sys` means the client tells the server "I'm UID 1000" and the server trusts that. Anyone with root on the client (which is the host running Docker) can claim any UID. **This is not authentication; it's a convention.**

For regulated data, three options:

1. **`sec=krb5p`** — Kerberos auth + on-wire encryption. Requires KDC infra (typically AD).
2. **Network isolation** — put the NFS storage VLAN behind firewalls reachable only from blessed hosts.
3. **NFSv4 ACLs + per-host export rules** — each host only mounts what it needs; per-export root-squash to nobody.

For a Capital One–style regulated shop on-prem, **`sec=krb5p` + per-export root-squash + network-isolated storage VLAN** is the minimum.

### 2.3 UID/GID alignment

NFS reads/writes succeed based on UID/GID match between the container process and the file on the NFS server. Three common patterns:

- **All-hosts-converge**: every container that needs to access `ml-data` runs as UID 10001:10001; the NFS export is chown'd 10001:10001. Simple, brittle to multiple teams.
- **Per-team namespaces**: each ML team has a dedicated UID range; NFS exports per-team-dir with that UID's ACL. Scales better.
- **idmapd + NFSv4 names**: Linux `idmapd` maps remote NFSv4 names (`alice@CORP.EXAMPLE`) to local UIDs. Requires Kerberos and aligned name service.

### 2.4 NFS performance for ML training

For multi-node training where 8–256 GPUs read the same dataset:

- **`nconnect=16`** is the single biggest knob.
- **NFS pNFS (Parallel NFS)** with backends like NetApp ONTAP, Dell PowerScale (formerly Isilon), or BeeGFS gives parallel-stripe reads — same multi-GB/s as Lustre, less operational pain.
- For *very* large training (1k+ GPU), **Lustre** beats NFS. AWS FSx for Lustre is the cloud sibling.

### 2.5 NFS encryption at rest

NFS protocol itself doesn't encrypt at rest — that's the backend's job. NetApp Volume Encryption (NVE), Dell PowerScale at-rest encryption, CephFS via LUKS-backed OSD disks, etc. Without backend at-rest encryption, a stolen disk is a data breach.

---

## 3. CIFS / SMB — the Windows-shop default

For shops running file servers on Windows or where users access the same shares from Windows + Linux + containers:

```bash
docker volume create \
  --driver local \
  --opt type=cifs \
  --opt o=username=svc-mlpipe,password=...,uid=10001,gid=10001,vers=3.1.1 \
  --opt device="//fileserver.corp.example/ml-shared" \
  ml-shared
```

- `vers=3.1.1` is the modern dialect — has end-to-end encryption.
- Avoid putting passwords in volume options; bind-mount a credentials file instead.
- For Active Directory shops, Kerberos with `sec=krb5` is preferred over user/password.

CIFS is generally slower than NFS for large-file reads. For ML training, prefer NFS or object storage even in mixed Win/Linux shops.

---

## 4. iSCSI / FC / NVMe-oF — block storage to the host

Block storage is **mounted to the host**, then bind-mounted (or volume-mounted) into the container. The container never sees iSCSI directly.

```bash
# On the host
iscsiadm -m discovery -t st -p 10.0.20.50
iscsiadm -m node -T iqn.2026-05.com.example:lun.5 -l
mkfs.xfs /dev/sda
mount -o noatime /dev/sda /mnt/ml-block

# Now bind-mount or named-volume bind that path
docker run -v /mnt/ml-block:/data myorg/train:1.0
```

For containers this is just a bind mount; the container has no awareness of the underlying iSCSI session. Implications:

- **Host outage** = the data is unmounted, but a different host can re-attach the LUN (with multipathing).
- **Multi-host concurrent write**: NOT supported on a normal block FS. Use a clustered FS (GFS2, OCFS2) or a clustered block storage (Ceph RBD with appropriate locking) if you need RWX. Or skip block — file is what you want.
- **Encryption at rest**: LUKS on the block device. The host has the key (or KMS-backed via Clevis + Tang). Containers see decrypted files.

Block storage suits **single-writer, high-IOPS** workloads — Postgres, MySQL data dirs, Vault's storage backend. Not the right primitive for shared training data.

---

## 5. Ceph — the OSS distributed-storage answer

Ceph provides three interfaces:

- **CephFS** — POSIX file (RWX); NFS-compatible.
- **Ceph RBD** — block (one writer).
- **Ceph RGW** — S3-compatible object storage.

For containers:

- **CephFS** via NFS gateway or via CephFS kernel client on the host. Works with Docker's NFS volume driver.
- **RBD** mapped to host, then mounted into container (same pattern as iSCSI).
- **RGW** accessed via S3 SDK from the container; or mounted via `goofys`/`s3fs` (FUSE).

Ceph is operationally heavy. For ML on-prem with budget, **Rook-Ceph on K8s** (module 29) is what you'll meet most. For Docker-on-VM, NFS appliances (NetApp/Isilon) usually win on operational sanity.

---

## 6. MinIO — S3 protocol on-prem

[MinIO](https://min.io/) is the dominant on-prem S3-compatible object store. Single binary, K8s-native operator, drop-in for S3 SDKs. Used by:

- **Spark / Iceberg / Delta** for the storage layer (`s3a://bucket/path` with MinIO endpoint override).
- **Model artifact stores** (MLflow's S3 backend).
- **Vault snapshots**, **Velero backup targets**, **Loki object backend**, **Tempo** — basically anywhere "S3" is the protocol.

Container access pattern:

```bash
# In the container's env (or via secrets file)
AWS_ACCESS_KEY_ID=minio-svc-mlpipe
AWS_SECRET_ACCESS_KEY=...
AWS_ENDPOINT_URL_S3=https://minio.corp.example:9000
S3_BUCKET=ml-artifacts
```

```python
import boto3
s3 = boto3.client("s3", endpoint_url=os.environ["AWS_ENDPOINT_URL_S3"])
s3.upload_file("model.pt", "ml-artifacts", "models/2026/v1/model.pt")
```

The app uses the **standard boto3 SDK** with the endpoint override. No FUSE, no kernel-side mounts. This is the cleanest container-data pattern on-prem and the one most regulated shops adopt.

### 6.1 MinIO security

- **TLS mandatory** in production. Self-signed CA OK for internal; install CA bundle in container at `/etc/ssl/certs/internal-ca.pem`.
- **MinIO Identity & Access Management (IAM)** — AWS-compatible JSON policies. Use STS for short-lived credentials.
- **Encryption at rest** — MinIO supports SSE-S3 (server-side, MinIO-managed key) and SSE-KMS (with HashiCorp Vault as KMS). Use SSE-KMS for compliance.
- **Object Lock + Retention** for WORM (write-once-read-many) compliance use cases — same API as S3.
- **Auditing** — MinIO audit logs to a webhook or to Kafka. Ship to SIEM.

### 6.2 MinIO + Vault for short-lived credentials

The production pattern: app authenticates to Vault (via AppRole / Kubernetes auth / TLS cert), Vault issues a 1-hour MinIO access key. App uses it via boto3. Vault rotates automatically.

```bash
vault read minio/creds/ml-pipeline-role
# Returns: access_key, secret_key, lease_duration=3600
```

No long-lived secrets in containers. This is the on-prem equivalent of IRSA / Workload Identity Federation.

---

## 7. The on-prem volume driver alternatives

Beyond NFS/CIFS/iSCSI, three plugin ecosystems matter on-prem:

### 7.1 Portworx (Pure Storage)

Commercial, K8s-first but has Docker plugin. Block storage atop your existing disks (DAS / SAN / SSDs). Features:

- Storage classes per workload (gold = SSD replicated, silver = HDD).
- Snapshots, clones, sync replication across DCs.
- Per-volume encryption with PX-Backup integration.
- BYOK with Vault KMS.

Adopt when: K8s-centric ML platform, need disaster-recovery-grade primitives.

### 7.2 Longhorn (Rancher / SUSE)

OSS, CNCF Incubating. K8s-first (DaemonSet on each node). Each volume is a striped replicated block device backed by the local disks of N nodes. Features:

- Snapshots + backups to S3 (or MinIO) compatible target.
- Volume encryption via LUKS.
- Multi-region replication via DR.

Adopt when: low budget, K8s on bare-metal, willing to operate the OSS.

### 7.3 OpenEBS (Mayastor / cStor / Jiva engines)

OSS, CNCF Sandbox. K8s-first. Multiple engines for different performance profiles (Mayastor = NVMe-fabric for performance, cStor = ZFS-based for snapshots, Jiva = simple per-node).

Adopt when: K8s on bare metal, need NVMe performance, OK with operating CNCF sandbox.

For pure Docker (no K8s) on-prem, **NFS + MinIO + iSCSI for stateful DBs** is the most-operated pattern. Portworx/Longhorn/OpenEBS shine in K8s (module 29).

---

## 8. Encrypting data at rest without a cloud KMS

The cloud's biggest hidden gift is KMS — managed key storage with hardware HSMs. On-prem, you have three paths:

### 8.1 Self-hosted Vault Transit / KMS

HashiCorp Vault's `transit` engine acts as a KMS: applications send plaintext for encryption, receive ciphertext, and the key never leaves Vault. Backed by an in-cluster HSM or by Vault's `auto-unseal` against an actual HSM (Thales, Entrust).

Pattern: container fetches the data encryption key (DEK) from Vault Transit, encrypts/decrypts data locally; the DEK is wrapped by a key encryption key (KEK) that never leaves Vault.

### 8.2 LUKS on storage volumes

For host-level disk encryption: LUKS (Linux Unified Key Setup) with key in Vault. `clevis` automates LUKS unlock against `tang` (a network presence service); a host can boot only when it can reach `tang`. This means a stolen disk is unreadable; a stolen host without network access is unreadable.

### 8.3 Storage appliance native encryption

NetApp NVE, Dell PowerStore native encryption, Pure FlashArray DARE. The storage controller handles encryption at rest; key management often integrates with Vault, Thales, or Entrust.

For a regulated-finance shop on-prem, **defense in depth**: storage-controller encryption + LUKS on dedicated volumes + Vault Transit for application-level field encryption (PII).

---

## 9. Backups

Container data backup on-prem:

- **For NFS/CephFS**: storage-controller snapshots (NetApp Snapshots, Ceph FS snapshots) + replicate snapshots to a backup site or to MinIO via `restic`.
- **For block volumes**: storage-controller snapshots + LVM thin snapshots; ship to backup with `borgbackup` / `restic`.
- **For MinIO**: bucket replication to a DR MinIO cluster.
- **For container state**: `restic` from inside a backup container — `docker run --rm -v mydata:/data:ro -v backup-cache:/cache restic/restic ...`

For K8s on-prem (module 29), **Velero** is the standard with CSI snapshots.

---

## 10. Air-gap and the private registry mirror

Many regulated shops are **air-gapped**: no internet from production. Two implications for containers:

1. **No Docker Hub / Quay / GHCR pulls in prod.** All images must come from a self-hosted registry (Harbor, JFrog Artifactory, ECR/GAR/ACR if running an on-prem-mirror service).
2. **PyPI / npm / Maven mirrors.** Sonatype Nexus or JFrog Artifactory or pypiserver mirrors that are sync'd from upstream via a controlled "diode."

Pattern:
- DMZ host with internet pulls upstream images, scans, signs.
- Promotes by digest into the air-gapped registry.
- Production hosts pull only from air-gapped registry.

CI/CD inside the air gap needs:
- Hermetic builders (no internet egress allowed).
- Pinned dependencies in lockfiles.
- All build tooling pre-pulled.

---

## 11. On-prem container egress controls — IMDS-equivalent risks

On-prem doesn't have IMDS, but it has analogues:

- **Service accounts on shared file systems**: if a container has access to a host path containing service-account JSON keys (`/etc/secrets/gcp-sa.json` left over from migration), it can pivot.
- **Internal-only services like config servers**: a Vault server reachable from one container is reachable from any compromised container on the same network. Egress filter to `vault.corp.example:8200` per container via `iptables` / `nftables` in the DOCKER-USER chain.
- **DNS resolvers** as a covert channel: lock down DNS to your internal resolver and monitor query patterns.

The principle: **egress is a security control, not an availability one.** Default-deny outbound; explicitly allow per workload.

---

## 12. Pulling it together — the on-prem ML data architecture

A defensible reference architecture for ML containers on-prem:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Production VLAN (containers)                                   │
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │ training pod │    │ inference pod│    │ pipeline pod │      │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│          │ NFS krb5p          │ S3                │ DB           │
│          │ /data              │ via boto3         │ via PgBouncer│
└──────────┼───────────────────┼───────────────────┼──────────────┘
           │                   │                   │
   ┌───────▼──────┐    ┌───────▼──────┐    ┌───────▼──────┐
   │ NetApp ONTAP │    │ MinIO cluster│    │ PgBouncer +  │
   │ + NVE        │    │ + Vault KMS  │    │ Postgres HA  │
   │ + Snapshots  │    │ + bucket repl│    │ + LUKS       │
   └──────────────┘    └──────────────┘    └──────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │ Vault       │
                                            │ (Transit +  │
                                            │  K8s auth + │
                                            │  HSM-unseal)│
                                            └─────────────┘
```

Cross-cuts:

- **Image source**: Harbor on-prem, replicated from DMZ-Harbor (which pulls upstream).
- **Identity**: Vault K8s auth (for K8s) or AppRole (for VMs).
- **Secrets**: Vault Transit + dynamic credentials, not static.
- **Audit**: Falco + audit log shipped to SIEM.
- **Egress**: DOCKER-USER chain + per-VLAN firewall; default-deny outbound.
- **DR**: NFS snapshots replicated to DR site; MinIO bucket replication; Vault Raft replicated.

---

## Sanity check

1. What does `sec=sys` actually trust, and why isn't that authentication?
2. Why does `nconnect=8` materially change ML training throughput on NFS?
3. iSCSI is mounted to the host, then bind-mounted into the container. Why does that mean iSCSI is NOT suitable for multi-host RWX use cases?
4. What does MinIO's SSE-KMS need that SSE-S3 does not, and why does compliance often require SSE-KMS?
5. How does Vault Transit differ architecturally from Vault's regular KV engine for handling encryption?
6. In an air-gapped shop, name three categories of external dependency that must have on-prem mirrors.

---

## Sources

- [Linux NFS docs](https://www.kernel.org/doc/Documentation/filesystems/nfs/)
- [SMB/CIFS man page](https://linux.die.net/man/8/mount.cifs)
- [MinIO docs](https://min.io/docs/minio/)
- [HashiCorp Vault Transit](https://developer.hashicorp.com/vault/docs/secrets/transit)
- [Rook-Ceph](https://rook.io/)
- [Longhorn](https://longhorn.io/)
- [OpenEBS](https://openebs.io/)
- [Portworx](https://portworx.com/)
- [Tang & Clevis](https://github.com/latchset/tang)
- [Velero](https://velero.io/)

→ Next: [13 — **Data exposure — AWS**](13_data_exposure_aws.md)
