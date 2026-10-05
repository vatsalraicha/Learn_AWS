# 66 — Troubleshooting Applications (30% of CKA Exam)

## 1. The troubleshooting tier — top to bottom

When a pod isn't working:
```
1. Pod status (Pending? CrashLoopBackOff? ImagePullBackOff?)
2. Pod events (kubectl describe)
3. Pod logs (kubectl logs, --previous)
4. Service / endpoints (label match?)
5. NetworkPolicy (blocking traffic?)
6. DNS (CoreDNS healthy?)
7. Node (cordoned? out of resources?)
8. Control plane components (kube-system pods running?)
9. CNI (pods getting IPs?)
```

## 2. Pod statuses

| Status | Means |
|---|---|
| **Pending** | Not scheduled yet (no matching node, taint, resources unavailable) |
| **Running** | Scheduled + container started |
| **Succeeded** | All containers exited 0 |
| **Failed** | All containers exited non-zero |
| **Unknown** | Node communication lost |
| **CrashLoopBackOff** | Container keeps crashing; restart-backed-off |
| **ImagePullBackOff** | Can't pull image |
| **ErrImagePull** | Image pull error |
| **ContainerCreating** | Starting; usually < 30s; if longer = volume / image / network issue |

## 3. The diagnostic workflow

```bash
# Pod-level diagnosis
k get pods                              # see status
k describe pod <name>                   # events at bottom!
k logs <name>                           # current logs
k logs <name> --previous                # logs from previous (crashed) container
k logs <name> -c <container>            # specific container
k logs <name> -f --tail=100             # follow last 100

# Node-level
k get nodes                             # Ready?
k describe node <name>                  # conditions + capacity + taints
k top nodes                             # resource usage (needs metrics-server)
k top pods -A

# Cluster-level
k get componentstatuses                 # legacy but useful
k get events --sort-by=.lastTimestamp -A
k get all -A                            # everything
```

## 4. Pod stuck in Pending

```bash
k describe pod <name>
# Events:
#   FailedScheduling: 0/3 nodes are available: 3 Insufficient cpu
# OR
#   FailedScheduling: 0/3 nodes are available: 3 node(s) had untolerated taint
```

Causes:
- **Insufficient resources** — bump resources.requests down, or add nodes
- **Untolerated taint** — pod doesn't tolerate node taint
- **No node matches nodeSelector** — wrong label
- **PVC unbound** — no matching PV

## 5. Pod stuck in ImagePullBackOff

```bash
k describe pod <name>
# Events:
#   Failed to pull image "myimage:bad": rpc error
#   Failed to pull image "myimage:bad": ErrImagePull
```

Causes:
- Image doesn't exist (typo, never pushed)
- Private registry without imagePullSecrets
- Wrong tag
- Network issue from node to registry
- Image is for wrong architecture (arm64 image on amd64 node)

Fix:
```bash
# For private registry
k create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user --docker-password=pass

# Reference in pod spec
spec:
  imagePullSecrets:
  - name: regcred
  containers: [...]
```

## 6. Pod stuck in CrashLoopBackOff

```bash
k logs <name> --previous
# Shows logs from the crashed container
```

Causes:
- Application error on startup (env var missing, can't connect to DB)
- Wrong command/args
- Missing config / secrets mount
- OOMKilled (exit 137)
- Health check killed it before ready

Check resource events:
```bash
k describe pod <name> | grep -A 5 "Last State"
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
```

OOM means memory limit too low or memory leak.

## 7. Service has no endpoints

```bash
k get endpoints <svc>
# NAME    ENDPOINTS    AGE
# my-svc  <none>       5m         ← no endpoints!
```

Causes:
- Service selector doesn't match any pod labels
- Pods are not Ready (failing readiness probe)
- Pods are in a different namespace

```bash
k get pods --show-labels                          # what labels do pods have?
k get svc my-svc -o jsonpath='{.spec.selector}'   # what does svc select?
```

## 8. DNS not resolving

```bash
# In a debug pod
k run debug --rm -it --image=alpine -- sh
apk add bind-tools
nslookup kubernetes.default
nslookup my-svc.my-app
nslookup my-svc.my-app.svc.cluster.local
```

If resolution fails:
- CoreDNS pods in kube-system not running?
- CoreDNS ConfigMap broken?
- NetworkPolicy blocking DNS traffic?

```bash
k get pods -n kube-system -l k8s-app=kube-dns
k logs -n kube-system -l k8s-app=kube-dns
k get configmap coredns -n kube-system -o yaml
```

## 9. Debugging with temporary pods

The exam's go-to:
```bash
# Network debugging
k run debug --rm -it --image=nicolaka/netshoot -- bash

# Inside:
curl -v http://my-svc:80
nslookup my-svc.my-app
nc -zv my-svc 80
traceroute my-svc

# Single-shot
k run curl --rm -it --image=curlimages/curl -- curl -v http://my-svc

# Test from a specific node
k run debug --rm -it --image=alpine \
  --overrides='{"spec":{"nodeName":"worker01"}}' -- sh
```

## 10. `kubectl debug` (newer; ephemeral containers)

```bash
# Attach ephemeral debug container to running pod
k debug -it <pod-name> --image=nicolaka/netshoot --target=<container-name>

# Copy a pod with image swap (debug crash-looping pod with shell-based image)
k debug <pod-name> -it --image=alpine --copy-to=debug-pod --share-processes
```

This avoids "I need to debug this prod pod but can't `exec` into a crashed container."

## 11. `kubectl` format output

```bash
k get pod my-pod -o yaml
k get pod my-pod -o json
k get pod my-pod -o jsonpath='{.status.phase}'
k get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
k get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName
k get pods --sort-by=.metadata.creationTimestamp
k get pods --selector=app=web -o name | xargs -I{} kubectl logs {}
```

For exam: practice jsonpath + custom-columns. Faster than `-o yaml | grep`.

## 12. Kubelet + kubectl issues

### Kubelet not starting (on a node)
```bash
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 100
# Common causes:
# - swap not disabled
# - CRI not running (containerd down?)
# - Wrong cgroup driver mismatch
# - Cert expired (kubelet client cert)
```

### kubectl can't connect
```bash
kubectl cluster-info dump | head
# Check:
# - $KUBECONFIG env var?
# - ~/.kube/config exists + has correct cluster endpoint?
# - API server cert expired?
# - API server pod healthy?

k get pods -n kube-system | grep apiserver
ssh control-plane "sudo crictl ps | grep apiserver"
```

### API server not running
```bash
ssh control-plane
ls /etc/kubernetes/manifests/
# kube-apiserver.yaml should be there; if you accidentally moved it, the static pod stopped
# Restore + kubelet will start it again within seconds
```

## 13. Quick self-check

1. What's the difference between `k logs` and `k logs --previous`?
2. What does exit code 137 mean?
3. Why might `k get endpoints my-svc` return `<none>`?
4. What's `kubectl debug` used for?
5. Where do static control plane pod manifests live?

(Answers: --previous shows logs from the container before the current restart (the crashed one); OOMKilled — process was killed by Linux OOM killer (memory limit exceeded); selector doesn't match any pod's labels, or pods aren't Ready (failing readiness probe); attaching ephemeral debug containers or making a copy of a pod with image swap — for debugging crash-looping pods you can't exec into; /etc/kubernetes/manifests/ on control plane nodes — kubelet watches this directory.)
