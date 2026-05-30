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

## Security Middlewares

The role enables a global HTTPS middleware chain applied to all Traefik HTTP routers on the `https` entrypoint:
- HSTS headers
- Request rate limiting
- Inflight request limiting

You can tune those limits with these variables:
- `traefik_security_hsts_seconds`
- `traefik_security_hsts_include_subdomains`
- `traefik_security_hsts_preload`
- `traefik_security_rate_average`
- `traefik_security_rate_burst`
- `traefik_security_rate_period`
- `traefik_security_inflight_amount`
