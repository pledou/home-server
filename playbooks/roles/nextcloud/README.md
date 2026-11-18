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

## Nextcloud MCP backend

The role supports two MCP implementations:

- `nextcloud_mcp_backend: existing` (default) keeps the Nextcloud `mcp_connector`
  ExApp as the backend.
- `nextcloud_mcp_backend: standalone` deploys
  [`nextcloud-mcp-server`](https://github.com/cbcoutinho/nextcloud-mcp-server)
  behind Traefik at `https://mcp.<app_domain_name>/mcp`.

### Open WebUI configuration: existing connector

In Open WebUI, add the following MCP server under **Admin → Tools → MCP Servers**
when `nextcloud_mcp_backend` is `existing`:

| Setting | Value |
|---|---|
| Type | MCP Streamable HTTP |
| Username | Nextcloud |
| Connection ID | `nextcloud` |
| Description | Nextcloud MCP Connector |
| URL | `https://<app_domain_name>/exapps/mcp_connector/mcp` |
| Authentication | Oauth 2.1 |

### Open WebUI configuration: standalone server

When `nextcloud_mcp_backend` is `standalone`, add a separate MCP connection in
Open WebUI (**Admin → Tools → MCP Servers**). Do not reuse the existing
connector's URL or OAuth scope values:

| Setting | Value |
|---|---|
| Type | MCP Streamable HTTP |
| Name | Nextcloud (standalone) |
| Connection ID | `nextcloud-std` |
| Description | Standalone Nextcloud MCP server |
| URL | `https://mcp.<app_domain_name>/mcp` |
| Authentication | OAuth 2.1 |
| OAuth scopes | Request only the Nextcloud app scopes you want to enable, such as `files.read`, `notes.read`, or `calendar.read`; add write scopes only when needed. `offline_access` is optional for refresh tokens. |

Save the connection and authorize it when Open WebUI prompts you. The browser
flow authenticates you with the configured OIDC provider. On first use, the
MCP server may also ask you to complete Nextcloud Login Flow v2 to create a
revocable app password for your own Nextcloud account. Open WebUI does not need
your Nextcloud password or app password.

The scope names differ from the existing connector. Available scope names are
published by the standalone server at
`https://mcp.<app_domain_name>/.well-known/oauth-protected-resource/mcp`
in `scopes_supported`. The OIDC client configured on Nextcloud must be allowed
to issue the requested app scopes (as well as `openid`, `profile`, and `email`);
otherwise authentication may succeed while the server hides tools whose
scopes were not granted.

The standalone mode uses Nextcloud Login Flow v2 and a dedicated static OIDC
client for the server itself. 

The [IA role](../ia/README.md) deploys the standalone server and automatically
generates and persists its token-encryption key.

Switch the backend in `inventories/group_vars/all.yml`:

```yaml
nextcloud_mcp_backend: standalone
```

Then configure Open WebUI under **Admin → Tools → MCP Servers** to use the
selected endpoint. The role does not edit Open WebUI's saved MCP connections,
so update that URL in the UI when switching backends. Selecting `standalone`
disables the existing `mcp_connector` ExApp; selecting `existing` removes the
standalone container and re-enables the ExApp. Neither mode deletes the other
backend's persistent data.

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
## Preview Generation Configuration

Preview generation is a resource-intensive operation that can cause PHP-FPM worker exhaustion if not properly limited. This role configures reasonable limits to prevent system overload while maintaining good user experience.

### Configuration

The following limits are configured in `nextcloud_system_config`:
- **preview_max_x**: 2048 pixels (maximum preview width)
- **preview_max_y**: 2048 pixels (maximum preview height)
- **preview_max_scale_factor**: 1 (no upscaling)
- **preview_max_filesize_image**: 50 MB (maximum file size for preview generation)

### Enabled Preview Providers

The role enables 21 preview providers by default, including:
- **Images**: PNG, JPEG, GIF, BMP, XBitmap, TIFF, SVG
- **Documents**: PDF, MarkDown, TXT, MSOffice (2003/2007/Doc), OpenDocument, StarOffice
- **Media**: MP3, Movie
- **Graphics**: Illustrator, Photoshop, Postscript, Font

**Note**: Heavy formats like Movie, PDF, and Office documents can cause significant CPU load during preview generation. The file size limit (`preview_max_filesize_image`) prevents processing of very large files.

### Preview Generation Schedule

**Pre-generation is DISABLED by default** (`nextcloud_preview_pregenerate_cron: ""`).

**Why disabled:**
With a large media library (50k+ files), the cron job `preview:pre-generate` can saturate all PHP-FPM workers when trying to process thousands of files simultaneously. This causes:
- All 48 PHP-FPM workers occupied with preview generation
- Normal user requests blocked (502/504 errors)
- epoll errors and container freeze
- System appears unresponsive despite adequate CPU/RAM resources

**Alternative approaches:**
1. **On-demand generation** (default): Previews generated when users access files - slower first load but no worker saturation
2. **Manual pre-generation**: Run during maintenance windows when users aren't active:
   ```bash
   docker exec nc-nextcloud-1 php occ preview:pre-generate
   ```
3. **Scheduled during low-usage**: If you want automatic pre-generation, schedule it once daily at night:
   ```
   nextcloud_preview_pregenerate_cron: "0 3 * * * cd /var/www/html && flock -n /tmp/preview-pregenerate.lock timeout 6h php -f occ preview:pre-generate"
   ```
   
**Note**: The original schedule (every 30 minutes) was identified as the root cause of container freezes on 2026-06-10.

### Common Issues

**Symptom**: PHP-FPM workers exhaust (48/48 busy), epoll errors, container freeze  
**Cause**: `preview:pre-generate` cron running too frequently on large media libraries (50k+ files)  
**Solution**: Disable pre-generation cron (default) or run manually during maintenance windows

**Symptom**: Slow first-time file access in web UI  
**Cause**: On-demand preview generation for large files  
**Solution**: This is expected with on-demand generation. Consider manual pre-generation during off-peak hours.

**Symptom**: High CPU usage during preview generation  
**Cause**: Processing heavy file formats (videos, large PDFs, Office documents)  
**Solution**: The file size limit (`preview_max_filesize_image: 50`) already prevents processing of very large files.
