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
- Optional Coraza WAF sidecar with OWASP Core Rule Set in blocking mode

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
response bodies are not inspected. Coraza runs in blocking mode, so matching
disruptive CRS rules can reject requests. The role loads
`99-coraza-engine.conf` after the CRS rules to enable `SecRuleEngine On`.
At `WAF_VERBOSITY=1`, the image logs blocks only; it does not emit a concise
line for every rule match. Therefore an empty Coraza log does not prove that
requests were not inspected.
Docker sends the Coraza container's syslog output to
`{{ traefik_coraza_wazuh_log_path }}` through host rsyslog, and the Wazuh agent
collects that file when its security role is applied. The log destination can
be changed with `traefik_coraza_wazuh_log_path`. Disabling Coraza also removes
its rsyslog routing and log-rotation configuration. The sidecar only shares an
internal Docker network with Traefik.

The role sets `WAF_VERBOSITY=1` (the image default) to avoid verbose Coraza
debug/trace output. At this level, blocked requests are logged; increase the
verbosity to `4` only when detailed Coraza diagnostics are needed. Blocking
can interrupt legitimate requests if CRS produces false positives, so monitor
the application logs and Coraza log after deployment.

The upstream image was last updated in January 2026 and has no GitHub releases;
its source repository has no published license. The role pins its published
`v0.1.2` image tag; confirm the upstream license/terms and maintenance status
before production use. To disable Coraza, set `traefik_coraza_enabled: false`;
this removes the sidecar and generated middleware configuration.
