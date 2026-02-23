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
- `speaches_image`, `speaches_cpu_version`, `speaches_cuda_version`
- `speaches_stt_model`, `speaches_tts_model`, `speaches_preload_models`
- `speaches_postdeploy_models`

Default french-oriented setup:

- STT model: `Systran/faster-whisper-small`
- TTS model: `rhasspy/piper-voices`

By default, only the STT model is preloaded at Speaches startup through `PRELOAD_MODELS`.
This avoids startup failure when a TTS model ID is not available in the Speaches registry.

Important: if any model in `speaches_preload_models` is invalid, Speaches can fail to start.
In that case, Open WebUI transcription fails with `Server Connection Error`.

For additional models, you can either:

- add a valid model ID to `speaches_preload_models`, or
- install it after startup via Speaches API (`POST /v1/models/{model_id}`).
Aliases are also generated in `stacks/ia/model_aliases.json`:

- `whisper-1` → `speaches_stt_model`
- `tts-1` / `tts-1-hd` → `speaches_tts_model`

### Post-deploy model installation task

The role now includes a post-deploy step that:

1. waits for Speaches health (`/health`),
2. reads local models (`/v1/models`),
3. installs missing models from `speaches_postdeploy_models` via `POST /v1/models/{model_id}`.

Default post-deploy models:

- `speaches_postdeploy_models:`
	- `speaches-ai/piper-fr_FR-upmc-medium`

Unknown IDs (`404`) or server-side model install errors (`500`) are skipped with a warning (non bloquant).

## Home Assistant voice setup

After IA deployment, configure Home Assistant/Home Agent voice endpoints to use Speaches.

- OpenAI-compatible base URL: `http://<ia-host>:8000/v1`

If Home Assistant runs on the same host/network, use the Docker host IP (or DNS name) from the Home Assistant container perspective.

### HACS prerequisites (required)

For Home Assistant voice with Speaches, install both custom integrations from HACS:

1. `openai_tts` for text-to-speech
2. `OpenAI Whisper Cloud` for speech-to-text

Repository links:

- `https://github.com/sfortis/openai_tts`
- `https://github.com/fabio-garavini/ha-openai-whisper-stt-api`

After installation, restart Home Assistant before configuring providers.

### Home Assistant TTS with `openai_tts` custom integration

You can use Speaches directly in Home Assistant with the custom integration:

- Repository: `https://github.com/sfortis/openai_tts`

Recommended setup:

1. Install `openai_tts` from HACS (or manually from the repository).
2. In Home Assistant, add/configure the OpenAI TTS integration.
3. Use your Speaches endpoint and model aliases from this role:
	- Base URL: `http://<ia-host>:8000/v1`
	- API key: `openai-api-key` (or the value you set)
	- Model: `tts-1` (alias mapped to `speaches_tts_model`)

Notes:

- `tts-1` and `tts-1-hd` aliases are generated in `stacks/ia/model_aliases.json`.
- If Home Assistant cannot resolve `speaches` by Docker DNS, use the IA host IP/FQDN.
- Keep one TTS backend enabled in Home Assistant to avoid duplicate voice providers.

### Home Assistant STT with `OpenAI Whisper Cloud` custom integration

Use Speaches for STT in Home Assistant with `OpenAI Whisper Cloud` (HACS custom integration).

Recommended setup:

1. Install `OpenAI Whisper Cloud` from HACS.
2. In Home Assistant, add/configure the integration via UI.
3. Choose **Custom** as the source and configure:
	- API Key: `openai-api-key` (or your configured value)
	- API URL: `http://<ia-host>:8000/v1`
	- Model: `whisper-1` (alias mapped to `speaches_stt_model`)
	- Temperature: `0` (default)

Notes:

- `whisper-1` alias is available from `model_aliases.json` and maps to your configured STT model.
- This integration is UI-only (no YAML configuration).
- Keep one STT backend enabled in Home Assistant to avoid duplicate transcription providers.

## Open WebUI wiring

The role sets Open WebUI audio STT variables to Speaches automatically:

- `AUDIO_STT_ENGINE=openai`
- `AUDIO_STT_OPENAI_API_BASE_URL=http://speaches:8000/v1`
- `AUDIO_STT_MODEL={{ speaches_stt_model }}`

If Open WebUI UI settings were previously customized, UI values can override env defaults. In that case, re-check Admin → Audio and point STT to Speaches.

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
