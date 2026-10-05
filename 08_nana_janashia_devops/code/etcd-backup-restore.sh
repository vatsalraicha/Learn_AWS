#!/usr/bin/env bash
# etcd-backup-restore.sh — Reference for CKA exam (and production cron)
# Pairs with Module 74 (etcd backup/restore)

set -euo pipefail

ETCDCTL_API=3
export ETCDCTL_API

CACERT=/etc/kubernetes/pki/etcd/ca.crt
CERT=/etc/kubernetes/pki/etcd/server.crt
KEY=/etc/kubernetes/pki/etcd/server.key
ENDPOINT=https://127.0.0.1:2379

backup() {
  local OUT="${1:-/tmp/etcd-backup-$(date +%F-%H%M).db}"
  echo "==> Backing up etcd to $OUT"
  sudo etcdctl \
    --endpoints="$ENDPOINT" \
    --cacert="$CACERT" \
    --cert="$CERT" \
    --key="$KEY" \
    snapshot save "$OUT"

  echo "==> Verifying snapshot"
  sudo etcdctl --write-out=table snapshot status "$OUT"
  echo "==> Done."
}

restore() {
  local SNAP="${1:-}"
  local DATA_DIR="${2:-/var/lib/etcd-restored}"
  if [ -z "$SNAP" ]; then
    echo "Usage: $0 restore <snapshot.db> [data-dir]"
    exit 1
  fi

  echo "==> Stopping kube-apiserver + etcd by moving static manifests"
  sudo mkdir -p /etc/kubernetes/manifests-bak
  sudo mv /etc/kubernetes/manifests/etcd.yaml /etc/kubernetes/manifests-bak/
  sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /etc/kubernetes/manifests-bak/
  sleep 30
  echo "Waiting for apiserver + etcd containers to stop..."
  sudo crictl ps | grep -E 'etcd|apiserver' || echo "  (gone — good)"

  echo "==> Restoring snapshot to $DATA_DIR"
  sudo etcdctl snapshot restore "$SNAP" --data-dir="$DATA_DIR"

  echo "==> Updating /etc/kubernetes/manifests-bak/etcd.yaml to use new data dir"
  sudo sed -i "s|--data-dir=/var/lib/etcd|--data-dir=$DATA_DIR|" \
    /etc/kubernetes/manifests-bak/etcd.yaml
  sudo sed -i "s|path: /var/lib/etcd|path: $DATA_DIR|" \
    /etc/kubernetes/manifests-bak/etcd.yaml

  echo "==> Restoring manifests"
  sudo mv /etc/kubernetes/manifests-bak/etcd.yaml /etc/kubernetes/manifests/
  sudo mv /etc/kubernetes/manifests-bak/kube-apiserver.yaml /etc/kubernetes/manifests/

  echo "==> Waiting for control plane to come back up..."
  sleep 60
  for i in {1..30}; do
    if kubectl get nodes &>/dev/null; then
      echo "==> Control plane up"
      kubectl get nodes
      return
    fi
    echo "  ... still waiting ($i/30)"
    sleep 5
  done
  echo "ERROR: Control plane did not come up within 150s"
  exit 1
}

s3_backup() {
  local BUCKET="${1:?usage: $0 s3-backup <bucket>}"
  local TS=$(date +%F-%H%M)
  local TMP="/tmp/etcd-snap-$TS.db"
  backup "$TMP"
  aws s3 cp "$TMP" "s3://$BUCKET/etcd-backups/$TS.db" --sse aws:kms
  rm "$TMP"
}

case "${1:-}" in
  backup)    shift; backup "${1:-}" ;;
  restore)   shift; restore "$@" ;;
  s3-backup) shift; s3_backup "${1:-}" ;;
  *)
    echo "Usage: $0 {backup [out-file] | restore <snap> [data-dir] | s3-backup <bucket>}"
    exit 1
    ;;
esac
