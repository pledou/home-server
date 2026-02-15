# Kresus Role

This role deploys Kresus for personal finance management and banking aggregation.

## Dependencies

This role requires the following roles to be executed first:
- **authentik** - Provides SSO/authentication services

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: kresus
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags kresus
```
