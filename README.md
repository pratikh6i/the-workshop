# The Workshop 🛡️

> **A 90-Day Hands-On Security Workshop** — Learn cloud security by building real infrastructure from first principles.

![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=flat-square&logo=google-cloud&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black)
![Security](https://img.shields.io/badge/Security-Hands--On-red?style=flat-square)

## 🎯 What is This?

Most cloud security courses teach theory. This workshop teaches **implementation**.

You'll build real infrastructure on Google Cloud, deliberately break it, fix it, and understand **why** things work the way they do. Each day focuses on a core security primitive that professionals use in production.

**Goal:** Transform from "I can click buttons in the console" to "I understand how the internet actually works."

---

## 📚 Prerequisites

- **Google Cloud Account** (Free tier works for most projects)
- **gcloud CLI** installed ([guide](https://cloud.google.com/sdk/docs/install))
- **Basic Linux knowledge** (navigating directories, editing files)
- **Terminal comfort** (you'll be using SSH extensively)

### Setting Up gcloud CLI

```bash
# Install gcloud (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Initialize and authenticate
gcloud init
gcloud auth login

# Set your default project
gcloud config set project YOUR_PROJECT_ID
```

---

## 🗺️ Learning Path

| Day | Topic | Difficulty | Key Concepts |
|-----|-------|-----------|--------------|
| [01](#-day-01-process-binding) | Process Binding | ⭐ Fundamental | Network interfaces, 0.0.0.0 vs 127.0.0.1 |
| [02](#-day-02-filesystem-security) | Filesystem Security | ⭐⭐ Intermediate | ACLs, mount options, noexec |
| [03](#-day-03-ssh-keys--metadata) | SSH Keys & Metadata | ⭐ Fundamental | Asymmetric encryption, key management |
| [04](#-day-04-ip-capacity--cidr) | IP Capacity & CIDR | ⭐⭐ Intermediate | Subnet sizing, Alias IPs, Kubernetes networking |
| [05](#-day-05-manual-nat-gateway) | Manual NAT Gateway ⭐ | ⭐⭐⭐ Advanced | IP forwarding, iptables, masquerading |

---

## 🔥 Day 01: Process Binding

**Learn:** Why opening the firewall isn't enough to make a server public.

### What You'll Build
A raw Python web server that teaches you the difference between network access (firewall) and process binding (0.0.0.0 vs 127.0.0.1).

### Setup Commands

```bash
# 1. Create VM
gcloud compute instances create manual-server-day1 \
    --machine-type=e2-micro \
    --zone=us-central1-a

# 2. Create Firewall Rule
gcloud compute firewall-rules create allow-8080 \
    --allow=tcp:8080 \
    --source-ranges=0.0.0.0/0

# 3. SSH into VM
gcloud compute ssh manual-server-day1 --zone=us-central1-a
```

**Inside the VM:**
```bash
# Create server code
cat > server.py << 'EOF'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        hostname = socket.gethostname()
        self.wfile.write(f"<h1>Hello from {hostname}!</h1>".encode())

server_address = ('0.0.0.0', 8080)
httpd = HTTPServer(server_address, SimpleHandler)
print("Server running on port 8080...")
httpd.serve_forever()
EOF

# Run the server
python3 server.py
```

### Key Concepts
- **0.0.0.0** = Listen on ALL interfaces (public + private)
- **127.0.0.1** = Listen ONLY on localhost (private)
- **Golden Command:** `sudo ss -tulpn | grep 8080` (Check what interface a process is bound to)

### Cleanup

```bash
# Exit the VM
exit

# Delete resources
gcloud compute instances delete manual-server-day1 --zone=us-central1-a --quiet
gcloud compute firewall-rules delete allow-8080 --quiet
```

---

## 🔒 Day 02: Filesystem Security

**Learn:** Cloud IAM stops intruders at the door, but Linux permissions protect the files.

### What You'll Build
A multi-user Linux environment with ACLs and hardened mount options to prevent malware execution.

### Setup Commands

```bash
# 1. Create VM
gcloud compute instances create manual-server-day2 \
    --machine-type=e2-micro \
    --zone=us-central1-a

# 2. Create Data Disk
gcloud compute disks create vault-disk \
    --size=10GB \
    --zone=us-central1-a

# 3. Attach the Disk
gcloud compute instances attach-disk manual-server-day2 \
    --disk=vault-disk \
    --zone=us-central1-a

# 4. SSH into VM
gcloud compute ssh manual-server-day2 --zone=us-central1-a
```

**Inside the VM:**
```bash
# 1. Find the disk
lsblk

# 2. Format the disk (replace /dev/sdb with your device)
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb

# 3. Mount the disk
sudo mkdir -p /mnt/vault
sudo mount -o discard,defaults /dev/sdb /mnt/vault

# 4. Create users
sudo adduser manager
sudo adduser hacker

# 5. Set ownership
sudo chown manager:manager /mnt/vault

# 6. Create secret file (as manager)
sudo su - manager
echo "Top Secret Codes" > /mnt/vault/secret.txt
chmod 600 /mnt/vault/secret.txt
exit

# 7. Grant read-only access with ACL
sudo setfacl -m u:hacker:r /mnt/vault/secret.txt

# 8. Verify (as hacker)
sudo su - hacker
cat /mnt/vault/secret.txt  # Should work
echo "hack" >> /mnt/vault/secret.txt  # Should fail
exit

# 9. Harden against malware execution
sudo mount -o remount,noexec /mnt/vault
```

### Key Concepts
- **ACLs** = Surgical permissions without chmod 777
- **noexec** = Prevent execution from data disks
- **Golden Commands:**
  - `getfacl <file>` = View ACL permissions
  - `mount -o remount,noexec <path>` = Harden live filesystem

### Cleanup

```bash
# Exit the VM
exit

# Delete resources
gcloud compute instances delete manual-server-day2 --zone=us-central1-a --quiet
gcloud compute disks delete vault-disk --zone=us-central1-a --quiet
```

---

## 🔑 Day 03: SSH Keys & Metadata

**Learn:** Manual SSH key management without "OS Login" automation.

### What You'll Build
A VM that uses raw SSH keys instead of Google's automatic authentication, simulating traditional server management.

### Setup Commands

```bash
# 1. Create VM (disable OS Login)
gcloud compute instances create keymaster-vm \
    --machine-type=e2-micro \
    --zone=us-central1-a \
    --metadata=enable-oslogin=FALSE

# 2. Generate SSH key (on your local machine)
ssh-keygen -t rsa -f ~/.ssh/gcp_key -C manual-user

# 3. Add public key to VM metadata
gcloud compute instances add-metadata keymaster-vm \
    --zone=us-central1-a \
    --metadata-from-file ssh-keys=<(echo "manual-user:$(cat ~/.ssh/gcp_key.pub)")

# 4. Connect with your key
VM_IP=$(gcloud compute instances describe keymaster-vm --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
ssh -i ~/.ssh/gcp_key manual-user@$VM_IP
```

### Key Concepts
- **Public Key** = The "lock" (safe to share)
- **Private Key** = The "key" (never share)
- **Metadata Server** = GCP's way of injecting config into VMs
- **Golden Command:** `ssh -i <private_key> <user>@<ip>`

### Disaster Recovery
If you lose your private key:
```bash
# Generate new key
ssh-keygen -t rsa -f ~/.ssh/rescue_key -C manual-user

# Update VM metadata
gcloud compute instances add-metadata keymaster-vm \
    --zone=us-central1-a \
    --metadata-from-file ssh-keys=<(echo "manual-user:$(cat ~/.ssh/rescue_key.pub)")

# Connect with new key
ssh -i ~/.ssh/rescue_key manual-user@$VM_IP
```

### Cleanup

```bash
gcloud compute instances delete keymaster-vm --zone=us-central1-a --quiet
rm ~/.ssh/gcp_key ~/.ssh/gcp_key.pub ~/.ssh/rescue_key ~/.ssh/rescue_key.pub
```

---

## 📐 Day 04: IP Capacity & CIDR

**Learn:** Why GCP "steals" 4 IPs from every subnet and how Kubernetes gets unique IPs for containers.

### What You'll Build
A tiny /29 subnet to prove GCP's IP reservation rules, then expand it live without downtime.

### Setup Commands

```bash
# 1. Create custom VPC
gcloud compute networks create day4-vpc --subnet-mode=custom

# 2. Create tiny /29 subnet (only 4 usable IPs)
gcloud compute networks subnets create day4-tiny-subnet \
    --network=day4-vpc \
    --range=10.0.1.0/29 \
    --region=us-central1

# 3. Reserve all usable IPs to prove capacity
for i in {3..6}; do
  gcloud compute addresses create ip-$i \
    --region=us-central1 \
    --subnet=day4-tiny-subnet \
    --addresses=10.0.1.$i
done

# 4. Try to reserve one more (this will fail)
gcloud compute addresses create ip-fail \
    --region=us-central1 \
    --subnet=day4-tiny-subnet \
    --addresses=10.0.1.7
# ERROR: No more capacity

# 5. Expand subnet LIVE (no downtime)
gcloud compute networks subnets expand-ip-range day4-tiny-subnet \
    --region=us-central1 \
    --prefix-length=28

# 6. Now reserve an IP in the new space
gcloud compute addresses create ip-success \
    --region=us-central1 \
    --subnet=day4-tiny-subnet \
    --addresses=10.0.1.9
# SUCCESS!

# 7. Create VM with Alias IP (Kubernetes pattern)
gcloud compute instances create alias-test-vm \
    --machine-type=e2-micro \
    --subnet=day4-tiny-subnet \
    --network-interface=aliases=10.0.1.10 \
    --zone=us-central1-a
```

### Key Concepts
- **GCP reserves 4 IPs:** Network (.0), Gateway (.1), Reserved (.2), Broadcast (.7)
- **/29 = 8 IPs total, 4 usable**
- **Shrinking forbidden:** Would break routing for existing VMs
- **Alias IPs:** How containers get unique IPs (Kubernetes magic)
- **Golden Command:** `gcloud compute networks subnets expand-ip-range`

### Cleanup

```bash
# Delete VM
gcloud compute instances delete alias-test-vm --zone=us-central1-a --quiet

# Delete reserved IPs
for i in {3..6} success; do
  gcloud compute addresses delete ip-$i --region=us-central1 --quiet
done

# Delete subnet and VPC
gcloud compute networks subnets delete day4-tiny-subnet --region=us-central1 --quiet
gcloud compute networks delete day4-vpc --quiet
```

---

## 🌐 Day 05: Manual NAT Gateway ⭐

**Learn:** Build a Linux router from scratch using IP forwarding and iptables (the foundation of "Cloud NAT").

### What You'll Build
A Gateway VM that acts as a router, allowing a Private VM (with NO public IP) to access the internet.

### Setup Commands

```bash
# 1. Create Gateway VM (with IP forwarding enabled)
gcloud compute instances create gateway-vm \
    --machine-type=e2-micro \
    --zone=us-central1-a \
    --can-ip-forward \
    --tags=nat-gateway

# 2. Create Private VM (NO external IP)
gcloud compute instances create private-vm \
    --machine-type=e2-micro \
    --zone=us-central1-a \
    --no-address \
    --tags=no-ip

# 3. Create Custom Route (send internet traffic through gateway)
gcloud compute routes create route-private-to-internet \
    --network=default \
    --destination-range=0.0.0.0/0 \
    --next-hop-instance=gateway-vm \
    --next-hop-instance-zone=us-central1-a \
    --tags=no-ip \
    --priority=800

# 4. Configure the Gateway VM
gcloud compute ssh gateway-vm --zone=us-central1-a
```

**Inside Gateway VM:**
```bash
# Enable IP forwarding in kernel
sudo sysctl -w net.ipv4.ip_forward=1

# Find network interface name (usually ens4, NOT eth0)
ip link show

# Enable NAT masquerading (replace ens4 if different)
sudo iptables -t nat -A POSTROUTING -o ens4 -j MASQUERADE

# Verify rules
sudo iptables -t nat -L -v

# Exit gateway
exit
```

**Test from Private VM:**
```bash
# Connect to private VM via IAP
gcloud compute ssh private-vm --zone=us-central1-a --tunnel-through-iap

# Test internet access
ping -c 2 8.8.8.8
# SUCCESS! Private VM can reach internet via gateway
```

### Key Concepts
- **IP Forwarding:** Must enable in GCP Console AND Linux kernel
- **Masquerading:** Rewrites source IP to gateway's public IP
- **Interface Names:** Modern Linux uses `ens4`, not `eth0`
- **IAP Tunnel:** Access private VMs without public IPs
- **Golden Command:** `sudo iptables -t nat -A POSTROUTING -o <interface> -j MASQUERADE`

### Troubleshooting
If traffic doesn't flow:
```bash
# Check interface name
ip link show

# Flush bad rules and reapply
sudo iptables -t nat -F
sudo iptables -t nat -A POSTROUTING -o ens4 -j MASQUERADE
```

### Cleanup

```bash
# Exit private VM
exit

# Delete resources
gcloud compute instances delete gateway-vm --zone=us-central1-a --quiet
gcloud compute instances delete private-vm --zone=us-central1-a --quiet
gcloud compute routes delete route-private-to-internet --quiet
```

---

## 🌐 View the Live Blog

While this README focuses on **doing the projects**, you can read the detailed explanations and theory at:

**[The Workshop Blog](https://pratikh6i.github.io/the-workshop/)**

The blog includes:
- Detailed first-principles explanations
- Architecture diagrams
- Troubleshooting guides
- Real-world applications

---

## 💡 Learning Tips

1. **Do Every Command:** Don't just read. Type every command yourself.
2. **Break Things:** The "breaker" sections are critical for understanding.
3. **Use Free Tier:** Most projects use e2-micro instances (usually free).
4. **Clean Up Daily:** Run cleanup commands to avoid surprise bills.
5. **Read Errors:** Error messages teach you more than success.

---

## 💰 Cost Management

**Free Tier Resources:**
- e2-micro VMs (1 per month in us-central1, us-east1, us-west1)
- 30 GB of standard persistent disk
- Firewall rules (free)

**Paid Resources:**
- Extra compute instances beyond free tier (~$7/month per e2-micro)
- Data egress (internet downloads from VMs)

**Safety Tips:**
- Always run cleanup commands after each day
- Set a GCP billing alert at $10
- Use `gcloud compute instances list` to check for forgotten VMs

---

## 🤝 Contributing

Found a bug or have a suggestion? Open an issue or PR!

---

## 📄 License

MIT © 2026

**Remember:** The best way to learn security is to build systems that break, then figure out why. Happy hacking! 🛡️
