# 02 — Operating Systems + Linux Basics

> Cross-link: [Topic 05 Module 1 — Linux primitives](../05_docker_kubernetes/01_linux_primitives.md). This module is a *DevOps-task-driven* refresher — what you actually do in a pipeline, on a Jenkins agent, on a Linux VM.

## Why this module exists

A senior AI/ML engineer can write Python all day but freeze on "find the process eating CPU on this Jenkins agent and kill it." This module is the muscle memory.

## 1. Why Linux dominates DevOps

- **~96% of public cloud workloads** run Linux as of 2025 (AWS, GCP, Azure surveys).
- **~100% of K8s clusters** run Linux node pools (Windows nodes exist but rare).
- **Container runtimes** (runc, containerd, crun) are Linux-kernel-feature-dependent (namespaces, cgroups).
- **Ubuntu LTS** is the default for most dev shops (Ubuntu 24.04 "Noble Numbat" is current LTS, EOL Apr 2029). RHEL/Rocky/Alma for regulated shops. Amazon Linux 2023 for AWS-native.

## 2. Virtualization vs containers

| Concept | VM | Container |
|---|---|---|
| **Isolation** | Hardware (hypervisor) | Process (namespaces + cgroups) |
| **Boot time** | 10s–minutes | Milliseconds |
| **Resource overhead** | ~5–15% | < 1% |
| **OS** | Full guest OS | Shares host kernel |
| **Use case** | Multi-tenant, full isolation | App packaging + portability |

Hypervisors: KVM (Linux kernel module), Xen, VMware ESXi, Hyper-V. Cloud VMs (EC2, GCE, Azure VM) run on these.

## 3. The Linux file system tree (DevOps essentials)

```
/etc/         # config files (nginx.conf, ssh_config, systemd units)
/var/log/     # log files (syslog, auth.log, app logs)
/var/lib/     # persistent app state (docker, postgres, etcd)
/usr/local/bin/  # user-installed binaries
/opt/         # third-party software (often Java apps)
/home/<user>/ # user homes
/tmp/         # ephemeral, world-writable, often cleared on reboot
/proc/        # virtual fs exposing kernel + process info
/sys/         # virtual fs exposing devices + kernel objects
/dev/         # device files (/dev/null, /dev/sda1)
```

When debugging a container: `/proc/<pid>/cgroup` shows which cgroup the process is in (and thus which container).

## 4. The CLI commands you actually use daily

### Filesystem navigation
```bash
ls -lah                # long, all, human-readable
cd -                   # previous directory
pwd                    # where am I
find /var/log -name "*.log" -mtime -1   # logs modified in last day
du -sh /var/lib/docker # disk usage, human-readable
df -h                  # disk free, human-readable
```

### Text + log triage (replace `grep` with `rg` ripgrep)
```bash
rg "ERROR" /var/log/app.log         # ripgrep — 5-10x faster than grep
tail -f /var/log/syslog             # follow live
journalctl -u nginx --since "1 hour ago"  # systemd logs
less +F /var/log/app.log            # follow with scrollback
awk -F'|' '{print $3}' file         # column extract
sed -i 's/old/new/g' file           # in-place substitute
```

### Process + resource
```bash
ps aux | rg python                  # processes
top                                 # real-time CPU/mem; press M for mem-sort
htop                                # nicer top (install separately)
btop                                # modern alternative
kill -9 <pid>                       # SIGKILL
kill -15 <pid>                      # SIGTERM (graceful)
lsof -i :8080                       # what's listening on port 8080
ss -tulpn                           # modern netstat
```

### Pipes + redirects
```bash
cmd1 | cmd2                         # stdout → stdin
cmd > file                          # stdout overwrite file
cmd >> file                         # stdout append
cmd 2> err.log                      # stderr to file
cmd > out.log 2>&1                  # both to file
cmd &> all.log                      # bash shorthand for above
cmd < input.txt                     # stdin from file
```

## 5. Package managers (the DevOps reality)

| Distro | PM | Example |
|---|---|---|
| Ubuntu/Debian | apt | `sudo apt update && sudo apt install -y jq curl` |
| RHEL/CentOS/Rocky | dnf (yum legacy) | `sudo dnf install -y jq` |
| Alpine | apk | `apk add --no-cache jq` |
| Amazon Linux 2023 | dnf | `sudo dnf install -y jq` |
| macOS | brew | `brew install jq` |

For Dockerfiles, prefer Alpine-based images (smaller) unless you need glibc compatibility — then use Debian-slim or Ubuntu-minimal.

## 6. Vim (the survival subset)

You will SSH into a server with no editor but vim. Survive with:

- `i` insert mode, `Esc` back to normal mode
- `:w` save, `:q` quit, `:wq` save+quit, `:q!` quit without saving
- `dd` delete line, `yy` copy line, `p` paste below
- `/pattern` search, `n` next, `N` previous
- `:s/old/new/g` substitute on current line, `:%s/old/new/g` whole file
- `u` undo, `Ctrl+r` redo
- `gg` top, `G` bottom, `:42` go to line 42

For real work, use VS Code with Remote SSH, but vim is the unavoidable fallback.

## 7. Users, groups, permissions

```bash
sudo adduser alice               # create user
sudo usermod -aG sudo alice      # add to sudo group
sudo usermod -aG docker alice    # add to docker group (avoid sudo for docker)
groups alice                     # list user's groups
chmod 755 script.sh              # rwxr-xr-x
chmod +x script.sh               # add execute for all
chown alice:alice file           # change owner + group
```

Permission octal cheat sheet:
- `4` = read, `2` = write, `1` = execute
- `755` = owner rwx, group rx, other rx → standard for executable scripts/dirs
- `644` = owner rw, group r, other r → standard for files
- `600` = owner rw only → SSH keys, sensitive config

## 8. Shell scripting essentials

```bash
#!/usr/bin/env bash
set -euo pipefail   # -e exit on error, -u undefined vars error, -o pipefail
IFS=$'\n\t'         # safe word splitting

# Variables
NAME="world"
echo "Hello, ${NAME}"

# Conditionals
if [[ -f /etc/passwd ]]; then
  echo "exists"
elif [[ "${1:-}" == "test" ]]; then
  echo "test mode"
else
  echo "other"
fi

# Loops
for host in web1 web2 web3; do
  ssh "$host" "uptime"
done

# Functions
deploy() {
  local env="$1"
  echo "deploying to $env"
}
deploy "prod"

# Trap errors
trap 'echo "FAIL on line $LINENO"' ERR
```

Tip: every CI/CD pipeline boils down to "run shell scripts on a Linux box." Mastering bash is the highest-leverage skill for pipeline debugging.

## 9. Environment variables

```bash
export AWS_REGION=us-east-1            # set for current shell + children
echo $AWS_REGION
env | rg AWS                           # all AWS-related env vars
unset AWS_REGION
```

In Jenkins/GitLab/Actions, env vars are how secrets and config flow into your build. The pattern: secrets manager → CI/CD masked variable → env var in build job → app reads it.

## 10. Networking + SSH primer

```bash
ping google.com                       # ICMP
curl -fsSL https://example.com         # HTTP test (fail silently, follow redirects)
dig +short example.com                # DNS lookup
nslookup example.com                  # alternative
traceroute google.com                 # path
mtr google.com                        # mtr = traceroute + ping
```

### SSH
```bash
ssh-keygen -t ed25519 -C "vatsal@laptop"  # generate key (ed25519, not RSA in 2026)
ssh-copy-id user@host                     # copy public key to server
ssh -i ~/.ssh/id_ed25519 user@host        # connect with specific key
ssh -L 8080:localhost:8080 user@host      # local port forward
ssh -A user@host                          # forward agent (use with care)
~/.ssh/config                             # define aliases
```

Sample `~/.ssh/config`:
```
Host bastion
  HostName bastion.example.com
  User vatsal
  IdentityFile ~/.ssh/id_ed25519

Host prod-jump
  HostName 10.0.1.42
  User ec2-user
  ProxyJump bastion
```

## 11. Quick self-check

1. Where do systemd logs live, and what command tails them?
2. What's the difference between `kill -9` and `kill -15`?
3. Which group should you add a user to so they can run docker without sudo?
4. What does `set -euo pipefail` do?
5. Which SSH key algorithm should you generate in 2026 and why not RSA?

(Answers: journalctl + journal log; SIGKILL is immediate, SIGTERM is graceful; `docker` group; exit on error, error on unset, fail pipelines on mid-pipe failure; ed25519 — smaller, faster, simpler than RSA-4096 with equivalent security.)
