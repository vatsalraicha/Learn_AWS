# 06 — Docker networking: bridge, host, overlay, macvlan, port publishing

> *"`-p 8080:8080` is iptables NAT. Understanding what that actually does explains 80% of 'works on my laptop, doesn't work in prod' bugs."*

## Why this module exists

Docker networking is **iptables and Linux network namespaces with helpful defaults**. When you understand the defaults, you understand the production failure modes. This module covers the five network drivers, the port-publishing model (and its surprising defaults), and the DNS resolver that makes service-by-name discovery work.

Cross-references: Linux NET namespaces (module 1), bridge/host trade-offs (module 10), K8s networking which is a different model entirely (module 18).

---

## 1. The five network drivers

Docker ships five built-in drivers. The first three handle 99% of cases.

| Driver | Scope | When to use |
|---|---|---|
| **bridge** | Single host | The default. Containers on a user-defined bridge see each other; isolated from host |
| **host** | Single host | Container shares host's network namespace — no isolation, full performance |
| **none** | Single host | No networking at all; for batch jobs that talk only to mounted volumes |
| **overlay** | Multi-host (Swarm) | Cross-host container-to-container via VXLAN; uses Swarm clustering |
| **macvlan** | Single host (with layer-2 connectivity to physical net) | Container gets its own MAC + IP on physical network; for legacy apps expecting "real" IPs |
| **ipvlan** | Single host | Layer-2 or layer-3 mode; lower overhead than macvlan |

### 1.1 Bridge networking

The Docker daemon creates `docker0`, a Linux bridge interface, on host startup. Each container gets a veth pair: one end inside the container's NET namespace (named `eth0`), the other end attached to `docker0`. Routes between `docker0` and the host's physical interface go through iptables NAT.

```
Host
├── eth0  (e.g. 192.0.2.10)
├── docker0 (172.17.0.1)  ← Linux bridge
│   ├── vethXXX ↔ container A eth0 (172.17.0.2)
│   └── vethYYY ↔ container B eth0 (172.17.0.3)
```

#### 1.1.1 Default bridge vs user-defined bridge

The `docker0` default bridge has historical baggage:
- **No built-in DNS resolution between containers** — you can only reach others by IP.
- **All containers on it can talk to each other** (no isolation).
- **Container names are not resolvable**.

User-defined bridges (created with `docker network create mynet`) fix all three:
- **Embedded DNS** resolves container names to IPs.
- **Per-network isolation**: containers only see others on the same user-defined network.
- **Can be deleted independently**.

**Rule: never use the default bridge in production.** Always `docker network create` or use Compose, which creates one per project automatically.

#### 1.1.2 Internal vs external bridges

```bash
docker network create --internal db-net
```

`--internal` networks have **no route to the outside**. Useful for databases or message queues that should only be reachable from siblings — even if a container on `db-net` had `CAP_NET_RAW`, it can't egress. Sibling containers can be on both `db-net` and a regular bridge if they need both intra-cluster + external access.

---

## 2. Port publishing (`-p`) — what really happens

`docker run -p 8080:80 nginx` is the canonical command. Under the hood:

1. Docker reserves host port 8080 (and fails with "port already allocated" if taken).
2. Docker adds an iptables NAT rule: `DNAT --to-destination 172.17.0.2:80` on incoming packets to `<host>:8080`.
3. The kernel rewrites destination addresses on inbound packets; the container responds; iptables SNATs the return traffic.

Three surprising defaults that bite everyone:

### 2.1 Default bind is ALL interfaces

`-p 8080:80` is shorthand for `-p 0.0.0.0:8080:80`. The container is reachable from any IP that can route to the host — including the public internet if the host has a public IP. This is why you find Mongo/Redis/etcd instances on Shodan: developers ran `-p 6379:6379` on a server with a public IP and a permissive firewall.

**The fix**: bind to a specific host IP.

```bash
docker run -p 127.0.0.1:8080:80 nginx       # localhost only
docker run -p 10.0.1.5:8080:80 nginx        # specific interface
```

For ML model servers in dev, **always** `127.0.0.1:`. For prod, the firewall/security-group is usually the last line — but binding to `127.0.0.1` (with a reverse proxy in front) is defense in depth.

### 2.2 iptables vs UFW conflict

Docker writes its own iptables rules in the `DOCKER` and `DOCKER-USER` chains, **bypassing UFW**. A `ufw deny 8080/tcp` rule does **nothing** to a port published by Docker — the packet matches DOCKER chain before INPUT. The fix:

```bash
# /etc/docker/daemon.json
{
  "iptables": true,
  "ip-forward": true
}

# DOCKER-USER chain (Docker adds DOCKER, you add DOCKER-USER, your rules win)
iptables -I DOCKER-USER -i eth0 ! -s 10.0.0.0/8 -j DROP
```

This is a frequent root cause of "my server is somehow accessible from the internet even though I have a firewall."

### 2.3 `EXPOSE` does NOT publish

`EXPOSE 8080` in the Dockerfile is documentation. The port is **not** reachable from outside the container unless you also pass `-p` (or use `--publish-all` which publishes all EXPOSEd ports to random host ports).

---

## 3. Host networking — when isolation isn't worth it

```bash
docker run --network host nginx
```

The container shares the host's NET namespace. **No port publishing**, no NAT, no overlay. The container can:

- Bind to any host port directly.
- See all host network interfaces.
- Sniff host traffic with `tcpdump` (if it has `CAP_NET_RAW`).
- See `/proc/net` of the host.

When to use:

- Maximum network performance (DPDK, high-frequency trading, large `tcp_window` workloads).
- Tools that need to inspect host network state (Falco, monitoring agents).
- Workloads that need raw socket access without iptables NAT overhead.

When **not** to use: any production multi-tenant context. Host networking is a privilege escalation. Capital One–style postures forbid `network_mode: host` outside of allow-listed monitoring DaemonSets.

In Kubernetes, the equivalent is `hostNetwork: true` — PSA `restricted` policy forbids it for the same reason.

---

## 4. Overlay networks (Swarm)

Docker Swarm's overlay driver lets containers on different hosts talk over an encrypted VXLAN tunnel. Swarm is mostly dead — Kubernetes won. But if you encounter a Swarm cluster:

- VXLAN encapsulates Ethernet frames in UDP (port 4789).
- Control plane uses TLS-mTLS via Swarm's built-in PKI.
- IPSec encryption available with `--opt encrypted=true`.

For multi-host container networking outside Swarm: use Kubernetes (module 18) or Nomad with its CNI.

---

## 5. Macvlan & ipvlan — when containers need "real" IPs

Some legacy apps expect to be on a Layer-2 network, with a unique MAC and an IP routable from the upstream switch. Macvlan creates a virtual NIC per container that the host's physical NIC presents to the switch.

```bash
docker network create -d macvlan \
  --subnet=192.0.2.0/24 \
  --gateway=192.0.2.1 \
  -o parent=eth0 \
  mvlan
docker run --network mvlan --ip 192.0.2.50 my-legacy-app
```

The container at `192.0.2.50` is **directly addressable from the upstream switch** — no NAT.

Gotchas:
- The host itself **cannot** reach its own macvlan containers via the macvlan interface (kernel limitation). You either reach them from another host or attach the host to its own macvlan network.
- Many cloud VMs disable promiscuous mode and break macvlan (AWS, GCP, Azure security groups assume one MAC per ENI).

**Macvlan is on-prem-only in practice.** Cloud networking forces NAT/overlay patterns.

---

## 6. Container DNS

User-defined bridge networks include an **embedded DNS resolver** at `127.0.0.11`. Inside the container, `/etc/resolv.conf` is set to `127.0.0.11`. The resolver:

1. Resolves other container names on the same network to their internal IPs.
2. Falls back to the host's resolvers for everything else (Google DNS / corporate DNS / cloud DNS).

This is how `db:5432` works inside Compose without any host-name configuration — the embedded resolver returns the db container's IP.

In K8s the equivalent is **CoreDNS** running as a deployment with a Service IP; pods get `/etc/resolv.conf` pointed at the cluster DNS service. The model is identical in spirit.

---

## 7. Container ↔ host: "host.docker.internal"

A container talking to the host (e.g., a process on the host's `localhost:5432`) is awkward. From inside the container, `127.0.0.1` is the container itself, not the host.

Docker Desktop (Mac/Win/WSL) provides the magic DNS name `host.docker.internal` that resolves to the host's gateway IP. On Linux, you must add `--add-host=host.docker.internal:host-gateway`:

```bash
docker run --add-host=host.docker.internal:host-gateway myapp
```

In K8s this pattern is uncommon — pods talk to services, not to the host. If you do need it, use `hostNetwork: true` (with caveats) or expose a host-port Service.

---

## 8. Network anti-patterns (you will see these)

| Anti-pattern | What's wrong | Fix |
|---|---|---|
| `docker run -p 6379:6379 redis` on a public-IP server | Public Redis on the internet | `127.0.0.1:6379:6379` + reverse proxy with auth |
| `network_mode: host` for everything | No isolation | Use a user-defined bridge |
| `EXPOSE` as a firewall | It's not a firewall, it's documentation | Real firewall + minimal `-p` |
| UFW rule that "blocks" a Docker port | Docker bypasses UFW INPUT chain | Use `DOCKER-USER` chain |
| Containers on default `bridge` | No DNS, no isolation | User-defined bridge |
| `--network host` to debug DNS issues | Hides the actual problem | Run a debug sidecar (`nicolaka/netshoot`) on the same user-defined network |
| `iptables -P FORWARD DROP` | Breaks all container egress | Use DOCKER-USER chain rules |

---

## 9. The egress side — outbound traffic from containers

A container's outbound traffic goes:

```
container eth0 → veth → docker0 → host iptables MASQUERADE → host eth0 → upstream
```

Three layers can block egress:

1. **Network policy at the container layer**: Docker doesn't have a built-in egress policy. Tools like **Cilium-on-Docker** (rare) or just iptables rules in DOCKER-USER do it.
2. **Host firewall**: `iptables -A DOCKER-USER -d 169.254.169.254 -j DROP` blocks the EC2/GCP/Azure IMDS endpoint from all containers — this is **the Capital One 2019 lesson encoded as one iptables rule**.
3. **Cloud security groups / NSG**: outside the host, the VPC firewall.

In K8s the layer-1 control is **NetworkPolicy** (module 18). The IMDS block is implemented at the **VPC CNI level** by setting hop-limit=1 on IMDSv2 (module 26).

---

## 10. The Capital One 2019 incident in network terms

Re-tell the breach with networking glasses on:

1. A misconfigured WAF in Capital One's web tier had an **SSRF vulnerability**: it accepted user-supplied URLs and fetched them server-side.
2. An attacker pointed the SSRF at `http://169.254.169.254/latest/meta-data/iam/security-credentials/` — the EC2 **IMDSv1** endpoint.
3. IMDSv1 returned a 200 with temporary AWS credentials of the IAM role attached to the WAF instance.
4. The IAM role had `s3:ListAllMyBuckets` and overly broad `s3:GetObject` — the attacker pulled 106M records.

The fix at multiple layers:

- **App layer**: prevent SSRF.
- **Network layer (the new lesson)**: block `169.254.169.254` from any process that doesn't need it. For containers, the standard pattern is `iptables -A DOCKER-USER -d 169.254.169.254/32 -j DROP` on the host, OR use **IMDSv2 only** (`MetadataHttpEndpoint=enabled,MetadataHttpTokens=required, MetadataHttpPutResponseHopLimit=1`). The hop-limit=1 means a container's request to IMDS — which has TTL decremented to 0 in the veth — fails. IMDSv2-only is the modern AWS default.
- **IAM layer**: tight role permissions + permission boundaries.

For containerized ML workloads on AWS, the canonical hardening is:

```hcl
# Terraform — IMDSv2 only, hop limit 1
resource "aws_instance" "worker" {
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"     # IMDSv2 token required
    http_put_response_hop_limit = 1              # blocks containers
  }
  # ...
}
```

This single block would have prevented the Capital One breach pattern from the container side. We will reinforce this in module 13 (Data exposure — AWS).

---

## Sanity check

1. What does `-p 8080:80` actually do at the iptables level, and why does that bypass UFW?
2. What does `docker0` resolve to, and why is the default bridge unsuitable for production?
3. Container A on user-defined network `app-net`, container B on `db-net`. Can A reach B by name? By IP?
4. Why does `--network host` make a container a security risk equivalent to running on the host directly?
5. From inside a Linux Docker container without Docker Desktop, how do you reach a service on the host's `localhost`?
6. What iptables rule (or AWS instance setting) would have prevented the Capital One 2019 IMDS pivot from a containerized workload?

---

## Sources

- [Docker network drivers](https://docs.docker.com/network/)
- [User-defined bridge networks](https://docs.docker.com/network/bridge/)
- [DOCKER-USER chain & iptables integration](https://docs.docker.com/network/iptables/)
- [Macvlan networks](https://docs.docker.com/network/macvlan/)
- [AWS IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- [Capital One 2019 breach case study (OCC consent order)](https://www.occ.treas.gov/news-issuances/news-releases/2020/nr-occ-2020-101a.pdf)
- [`netshoot` debug image](https://github.com/nicolaka/netshoot)

→ Next: [07 — Docker storage — bind mounts, volumes, tmpfs, volume drivers](07_docker_storage.md)
