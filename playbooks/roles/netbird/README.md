# NetBird VPN Role

This role deploys NetBird, an open-source VPN solution. Its dashboard and management server use NetBird's embedded OIDC issuer by default; Authentik is not connected as an external identity provider automatically.

## Overview

NetBird is a modern VPN/mesh networking solution that:
- Works peer-to-peer without VPN server overhead
- Supports multiple platforms (Linux, macOS, Windows, iOS, Android)
- Supports adding Authentik as an external OIDC provider after initial setup
- Zero-trust network architecture
- Built-in firewall rules and access control

## Stack Architecture

```
Internet → NetBird Management API (Port 443)
           ↓
        NetBird Signal Server (UDP)
           ↓
        NetBird Relay Server (STUN/TURN)

NetBird Dashboard/Management → embedded OIDC by default
                            → Authentik (optional external OIDC provider)
```

## Components

### NetBird Management Server
- API server for peer management
- OIDC authentication using NetBird's embedded issuer by default
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
- **docker** role - Container runtime
- **traefik** role - Reverse proxy for Management API

## Usage

### Initial setup and Authentik OIDC

1. Deploy the role and open the NetBird management web page at `https://vpn.{{ app_domain_name }}`.
2. Use NetBird's internal initialization flow to create the first administrator account.
3. Sign in with that account and add Authentik as an external OIDC provider in the management interface.

The role does not automatically connect NetBird to Authentik. Its dashboard and management server are configured to use NetBird's embedded OIDC issuer (`https://vpn.{{ app_domain_name }}/oauth2/`). If `authentik_api_token` is defined, Ansible may create the corresponding Authentik provider and application, but that does not replace the NetBird administrator initialization or adding the external provider in NetBird.

After completing setup, sign in through the configured provider and install the NetBird client.

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
