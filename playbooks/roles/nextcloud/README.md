# Nextcloud Role

This role deploys Nextcloud for file sharing, collaboration, and cloud storage.

## Dependencies

This role requires the following roles to be executed first:
- **traefik** - Provides reverse proxy and SSL certificate management

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: traefik
- role: nextcloud
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags nextcloud
```
