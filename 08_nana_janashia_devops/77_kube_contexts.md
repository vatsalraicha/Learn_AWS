# 77 — Kube Contexts (Multi-Cluster)

## 1. The kubeconfig file

`~/.kube/config` (or `$KUBECONFIG` if set). Three top-level sections:

```yaml
apiVersion: v1
kind: Config

clusters:
- name: prod
  cluster:
    server: https://prod.example.com:6443
    certificate-authority: /home/vatsal/.kube/prod-ca.crt
- name: dev
  cluster:
    server: https://dev.example.com:6443
    insecure-skip-tls-verify: true

users:
- name: alice
  user:
    client-certificate: /home/vatsal/.kube/alice.crt
    client-key: /home/vatsal/.kube/alice.key
- name: bob
  user:
    token: eyJhbGciOiJSUzI1NiIs...

contexts:
- name: prod-as-alice
  context:
    cluster: prod
    user: alice
    namespace: my-app
- name: dev-as-bob
  context:
    cluster: dev
    user: bob
    namespace: testing

current-context: prod-as-alice
```

A **context** binds (cluster, user, namespace) into a name.

## 2. The kubectl config commands

```bash
# View
k config view                                 # full config
k config view --minify                        # just current
k config view --minify -o jsonpath='{.contexts[0].context.namespace}'

# Contexts
k config get-contexts                         # list all
k config current-context                      # show active
k config use-context dev-as-bob               # switch

# Add a cluster
k config set-cluster prod \
  --server=https://prod:6443 \
  --certificate-authority=/path/ca.crt

# Add a user (cert-based)
k config set-credentials alice \
  --client-certificate=/path/alice.crt \
  --client-key=/path/alice.key

# Add a user (token-based)
k config set-credentials bob --token=<jwt>

# Add a context
k config set-context prod-as-alice \
  --cluster=prod --user=alice --namespace=my-app

# Set namespace in current context
k config set-context --current --namespace=my-app

# Delete things
k config delete-context dev-as-bob
k config delete-cluster dev
k config unset users.bob
```

## 3. Multiple kubeconfig files

```bash
export KUBECONFIG=~/.kube/config:~/.kube/eks-prod.yaml:~/.kube/eks-dev.yaml
k config get-contexts             # merges all 3 files
```

Merging is in-memory; doesn't write. Use this when you have separate config files from different sources.

## 4. Helper tools

### kubectx + kubens
The killer multi-cluster productivity tools (https://github.com/ahmetb/kubectx):

```bash
brew install kubectx              # installs kubectx + kubens

kubectx                           # list contexts
kubectx dev-as-bob                # switch
kubectx -                         # switch to previous

kubens                            # list namespaces
kubens my-app                     # set current namespace
kubens -                          # previous
```

### k9s
TUI for cluster management — `brew install k9s`. Visual replacement for many kubectl commands.

### kubie
Like kubectx but spawns a subshell per context — prevents accidental context drift.

## 5. Multi-context workflow patterns

### Pattern 1: one context per cluster, switch via kubectx
```bash
kubectx prod        # work in prod
kubectx staging     # switch to staging
```

Risk: accidental prod ops. Mitigate with shell prompt showing current context.

### Pattern 2: one terminal per cluster
```bash
# Terminal 1
export KUBECONFIG=~/.kube/prod.yaml

# Terminal 2
export KUBECONFIG=~/.kube/staging.yaml
```

Less ambiguous.

### Pattern 3: kubie (subshell per context)
```bash
kubie ctx prod          # opens a subshell with prod context
# work, then exit
```

## 6. Shell prompt that shows context

Add to `~/.bashrc` or `~/.zshrc`:
```bash
function kctx() {
  k config current-context 2>/dev/null
}
PS1='[$(kctx)] \w \$ '

# Or for zsh:
PROMPT='[$(kctx)] %~ %# '
```

Or use **starship** prompt with the `kubernetes` module:
```toml
[kubernetes]
disabled = false
detect_files = ['k8s.yaml']
```

## 7. EKS update-kubeconfig

```bash
aws eks update-kubeconfig --name my-cluster --region us-east-1 \
  --alias my-cluster-prod
```

This:
- Adds a cluster entry pointing at EKS API
- Adds a user entry that uses `aws eks get-token` for auth (refreshing every ~15 min)
- Adds a context binding them, named via `--alias`
- Switches `current-context` to it

```bash
# For different role
aws eks update-kubeconfig --name my-cluster --profile prod-admin --alias prod-admin
```

## 8. Switching role + cluster via context

```bash
# Configure once
aws eks update-kubeconfig --name dev --profile dev --alias dev-readonly
aws eks update-kubeconfig --name dev --profile dev-admin --alias dev-admin
aws eks update-kubeconfig --name prod --profile prod-readonly --alias prod-readonly
aws eks update-kubeconfig --name prod --profile prod-admin --alias prod-admin

# Then daily
kubectx dev-readonly
# ... work safely ...
kubectx prod-admin
# ... privileged ops in prod ...
```

## 9. The "wrong context" footgun + mitigations

You ran `kubectl delete pod x` in prod thinking it was dev. The classic mistake.

Mitigations:
- **Prompt shows context** (kctx in PS1)
- **Different terminal colors per context** (e.g., red for prod, green for dev)
- **kubie subshell** isolates context
- **kube-ps1** plugin (oh-my-zsh)
- **Confirmation for destructive ops in prod** — alias `kdelete-prod` with confirm prompt
- **RBAC** — readonly role on prod for daily work; assume admin only when needed

## 10. CKA exam — context tasks

Typical exam task:
> "Switch to context `kubernetes-admin@cluster2`. Find the pod named `important-pod` in namespace `tools`."

```bash
k config use-context kubernetes-admin@cluster2
k get pod important-pod -n tools
```

Easy if you remember to use `use-context` (not `set-context`).

## 11. Quick self-check

1. What 3 things does a context bind?
2. How do you merge multiple kubeconfig files?
3. What does `aws eks update-kubeconfig` actually write to your kubeconfig?
4. What's `kubectx` and `kubens`?
5. How do you set the current namespace without typing `-n` every command?

(Answers: cluster + user + namespace; `KUBECONFIG=file1:file2:file3` — kubectl reads all and merges in memory; cluster entry + user entry (using aws eks get-token for auth) + context binding them; CLI helpers for switching contexts and namespaces faster than typing `kubectl config use-context`; `k config set-context --current --namespace=my-ns`.)
