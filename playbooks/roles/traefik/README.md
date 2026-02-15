# Traefik Role

This role deploys Traefik as a reverse proxy with automatic SSL certificate management via Let's Encrypt.

## Dependencies

This role requires the following roles to be executed first:
- **authentik** - Provides SSO/authentication services for Traefik dashboard

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: traefik
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags traefik
```
