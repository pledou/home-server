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
- Optional Coraza WAF sidecar with OWASP Core Rule Set, in detection-only mode

You can tune those limits with these variables:
- `traefik_security_hsts_seconds`
- `traefik_security_hsts_include_subdomains`
- `traefik_security_hsts_preload`
- `traefik_security_rate_average`
- `traefik_security_rate_burst`
- `traefik_security_rate_period`
- `traefik_security_inflight_amount`

Set `traefik_coraza_enabled: true` to run Coraza as a separate
ForwardAuth container using the prebuilt
[`ghcr.io/le0developer/traefik-waf`](https://github.com/Le0Developer/traefik-waf)
image (`{{ traefik_coraza_version }}`). The role downloads the Coraza
`v3.3.3` recommended configuration and clones OWASP CRS
`{{ traefik_coraza_crs_version }}` into the read-only rules volume.

Traefik sends request headers to the sidecar before forwarding requests.
Request bodies are not sent to Coraza, preserving streaming and large uploads;
response bodies are not inspected. Coraza runs in detection-only mode, so
detections are logged but do not block requests. View Coraza logs with
`docker compose logs coraza`; Traefik's JSON log remains at
`{{ traefik_coraza_log_path }}` for Wazuh collection. The sidecar only shares
an internal Docker network with Traefik.

The upstream image was last updated in January 2026 and has no GitHub releases;
its source repository has no published license. The role pins its published
`v0.1.2` image tag; confirm the upstream license/terms and maintenance status
before production use. To disable Coraza, set `traefik_coraza_enabled: false`;
this removes the sidecar and generated middleware configuration.

Do not enable blocking until detections have been reviewed and the rules have
been tuned for the applications behind Traefik.
