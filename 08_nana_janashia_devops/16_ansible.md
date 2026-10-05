# 16 — Configuration Management with Ansible

## Why this module exists

Ansible is the dominant configuration-management tool (vs declining Salt/Puppet/Chef). It's also the most useful "you have a fleet of VMs and need to do something to them" tool. Net-new module — no other topic in this project covers Ansible.

## 1. Why Ansible (vs alternatives)

| | Ansible | Salt | Puppet | Chef | cloud-init |
|---|---|---|---|---|---|
| **Agent** | Agentless (SSH) | Agent (Salt master+minions) | Agent | Agent | First-boot only |
| **Lang** | YAML | YAML + Python | DSL | Ruby DSL | Bash/cloud-config |
| **2026 trajectory** | Dominant + IBM-stable | Declining | Declining | Declining | Stable / different niche |
| **Push vs Pull** | Push | Pull (default) | Pull | Pull | N/A |

Ansible won the war ~2018-2020 because:
- Agentless (just needs SSH + Python on target)
- Readable YAML
- Idempotent built-in modules
- Red Hat backing (acquired AnsibleWorks 2015, then IBM acquired Red Hat 2019)

## 2. Architecture

```
┌──────────────────┐         SSH         ┌──────────────────┐
│   Control Node   │  ─────────────────► │  Managed Node 1  │
│  (your laptop /  │  ─────────────────► │  Managed Node 2  │
│   bastion EC2)   │  ─────────────────► │       ...        │
└──────────────────┘                     └──────────────────┘
   ansible-core
   collections
   inventory
   playbooks
```

The control node runs Python + ansible-core. It SSHes to managed nodes (which need Python — typically already there on Linux). No agent on managed nodes.

## 3. Install

```bash
# macOS
brew install ansible
# Or pip
uv pip install ansible-core ansible

# Verify
ansible --version
```

Latest ansible-core 2.18+ requires Python 3.11+ on control node.

## 4. Inventory — who you're managing

### Static INI
```ini
[web]
web1.example.com
web2.example.com

[db]
db1.example.com ansible_user=admin ansible_port=2222

[all:vars]
ansible_user=ubuntu
ansible_ssh_private_key_file=~/.ssh/id_ed25519
```

### Static YAML
```yaml
all:
  children:
    web:
      hosts:
        web1.example.com:
        web2.example.com:
    db:
      hosts:
        db1.example.com:
          ansible_user: admin
          ansible_port: 2222
```

### Dynamic — query the cloud
```yaml
# inventory.aws_ec2.yml
plugin: amazon.aws.aws_ec2
regions: [us-east-1]
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: placement.region
    prefix: aws_region
filters:
  tag:Environment: prod
```

Then: `ansible-inventory -i inventory.aws_ec2.yml --graph`. Pulls EC2 instances tagged Environment=prod into groups by their Role tag.

## 5. Ad-hoc commands

```bash
ansible all -i inventory.ini -m ping                   # check connectivity
ansible web -m apt -a "name=nginx state=present" -b   # install nginx with sudo (-b)
ansible all -m shell -a "uptime"
ansible all -m copy -a "src=local.conf dest=/etc/app/"
```

`-b` = become root (sudo). `-m <module>` = use specific module. `-a "args"` = module args.

## 6. Playbooks — the real work

```yaml
# site.yaml
- name: Configure web servers
  hosts: web
  become: true
  vars:
    nginx_version: "1.27.*"
  tasks:
    - name: Install nginx
      apt:
        name: "nginx={{ nginx_version }}"
        state: present
        update_cache: true

    - name: Render nginx config
      template:
        src: templates/nginx.conf.j2
        dest: /etc/nginx/nginx.conf
        mode: '0644'
      notify: Reload nginx

    - name: Ensure nginx running
      systemd:
        name: nginx
        state: started
        enabled: true

  handlers:
    - name: Reload nginx
      systemd:
        name: nginx
        state: reloaded
```

```bash
ansible-playbook -i inventory.ini site.yaml
ansible-playbook -i inventory.ini site.yaml --check    # dry run
ansible-playbook -i inventory.ini site.yaml --diff     # show file changes
ansible-playbook -i inventory.ini site.yaml --tags nginx --limit web1.example.com
```

## 7. Modules + Collections

Modules are units of work (apt, yum, copy, template, systemd, file, etc.). **Collections** are bundles of modules + roles. Since Ansible 2.10, modules ship in collections via Ansible Galaxy.

```bash
ansible-galaxy collection install community.general
ansible-galaxy collection install amazon.aws
ansible-galaxy collection install kubernetes.core
```

Reference: `amazon.aws.ec2_instance`, `kubernetes.core.k8s`, `community.general.terraform`.

## 8. Variables

Hierarchy (lowest to highest precedence — abbreviated):
1. Role defaults (`defaults/main.yml`)
2. Inventory group vars
3. Inventory host vars
4. Playbook vars
5. Task vars
6. Extra vars (`-e foo=bar`) — wins everything

Best practice: `group_vars/<group>.yml` and `host_vars/<host>.yml` for per-environment config.

```yaml
# group_vars/web.yml
nginx_worker_processes: 4
nginx_server_name: example.com

# group_vars/all.yml
timezone: UTC
admin_email: ops@example.com
```

## 9. Ansible Vault — encrypted secrets

```bash
ansible-vault create group_vars/prod/vault.yml
# Opens editor; type secrets:
# db_password: super-secret
ansible-vault edit group_vars/prod/vault.yml
ansible-vault view group_vars/prod/vault.yml
ansible-playbook -i inv site.yaml --ask-vault-pass
# Or
ansible-playbook -i inv site.yaml --vault-password-file ~/.vault_pass
```

Vault encrypts values at rest in the repo. Decrypt at runtime via password (or CI secret). For dynamic secrets prefer **HashiCorp Vault integration** or external lookup plugins.

## 10. Roles — reusable, modular

```
roles/
└── nginx/
    ├── defaults/main.yml     # default vars
    ├── files/                # static files
    ├── handlers/main.yml     # restart/reload handlers
    ├── tasks/main.yml        # actual tasks
    ├── templates/            # Jinja2 templates
    ├── vars/main.yml         # role vars (high precedence)
    └── meta/main.yml         # role metadata + dependencies
```

```yaml
# site.yaml using roles
- hosts: web
  become: true
  roles:
    - { role: common }
    - { role: nginx, nginx_worker_processes: 8 }
    - { role: app, app_version: "1.2.3" }
```

Ansible Galaxy has thousands of community roles: `ansible-galaxy install geerlingguy.nginx` (Jeff Geerling's roles are particularly well-maintained).

## 11. Ansible + Terraform together (the common pattern)

- **Terraform** provisions the EC2 instances + VPC + Security Groups
- **Terraform output** writes the instance IPs to a file or to Ansible inventory
- **Ansible** configures the instances (install nginx, deploy app)

This is "Terraform for the metal, Ansible for the meat." Pure Terraform with `remote-exec` provisioner is an anti-pattern (Module 13).

For modern setups, **Packer** + Ansible bakes an AMI, then Terraform provisions VMs from the AMI = immutable. No runtime config drift.

## 12. Ansible in Jenkins (the bootcamp project)

```groovy
stage('Configure servers') {
  steps {
    sshagent(credentials: ['deploy-key']) {
      sh '''
        ansible-playbook -i inventory.ini site.yaml \
          --extra-vars "app_version=$BUILD_NUMBER"
      '''
    }
  }
}
```

The Jenkinsfile runs `ansible-playbook` from the agent. Credentials managed via `sshagent` or vault password from secret store.

## 13. Ansible deploying to K8s

```yaml
- hosts: localhost
  tasks:
    - name: Apply deployment
      kubernetes.core.k8s:
        state: present
        definition:
          apiVersion: apps/v1
          kind: Deployment
          metadata: { name: myapp }
          spec:
            replicas: 3
            selector: { matchLabels: { app: myapp } }
            template:
              metadata: { labels: { app: myapp } }
              spec:
                containers:
                - name: app
                  image: "myapp:{{ app_version }}"
```

Honestly: for K8s deploys, prefer **Helm + ArgoCD/Flux** over Ansible. Ansible-to-K8s is a relic of the early days.

## 14. AAP (Ansible Automation Platform) — Red Hat commercial

What you get with AAP:
- Web UI for running playbooks (formerly Tower)
- Job scheduling
- RBAC
- Workflow chaining
- Execution Environments (containerized runner — replaces "install all collections everywhere")
- Event-Driven Ansible (EDA) — react to webhooks/events

Subscription-required since IBM acquisition. Pricing varies by node count (~$10-20k/yr for small teams up to enterprise).

## 15. The 2026 reality — where is Ansible going

- **Strong:** traditional VM-based infra, network device config (Cisco/Juniper/Arista), Windows VM mgmt
- **Weaker:** K8s-native shops (prefer Helm/Kustomize/ArgoCD); immutable-infra shops (prefer Packer + Terraform); GitOps shops (prefer pull-based agents)
- **Niche but growing:** Event-Driven Ansible for incident-response automation

For an AI/ML engineer at Capital One: Ansible knowledge is a "nice to have" but K8s + Helm + GitOps + Terraform is the daily reality.

## 16. Quick self-check

1. Why is Ansible agentless an advantage over Puppet/Chef?
2. What does `become: true` do?
3. When should you use dynamic inventory?
4. What's the difference between a role and a collection?
5. Why is Ansible-to-K8s an anti-pattern in 2026?

(Answers: no agent install/upgrade burden, just SSH + Python; equivalent to sudo on the target; for cloud resources where IPs/hostnames change — query the cloud at runtime; role = reusable bundle of tasks + vars + templates for one thing, collection = bundle of modules + roles + plugins for a vendor/topic; K8s has native declarative tooling, Helm/Kustomize/ArgoCD beat Ansible's imperative push model.)
