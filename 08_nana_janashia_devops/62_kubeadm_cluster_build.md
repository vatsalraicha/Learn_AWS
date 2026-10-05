# 62 — Build K8s Cluster from Scratch (kubeadm + containerd + Cilium)

## 1. Why this matters for CKA

Building a cluster from scratch is **the** Cluster Architecture + Install + Configuration exam topic (25% of the exam). You won't build a full cluster on exam day, but you will:
- Initialize a control plane with kubeadm
- Join worker nodes
- Configure CRI (containerd)
- Install a CNI (Cilium / Calico / Flannel)
- Troubleshoot when any step fails

## 2. The provisioning prerequisites

For a 3-node lab (1 control + 2 workers):
- 3 VMs (Ubuntu 24.04, ≥ 2 vCPU, ≥ 2GB RAM)
- Network connectivity between them
- Unique hostnames
- Swap disabled (kubelet requires)
- Kernel modules + sysctls configured

## 3. AWS quick provisioning (3 EC2 instances)

```bash
# Create SG allowing K8s ports
aws ec2 create-security-group --group-name k8s-lab --description "K8s lab"
aws ec2 authorize-security-group-ingress --group-name k8s-lab --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-name k8s-lab --protocol -1 --source-group k8s-lab

# Launch 3 instances
aws ec2 run-instances --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium --count 3 \
  --key-name my-key --security-groups k8s-lab \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=k8s-lab}]'
```

Cost trick: **stop instances when not learning** ($0/hour stopped; only pay for EBS storage ~$3/mo per disk).

## 4. Prepare each node (run on ALL 3)

```bash
# Disable swap permanently
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Load kernel modules
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl for K8s networking
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system
```

## 5. Install containerd (CRI)

```bash
sudo apt update
sudo apt install -y containerd

sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Use systemd cgroup driver (matches kubelet)
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml

sudo systemctl restart containerd
sudo systemctl enable containerd
```

## 6. Install kubeadm + kubelet + kubectl

```bash
# Add Kubernetes apt repo (v1.31 example — match exam version)
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gpg

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
  https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl   # prevent auto-upgrade

# Enable kubelet
sudo systemctl enable kubelet
```

## 7. Initialize control plane (on controlplane01)

```bash
sudo kubeadm init \
  --pod-network-cidr=10.244.0.0/16 \
  --apiserver-advertise-address=<control-plane-ip>
```

Output ends with:
```
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join <ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

Run the user-config commands. Verify:
```bash
kubectl get nodes
# control-plane01   NotReady   control-plane   2m   v1.31.x
# (NotReady is correct — no CNI yet)
```

## 8. Install CNI (Cilium recommended)

```bash
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
curl -L --fail --remote-name-all "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}"
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

cilium install --version 1.16.0
cilium status --wait
```

Alternative: **Calico** (still widely used):
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml
```

Or **Flannel** (simpler, for labs):
```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

After CNI install, node should become Ready:
```bash
kubectl get nodes
# control-plane01   Ready   control-plane   5m   v1.31.x
```

## 9. Join worker nodes

On each worker, run the `kubeadm join` command from step 7. If you lost it:
```bash
# On control plane
kubeadm token create --print-join-command
```

After joining, on control plane:
```bash
kubectl get nodes
# control-plane01   Ready   control-plane   10m   v1.31.x
# worker01          Ready   <none>          1m    v1.31.x
# worker02          Ready   <none>          1m    v1.31.x
```

## 10. Common gotchas

- **Swap not disabled** → kubelet won't start
- **`net.bridge.bridge-nf-call-iptables` not set** → pod networking broken
- **Mismatched containerd cgroup driver** → kubelet errors; both must be `systemd`
- **kubeadm join fails** → token expired (24hr default); regenerate
- **Pods stuck Pending** → no CNI installed yet (Ready won't happen)
- **CoreDNS Pending** → no CNI; install one

## 11. The `kube-system` namespace (what's running)

```bash
kubectl get pods -n kube-system
# coredns-...               2/2 Running
# etcd-controlplane01       1/1 Running
# kube-apiserver-...        1/1 Running
# kube-controller-mgr-...   1/1 Running
# kube-proxy-...            1/1 Running (DaemonSet)
# kube-scheduler-...        1/1 Running
# cilium-...                1/1 Running (DaemonSet)
# cilium-operator-...       1/1 Running
```

These are **static pods** for the control plane (managed by kubelet directly via `/etc/kubernetes/manifests/`) + the CNI pods.

## 12. Networking in K8s — the conceptual model

K8s requires:
1. Every pod gets a unique IP (no NAT between pods)
2. Pods on same node can communicate
3. Pods on different nodes can communicate (no NAT)
4. Pods see themselves at the same IP others see

The CNI plugin implements this. Pod CIDR (`10.244.0.0/16` above) is the address space. Each node gets a /24 from this, allocates /32s to pods.

## 13. Quick self-check

1. Why must swap be disabled before installing kubeadm?
2. What does `kubeadm init` write to `/etc/kubernetes/`?
3. Why does the control-plane node show NotReady right after init?
4. Why must containerd cgroup driver match kubelet?
5. What does the CNI plugin provide that kubeadm doesn't?

(Answers: kubelet refuses to start with swap on because of QoS guarantees + scheduling assumptions; admin.conf (kubeconfig), pki/ (certs), manifests/ (static pod manifests for control plane); no CNI = no pod networking = node not Ready; cgroups inconsistency → kubelet can't manage containers correctly; pod networking — IPAM + routing across nodes — kubeadm doesn't include this.)
