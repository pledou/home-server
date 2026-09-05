# NetBird VPN Role

This role deploys NetBird, an open-source VPN solution with Authentik SSO integration via OIDC.

## Overview

NetBird is a modern VPN/mesh networking solution that:
- Works peer-to-peer without VPN server overhead
- Supports multiple platforms (Linux, macOS, Windows, iOS, Android)
- Integrates with Authentik via OIDC for user authentication
- Zero-trust network architecture
- Built-in firewall rules and access control

## Stack Architecture

```
Internet → NetBird Management API (Port 443)
           ↓
        NetBird Signal Server (Port 51820/UDP)
           ↓
        NetBird Relay Server (STUN/TURN)
           ↓
        Authentik OIDC Provider ← User Authentication
```

## Components

### NetBird Management Server
- API server for peer management
- OIDC integration with Authentik
- Admin dashboard
- Access control policies

### NetBird Signal Server
- Peer discovery and coordination
- NAT traversal assistance
- Connection establishment

### NetBird Relay Server
- STUN/TURN for peers behind NAT
- Encrypted relay for restricted networks
- Optional component (can run multiple relays)

## Dependencies

This role requires:
- **authentik** role - Provides OIDC authentication
- **docker** role - Container runtime
- **traefik** role - Reverse proxy for Management API

## Installation

### Full Installation

```bash
ansible-playbook playbooks/install.yml --tags netbird
```

### One-time Authentik Setup

1. Ensure `authentik_api_token` is set in your inventory (vault-encrypted)
2. Deploy the NetBird role: `ansible-playbook playbooks/install.yml --tags netbird`
3. The role will automatically create via Authentik API:
   - OIDC application
   - Service account for API calls
   - Access control provider

## Configuration

### Required Variables (in group_vars/all.yml)

```yaml
# NetBird Configuration
netbird_enabled: true
netbird_domain: "vpn.{{ app_domain_name }}"  # e.g., vpn.example.duckdns.org
netbird_admin_email: "admin@example.com"
netbird_oidc_client_id: "netbird"  # Auto-generated if not provided
# netbird_oauth_client_secret is generated at runtime by the shared
# authentik OAuth tasks (tasks/authentik_common.yml) — no vault needed.

# Authentik OIDC Provider (created automatically)
authentik_api_token: !vault |
  # Your Authentik API token
```

### Optional Variables

```yaml
# Signal Server Configuration
netbird_signal_port: 51820
netbird_signal_log_level: info  # debug, info, warning, error

# Relay Server Configuration
netbird_relay_enabled: false  # Set to true if running relay
netbird_relay_port: 3478

# Network Settings
netbird_network_cidr: "10.200.0.0/16"  # Virtual network range
netbird_dns_enabled: true
netbird_dns_servers:
  - "1.1.1.1"
  - "8.8.8.8"

# Security
netbird_peer_login_expiration: 24h
netbird_idp_sign_key_refresh_duration: 3600
```

## Usage

### Web Dashboard

1. Navigate to `https://vpn.{{ app_domain_name }}`
2. Click "Login with Authentik"
3. Authenticate with your Authentik credentials
4. Accept consent screen
5. Download client configuration or install NetBird client

### Command Line

#### Access Management Server
```bash
# SSH into server
ssh -i your-key user@your-server

# Check NetBird status
docker ps | grep netbird

# View logs
docker compose -f /opt/netbird/docker-compose.yml logs -f
```

### Client Installation

#### Linux
```bash
# Ubuntu/Debian
wget -q https://pkgs.netbird.io/linux/ubuntu/pubkey.asc -O - | sudo apt-key add -
echo 'deb https://pkgs.netbird.io/linux/ubuntu focal main' | sudo tee /etc/apt/sources.list.d/netbird.list
sudo apt update
sudo apt install netbird

# Connect
netbird up
```

#### macOS
```bash
brew install netbird
netbird up
```

#### Windows
- Download from https://releases.netbird.io/
- Run installer
- Login with your Authentik credentials

#### Mobile (iOS/Android)
- Download from App Store / Google Play
- Search for "NetBird"
- Login with your Authentik credentials

## Network Access Control

After connecting, configure firewall rules in NetBird dashboard:

1. Go to **Access Control** → **Rules**
2. Create new rule:
   ```yaml
   Name: Allow SSH
   Source Group: Everyone
   Destination Group: SSH Servers
   Protocol: TCP
   Port: 22
   Action: Accept
   ```

## DNS Configuration

NetBird provides split DNS:

1. Go to **Network** → **DNS**
2. Add custom domains:
   ```yaml
   Domain: internal.example.com
   Nameserver: 192.168.1.1
   ```
3. Clients automatically resolve via NetBird DNS

## User Groups

Create groups to organize access control:

1. Go to **Network** → **Groups**
2. Create group:
   ```yaml
   Name: vpn-users
   Members: Add via Authentik directory
   ```
3. Use in firewall rules for access control

## Troubleshooting

### Peer Cannot Connect

1. Check client logs: `netbird status`
2. Verify Authentik login successful
3. Check firewall rules allow peer-to-peer traffic
4. Enable relay server if peers are behind restrictive NAT

### DNS Not Resolving

1. Verify DNS settings in NetBird dashboard
2. Check client DNS settings: `netbird dns status`
3. Restart NetBird client: `netbird down && netbird up`

### Authentication Fails

1. Verify Authentik is running: `docker ps | grep authentik`
2. Check OIDC application in Authentik (settings → applications)
3. Verify callback URL matches: `https://vpn.{{ app_domain_name }}/auth/callback`
4. Check role logs: `docker compose -f /home/{{ ansible_user }}/home-server/stacks/netbird/docker-compose.yml logs -f`

### Performance Issues

1. Check signal server logs for errors
2. Monitor peer connections: `netbird status`
3. If many peers, consider enabling relay server
4. Adjust log level to `debug` for detailed diagnostics

## Security Considerations

### Access Control
- NetBird uses zero-trust model
- All access must be explicitly allowed
- Default deny all peer-to-peer connections
- Create explicit rules for required access

### Authentik Integration
- OIDC tokens have configurable expiration
- MFA should be enabled in Authentik for VPN access
- Service account is created with minimal permissions
- Regularly audit connected peers in dashboard

### Network Isolation
- NetBird creates isolated virtual network
- Can coexist with other VPN solutions
- No direct access to host unless explicitly configured

## Backup & Recovery

### Database Backup
NetBird stores configuration in SQLite database:
```bash
Docker volume: netbird_data
Location: /opt/netbird/data
```

Included in Restic backups (if prep_backup role enabled).

### Restore Configuration
```bash
# Stop NetBird
docker compose -f /opt/netbird/docker-compose.yml down

# Restore volume from backup
restic restore latest --target /

# Restart
docker compose -f /opt/netbird/docker-compose.yml up -d
```

## Monitoring

### Prometheus Metrics
NetBird exposes Prometheus metrics on `:9090/metrics`

Add to Grafana (monitoring role handles this):
- Peer connections count
- Data transfer rates
- Connection latency
- API request metrics

## Additional Resources

- [NetBird Documentation](https://netbird.io/docs)
- [NetBird GitHub](https://github.com/netbirdio/netbird)
- [Authentik OIDC Setup](https://goauthentik.io/docs/providers/oauth2/)
- [NetBird Self-Hosted Guide](https://netbird.io/docs/selfhosted/architecture)
