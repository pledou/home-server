# IA Role

This role deploys Immich (IA - Immich Application) for photo and video management.

## Dependencies

This role requires the following roles to be executed first:
- **authentik** - Provides SSO/authentication services

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: ia
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags ia
```
