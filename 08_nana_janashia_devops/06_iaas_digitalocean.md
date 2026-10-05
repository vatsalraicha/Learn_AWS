# 06 — Cloud & Infrastructure as a Service (DigitalOcean lens)

## Why this module exists

Nana picks DigitalOcean for her bootcamp because it's the cheapest way for a learner to spin up a real Linux VM ($4-6/mo droplets). The principles transfer to EC2/Compute Engine/Azure VM — and from a Capital One perspective, AWS EC2 is the production reality. This module is the bridge.

## 1. The IaaS / PaaS / SaaS taxonomy

| Layer | You manage | Examples |
|---|---|---|
| **On-prem** | Everything: power, network, hardware, OS, runtime, app | Your data center |
| **IaaS** | OS, runtime, app | EC2, GCE, Azure VM, DigitalOcean Droplets |
| **PaaS** | App + config | App Engine, App Runner, Render, Fly.io, Vercel |
| **CaaS** | Container + config | ECS, Cloud Run, Fargate, Container Apps |
| **FaaS** | Function + event | Lambda, Cloud Functions, Azure Functions |
| **SaaS** | Nothing — just use it | Snowflake, Salesforce, GitHub, Notion |

The boundary you choose determines your team's ops burden.

## 2. DigitalOcean essentials (cheap learning lab)

- **Droplet**: their VM. Smallest = $4/mo (1vCPU, 512MB), reasonable = $6/mo (1vCPU, 1GB).
- **Spaces**: their S3-compatible object storage ($5/mo for 250GB).
- **Managed K8s (DOKS)**: free control plane, pay for nodes (cheap for learning).
- **Managed Databases**: Postgres / MySQL / Redis / MongoDB.
- **App Platform**: their PaaS, similar to Heroku.

Why use it? Sandbox + learning. **Not** for serious production at scale (~10% of AWS's service breadth).

## 3. The "set up a server" lifecycle (universal across IaaS)

```bash
# 1. Provision (DO CLI, AWS CLI, etc.)
doctl compute droplet create web1 \
  --region nyc3 --size s-1vcpu-1gb --image ubuntu-24-04-x64 \
  --ssh-keys "your-key-id" --enable-monitoring

# Or AWS:
aws ec2 run-instances --image-id ami-0abc \
  --instance-type t3.micro --key-name mykey \
  --security-group-ids sg-0abc --subnet-id subnet-0abc

# 2. Connect
ssh root@<ip>     # DO uses root by default; AWS uses ec2-user or ubuntu

# 3. Initial hardening (every server, every time)
adduser deploy
usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
cp /root/.ssh/authorized_keys /home/deploy/.ssh/
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh && chmod 600 /home/deploy/.ssh/authorized_keys

# Disable root SSH + password auth
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd

# Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Updates
apt update && apt upgrade -y
apt install -y unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

## 4. Deploying an artifact on a Droplet (the manual baseline)

```bash
# As deploy user
scp app-1.2.3.jar deploy@<ip>:/opt/app/
ssh deploy@<ip>
sudo systemctl restart app
```

This works once. It does NOT scale. The next 10 modules of this curriculum are about replacing this manual flow with: Jenkins → build artifact → push to Nexus → deploy to EC2 via Ansible → containerize → K8s → IaC → GitOps.

## 5. Cloud-init — the bootstrap mechanism

Most clouds let you pass a "user-data" script that runs on first boot:

```bash
#!/bin/bash
apt update
apt install -y docker.io
systemctl enable --now docker
usermod -aG docker ubuntu
```

This script bakes baseline config into the VM at provisioning time. It's the simplest form of configuration management; Ansible (Module 16) is the more powerful version.

## 6. From IaaS to immutable infrastructure

The 2026 best practice: **never SSH into a server to fix something**. Instead:
- Build a new AMI (Packer) or container image (Docker) with the fix
- Roll out via auto-scaling group / K8s rolling update
- Old instances terminated

Why: ephemeral, reproducible, auditable. The "Cattle vs Pets" metaphor — your servers are interchangeable cattle, not beloved pets you name and nurse back to health.

## 7. AWS equivalents at a glance

| DO concept | AWS equivalent |
|---|---|
| Droplet | EC2 instance |
| Spaces | S3 |
| DOKS | EKS |
| Managed Postgres | RDS |
| App Platform | App Runner (or Elastic Beanstalk for older shops) |
| Load Balancer | ALB / NLB |
| VPC | VPC (same name) |
| Floating IP | Elastic IP |

See [Topic 04 — AWS for AI/ML Engineers](../04_aws_for_ai_ml/) for the full AWS depth.

## 8. Quick self-check

1. What's the difference between IaaS and PaaS?
2. What does "cattle vs pets" mean?
3. Name three baseline hardening steps for a new Ubuntu droplet.
4. What's cloud-init / user-data?
5. Why isn't `scp + ssh + systemctl restart` enough for production deploys?

(Answers: IaaS = OS+up; PaaS = app+up; treat servers as fungible not unique; create non-root user, disable root SSH, ufw firewall + unattended-upgrades; bootstrap script run on first boot; manual, error-prone, no rollback, no audit trail, doesn't scale.)
