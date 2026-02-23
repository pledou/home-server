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

## LLM Integration Options for Home Assistant

Home Assistant offers two ways to integrate LLMs:

### Native Ollama Integration vs Home Agent

| Feature | Native Ollama | Home Agent (HACS) |
|---------|--------------|-------------------|
| **Installation** | Built-in | HACS required |
| **Complexity** | Simple | Advanced |
| **Entity Limit** | < 25 recommended | No limit (vector DB) |
| **Conversation Memory** | ❌ No | ✅ Persistent |
| **Custom Tools** | ❌ No | ✅ REST APIs + Services |
| **Entity Control** | ⚠️ Experimental | ✅ Reliable (ha_control) |
| **Vector Database** | ❌ No | ✅ ChromaDB support |
| **Streaming** | ❌ No | ✅ For voice assistants |
| **Memory System** | ❌ No | ✅ Long-term facts |
| **Multi-LLM** | ❌ No | ✅ Yes |

**Recommendation**: 
- **Small homes** (< 25 entities) → Use native Ollama integration
- **Large/complex homes** → Use Home Agent

This documentation covers **Home Agent** setup. For native Ollama, see [Home Assistant docs](https://www.home-assistant.io/integrations/ollama/).

## Home Agent (HACS custom integration)

**Home Agent** is a Home Assistant custom integration that provides advanced natural language control via OpenAI-compatible LLMs.

### What is Home Agent?

Home Agent extends Home Assistant's native conversation platform to enable:
- Natural language control of smart home devices
- Persistent conversation memory
- Built-in tools (`ha_control`, `ha_query`) for home automation
- Custom REST API and service tools
- Streaming responses for voice assistants
- Optional vector database (ChromaDB) for semantic entity search

### Installation

The **hassio** role automatically adds Home Agent to HACS. After deployment:

1. Open HACS in Home Assistant → Integrations
2. Search for **Home Agent** (aradlein/hass-agent-llm)
3. Click Install
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration**
6. Configure Home Agent (see below)

### Recommended Configuration

**Connect directly to Ollama** (not Open WebUI) for best performance:

```yaml
Name: Home Agent
LLM Base URL: http://<ia-host>:11434/v1
API Key: (leave empty or any value)
Model: llama3.2 (or your preferred model)
Temperature: 0.7
Max Tokens: 500
```

**Why direct to Ollama?**
- Simpler configuration
- Lower latency
- Avoids Open WebUI's additional UI overhead
- Better for voice assistants and automation

### Integration with Open WebUI (Optional)

If you want to use Open WebUI features (chat UI, tools, workflows), you can:

1. **Option A: Keep separate** (Recommended)
   - Home Agent → Ollama (for HA voice/automation)
   - Open WebUI → Ollama (for chat/tools)
   - Both use the same models, but different contexts

2. **Option B: Point Home Agent to Open WebUI**
   - LLM Base URL: `http://<ia-host>:3000/ollama/v1`
   - API Key: Generate in Open WebUI (Settings → Account → API Keys)
   - This routes through Open WebUI but adds complexity

### Home Agent + MCP Strategy

For advanced integrations:

1. **Home Assistant side** (Home Agent):
   - Use for voice assistants and HA automation
   - Configure custom tools if needed (REST APIs, HA services)
   - Enable conversation history for context
   
2. **Open WebUI side** (MCP servers):
   - Add Home Assistant MCP server in Open WebUI
   - Add Nextcloud MCP server in Open WebUI
   - Use for complex multi-tool workflows

**Key principle**: Keep one tool per capability to avoid conflicts
- One Home Assistant endpoint (either MCP in Open WebUI OR Home Agent in HA)
- One Nextcloud endpoint
- Avoid duplicate tools competing for the same actions

### Usage Examples

See the [hassio role README](../hassio/README.md#home-agent-llm-powered-conversation) for:
- Voice control examples
- Automation integration
- Conversation management
- Advanced features (vector DB, memory system, custom tools)
- Troubleshooting

### Documentation

Full documentation: https://github.com/aradlein/hass-agent-llm/tree/main/docs
