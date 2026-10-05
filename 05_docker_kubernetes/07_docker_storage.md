# 07 — Docker storage: bind mounts, volumes, tmpfs, volume drivers

> *"`-v /:/host` is RCE. `-v /var/run/docker.sock:/var/run/docker.sock` is RCE. `-v ~/.aws:/root/.aws` is credential theft. The volume flag is the most security-critical thing in `docker run`."*

## Why this module exists

Volumes are how data crosses the container/host boundary. They are also how the most common container escapes happen. This module covers the three volume types, the eight common patterns, and the four anti-patterns that will land you in a Capital One–style postmortem.

We focus on Docker semantics; module 19 covers Kubernetes' PV/PVC/StorageClass model which is a different abstraction with similar primitives underneath.

---

## 1. Three storage types

| Type | Where it lives | Lifecycle | Use case |
|---|---|---|---|
| **Bind mount** | Arbitrary host path | Host file's lifecycle | Dev (code reload), legacy apps expecting host paths |
| **Named volume** | `/var/lib/docker/volumes/<name>/_data` (or volume driver backend) | Independent of container; explicit delete | The default for any persistent state |
| **tmpfs mount** | RAM (host page cache, not host disk) | Lost on container stop | Secrets at runtime, scratch space, CI temp files |

### 1.1 Bind mount

```bash
docker run -v /home/vr/data:/data:ro,Z myapp
```

- `:ro` — read-only mount.
- `:Z` — relabel the source with the SELinux container label (RHEL/AL2/AL2023; lowercase `z` is shared, uppercase `Z` is private to this container).
- `:rshared` / `:rslave` — mount propagation; rarely needed; common in monitoring sidecars.

**Bind mounts are the most dangerous primitive in Docker.** They bypass image immutability — anything on the host is visible to the container, subject to UID/GID/SELinux. Three rules:

1. **Never** mount `/`, `/etc`, `/var`, `/home`, `~`, or any directory containing config or keys.
2. **Always** mount read-only if the container only needs to read.
3. **Always** use a dedicated, locked-down directory whose owner/perms match the container's UID.

### 1.2 Named volume

```bash
docker volume create mydata
docker run -v mydata:/data myapp
```

The volume is managed by Docker; its on-disk path is `/var/lib/docker/volumes/mydata/_data`. Named volumes:

- Persist beyond container deletion.
- Get backed up by `docker volume` commands or via volume drivers.
- Can be exposed by **volume drivers** to remote backends: NFS, EFS, Ceph, Portworx, AWS EBS via `rexray`, etc.
- Are the recommended default for any state.

**Volume drivers** are the cloud-data-exposure hook. We cover them in modules 12–15.

### 1.3 tmpfs mount

```bash
docker run --tmpfs /tmp:size=64m,mode=1777 myapp
```

The mount lives in RAM. Tmpfs is mandatory when running with `--read-only` (containers need *some* writable space for `/tmp`). It's also the right place for:

- Cached secrets (loaded once at startup, mounted in RAM, never hit disk).
- Temporary files that contain sensitive data (model intermediate outputs, query results).
- Scratch space that must not persist.

---

## 2. The anti-pattern hall of fame

| Anti-pattern | Why it's catastrophic | The fix |
|---|---|---|
| `-v /var/run/docker.sock:/var/run/docker.sock` | Root on host via Docker API | Use a socket proxy (Tecnativa, Datadog) with verb whitelist; or use rootless |
| `-v /:/host` | Trivial root escape — chroot + writes to /etc/sudoers | Never. If you must read host data, mount the specific path read-only |
| `-v ~/.aws:/root/.aws` or `-v ~/.kube:/root/.kube` | Steals user's cloud creds | Use IRSA / Workload Identity / Managed Identity instead (modules 13-15) |
| `-v ~/.ssh:/root/.ssh` | Steals SSH keys | Use BuildKit `--mount=type=ssh` at build, runtime needs no SSH |
| `-v /etc:/etc` | Container can read `/etc/shadow`, modify `/etc/passwd` | Never |
| Mount a Postgres data dir into a container with UID mismatch | Postgres refuses to start (correctly) | `--user $(id -u):$(id -g)` and `chown` the host dir |
| Host path used as both container data AND container runtime cache | Container can corrupt its own image artifacts | Separate paths |
| Bind mount over a Dockerfile-defined VOLUME | Image's seed data is hidden | Either bind-mount-only-the-subdirs or remove `VOLUME` from Dockerfile |

The `docker.sock` mount is so dangerous that any code review tool should flag it. The Cloud Custodian / Falco / Kyverno rule for "containers must not mount the Docker socket" is table stakes.

---

## 3. The Dockerfile `VOLUME` directive

`VOLUME /data` in a Dockerfile marks that path as a volume mount point. At runtime, if you don't supply `-v`, Docker creates an **anonymous volume** at that path. Anonymous volumes get a random ID; `docker volume ls --filter dangling=true` finds them.

Implications:

- Any state your image writes to that path **must** be in a volume — you can't bake initial state into the image after `VOLUME` is declared in the Dockerfile (it'd be shadowed by the volume mount).
- Anonymous volumes accumulate. Long-running production hosts gather hundreds of GB of "where did this come from?" volumes.
- Some images (Postgres, MySQL) declare `VOLUME /var/lib/postgresql/data`; this is why `-v pgdata:/var/lib/postgresql/data` is the standard pattern.

**Production rule**: always supply `-v` for any `VOLUME` directive. Use named volumes for clarity.

---

## 4. Volume drivers — the extension point

Docker volumes can be backed by remote storage via volume drivers. The driver ecosystem peaked around 2018 and has consolidated. Current healthy options:

| Driver | Backend | Notes |
|---|---|---|
| `local` (default) | Host filesystem | The default; also supports `tmpfs`, `nfs`, `cifs` options |
| `nfs` (via local + opts) | NFS server | `docker volume create -d local --opt type=nfs --opt o=addr=nfs.internal,rw --opt device=:/exports/data nfsvol` |
| `cifs` (Windows shares) | SMB/CIFS | Similar pattern, `type=cifs` |
| Portworx (`pxd`) | Portworx | Multi-node block storage, commercial |
| Longhorn | Rancher | OSS, K8s-first, has Docker plugin |
| REX-Ray | Multi-cloud (EBS, Azure Disk, GCE PD) | Mostly deprecated since 2020; use cloud CSI on K8s instead |

The Docker volume driver model is largely **deprecated for new development**. Kubernetes CSI replaced it; the volume primitives in Compose v2 still work but no new drivers are landing. For Docker-on-VM workloads, the local-NFS option is what you'll see most.

### 4.1 NFS volume — the on-prem default

```bash
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=10.0.0.50,rw,vers=4.1,nconnect=8 \
  --opt device=:/exports/mldata \
  mldata

docker run -v mldata:/data myimage
```

For ML workloads on-prem, this is how training data lives on a NetApp/Isilon/MinIO-NFS and is exposed to PyTorch containers.

---

## 5. Volume hygiene & lifecycle

### 5.1 Inspection

```bash
docker volume ls
docker volume ls --filter dangling=true        # not attached to any container
docker volume inspect mydata
docker system df -v                            # disk usage by volume
```

### 5.2 Cleanup

```bash
docker volume prune                            # remove dangling
docker volume prune --filter "label!=keep"     # respect a label
```

In production: tag volumes with `--label backup=daily` or similar; prune everything without the label periodically.

### 5.3 Backup

There is no built-in volume backup. The standard pattern:

```bash
docker run --rm \
  -v mydata:/data:ro \
  -v $(pwd):/backup \
  alpine \
  tar czf /backup/mydata-$(date +%F).tar.gz -C /data .
```

For cloud volume backends (EBS, EFS), use the native snapshot API. For NFS, use the storage appliance's snapshot (NetApp, Isilon, Ceph RBD). For self-hosted production volume backup, **Velero** is the K8s answer (module 29).

---

## 6. Read-only root + writable tmpfs — the production pattern

The hardest container is one whose root filesystem is read-only:

```bash
docker run \
  --read-only \                            # root FS is RO
  --tmpfs /tmp:size=64m,mode=1777 \        # writable /tmp
  --tmpfs /run:size=16m,mode=755 \         # writable /run for nginx, etc
  -v mydata:/data \                        # explicit named volume for state
  myimage
```

Benefits:

- Eliminates the "attacker writes a webshell into `/opt/`" class of attacks.
- Makes the container immutable at runtime — drift is impossible.
- Forces explicit declaration of every writable path.

Apps that don't tolerate read-only root usually need writable `/var/cache`, `/var/run`, or `/tmp`. Add a tmpfs for each. Some images (Postgres) need a writable data dir, which is your named volume.

---

## 7. UID/GID, ownership, and the "perm denied" mystery

The most-asked Docker question on Stack Overflow: "I mounted a volume but the container can't write to it." The cause is always UID mismatch.

```
Container UID = 10001 (your image's USER)
Host directory owner = 1000 (your dev user)

Container tries to write → kernel checks owner → not allowed.
```

Three fixes, in order of preference:

1. **Use a named volume** (`-v mydata:/data`). The volume directory is created with the container's UID; ownership is correct by definition.
2. **`chown` the host directory** to match the container's UID. Pre-create with `chown -R 10001:10001 /host/path` before mounting.
3. **Run the container as the host user** via `--user $(id -u):$(id -g)`. The container process runs with your UID; reads/writes succeed. Caveat: the container's `USER` directive is ignored.

SELinux adds a label dimension on top of UID. On RHEL/AL2/AL2023, even with UID alignment, the wrong type label denies access. `:Z` relabels for the container; ` :z` for shared use.

---

## 8. Volumes for ML containers

ML containers have three storage needs distinct from general apps:

1. **Training data** — large (TBs), read-mostly, often shared across many containers/jobs. → mount via NFS (on-prem), EFS (AWS), Filestore (GCP), Azure Files (Azure), or pull from S3/GCS/Blob to local SSD on job start.
2. **Model artifacts** — large (GBs), read-only at serve time, versioned. → either bake into image (only if <500 MB and updates rare) or mount from object store via Mountpoint/gcsfuse/blobfuse2.
3. **Checkpoints / intermediate state** — write-heavy during training, transient. → local SSD + periodic upload to object store. Mount as a named volume backed by host SSD with explicit cleanup.

We will go deep on each in modules 12–15.

---

## 9. The `dockerd` storage driver (the layer driver)

Distinct from volumes is the **storage driver** that manages the **image and container layer overlayfs**. Options:

| Driver | When |
|---|---|
| `overlay2` | Default on every modern Linux. Use this. |
| `aufs` | Old Ubuntu kernels. Replaced by overlay2. |
| `btrfs` / `zfs` | When host root FS is btrfs/zfs; copy-on-write snapshots are nice. |
| `devicemapper` | Removed; used to be default on RHEL. Don't. |
| `vfs` | No copy-on-write, used inside containers (e.g., DinD). Slow. |

You will only touch this if you're chasing a "container start is slow" problem on an old host. On EKS/GKE/AKS the answer is overlay2.

---

## 10. Compose volumes — the project model

Compose v2 (the modern `docker compose` not `docker-compose`) namespaces volumes per project:

```yaml
# compose.yml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
  app:
    image: myorg/myapp:1.0
    volumes:
      - ./src:/app/src:ro      # bind mount: dev source reload
      - cache:/app/.cache

volumes:
  pgdata:
  cache:
```

When you `docker compose up`, Docker creates volumes named `<project>_pgdata` and `<project>_cache`. Down → `docker compose down -v` to remove them.

For production (K8s), the equivalents are PV/PVC declarations. The Compose primitives are clean but the abstraction is host-local.

---

## Sanity check

1. Why is `-v /var/run/docker.sock:/var/run/docker.sock` equivalent to giving the container root on the host?
2. What's the production-grade pattern when a container needs a writable `/tmp` but you want `--read-only` on the root FS?
3. Why does `:Z` matter on RHEL/AL2 but not on Ubuntu?
4. You bind-mount a host directory and the container gets "permission denied." Name three fixes in order of preference.
5. The Dockerfile says `VOLUME /data` and you don't supply `-v`. What happens, and why is this a long-term problem?
6. For an ML training container that needs to read 10 TB of training data, what storage pattern do you reach for first on-prem? On AWS?

---

## Sources

- [Docker volumes](https://docs.docker.com/storage/volumes/)
- [Bind mounts](https://docs.docker.com/storage/bind-mounts/)
- [tmpfs mounts](https://docs.docker.com/storage/tmpfs/)
- [Volume drivers](https://docs.docker.com/storage/volumes/#use-a-volume-driver)
- [SELinux container labels](https://docs.docker.com/storage/bind-mounts/#configure-the-selinux-label)
- [Storage drivers](https://docs.docker.com/storage/storagedriver/)
- [Compose v2 volumes](https://docs.docker.com/compose/compose-file/07-volumes/)

→ Next: [08 — Secrets in Docker — BuildKit secrets, Swarm secrets, runtime patterns](08_docker_secrets.md)
