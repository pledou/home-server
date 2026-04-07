# Home Server Ansible Configuration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/pledou/home-server/workflows/CI/badge.svg?branch=master)](https://github.com/pledou/home-server/actions/workflows/ci.yml)
[![Security Scan](https://img.shields.io/badge/security-scanned-brightgreen)](https://github.com/pledou/home-server/actions/workflows/ci.yml)
[![Renovate enabled](https://img.shields.io/badge/renovate-enabled-%231473e6)](https://github.com/renovatebot/renovate)
[![Renovate PRs](https://img.shields.io/github/issues-pr/pledou/home-server?label=renovate%20updates&author=renovate&logo=renovatebot)](https://github.com/pledou/home-server/pulls?q=author:renovate)

An Infrastructure-as-Code solution for deploying and managing a self-hosted home server environment using Ansible. This setup provides automated deployment of multiple containerized services including cloud storage, home automation, monitoring, authentication, and more.

## 🚀 Features

This Ansible playbook automates the deployment of:

- **🐳 Docker Infrastructure** - Container runtime with optimized daemon configuration
- **🌐 Traefik** - Reverse proxy with automatic Let's Encrypt SSL certificates and DuckDNS integration
- **☁️ Nextcloud** - Self-hosted cloud storage and collaboration platform (v32)
- **🏠 Home Assistant** - Home automation platform with:
  - Mosquitto MQTT broker
  - Zigbee2MQTT
  - ESPHome
  - Frigate NVR
  - MyElectricalData integration
- **🔐 Authentik** - Identity provider and SSO solution
- **📊 Monitoring Stack** - Comprehensive observability with Grafana, Prometheus, and exporters
- **💰 Kresus** - Personal finance management
- **🔋 NUT (Network UPS Tools)** - UPS monitoring and management
- **🤖 AI Stack** - Ollama and Open WebUI for local LLM deployment
- **📦 GitLab** - Self-hosted Git repository and CI/CD
- **💾 Backup System** - Automated backups with Restic to local and S3-compatible storage
- **🔔 DIUN** - Docker image update notifications
- **🔒 VPN** - strongSwan IKEv2/EAP-RADIUS with FreeRADIUS and Authentik user auth (no extra client software — uses OS built-in IKEv2)

## 📋 Prerequisites

- **Target System**: Ubuntu/Debian-based Linux server
- **Control Machine**: Linux/macOS with Ansible installed
- **Requirements**:
  - Ansible 2.9+ (with `ansible-vault` support)
  - SSH access to target server
  - Python 3.8+ on both control and target machines
  - Domain name (DuckDNS recommended for dynamic DNS)
  - Storage device for Docker volumes (recommended: separate disk/partition)

## 🏗️ Architecture

```
Internet → DuckDNS → Traefik (Port 80/443)
                       ↓
    ┌──────────────────┼──────────────────┐
    ↓                  ↓                  ↓
Nextcloud      Home Assistant      Authentik (SSO)
    ↓                  ↓                  ↓
PostgreSQL         MQTT Broker       Monitoring
    ↓                  ↓                  ↓
[Additional Services]
```

## 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/home-server.git
cd home-server
```

### 2. Set Up Private Configuration

This repository uses **template files** for sensitive configuration. You need to create your actual configuration files:

#### Option A: Manual Setup

```bash
# Copy template files
cp ansible.cfg.example ansible.cfg
cp inventories/inventory.example.yml inventories/inventory.yml
cp inventories/group_vars/all.example.yml inventories/group_vars/all.yml

# Create vault password file
echo "your-secure-vault-password" > vault-pass.txt
chmod 600 vault-pass.txt
```

#### Option B: Use Private Data Repository (Recommended)

If you have a separate private repository with your configuration:

```bash
# Clone your private data repo
git clone https://github.com/YOUR_USERNAME/home-server-private-data.git

# Run the setup script
cd home-server-private-data
./setup-links.sh /path/to/home-server
```

### 3. Configure Your Inventory

Edit [`inventories/inventory.yml`](inventories/inventory.yml) with your server details:

```yaml
all:
  hosts:
    your-server:
      ansible_connection: ssh
      ansible_host: YOUR_SERVER_IP
      ansible_user: YOUR_SSH_USER
      # Recommended: SSH key authentication
      ansible_ssh_private_key_file: ~/.ssh/your_server_key
      # Or use password (less secure, must be encrypted):
      # ansible_ssh_pass: !vault |
      #   # Encrypt with: ansible-vault encrypt_string 'your-password' --name 'ansible_ssh_pass'
```

**Security Note**: SSH key authentication is strongly recommended. See [SETUP.md](SETUP.md#4-set-up-ssh-key-authentication-recommended) for detailed SSH key setup instructions.

### 4. Configure Variables

Edit [`inventories/group_vars/all.yml`](inventories/group_vars/all.yml) to customize:

- **Email Settings**: Admin email, SMTP configuration
- **Domain**: Your DuckDNS subdomain or custom domain
- **Paths**: Docker volumes location
- **Service Ports**: Custom port configurations
- **Secrets**: Encrypted tokens, passwords, API keys

**Important**: Use `ansible-vault` to encrypt sensitive values:

```bash
# Encrypt a string
ansible-vault encrypt_string 'your-secret-value' --name 'variable_name'

# Edit encrypted file
ansible-vault edit inventories/group_vars/all.yml
```

### 5. Customize Network Configuration (Optional)

If you need custom network settings, edit these template files:

- [`playbooks/templates/netplan.yml`](playbooks/templates/netplan.yml) - Static IP configuration
- [`playbooks/templates/dnsmasq.conf`](playbooks/templates/dnsmasq.conf) - DNS forwarding
- [`playbooks/templates/dhcpd.conf`](playbooks/templates/dhcpd.conf) - DHCP server settings

**Note**: These contain example IPs (192.168.21.x) - adjust for your network.

## 🚀 Usage

### Before Running Playbooks

**Authentication Setup:**

1. **SSH Key** (if using key authentication):
   ```bash
   eval $(ssh-agent)
   ssh-add ~/.ssh/your_server_key
   ```

2. **Vault Password**: Either configure `vault_password_file` in `ansible.cfg`:
   ```ini
   [defaults]
   vault_password_file = vault-pass.txt
   ```
   
   Or use `--ask-vault-pass` flag with each command.

See [SETUP.md](SETUP.md) for detailed authentication configuration.

### Full Installation

Deploy all services:

```bash
ansible-playbook playbooks/install.yml

# Or with vault password prompt (if vault_password_file not configured):
ansible-playbook playbooks/install.yml --ask-vault-pass
```

### Selective Deployment

Deploy specific components using tags:

```bash
# Docker and system preparation
ansible-playbook playbooks/install.yml --tags docker

# Web services
ansible-playbook playbooks/install.yml --tags traefik
ansible-playbook playbooks/install.yml --tags nextcloud

# Home automation
ansible-playbook playbooks/install.yml --tags hassio

# Authentication and monitoring
ansible-playbook playbooks/install.yml --tags authentik
ansible-playbook playbooks/install.yml --tags monitoring

# Backup system
ansible-playbook playbooks/install.yml --tags prep_backup

# AI services
ansible-playbook playbooks/install.yml --tags ia

# VPN only
ansible-playbook playbooks/install.yml --tags vpn

# All Docker applications
ansible-playbook playbooks/install.yml --tags docker-apps
```

### VPN (strongSwan IKEv2 + Authentik)

Stack: **strongSwan** (IKEv2 server) → **FreeRADIUS** (EAP-RADIUS) → **Authentik LDAP outpost** → **Authentik** users.

Native IKEv2 clients are built into Windows 10+, macOS/iOS, and most Android builds — no extra software needed.

#### One-time Authentik setup

1. Ensure `authentik_api_token` is set in your inventory (vault-encrypted).
2. Deploy the VPN role once: `ansible-playbook playbooks/install.yml --tags vpn`.
3. The role will create/update via Authentik API:
  - LDAP service account (default username: `ldapservice`)
  - LDAP provider (default name: `vpn-ldap-provider`)
  - LDAP outpost (default name: `vpn-ldap-outpost`)
4. Optional: create a `vpn-users` group in Authentik and add a FreeRADIUS group check to restrict VPN access.

#### Secrets

`vpn_radius_secret`, `vpn_authentik_ldap_outpost_token`, and `vpn_authentik_ldap_bind_password` are auto-generated by `playbooks/tasks/retrieve_password.yml` and persisted under `{{ docker_volumes_path }}/secrets/`.
The role then pushes `vpn_authentik_ldap_outpost_token` into Authentik through `/api/v3/core/tokens/{identifier}/set_key/` for the LDAP outpost token.

#### Connect from a client device

- **Server**: your `vpn_server_address`
- **Auth type**: IKEv2 / EAP (username + password)
- **Credentials**: Authentik username and password
- **Certificate**: import your Let's Encrypt CA if your device does not trust it automatically

### Maintenance Tasks

```bash
# Update all packages
ansible-playbook playbooks/upgrade-packages.yml

# Check backup status
ansible-playbook playbooks/CheckBackup.yml

# Run tests
ansible-playbook playbooks/test.yml
```

## 🔧 Configuration Details

### Docker Volumes

By default, volumes are stored at `/opt` but can be customized:

```yaml
# In inventories/group_vars/all.yml
docker_volumes_path: /opt
docker_volume_device: /dev/disk/by-id/YOUR_DISK_ID
```

### SSL Certificates

Traefik automatically manages Let's Encrypt certificates. Configure:

```yaml
traefik_email: your-email@example.com
traefik_duckdns_token: !vault | # Your DuckDNS token (encrypted)
app_domain_name: yourdomain.duckdns.org
```

### Backup Configuration

Restic backups support local and S3-compatible storage:

```yaml
backup:
  hosts:
    your-server:
      restic_repo: '/path/to/backup/location'
      backup_day: '*'
      backup_hour: 4
      backup_minute: 0
      aws_access_key_id: !vault | # For S3 backups
      aws_secret_access_key: !vault |
```

## 📁 Project Structure

```
.
├── ansible.cfg                 # Ansible configuration
├── inventories/               # Inventory and variables
│   ├── inventory.yml         # Server definitions
│   └── group_vars/
│       └── all.yml          # Global variables
├── playbooks/
│   ├── install.yml          # Main installation playbook
│   ├── roles/               # Service-specific roles
│   │   ├── authentik/      # SSO/Identity provider
│   │   ├── docker/         # Docker setup
│   │   ├── gitlab/         # GitLab installation
│   │   ├── hassio/         # Home Assistant stack
│   │   ├── ia/             # AI services (Ollama/WebUI)
│   │   ├── kresus/         # Finance management
│   │   ├── monitoring/     # Grafana/Prometheus
│   │   ├── nextcloud/      # Cloud storage
│   │   ├── nut/            # UPS monitoring
│   │   ├── prep_backup/    # Backup automation
│   │   ├── vpn/            # VPN (strongSwan IKEv2 + FreeRADIUS + Authentik)
│   │   └── traefik/        # Reverse proxy
│   └── tasks/              # Shared tasks
└── docs/                    # Additional documentation
```

## 🔒 Security Considerations

1. **Vault Password**: Keep `vault-pass.txt` secure and never commit it
2. **SSH Keys**: Use SSH key authentication instead of passwords when possible
3. **Firewall**: UFW rules are configured automatically, review for your needs
4. **Updates**: Regularly run `upgrade-packages.yml` to keep services updated
5. **Secrets Rotation**: Periodically rotate encrypted secrets in your vault
6. **Access Control**: Use Authentik SSO for centralized authentication

## 🐛 Troubleshooting

### Check Service Status

```bash
# On the target server
docker ps
docker-compose -f /opt/nextcloud/docker-compose.yml logs
```

### Verify Ansible Connection

```bash
ansible all -m ping
```

### Validate Playbook Syntax

```bash
ansible-playbook playbooks/install.yml --syntax-check
```

### Decrypt Vault Values

```bash
ansible-vault view inventories/group_vars/all.yml
```

## 📚 Additional Documentation

- [`SETUP.md`](SETUP.md) - Detailed setup guide
- [`docs/MCP_DEPLOYMENT_SUMMARY.md`](docs/MCP_DEPLOYMENT_SUMMARY.md) - MCP server deployment
- [`docs/PostgreSQL_Upgrade_System.md`](docs/PostgreSQL_Upgrade_System.md) - Database upgrade procedures

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Test changes thoroughly
4. Submit a pull request
5. **Never commit sensitive data** - use the `.example.yml` templates

## 📄 License

[Add your chosen license here - MIT, GPL-3.0, Apache-2.0, etc.]

## ⚠️ Security Policy

See [`SECURITY.md`](SECURITY.md) for information on reporting security vulnerabilities.

## 📧 Contact

For questions or support:
- Open an issue on GitHub
- [Add your contact method if desired]

---

**Note**: This is a self-hosted solution. You are responsible for securing your infrastructure, maintaining backups, and keeping software up to date.
