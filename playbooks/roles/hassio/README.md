# Home Assistant Role

This role deploys Home Assistant (Hassio) for home automation.

## Dependencies

This role requires the following roles to be executed first:
- **authentik** - Provides SSO/authentication services

## Installation

When running the full installation, ensure roles are executed in the correct order in your playbook:
```yaml
- role: authentik
- role: hassio
```

For targeted deployment:
```bash
ansible-playbook install.yml --tags hassio
```

## HACS (Home Assistant Community Store)

This role can automatically install HACS and configure custom integration repositories.

### Automated Installation

By default (`homeassistant_hacs_enabled: true`), the role will:

1. Download and install HACS if not present
2. Add the STT, TTS, and Home Agent integration repositories to HACS
3. Prepare them for download via HACS UI

To disable automatic HACS setup:
```yaml
homeassistant_hacs_enabled: false
```

### Post-Installation Steps

After Ansible completes:

1. **First-time HACS setup** (if HACS was just installed):
   - Restart Home Assistant
   - Go to **Settings → Devices & Services**
   - Configure HACS integration when prompted
   - Link your GitHub account

2. **Install the integrations**:
   - Open HACS in Home Assistant
   - Go to **Integrations**
   - Find and download:
     - **OpenAI Whisper Cloud** (fabio-garavini/ha-openai-whisper-stt-api)
     - **OpenAI TTS** (sfortis/openai_tts)
     - **Home Agent** (aradlein/hass-agent-llm)
   - Restart Home Assistant after downloading

3. **Configure via UI** (see sections below for details)

## Speech-to-Text (OpenAI Whisper Cloud via HACS)

`OpenAI Whisper Cloud` is configured through Home Assistant UI (Config Entry), not via `configuration.yaml`.

### Installation

The role automatically adds this repository to HACS (if `homeassistant_hacs_enabled: true`):

- Repository: `https://github.com/fabio-garavini/ha-openai-whisper-stt-api`
- Integration name in HACS: `OpenAI Whisper Cloud`

After Ansible deployment, download the integration from HACS and restart Home Assistant.

### Configuration (UI)

In Home Assistant:

1. Go to **Settings → Devices & Services → Add Integration**
2. Select **OpenAI Whisper Cloud**
3. Choose **Custom** as the source
4. Configure with your Speaches endpoint:
	- API Key: `openai-api-key` (or your configured value)
	- API URL: `http://127.0.0.1:8000/v1` (or `http://<ia-host>:8000/v1`)
	- Model: `whisper-1` (mapped by IA role aliases)
	- Temperature: `0` (default, optional)
	- Prompt: (optional - list of words/names to improve recognition)

### Note about automation

Automatic setup via Ansible `blockinfile` is not recommended for `OpenAI Whisper Cloud`, because this integration is managed by Home Assistant config entries (UI storage).

## Text-to-Speech (openai_tts via HACS)

`openai_tts` is primarily configured through Home Assistant UI (Config Entry), not reliably via `configuration.yaml`.

### Installation

The role automatically adds this repository to HACS (if `homeassistant_hacs_enabled: true`):

- Repository: `https://github.com/sfortis/openai_tts`
- Integration name in HACS: `OpenAI TTS`

After Ansible deployment, download the integration from HACS and restart Home Assistant.

### Configuration (UI)

In Home Assistant:

1. Go to **Settings → Devices & Services → Add Integration**
2. Select **OpenAI TTS**
3. Configure with your Speaches endpoint:
	- API URL: `http://127.0.0.1:8000/v1` (or `http://<ia-host>:8000/v1`)
	- API Key: `openai-api-key` (or your configured value)
	- Model: `tts-1` (mapped by IA role aliases)
	- Voice: choose a voice compatible with your installed Speaches TTS model

### Note about automation

Automatic full setup via Ansible `blockinfile` is not recommended for `openai_tts`, because this integration is managed by Home Assistant config entries (UI storage).

## LLM Integration for Home Assistant

There are two main options for integrating LLMs with Home Assistant:

### Option 1: Native Ollama Integration (Built-in)

**Best for**: Simple setups, < 25 entities, basic voice commands

The official [Home Assistant Ollama integration](https://www.home-assistant.io/integrations/ollama/) is built-in and simple to configure:

**Pros:**
- ✅ Official integration (no HACS needed)
- ✅ Simple setup
- ✅ Built-in to Home Assistant
- ✅ Good for small homes

**Cons:**
- ❌ Limited features
- ❌ No persistent conversation memory
- ❌ No custom tools
- ❌ Entity control is experimental (< 25 entities recommended)
- ❌ Requires tool-capable models for control
- ❌ No vector database support for large installations

**Configuration:** Settings → Devices & Services → Add Integration → Ollama

### Option 2: Home Agent (HACS - Recommended for Advanced Use)

**Best for**: Complex setups, large homes (> 25 entities), advanced features, custom integrations

`Home Agent` provides natural language control of Home Assistant via OpenAI-compatible LLMs, including Open WebUI.

- ✅ Advanced context injection (direct or vector DB with ChromaDB)
- ✅ Persistent conversation memory across sessions
- ✅ Built-in control tools (`ha_control`, `ha_query`)
- ✅ Custom REST API and service tools
- ✅ Memory system for long-term personalization
- ✅ Streaming responses for voice assistants
- ✅ Multi-LLM support (fast local + powerful cloud)
- ✅ Semantic entity search for large homes
- ✅ Better entity control reliability

**Cons:**
- ❌ Requires HACS
- ❌ More complex configuration
- ❌ Custom integration (not official)

### Recommendation

**Use Native Ollama if:**
- You have a small home (< 25 entities)
- You want simple voice commands ("turn on the lights")
- You prefer official integrations
- You don't need conversation memory or custom tools

**Use Home Agent if:**
- You have a large home (> 25 entities)
- You want persistent conversations
- You need custom tools or advanced features
- You want better control reliability
- You're willing to use HACS

### Home Agent Installation

The role automatically adds this repository to HACS (if `homeassistant_hacs_enabled: true`):

- Repository: `https://github.com/aradlein/hass-agent-llm`
- Integration name in HACS: `Home Agent`

After Ansible deployment, download the integration from HACS and restart Home Assistant.

### Configuration (UI)

In Home Assistant:

1. Go to **Settings → Devices & Services → Add Integration**
2. Select **Home Agent**
3. **Basic Configuration**:
	- Name: `Home Agent` (or your preference)
	- LLM Base URL: Your LLM endpoint
	  - **Open WebUI**: `http://<ia-host>:3000/ollama/v1` or `http://<ia-host>:3000/api/v1` (see note below)
	  - **Ollama direct**: `http://<ia-host>:11434/v1`
	  - **OpenAI**: `https://api.openai.com/v1`
	- API Key: Your API key (or `openai-api-key` for local setups, or leave empty if using Ollama directly)
	- Model: `llama3.2` (or your preferred model name)
	- Temperature: `0.7` (recommended)
	- Max Tokens: `500` (adjust as needed)

4. **Advanced Configuration** (optional, via Settings → Devices & Services → Home Agent → Configure):
	- **Context Injection Mode**: 
	  - `direct` - Simple entity state injection (default, no extra dependencies)
	  - `vector_db` - Semantic search with ChromaDB (requires additional setup)
	- **Conversation History**: Enable to maintain context across interactions
	- **Custom Tools**: Define REST API endpoints or Home Assistant services
	- **Memory System**: Enable long-term memory for personalized experiences
	- **Streaming**: Enable for low-latency voice assistant integration

### Connecting to Open WebUI

Home Agent can work with Open WebUI in two ways:

#### Option A: Direct to Ollama (Recommended)
Point Home Agent directly to Ollama, bypassing Open WebUI:
- **LLM Base URL**: `http://<ia-host>:11434/v1`
- **Model**: `llama3.2` or any model you have in Ollama
- **API Key**: Leave empty or use any value

#### Option B: Via Open WebUI API
Point to Open WebUI's API endpoint:
- **LLM Base URL**: `http://<ia-host>:3000/ollama/v1`
- **API Key**: Get from Open WebUI (Settings → Account → API Keys)
- **Model**: Model name as shown in Open WebUI

**Note**: Open WebUI adds its own UI and features. For voice assistants or simple automation, direct Ollama connection (Option A) is simpler and faster.

### Usage Examples

#### Voice Control
Once configured, Home Agent works with Home Assistant's native voice assistants. Just speak naturally:
- "Turn on the kitchen lights to 50%"
- "What's the temperature in the living room?"
- "Is the garage door locked?"

#### Automation Integration
```yaml
automation:
  - alias: "Morning Briefing"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: home_agent.process
        data:
          text: "Good morning! What's the weather and are all doors locked?"
          conversation_id: "morning_routine"
```

#### Clear Conversation Context
```yaml
# Clear current conversation
service: home_agent.clear_conversation

# Clear for specific device
service: home_agent.clear_conversation
data:
  device_id: "kitchen_satellite"
```

### Advanced Features

For advanced features, refer to the [Home Agent documentation](https://github.com/aradlein/hass-agent-llm/tree/main/docs):

- **Vector Database**: Semantic entity search for large installations
- **Memory System**: Long-term memory and fact extraction
- **Custom Tools**: Add REST APIs or Home Assistant services as LLM tools
- **Multi-LLM**: Use fast local model for control + cloud model for analysis
- **Streaming**: Low-latency responses for voice assistants

### Troubleshooting

- **"Connection refused"**: Ensure the IA role is deployed and Ollama/Open WebUI is running
- **"Model not found"**: Verify model name matches exactly what's in Ollama (`docker exec -it ia-ollama-1 ollama list`)
- **High memory usage**: Check documentation for memory leak fixes in v0.9.1+
- **Setup timeout**: Update to v0.9.2+ which fixes timeout on large installations
