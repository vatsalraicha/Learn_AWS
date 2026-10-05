# 56 — Linux Server Deployment

## 1. The "deploy to a single VM" reality check

In 2026 most production traffic runs on K8s, but **single-VM deploys are still common** for:
- Small projects / side projects
- Internal tools
- Legacy apps
- Learning + skill-building

The skills you learn here transfer to: Bastion hosts, GitLab runners, monitoring agents, AI training VMs, etc.

## 2. Provisioning Ubuntu 24.04 on cloud

```bash
# AWS
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.small \
  --key-name my-key \
  --security-group-ids sg-0abc \
  --user-data file://bootstrap.sh

# DigitalOcean
doctl compute droplet create my-server \
  --region nyc3 --size s-1vcpu-2gb \
  --image ubuntu-24-04-x64 \
  --ssh-keys 12345

# Linode
linode-cli linodes create --label my-server \
  --image linode/ubuntu24.04 --type g6-nanode-1 --region us-east
```

Ubuntu 24.04 "Noble Numbat" — current LTS, EOL Apr 2029.

## 3. SSH into the server

```bash
ssh -i ~/.ssh/id_ed25519 ubuntu@<ip>
```

On macOS:
```bash
ssh root@<ip>       # DO uses root
ssh ubuntu@<ip>     # AWS Ubuntu AMI uses ubuntu
ssh ec2-user@<ip>   # AWS Amazon Linux
```

On Windows: use Windows Terminal + OpenSSH (built into Windows 10+).

## 4. Initial hardening (the 8-point checklist)

```bash
# 1. Update everything
sudo apt update && sudo apt upgrade -y

# 2. Create non-root user
sudo adduser deploy
sudo usermod -aG sudo deploy
sudo cp -r ~/.ssh /home/deploy/
sudo chown -R deploy:deploy /home/deploy/.ssh

# 3. Disable root SSH + password auth
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# 4. Firewall — UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 5. Unattended security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 6. fail2ban for brute-force protection
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban

# 7. Set timezone
sudo timedatectl set-timezone UTC

# 8. Set hostname
sudo hostnamectl set-hostname my-server.example.com
```

## 5. Reverse proxy — Caddy (the easiest TLS)

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

`/etc/caddy/Caddyfile`:
```
app.example.com {
  reverse_proxy localhost:3000
}

api.example.com {
  reverse_proxy localhost:8000
  encode gzip
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options nosniff
    Referrer-Policy strict-origin-when-cross-origin
  }
}
```

```bash
sudo systemctl reload caddy
```

**Caddy's killer feature: automatic Let's Encrypt TLS.** Add a domain to the Caddyfile + point DNS at the server — TLS just works.

## 6. Reverse proxy — Nginx (more traditional)

```bash
sudo apt install -y nginx
```

`/etc/nginx/sites-available/app`:
```nginx
server {
  listen 80;
  server_name app.example.com;
  location / {
    proxy_pass http://localhost:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

For TLS: install `certbot`:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d app.example.com
```

## 7. Run app as systemd service

`/etc/systemd/system/my-app.service`:
```ini
[Unit]
Description=My App
After=network.target

[Service]
Type=simple
User=deploy
WorkingDirectory=/opt/my-app
Environment=NODE_ENV=production
EnvironmentFile=/etc/my-app/env
ExecStart=/usr/bin/node /opt/my-app/dist/index.js
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/my-app/data
ProtectHome=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now my-app
sudo systemctl status my-app
journalctl -u my-app -f
```

## 8. Docker on Ubuntu (simpler alternative)

```bash
sudo apt install -y docker.io docker-compose-v2
sudo usermod -aG docker deploy
```

Run app:
```bash
docker compose up -d
```

For rootless Docker (better security):
```bash
curl -fsSL https://get.docker.com/rootless | sh
```

## 9. Multi-app deployment patterns

For multiple apps on one VM:
- **Docker Compose** — preferred; isolation + reproducibility
- **Systemd units** — each app a unit
- **Nginx/Caddy** routing to different ports
- **HAProxy** for advanced routing

Discipline: keep apps in `/opt/<app>` with own user; logs to journald; secrets in `/etc/<app>/env` mode 600.

## 10. The "deploy to single VM" vs "deploy to K8s" debate

**VM wins when:**
- < 5 services
- < 100 req/s
- Solo / small team
- No need for autoscaling
- Cost matters (< $50/mo budget)
- Simple, predictable workloads

**K8s wins when:**
- > 10 services
- Autoscaling needed
- Multi-team org
- Compliance/audit requirements
- Already have K8s expertise
- > $200/mo budget anyway

For learning: do both. VM for fundamentals; K8s for scale.

## 11. Modern PaaS alternatives

Skip Linux entirely:
- **Fly.io** — global edge deploy
- **Railway** — Heroku-style PaaS
- **Render** — Heroku-style
- **Vercel** / **Netlify** — frontends + serverless
- **Cloudflare Workers** — edge functions
- **AWS App Runner** — managed container PaaS

For Vatsal's side projects: Fly.io or Railway eliminates 80% of the Linux skills below — but the Linux skills still apply when you SSH into Jenkins agents or AWS instances at work.

## 12. Quick self-check

1. Why disable root SSH login?
2. What's Caddy's killer feature over Nginx?
3. What does systemd's `ProtectSystem=strict` do?
4. What's the difference between Docker and rootless Docker?
5. When does a single VM deploy beat K8s?

(Answers: prevents brute-force on the default username + forces named-user accountability + audit trail; automatic Let's Encrypt TLS just by adding a domain; mounts /usr and /boot read-only for the service — limits attack-driven file modification; rootless runs the daemon as a non-root user — escape from container doesn't give root on host; small service count, predictable load, solo/small team, cost-constrained.)
