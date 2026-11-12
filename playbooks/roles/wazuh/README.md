# Wazuh role

This role deploys the official Wazuh Docker single-node stack: manager, indexer,
and dashboard. It pins the upstream `wazuh-docker` repository to the release in
`defaults/main.yml`, generates the official node certificates, and keeps
deployment configuration under `/opt/wazuh` by default. Local-safe runs use
`{{ stacks_base_path }}/wazuh`. Generated certificates are in
`/opt/wazuh/single-node/config/wazuh_indexer_ssl_certs`. Stack data is stored
in named Docker volumes.

## Requirements

- Deploy Docker and Traefik first. Traefik must serve the `traefik_backend`
  Docker network and have a certificate resolver named `le`.
- Allow inbound TCP ports `1514` and `1515` from systems that will enroll Wazuh
  agents. The role publishes these ports for agent traffic. It does not expose
  the Wazuh indexer API or manager API on the host.
- The Wazuh indexer requires `vm.max_map_count` of at least `262144`; the role
  configures this persistently. Its default JVM heap is 1 GiB.
- Provide enough memory and disk for the indexer and its data. Wazuh recommends
  at least 4 GiB of RAM for a single-node deployment.

## Deployment

Run the normal deployment playbook with the Wazuh tag:

```bash
ansible-playbook playbooks/install.yml --tags wazuh
```

Test password-hash generation with a disposable password:

```bash
ansible-playbook playbooks/test.yml --tags wazuh_hash_test
```

The Wazuh dashboard is available at `https://wazuh.<app_domain_name>`. It uses
Wazuh's built-in login; it is not wrapped in Authentik forward authentication.
The manager API and indexer remain reachable only on the private Docker network.

The role generates unique credentials and stores them, root-readable only, below
`{{ docker_volumes_path }}/secrets`. It also stores bcrypt hashes and password
fingerprints for indexer users there so repeated deployments are stable. To
rotate an indexer user's credential, remove that password, `.hash`, and
`.fingerprint` files with the same base name from the secrets directory before
rerunning the role. To rotate the API credential, remove `wazuh_api_password`.
The matching internal indexer configuration is reapplied when an indexer user
password changes. The pinned upstream checkout is only refreshed when
`wazuh_version` changes, so role-owned configuration is not reset on each run.

## Host agent and notifications

The `security` role installs the matching Wazuh agent package on Debian-family
hosts by default. Run `ansible-playbook playbooks/security-hardening.yml` after
the Wazuh manager is up; the local agent connects to `127.0.0.1`. Override
`security_wazuh_agent_manager_address` when the manager is on another host, or
set `security_wazuh_agent_enabled: false` to disable agent installation. The
host agent always enables the Docker listener and installs its Python Docker
API dependencies from system packages, avoiding conflicts with Debian-managed
Python libraries. The Traefik role configures rsyslog to route Coraza sidecar
logs to `traefik_coraza_wazuh_log_path` (default `/var/log/traefik/coraza.log`).
When the Wazuh agent is enabled, the security role configures it to collect
that file. Apply the Traefik role to set up log routing and redeploy the stack,
then apply the security role to enable collection.

The manager forwards alerts at level 10 or higher to the existing Alertmanager
API. Alertmanager then delivers them using the configured Nextcloud Talk
receiver (or email when Talk is not configured). The manager and Alertmanager
share a dedicated internal Docker network; the Alertmanager API is not published
on the host. Configure `alertmanager_nextcloud_conversation_token` as described
in the monitoring role documentation to enable Talk delivery.

## Variables

| Variable | Default | Description |
|---|---|---|
| `wazuh_version` | `4.14.10` | Pinned Wazuh Docker release and image version |
| `wazuh_certs_generator_version` | `0.0.5` | Upstream certificate-generator image version |
| `wazuh_indexer_java_opts` | `-Xms1g -Xmx1g` | Indexer JVM heap |
| `wazuh_stack_path` | `/opt/wazuh` (local-safe: `{{ stacks_base_path }}/wazuh`) | Wazuh checkout and deployment configuration directory |
| `wazuh_dashboard_hostname` | `wazuh.<app_domain_name>` | Traefik dashboard host |
| `wazuh_alertmanager_url` | `http://alertmanager:9093/api/v2/alerts` | Internal Alertmanager API endpoint |
| `wazuh_alert_min_level` | `10` | Minimum Wazuh level forwarded to Alertmanager |
| `security_wazuh_agent_enabled` | `true` | Install the host agent from the security role |
| `security_wazuh_agent_version` | `{{ wazuh_version }}-1` | Debian package version for the host agent |
| `security_wazuh_agent_manager_address` | `127.0.0.1` | Wazuh manager address for the host agent |
