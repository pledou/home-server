# Detailed Setup Guide

This guide provides step-by-step instructions for setting up your home server infrastructure from scratch.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Configuration Strategy](#configuration-strategy)
- [Service-Specific Configuration](#service-specific-configuration)
- [First Deployment](#first-deployment)
- [Post-Deployment Tasks](#post-deployment-tasks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Control Machine (Your Computer)

Install required software:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ansible python3-pip git

# macOS
brew install ansible python3 git

# Verify installation
ansible --version  # Should be 2.9+
python3 --version  # Should be 3.8+
```

### Target Server

1. **Operating System**: Ubuntu 20.04+ or Debian 11+
2. **Hardware Requirements**:
   - CPU: 4+ cores recommended
   - RAM: 8GB minimum, 16GB+ recommended
   - Storage: 500GB+ recommended (separate disk for Docker volumes preferred)
   - Network: Static IP or reliable DHCP reservation

3. **Initial Server Setup**:

```bash
# On the server, create a user with sudo privileges
sudo adduser your-username
sudo usermod -aG sudo your-username

# Enable SSH
sudo apt update
sudo apt install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh

# Optional: Disable password auth after setting up SSH keys
# Edit /etc/ssh/sshd_config:
# PasswordAuthentication no
```

4. **Network Access**: Ensure your control machine can reach the server via SSH

### 4. Set Up SSH Key Authentication (Recommended)

For security and convenience, use SSH key authentication instead of passwords:

#### Generate SSH Key Pair

On your control machine:

```bash
# Generate a strong ED25519 key pair
ssh-keygen -t ed25519 -C "your_email@example.com" -f ~/.ssh/homeserver_ed25519

# Use a strong passphrase to protect your private key
```

**Important Security Notes:**
- Use a **strong passphrase** to protect your private key
- Keep your private key secure (`~/.ssh/homeserver_ed25519`)
- Never share or commit your private key
- Back up your keys securely

#### Copy Public Key to Server

```bash
# Option 1: Using ssh-copy-id (easiest)
ssh-copy-id -i ~/.ssh/homeserver_ed25519.pub username@server-ip

# Option 2: Manual copy
cat ~/.ssh/homeserver_ed25519.pub
# Copy the output, then on the server:
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### Test SSH Key Authentication

```bash
# Test connection with your key
ssh -i ~/.ssh/homeserver_ed25519 username@server-ip

# If successful, you should be able to log in without entering the server password
```

#### Use ssh-agent for Convenience

To avoid entering your key passphrase repeatedly:

```bash
# Start ssh-agent and add your key
eval $(ssh-agent)
ssh-add ~/.ssh/homeserver_ed25519
# Enter your key passphrase once

# Now SSH and Ansible will use the key without prompting
```

#### Configure Ansible to Use Your SSH Key

In your `inventories/inventory.yml`, specify the key file:

```yaml
all:
  hosts:
    homeserver:
      ansible_connection: ssh
      ansible_host: 192.168.1.100
      ansible_user: your-username
      ansible_ssh_private_key_file: ~/.ssh/homeserver_ed25519
      # No ansible_ssh_pass needed with key authentication
      ansible_become_pass: !vault |  # Only if sudo requires password
        $ANSIBLE_VAULT;1.1;AES256
        ...encrypted...
```

#### Disable Password Authentication (Optional but Recommended)

After confirming SSH key authentication works:

```bash
# On the server, edit SSH config
sudo nano /etc/ssh/sshd_config

# Set these values:
# PasswordAuthentication no
# PubkeyAuthentication yes
# ChallengeResponseAuthentication no

# Restart SSH service
sudo systemctl restart sshd
```

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/home-server.git
cd home-server
```

### 2. Configuration Strategy

You have two options for managing sensitive data:

#### **Option A: Local Configuration (Simpler)**

Best for: Single operator, local testing

```bash
# Create configuration from templates
cp ansible.cfg.example ansible.cfg
cp inventories/inventory.example.yml inventories/inventory.yml
cp inventories/group_vars/all.example.yml inventories/group_vars/all.yml

# These files are git-ignored and won't be committed
```

#### **Option B: Private Repository (Recommended for Production)**

Best for: Multi-user teams, backup of configurations, separate sensitive data

```bash
# Create a private repository on GitHub/GitLab
# Name it something like: home-server-private-data

# Clone and set up structure
git clone git@github.com:YOUR_USERNAME/home-server-private-data.git
cd home-server-private-data

# Create structure
mkdir -p inventories/group_vars
cp ../home-server/ansible.cfg.example ansible.cfg
cp ../home-server/inventories/inventory.example.yml inventories/inventory.yml
cp ../home-server/inventories/group_vars/all.example.yml inventories/group_vars/all.yml

# Create linking script
cat > setup-links.sh << 'EOF'
#!/bin/bash
if [ $# -eq 0 ]; then
    echo "Usage: $0 /path/to/home-server"
    exit 1
fi
TARGET="$1"
ln -sf "$(pwd)/ansible.cfg" "$TARGET/ansible.cfg"
ln -sf "$(pwd)/vault-pass.txt" "$TARGET/vault-pass.txt"
ln -sf "$(pwd)/inventories/inventory.yml" "$TARGET/inventories/inventory.yml"
ln -sf "$(pwd)/inventories/group_vars/all.yml" "$TARGET/inventories/group_vars/all.yml"
echo "Symbolic links created successfully"
EOF
chmod +x setup-links.sh

# Commit and push
git add .
git commit -m "Initial private configuration structure"
git push
```

### 3. Create Ansible Vault Password

```bash
# Generate a strong password
openssl rand -base64 32 > vault-pass.txt
chmod 600 vault-pass.txt

# IMPORTANT: Back this up securely (password manager, encrypted backup, etc.)
```

**Configure ansible.cfg to use vault password file:**

Edit `ansible.cfg` and ensure it contains:

```ini
[defaults]
vault_password_file = vault-pass.txt
```

This allows Ansible to automatically read the vault password without prompting. If you prefer to enter the password manually each time, you can omit this configuration and use `--ask-vault-pass` with each ansible-playbook command.

### 4. Configure Inventory

Edit `inventories/inventory.yml`:

```yaml
all:
  hosts:
    homeserver:  # Choose a descriptive name
      ansible_connection: ssh
      ansible_host: 192.168.1.100  # Your server's IP
      ansible_user: your-username
      # For SSH key authentication (recommended):
      ansible_ssh_private_key_file: ~/.ssh/id_rsa
      
      # For password authentication (encrypt first):
      # ansible_ssh_pass: !vault |
      #   $ANSIBLE_VAULT;1.1;AES256
      #   ...encrypted...
      
      # Sudo password (if required):
      # ansible_become_pass: !vault |
      #   $ANSIBLE_VAULT;1.1;AES256
      #   ...encrypted...
  
  vars:
    my_ipv6_network: 2001:db8::/64  # Your IPv6 prefix (if applicable)

docker_server:
  hosts:
    homeserver:

backup:
  hosts:
    homeserver:
      restic_repo: '/mnt/backup/restic'
      backup_day: '*'  # Daily
      backup_hour: 3
      backup_minute: 0
      # For S3 backups:
      # aws_access_key_id: !vault |
      # aws_secret_access_key: !vault |
```

**Encrypting passwords:**

```bash
# Encrypt SSH password
ansible-vault encrypt_string 'your-ssh-password' --name 'ansible_ssh_pass'

# Encrypt sudo password
ansible-vault encrypt_string 'your-sudo-password' --name 'ansible_become_pass'

# Copy the output (including the !vault | line) into your inventory.yml
```

### 5. Configure Global Variables

Edit `inventories/group_vars/all.yml`:

#### **Essential Variables**

```yaml
# Admin email for notifications and Let's Encrypt
admin_mail: "admin@example.com"

# Domain configuration
duckdns_subdomain: your-subdomain
app_domain_name: "{{ duckdns_subdomain }}.duckdns.org"

# Docker volume configuration
docker_volumes_path: /opt  # Base path for all Docker volumes
docker_volume_device: /dev/sda2  # Optional: specific device to mount

# DuckDNS token (get from https://www.duckdns.org/)
traefik_duckdns_token: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...encrypt using ansible-vault...

traefik_email: "{{ admin_mail }}"
```

**Get DuckDNS Token:**
1. Visit https://www.duckdns.org/
2. Sign in with your preferred method
3. Copy your token
4. Encrypt it: `ansible-vault encrypt_string 'your-token' --name 'traefik_duckdns_token'`

#### **Email Configuration** (for notifications)

```yaml
kresus_email_from: notifications@example.com
kresus_email_host: smtp.example.com
kresus_email_port: 587
kresus_email_user: notifications@example.com
kresus_email_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...encrypted password...
```

#### **Service-Specific Tokens**

```yaml
# Nextcloud exporter authentication
nextcloud_exporter_auth_token: !vault |
  # Generate with: openssl rand -base64 32

# Grafana OAuth (if using Authentik SSO)
# Client ID/secret are auto-generated by the playbook and stored on the server.
# No manual configuration is required.
```

### 6. Test Ansible Connection

Before testing, ensure your authentication is set up:
- SSH key added to ssh-agent (if using key authentication): `ssh-add ~/.ssh/homeserver_ed25519`
- Vault password file configured in `ansible.cfg`, or be ready to use `--ask-vault-pass`

```bash
# Test connectivity
ansible all -m ping

# If you didn't configure vault_password_file in ansible.cfg:
ansible all -m ping --ask-vault-pass

# Expected output:
# homeserver | SUCCESS => {
#     "changed": false,
#     "ping": "pong"
# }

# Test sudo access
ansible all -m shell -a "sudo whoami" --become

# Expected output: root
```

## Service-Specific Configuration

### Docker

No additional configuration required. The role handles:
- Docker installation
- Daemon configuration (IPv6, log drivers, insecure registries)
- Volume mounting (if `docker_volume_device` is specified)
- Network configuration (ndppd for IPv6)

### Traefik

Automatically configured with:
- Let's Encrypt ACME for SSL
- DuckDNS DNS challenge
- Dashboard at https://traefik.yourdomain.com

### Nextcloud

**Version**: Configured in `inventories/group_vars/all.yml`:

```yaml
nextcloud_version: 32  # Adjust as needed
```

**Email settings** (uses kresus email configuration by default):

```yaml
nextcloud_mail_from: "{{ kresus_email_from }}"
nextcloud_mail_smtphost: "{{ kresus_email_host }}"
nextcloud_mail_smtpport: 465
nextcloud_mail_smtpname: "{{ kresus_email_user }}"
nextcloud_mail_smtppwd: "{{ kresus_email_password }}"
```

**TURN Server Secret** (for Nextcloud Talk):

The TURN server requires a secret for authentication. This is stored as a Docker secret file and must be created before deployment:

```bash
# Generate a secure random secret (64 characters recommended)
openssl rand -hex 32

# On the target server, create the secret file
# Replace {{ docker_volumes_path }} with your actual path (e.g., /opt)
echo -n 'YOUR_GENERATED_SECRET' > {{ docker_volumes_path }}/secrets/turn_secret
chmod 600 {{ docker_volumes_path }}/secrets/turn_secret
```

**Important**: Never commit the TURN secret to your repository. The secret is referenced in the docker-compose template but stored securely on the server.

### Home Assistant

**Default services included**:
- Home Assistant Core
- Mosquitto MQTT (with authentication)
- Zigbee2MQTT
- ESPHome
- Frigate NVR
- EnOcean2MQTT
- MyElectricalData

**Configuration files location** (after deployment):
- Home Assistant: `/opt/homeassistant/homeassistant/`
- Zigbee2MQTT: `/opt/homeassistant/zigbee2mqtt/data/configuration.yaml`
- Frigate: `/opt/homeassistant/frigate_config/config.yaml`

### Authentik

SSO and authentication provider. After deployment:

1. Access at https://authentik.yourdomain.com
2. Initial admin setup will be prompted
3. Configure OAuth providers for other services

### Monitoring

Includes:
- Grafana: https://grafana.yourdomain.com
- Prometheus
- Node Exporter
- cAdvisor
- Nextcloud Exporter

### Backup System

**Local Backup**:

```yaml
restic_repo: '/mnt/backup/restic'
```

**S3-Compatible Backup** (Wasabi, Backblaze B2, AWS S3):

```yaml
restic_repo: 's3:s3.wasabisys.com/your-bucket-name/restic'
aws_access_key_id: !vault | ...
aws_secret_access_key: !vault | ...
```

## First Deployment

### 0. Prepare Authentication

Before running any Ansible playbooks, set up your authentication:

#### SSH Key Passphrase (if using SSH keys)

If your SSH key is password-protected, add it to ssh-agent to avoid entering the passphrase multiple times:

```bash
# Start ssh-agent
eval $(ssh-agent)

# Add your SSH key (will prompt for passphrase once)
ssh-add ~/.ssh/homeserver_ed25519
# Enter passphrase for /home/user/.ssh/homeserver_ed25519: ****

# Verify key is loaded
ssh-add -l
```

Now all Ansible commands will use your key without prompting for the passphrase.

#### Ansible Vault Password

You have two options for providing the vault password:

**Option 1: Use vault password file (recommended)**

If you configured `vault_password_file` in your `ansible.cfg`:

```ini
[defaults]
vault_password_file = vault-pass.txt
```

Ansible will automatically read the password from this file. No additional flags needed:

```bash
ansible-playbook playbooks/install.yml
```

**Option 2: Prompt for vault password**

If you don't have a vault password file configured, use the `--ask-vault-pass` flag:

```bash
ansible-playbook playbooks/install.yml --ask-vault-pass
# Vault password: ****
```

**Security Note**: The vault password file (`vault-pass.txt`) should:
- Have restrictive permissions: `chmod 600 vault-pass.txt`
- Be listed in `.gitignore` (never commit it!)
- Be backed up securely (password manager, encrypted backup)

### 1. Dry Run (Check Mode)

```bash
# See what would change without making changes
ansible-playbook playbooks/install.yml --check --diff

# Or with vault password prompt (if not using vault-pass.txt)
ansible-playbook playbooks/install.yml --check --diff --ask-vault-pass
```

### 2. Deploy Core Services First

```bash
# Deploy Docker foundation
ansible-playbook playbooks/install.yml --tags docker

# Deploy Traefik (reverse proxy)
ansible-playbook playbooks/install.yml --tags traefik

# Verify Traefik is working
# Check: https://traefik.yourdomain.com
```

**Note**: If using `--ask-vault-pass`, add it to each command:
```bash
ansible-playbook playbooks/install.yml --tags docker --ask-vault-pass
```

### 3. Deploy Additional Services

```bash
# Deploy all services
ansible-playbook playbooks/install.yml

# Or deploy selectively
ansible-playbook playbooks/install.yml --tags nextcloud
ansible-playbook playbooks/install.yml --tags hassio
ansible-playbook playbooks/install.yml --tags monitoring
```

## Post-Deployment Tasks

### 1. Verify Services

Check that services are running:

```bash
# SSH into server
ssh your-username@your-server-ip

# Check Docker containers
docker ps

# Check specific service logs
docker-compose -f /opt/nextcloud/docker-compose.yml logs
docker-compose -f /opt/homeassistant/docker-compose.yml logs
```

### 2. Initial Service Configuration

#### Nextcloud

1. Access https://nextcloud.yourdomain.com
2. Create admin account
3. Run the post-installation commands (if needed):

```bash
cd /opt/nextcloud
docker-compose exec -u www-data nextcloud php occ db:add-missing-indices
docker-compose exec -u www-data nextcloud php occ db:convert-filecache-bigint
```

#### Authentik

1. Access https://authentik.yourdomain.com
2. Follow initial setup wizard
3. Configure OAuth providers for Grafana/other services

#### Home Assistant

1. Access https://ha.yourdomain.com
2. Follow onboarding wizard
3. Configure integrations for your devices

#### Grafana

1. Access https://grafana.yourdomain.com
2. Default credentials: admin/admin (change immediately)
3. Import dashboards from https://grafana.com/grafana/dashboards/

### 3. Test Backups

```bash
# Run backup check playbook
ansible-playbook playbooks/CheckBackup.yml

# Manually test restore (on server)
restic -r /mnt/backup/restic snapshots
restic -r /mnt/backup/restic restore latest --target /tmp/restore-test
```

### 4. SSL Certificate Verification

Check that Let's Encrypt certificates are working:

```bash
# Should show valid certificate
curl -vI https://nextcloud.yourdomain.com 2>&1 | grep -i "SSL certificate verify ok"
```

## Troubleshooting

### Connection Issues

**Problem**: `ansible all -m ping` fails

```bash
# Check SSH connectivity manually
ssh -v your-username@your-server-ip

# Verify inventory file syntax
ansible-inventory --list

# Test with explicit inventory
ansible -i inventories/inventory.yml all -m ping
```

### Vault Password Issues

**Problem**: "Decryption failed"

```bash
# Verify vault-pass.txt exists and is readable
cat vault-pass.txt

# Test decryption
ansible-vault view inventories/group_vars/all.yml

# Re-encrypt if password changed
ansible-vault rekey inventories/group_vars/all.yml
```

### Docker Issues

**Problem**: Containers won't start

```bash
# SSH into server
ssh your-username@your-server-ip

# Check Docker daemon
sudo systemctl status docker

# Check specific container logs
docker logs <container-name>

# Check compose file
cd /opt/nextcloud
docker-compose config  # Validates compose file
```

### Certificate Issues

**Problem**: Let's Encrypt rate limits or failures

```bash
# Check Traefik logs
docker logs traefik

# Verify DNS is pointing to your server
nslookup yourdomain.duckdns.org

# Test DuckDNS token
curl "https://www.duckdns.org/update?domains=yourdomain&token=YOUR_TOKEN&ip="
```

### Port Conflicts

**Problem**: "Port already in use"

```bash
# Check what's using a port
sudo netstat -tlnp | grep :PORT
sudo lsof -i :PORT

# Stop conflicting service
sudo systemctl stop service-name
```

## Maintenance

### Regular Updates

```bash
# Update all packages
ansible-playbook playbooks/upgrade-packages.yml

# Update specific service
ansible-playbook playbooks/install.yml --tags nextcloud
```

### Backup Verification

```bash
# Check backup status
ansible-playbook playbooks/CheckBackup.yml

# Manual backup test
ssh your-server
restic -r /your/backup/path snapshots
```

### Monitoring

- Check Grafana dashboards regularly
- Review Docker container health
- Monitor disk space
- Check backup logs

## Next Steps

- Configure additional integrations in Home Assistant
- Set up Grafana dashboards for your needs
- Configure Authentik OAuth for other services
- Set up additional monitoring targets
- Customize Nextcloud apps and configurations
- Review and adjust firewall rules
- Set up regular maintenance schedules

## Getting Help

- Check service-specific logs: `docker logs <container>`
- Review Ansible output for errors
- Check GitHub issues
- Consult official documentation for each service

---

**Remember**: Always test changes in a staging environment or with `--check` mode first!
