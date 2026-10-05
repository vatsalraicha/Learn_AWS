# 78 — Certificate Management + Renewal

## 1. The K8s PKI

K8s uses PKI everywhere:

```
/etc/kubernetes/pki/
├── ca.crt + ca.key                 # cluster root CA
├── apiserver.crt + apiserver.key
├── apiserver-kubelet-client.crt + .key
├── front-proxy-ca.crt + .key
├── front-proxy-client.crt + .key
├── sa.key + sa.pub                 # ServiceAccount signing
└── etcd/
    ├── ca.crt + ca.key
    ├── server.crt + .key
    ├── peer.crt + .key
    └── healthcheck-client.crt + .key
```

Plus per-kubelet certs in `/var/lib/kubelet/pki/`.

## 2. Default cert expiry

- **kubeadm-generated certs**: 1 year (365 days)
- **Cluster CA**: 10 years (rebuilt rarely)
- **kubelet client cert**: auto-rotated by default

Year-old self-managed clusters: this is the #1 cause of "cluster suddenly broken" — certs expired.

## 3. Checking certificate expiration

```bash
sudo kubeadm certs check-expiration

CERTIFICATE                EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
admin.conf                 Mar 15, 2026 12:34 UTC   285d            no
apiserver                  Mar 15, 2026 12:34 UTC   285d            no
apiserver-kubelet-client   Mar 15, 2026 12:34 UTC   285d            no
controller-manager.conf    Mar 15, 2026 12:34 UTC   285d            no
etcd-healthcheck-client    Mar 15, 2026 12:34 UTC   285d            no
etcd-peer                  Mar 15, 2026 12:34 UTC   285d            no
etcd-server                Mar 15, 2026 12:34 UTC   285d            no
front-proxy-client         Mar 15, 2026 12:34 UTC   285d            no
scheduler.conf             Mar 15, 2026 12:34 UTC   285d            no

CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
ca                      Jul 14, 2034 12:34 UTC   3000d           no
etcd-ca                 Jul 14, 2034 12:34 UTC   3000d           no
front-proxy-ca          Jul 14, 2034 12:34 UTC   3000d           no
```

## 4. Manual cert renewal

```bash
# Renew all certs (apiserver, kubelet-client, controller-mgr, scheduler, etcd, etc.)
sudo kubeadm certs renew all

# Or specific cert
sudo kubeadm certs renew apiserver
sudo kubeadm certs renew kubelet-client
sudo kubeadm certs renew etcd-server

# Verify
sudo kubeadm certs check-expiration
```

After renewal, **restart control plane components** (they don't pick up new certs automatically):

```bash
# Restart by moving + restoring static pod manifests (kubelet detects + restarts)
sudo mv /etc/kubernetes/manifests/*.yaml /tmp/
sleep 15
sudo mv /tmp/*.yaml /etc/kubernetes/manifests/
```

Or restart kubelet itself which restarts static pods:
```bash
sudo systemctl restart kubelet
```

## 5. Inspecting a cert manually

```bash
# What's in the file
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -text -noout

# Just expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate

# Decode the kubeconfig admin cert
k config view --raw -o jsonpath='{.users[?(@.name=="kubernetes-admin")].user.client-certificate-data}' | \
  base64 -d | openssl x509 -text -noout | grep -E "Not Before|Not After|Subject:"
```

## 6. kubelet client cert auto-rotation

The kubelet client cert (for kubelet → apiserver) auto-rotates **if** these flags are set on kubelet:
- `--rotate-certificates=true`
- `--rotate-server-certificates=true` (for kubelet's server cert)

Check on a node:
```bash
sudo grep -E "rotate" /var/lib/kubelet/config.yaml
# rotateCertificates: true
# serverTLSBootstrap: true
```

kubeadm enables these by default since v1.17. Older clusters may not have them.

When a rotation happens, kubelet:
1. Generates a new key
2. Submits a CSR
3. Controller approves (if signer is configured for auto-approval) or you manually approve
4. Picks up the new cert

## 7. Manually approving kubelet CSRs

```bash
# Pending CSRs
k get csr

# Approve
k certificate approve <csr-name>

# Deny
k certificate deny <csr-name>
```

## 8. cert-manager — for application-level certs

Different from K8s internal PKI: **cert-manager** issues TLS certs for your Ingress endpoints.

```bash
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true
```

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-prod }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef: { name: letsencrypt-prod }
    solvers:
    - http01: { ingress: { ingressClassName: nginx } }
```

```yaml
# Ingress requests a cert via annotation
metadata:
  annotations: { cert-manager.io/cluster-issuer: letsencrypt-prod }
spec:
  tls:
  - hosts: [app.example.com]
    secretName: app-tls
```

cert-manager talks to Let's Encrypt, gets a cert, stores in a K8s Secret. Renews automatically.

## 9. The CKA exam — certificate tasks

Typical task:
> "The apiserver-kubelet-client certificate expires in 30 days. Renew it. Verify the new cert is in use."

```bash
sudo kubeadm certs check-expiration | grep apiserver-kubelet-client
sudo kubeadm certs renew apiserver-kubelet-client
# Restart static pods (move manifests)
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /tmp/
sleep 15
sudo mv /tmp/kube-apiserver.yaml /etc/kubernetes/manifests/
# Verify
sudo kubeadm certs check-expiration | grep apiserver-kubelet-client
```

## 10. EKS / GKE / AKS — managed certs

EKS:
- Cluster control plane certs: AWS manages
- Cluster CA: AWS manages
- kubelet client cert: auto-rotated (or AWS-managed for new nodes)
- Anything else (workload TLS): cert-manager

You almost never touch EKS internal certs. The CKA still tests it because the exam is on kubeadm clusters.

## 11. Common cert-related cluster failures

| Symptom | Likely cause |
|---|---|
| `Unable to connect to the server: x509: certificate has expired` | API server cert expired |
| `Unable to authenticate the request due to an error: invalid bearer token` | SA token signing cert issue |
| kubelet logs `failed to renew bootstrap certificate` | CSR approval not happening; check controller-manager |
| etcd peers can't talk: `tls: bad certificate` | etcd peer certs expired |
| Webhook calls fail: `x509: certificate has expired` | webhook cert (e.g., from cert-manager) expired |

## 12. Quick self-check

1. What's the default expiration for kubeadm-generated certs?
2. What command checks all K8s cert expirations?
3. After renewing certs, why do you need to restart control plane components?
4. What's the difference between kubeadm-managed certs and cert-manager?
5. Why does the kubelet client cert auto-rotate by default in modern clusters?

(Answers: 1 year (365 days); `sudo kubeadm certs check-expiration`; static pods cache the old cert in memory — moving the manifest forces kubelet to restart them with the new cert; kubeadm manages K8s internal PKI (apiserver, kubelet, etcd, etc.), cert-manager manages TLS for application Ingresses; flags `--rotate-certificates=true` enable kubelet to submit CSRs and pick up new cert before old one expires — kubeadm sets this by default since v1.17.)
