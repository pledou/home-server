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

## Timeout Configuration for AI/LLM Tasks

This role configures extended timeouts (3600s / 1 hour) to support long-running AI and LLM tasks:

### PHP-FPM Configuration
- **request_terminate_timeout**: 3600s (configurable via `nextcloud_php_fpm_request_terminate_timeout`)
- **Slow log**: Enabled at 60s threshold with 20-level stack traces
- **Config file**: `/usr/local/etc/php-fpm.d/zzz-docker.conf` (loads AFTER www.conf)

### nginx Configuration
- **fastcgi_read_timeout**: 3600s
- **fastcgi_send_timeout**: 3600s

### Nextcloud Apps
- **Context Chat**: 3600s (configurable via `nextcloud_context_chat_request_timeout`)
- **integration_openai**: 3600s (configurable via `nextcloud_integration_openai_request_timeout`)

### Rationale
Analysis of task execution history showed:
- 62% of tasks exceed 300s (old timeout)
- 26% of tasks exceed 600s (10 minutes)
- Maximum observed: 5,348s (89 minutes)
- Typical AI/LLM tasks: 10-25 minutes

These timeouts ensure AI tasks (text generation, summarization, context analysis) can complete without being prematurely terminated.

### Monitoring
Slow requests (>60s) are logged to `/var/log/php-fpm-slow.log` inside the container for debugging.
