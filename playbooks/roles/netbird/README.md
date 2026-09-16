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

## Usage

### Web Dashboard

1. Navigate to `https://vpn.{{ app_domain_name }}`
2. Click "Login with Authentik"
3. Authenticate with your Authentik credentials
4. Accept consent screen
5. Download client configuration or install NetBird client

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
