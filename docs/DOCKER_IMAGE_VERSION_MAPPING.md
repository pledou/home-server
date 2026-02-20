# Docker Image Version Mapping

This document maps Docker images used in Ansible templates to their corresponding version variables defined in role defaults.

## Summary by Role

| Role | Docker Images | Variables Defined |
|------|---------------|-------------------|
| authentik | 3 images | 2 variables |
| gitlab | 2 images | 2 variables |
| hassio | 7 images | 7 variables |
| ia | 4 images | 4 variables |
| kresus | 3 images | 3 variables |
| monitoring | 10 images | 10 variables |
| nextcloud | 5 images | 4 variables |
| traefik | 3 images | 3 variables |

---

## Role: authentik

**Defaults file:** [playbooks/roles/authentik/defaults/main.yml](../playbooks/roles/authentik/defaults/main.yml)

**Template file:** [playbooks/roles/authentik/templates/docker-compose.yml](../playbooks/roles/authentik/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| postgresql | `postgres:{{ authentik_postgres_version }}` | `authentik_postgres_version` | `"17"` |
| redis | `redis:alpine` | *(hardcoded)* | `alpine` |
| server | `ghcr.io/goauthentik/server:{{ authentik_version }}` | `authentik_version` | `"2025.12"` |
| worker | `ghcr.io/goauthentik/server:{{ authentik_version }}` | `authentik_version` | `"2025.12"` |

---

## Role: gitlab

**Defaults file:** [playbooks/roles/gitlab/defaults/main.yml](../playbooks/roles/gitlab/defaults/main.yml)

**Template file:** [playbooks/roles/gitlab/templates/docker-compose.yml](../playbooks/roles/gitlab/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| gitlab | `gitlab/gitlab-ce:{{ gitlab_version }}` | `gitlab_version` | `"16.8.1-ce.0"` |
| gitlab-runner | `gitlab/gitlab-runner` | `gitlab_runner_version` | `"latest"` *(not used in template)* |

**Note:** The `gitlab-runner` image doesn't use the `gitlab_runner_version` variable in the template - it's hardcoded without a tag.

---

## Role: hassio

**Defaults file:** [playbooks/roles/hassio/defaults/main.yaml](../playbooks/roles/hassio/defaults/main.yaml)

**Template file:** [playbooks/roles/hassio/templates/docker-compose.yml](../playbooks/roles/hassio/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| homeassistant | `homeassistant/home-assistant:stable` | `homeassistant_version` | `"stable"` *(not used in template)* |
| zigbee2mqtt | `koenkk/zigbee2mqtt:{{ zigbee2mqtt_version }}` | `zigbee2mqtt_version` | `2` |
| esphome | `esphome/esphome:{{ esphome_version }}` | `esphome_version` | `stable` |
| mosquitto | `eclipse-mosquitto:{{ mosquitto_version }}` | `mosquitto_version` | `2.0` |
| myelectricaldata | `m4dm4rtig4n/myelectricaldata:{{ myelectricaldata_version }}` | `myelectricaldata_version` | `"latest"` |
| frigate | `ghcr.io/blakeblackshear/frigate:stable` | `frigate_version` | `"stable"` *(not used in template)* |
| wyoming-piper | `rhasspy/wyoming-piper` | `piper_version` | `"latest"` *(not used in template)* |
| faster-whisper | `lscr.io/linuxserver/faster-whisper:{{ faster_whisper_version }}` | `faster_whisper_version` | `"latest"` |

**Note:** Some variables are defined but not used in templates (hardcoded tags instead).

---

## Role: ia

**Defaults file:** [playbooks/roles/ia/defaults/main.yml](../playbooks/roles/ia/defaults/main.yml)

**Template file:** [playbooks/roles/ia/templates/docker-compose.yml](../playbooks/roles/ia/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| webui | `ghcr.io/open-webui/open-webui:{{ webui_version }}` | `webui_version` | `"main"` |
| ollama | `ollama/ollama:{{ ollama_version }}` | `ollama_version` | `"latest"` |
| ollama (Intel) | `intelanalytics/ipex-llm-inference-cpp-xpu:{{ ollama_intel_version }}` | `ollama_intel_version` | `"latest"` |
| speech | `ghcr.io/matatonic/openedai-speech:{{ speech_version }}` | `speech_version` | `"latest"` |

**Note:** The ollama service has two different images depending on the GPU type (nvidia/other vs intel).

---

## Role: kresus

**Defaults file:** [playbooks/roles/kresus/defaults/main.yml](../playbooks/roles/kresus/defaults/main.yml)

**Template file:** [playbooks/roles/kresus/templates/docker-compose.yml](../playbooks/roles/kresus/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| k-db | `postgres:{{ kresus_postgres_version }}` | `kresus_postgres_version` | `"15"` |
| apprise | `caronc/apprise:{{ apprise_version }}` | `apprise_version` | `"1.3"` |
| kresus | `bnjbvr/kresus:{{ kresus_version }}` | `kresus_version` | `"0.23.5"` |

---

## Role: monitoring

**Defaults file:** [playbooks/roles/monitoring/defaults/main.yml](../playbooks/roles/monitoring/defaults/main.yml)

**Template file:** [playbooks/roles/monitoring/templates/docker-compose.yml](../playbooks/roles/monitoring/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| prometheus | `prom/prometheus:{{ prometheus_version }}` | `prometheus_version` | `"v2.50.1"` |
| alertmanager | `prom/alertmanager:{{ alertmanager_version }}` | `alertmanager_version` | `"v0.27.0"` |
| node-exporter | `quay.io/prometheus/node-exporter:{{ node_exporter_version }}` | `node_exporter_version` | `"v1.7.0"` |
| grafana | `grafana/grafana:{{ grafana_version }}` | `grafana_version` | `"10.3.3"` |
| loki | `grafana/loki:{{ loki_version }}` | `loki_version` | `"2.9.4"` |
| promtail | `grafana/promtail:{{ promtail_version }}` | `promtail_version` | `"2.9.4"` |
| cadvisor | `gcr.io/cadvisor/cadvisor:{{ cadvisor_version }}` | `cadvisor_version` | `"v0.49.1"` |
| autoheal | `willfarrell/autoheal:{{ autoheal_version }}` | `autoheal_version` | `"latest"` |
| watchtower | `percona/watchtower:{{ watchtower_version }}` | `watchtower_version` | `"3"` |
| nextcloud-exporter | `xperimental/nextcloud-exporter:{{ nextcloud_exporter_version }}` | `nextcloud_exporter_version` | `"0.9.0"` |

---

## Role: nextcloud

**Defaults file:** [playbooks/roles/nextcloud/defaults/main.yml](../playbooks/roles/nextcloud/defaults/main.yml)

**Template file:** [playbooks/roles/nextcloud/templates/docker-compose.yml](../playbooks/roles/nextcloud/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| ncdb | `postgres:{{ nextcloud_postgres_version }}` | `nextcloud_postgres_version` | `"15"` |
| redis | `redis:{{ redis_version }}` | `redis_version` | `"8-alpine"` |
| elasticsearch | `docker.elastic.co/elasticsearch/elasticsearch:{{ elasticsearch_version }}` | `elasticsearch_version` | `"8.12.0"` |
| turn_server | `instrumentisto/coturn:{{ coturn_version }}` | `coturn_version` | `"4.6"` |
| nextcloud | *Custom build (Dockerfile)* | N/A | Built from Dockerfile |
| harp | `ghcr.io/nextcloud/nextcloud-appapi-harp:release` | `harp_version` | `"release"` *(not used in template)* |

**Note:** The nextcloud service is built from a custom Dockerfile, not pulled from a registry. The harp image has a hardcoded tag.

---

## Role: traefik

**Defaults file:** [playbooks/roles/traefik/defaults/main.yml](../playbooks/roles/traefik/defaults/main.yml)

**Template file:** [playbooks/roles/traefik/templates/docker-compose.yml](../playbooks/roles/traefik/templates/docker-compose.yml)

| Service | Docker Image | Variable | Default Value |
|---------|--------------|----------|---------------|
| traefik | `traefik:{{ traefik_version }}` | `traefik_version` | `"v3.6"` |
| unbound | `alpinelinux/unbound:{{ unbound_version }}` | `unbound_version` | `"latest"` |
| updateDuckDNSIP | `alpine:{{ alpine_version }}` | `alpine_version` | `"3.19"` |
| doh-proxy | *Custom build (Dockerfile)* | N/A | Built from Dockerfile |

---

## Issues and Recommendations

### 1. Inconsistent Variable Usage
Some roles define version variables but don't use them in templates:
- **hassio:** `homeassistant_version`, `frigate_version`, `piper_version` defined but not used
- **nextcloud:** `harp_version` defined but not used
- **gitlab:** `gitlab_runner_version` defined but not used

**Recommendation:** Either use these variables in templates or remove them from defaults.

### 2. Missing Variables
Some images don't have version variables:
- **authentik:** `redis:alpine` is hardcoded
- **gitlab:** `gitlab/gitlab-runner` has no tag

**Recommendation:** Create version variables for all docker images to enable version control.

### 3. Duplicate Variable Names
- **monitoring/hassio:** Both define `mosquitto_version` - only hassio uses it

**Recommendation:** Rename variables to be role-specific if they're different (e.g., `monitoring_mosquitto_version`).

### 4. Latest Tags
Several services use `"latest"` tags which is not recommended for production:
- ia: ollama, ollama_intel, speech
- hassio: myelectricaldata, faster-whisper
- kresus: kresus (if set to latest)
- monitoring: autoheal, watchtower
- traefik: unbound

**Recommendation:** Pin to specific versions for better stability and reproducibility.

---

## Usage

To update a Docker image version, modify the corresponding variable in the role's `defaults/main.yml` file. For example:

```yaml
# playbooks/roles/monitoring/defaults/main.yml
prometheus_version: "v2.51.0"  # Updated from v2.50.1
```

Then run the playbook with the appropriate tags:

```bash
ansible-playbook -i inventory.yml playbooks/install.yml --tags monitoring
```
