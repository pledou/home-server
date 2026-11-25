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

## Authentication modes

### Single user (default)

Kresus runs in single-user mode: the first user created (via the web UI) is
the admin. No SSO header is configured.

### Multiple users via authentik header

Set `kresus_http_header_login: true` and provision users from Ansible:

```yaml
kresus_http_header_login: true
kresus_user_login_http_header: "X-authentik-email"  # use email when login is a mail
kresus_users:
  - login: "user@example.com"
    admin: true
  - login: "family@example.com"
```

Users are created with:
`docker exec -w /home/user kresus-kresus-1 ./app/bin/kresus create:user "<login>" [--admin]`
(already-existing users are skipped without failing the run).
