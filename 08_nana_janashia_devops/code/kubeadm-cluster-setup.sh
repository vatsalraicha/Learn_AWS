#!/usr/bin/env bash
# kubeadm-cluster-setup.sh — script for setting up a K8s cluster from scratch
# Pairs with Module 62 (kubeadm cluster build)
#
# Usage:
#   Run on ALL nodes (control plane + workers):
#     sudo ./kubeadm-cluster-setup.sh prepare
#   Run on the CONTROL PLANE only:
#     sudo ./kubeadm-cluster-setup.sh init <api-server-ip>
#   On WORKERS, paste the kubeadm join command from init output.

set -euo pipefail

K8S_VERSION="${K8S_VERSION:-1.31.3-1.1}"
POD_CIDR="${POD_CIDR:-10.244.0.0/16}"

prepare() {
  echo "==> Disabling swap"
  swapoff -a
  sed -i '/ swap / s/^/#/' /etc/fstab

  echo "==> Loading kernel modules"
  cat > /etc/modules-load.d/k8s.conf <<EOF
overlay
br_netfilter
EOF
  modprobe overlay
  modprobe br_netfilter

  echo "==> Sysctl for K8s networking"
  cat > /etc/sysctl.d/k8s.conf <<EOF
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
  sysctl --system

  echo "==> Installing containerd"
  apt update
  apt install -y containerd
  mkdir -p /etc/containerd
  containerd config default | tee /etc/containerd/config.toml > /dev/null
  sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
  systemctl restart containerd
  systemctl enable containerd

  echo "==> Installing kubeadm/kubelet/kubectl"
  apt install -y apt-transport-https ca-certificates curl gpg
  K8S_MINOR=$(echo "$K8S_VERSION" | grep -oE '^[0-9]+\.[0-9]+')

  curl -fsSL "https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR}/deb/Release.key" | \
    gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

  echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v${K8S_MINOR}/deb/ /" | \
    tee /etc/apt/sources.list.d/kubernetes.list

  apt update
  apt install -y "kubelet=${K8S_VERSION}" "kubeadm=${K8S_VERSION}" "kubectl=${K8S_VERSION}"
  apt-mark hold kubelet kubeadm kubectl
  systemctl enable kubelet

  echo "==> Done. Node prepared."
}

init() {
  local IP="${1:-}"
  if [ -z "$IP" ]; then
    echo "Usage: $0 init <api-server-ip>"
    exit 1
  fi

  echo "==> Running kubeadm init"
  kubeadm init \
    --pod-network-cidr="$POD_CIDR" \
    --apiserver-advertise-address="$IP"

  # Configure kubectl for non-root user
  local USER_TO_CONFIGURE="${SUDO_USER:-ubuntu}"
  mkdir -p /home/$USER_TO_CONFIGURE/.kube
  cp /etc/kubernetes/admin.conf /home/$USER_TO_CONFIGURE/.kube/config
  chown -R $USER_TO_CONFIGURE:$USER_TO_CONFIGURE /home/$USER_TO_CONFIGURE/.kube

  echo "==> Installing Cilium CNI"
  CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
  curl -L --fail --remote-name "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz"
  tar xzvf cilium-linux-amd64.tar.gz -C /usr/local/bin
  rm cilium-linux-amd64.tar.gz

  sudo -u $USER_TO_CONFIGURE bash -c "
    export KUBECONFIG=/home/$USER_TO_CONFIGURE/.kube/config
    cilium install --version 1.16.0
    cilium status --wait
  "

  echo "==> Cluster initialized. Join command:"
  kubeadm token create --print-join-command
}

case "${1:-}" in
  prepare) prepare ;;
  init)    shift; init "$@" ;;
  *)
    echo "Usage: $0 {prepare|init <ip>}"
    exit 1
    ;;
esac
