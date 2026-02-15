# Home Assistant Role

This role deploys Home Assistant (Hassio) for home automation.

## Dependencies

This role requires the following roles to be executed first:
- **authentik** - Provides SSO/authentication services

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: hassio
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags hassio
```
