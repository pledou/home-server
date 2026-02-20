# IA Role

This role deploys the AI stack used by Open WebUI and Home Assistant integrations:

- Open WebUI (chat + tools frontend)
- Ollama (LLM inference)
- `speaches` (OpenAI-compatible audio API for STT/TTS)
- Ollama metrics exporter

## Rationalized scope

Audio is now centralized through a single `speaches` service so Open WebUI and Home Assistant use one audio backend.

The Home Assistant role stays focused on home-automation services.

## Single tool per function (target architecture)

To avoid duplicated capabilities and conflicting behavior, use only one integration per function:

- LLM inference for Open WebUI: `ollama`
- TTS for Open WebUI/Home Assistant voice workflows: `speaches`
- STT for Open WebUI/Home Assistant voice workflows: `speaches`
- Home automation tool access from Open WebUI: one Home Assistant MCP server (configured directly in Open WebUI admin tools)
- Files/documents tool access from Open WebUI: one Nextcloud MCP server (per-user)

Do not run multiple STT/TTS backends for the same function in parallel from Open WebUI configuration.

## Dependencies

- `authentik` role should run before `ia` for OAuth SSO integration.

## Deploy

```bash
ansible-playbook -i ../home-server-private-data/inventories/inventory.yml playbooks/install.yml --tags ia
```

## Main variables

Defined in `playbooks/roles/ia/defaults/main.yml`:

- `webui_image`, `webui_version`
- `ollama_image`, `ollama_version`, `ollama_intel_image`, `ollama_intel_version`
- `speaches_image`, `speaches_version`

## Home Assistant voice setup

After IA deployment, configure Home Assistant/Home Agent voice endpoints to use Speaches.

- OpenAI-compatible base URL: `http://<ia-host>:8000/v1`

If Home Assistant runs on the same host/network, use the Docker host IP (or DNS name) from the Home Assistant container perspective.

## MCP integration with Open WebUI

Use Open WebUI native MCP tooling directly from Admin settings.

Recommended:
- add one Nextcloud MCP server
- add one Home Assistant MCP server
- avoid duplicate servers for the same capability

Reference:
- Open WebUI Admin → Tools → MCP Servers

## Home Agent (HACS custom integration)

When using the Home Agent custom integration from HACS:

1. Install **Home Agent** from HACS in Home Assistant.
2. Configure Home Agent to use your Open WebUI endpoint (`https://ia.<domain>`).
3. In Open WebUI, enable the model/tools you want Home Agent to use.
4. Add and validate MCP servers directly in Open WebUI before enabling automations.

Recommended flow:
- Start with plain chat/model integration.
- Add one MCP/OpenAPI tool at a time.
- Validate each tool call before enabling advanced automations.

### Home Agent + MCP strategy

Use Home Agent as the Home Assistant-side orchestrator, but keep one backend tool endpoint per capability in Open WebUI:

- one Nextcloud MCP endpoint
- one Home Assistant MCP endpoint

This keeps behavior predictable and avoids duplicate tools competing for the same actions.
