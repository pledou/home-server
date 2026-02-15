# Monitoring Role

This role deploys a comprehensive monitoring stack using Docker Compose, including:
- **Prometheus** - Metrics collection and alerting evaluation
- **Alertmanager** - Alert routing and notification management
- **Grafana** - Metrics visualization and dashboards
- **Loki** - Log aggregation
- **Promtail** - Log collection agent
- **Node Exporter** - System metrics exporter
- **cAdvisor** - Container metrics exporter
- **Nextcloud Exporter** - Nextcloud-specific metrics

## Dependencies

This role requires the following roles to be executed first:
- **traefik** - Provides reverse proxy and SSL certificate management for Grafana
- **authentik** - Provides SSO authentication for Grafana and Alertmanager, dependency to authentik_backend network to request metrics from authentik

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: traefik
- role: monitoring
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags monitoring
```

## Alerting Configuration

The monitoring stack supports multi-channel alerting with intelligent fallback:

### Alert Channels (in priority order):
1. **Nextcloud Talk** (primary, optional) - Sends alerts to a Nextcloud Talk conversation
2. **Email** (fallback, always available) - Sends alerts via SMTP

### Alert Severity Levels

- **critical**: Highest priority alerts sent via email for maximum reliability
- **page**: Important alerts requiring immediate attention
- **warning**: Lower priority informational alerts

## Setting Up Alerting

### Email Alerting (Required)

Email alerting is configured automatically using your existing SMTP settings. Ensure these variables are set in your `group_vars/all.yml`:

```yaml
# Admin email to receive alerts
admin_mail: "admin@example.com"

# SMTP configuration (usually inherited from kresus_email_* vars)
alertmanager_email_to: "{{ admin_mail }}"
alertmanager_smtp_host: "{{ kresus_email_host }}"
alertmanager_smtp_port: 587
alertmanager_smtp_from: "{{ kresus_email_from }}"
alertmanager_smtp_user: "{{ kresus_email_user }}"
alertmanager_smtp_password: "{{ kresus_email_password }}"
alertmanager_smtp_require_tls: true
```

### Nextcloud Talk Alerting (Optional)

Nextcloud Talk provides real-time notifications through the Bot API. The Bot API requires HMAC-SHA256 signed requests, so we use a **webhook bridge bot** that receives simple webhooks from Alertmanager and forwards them to Nextcloud Talk with proper authentication.

#### Architecture

```
Alertmanager → Webhook Bot (Docker) → Nextcloud Talk Bot API
```

The webhook bot handles:
- HMAC-SHA256 signature generation (using auto-generated secret)
- Proper API headers (`X-Nextcloud-Talk-Bot-Random`, `X-Nextcloud-Talk-Bot-Signature`)
- Message formatting for Nextcloud Talk

#### Setup Process (Simplified - Auto-Generated Secrets!)

The bot secret is now **automatically generated and stored** by the playbook. You only need to configure the conversation token.

#### Step 1: Deploy to Auto-Install Bot

Run the playbook - it will automatically generate a bot secret and install the bot in Nextcloud:

```bash
ansible-playbook -i ../home-server-private-data/inventories/inventory.yml \
  playbooks/install.yml \
  --tags monitoring \
  --ask-vault-pass
```

The playbook will:
- Generate a secure random secret (stored in `/opt/secrets/alertmanager_nextcloud_bot_secret`)
- Install the "Prometheus Alerts" bot in Nextcloud with this secret
- Display the generated secret in the output

#### Step 2: Get Conversation Token

1. Open Nextcloud Talk and create or select a conversation for alerts
2. Note the **Conversation token** from the browser URL:
   - URL format: `https://cloud.example.com/call/CONVERSATION_TOKEN`
   - The token is the alphanumeric string after `/call/`

#### Step 3: Configure Conversation Token

Edit your `group_vars/all.yml` and add the conversation token:

```yaml
# Nextcloud Talk conversation token (from the URL after /call/)
alertmanager_nextcloud_conversation_token: "xhevvhbo"  # Replace with your conversation token from Step 2
```

Note: You do NOT need to configure `alertmanager_nextcloud_bot_secret` - it's auto-generated!

#### Step 4: Redeploy

Run the playbook again - it will automatically add the bot to your conversation:

```bash
ansible-playbook -i ../home-server-private-data/inventories/inventory.yml \
  playbooks/install.yml \
  --tags monitoring \
  --ask-vault-pass
```

Alerts will now be sent to your Nextcloud Talk conversation!

#### Step 3: Deploy the Configuration

```bash
ansible-playbook -i ../home-server-private-data/inventories/inventory.yml \
  playbooks/install.yml \
  --tags monitoring \
  --ask-vault-pass
```

### Testing Alerts

After deployment, you can test the alerting system:

1. **Access Alertmanager UI**: https://alertmanager.{{your_domain}}
2. **Access Prometheus UI**: https://prometheus.{{your_domain}}
3. **Create a test alert** by temporarily stopping a monitored service
4. Check that alerts appear in:
   - Alertmanager UI
   - Nextcloud Talk conversation (if configured)
   - Your email inbox

## Alert Rules

Alert rules are defined in `files/alerts.rules`. Current alerts include:

- **service_down**: Triggered when a monitored service is unreachable for >2 minutes
- **high_load**: Triggered when system load exceeds threshold

### Adding Custom Alerts

Edit `files/alerts.rules` to add custom alert rules:

```yaml
- alert: disk_space_low
  expr: node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"} < 0.1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Low disk space on {{ $labels.instance }}"
    description: "Filesystem {{ $labels.mountpoint }} has less than 10% space remaining"
```

## Troubleshooting

### Alerts Not Being Sent

1. **Check Alertmanager logs**:
   ```bash
   docker logs alertmanager
   ```

2. **Verify configuration**:
   ```bash
   sudo cat /opt/alertmanager-conf/config.yml
   ```

3. **Check Prometheus alerts**:
   Visit https://prometheus.{{your_domain}}/alerts to see pending/firing alerts

4. **Test bot manually**:
   ```bash
   # Test the webhook bot
   curl -X POST "http://localhost:81/send_message" \
     -H "Content-Type: application/json" \
     -d '{"message": "Test alert from Prometheus"}'
   
   # Or test directly via Nextcloud API (more complex, requires HMAC signing)
   # See: https://nextcloud-talk.readthedocs.io/en/latest/bots/#sending-a-chat-message
   ```

### Email Issues

- Verify SMTP credentials are correct
- Check that port 587 (or your SMTP port) is not blocked
- Review Grafana email settings (similar config) to ensure base SMTP setup works
- Test with: `docker exec alertmanager wget -O- localhost:9093/-/healthy`

### Nextcloud Talk Bot Not Working

- **Check bot installation**: 
  ```bash
  docker exec nc-nextcloud-1 php occ talk:bot:list
  ```
  Should show "Prometheus Alerts" bot
- **Check auto-generated secret**: 
  ```bash
  sudo cat /opt/secrets/alertmanager_nextcloud_bot_secret
  ```
  The secret is automatically generated and stored here
- **Check playbook output**: Look for "Install Nextcloud Talk bot for alerts" task results
- **Verify bot is in conversation**: Check Nextcloud Talk → Conversation → Settings → Bots
- **Check webhook bot logs**: `docker logs nextcloud-talk-bot`
- **Verify conversation token**: Ensure `alertmanager_nextcloud_bot_token` is set in your `all.yml`
- **Check Nextcloud logs**: `docker logs nc-nextcloud-1`
- **Test the webhook bot**: Use the curl command from the testing section above
- **Nextcloud Talk version**: Bot API requires Nextcloud Talk/Spreed 17.1+ (Nextcloud 27.1+)
- **Reinstall bot manually** if needed:
  ```bash
  docker exec nc-nextcloud-1 php occ talk:bot:uninstall "Prometheus Alerts"
  # Then redeploy with ansible
  ```

## Configuration Files

- `templates/prometheus.yml` - Prometheus configuration
- `templates/alertmanager-config.yml` - Alertmanager routing and receivers
- `files/alerts.rules` - Alert rule definitions
- `templates/docker-compose.yml` - Stack deployment
- `defaults/main.yml` - Default variables

## Access URLs

After deployment (replace `{{your_domain}}` with your actual domain):

- **Grafana**: https://grafana.{{your_domain}}
- **Prometheus**: https://prometheus.{{your_domain}}
- **Alertmanager**: https://alertmanager.{{your_domain}}

All services are protected by Authentik SSO authentication.

## Resources

- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [Nextcloud Talk Bot API](https://nextcloud-talk.readthedocs.io/en/latest/bots/)
- [Nextcloud Talk OCC Commands](https://nextcloud-talk.readthedocs.io/en/latest/occ/#talkbotinstall)
- [Nextcloud Talk Webhook Bot (Bridge)](https://github.com/weichwaren-schmiede/nextcloud-talk-webhook-bot)
