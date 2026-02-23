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
2. Add the STT and TTS integration repositories to HACS
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

2. **Install the integrations** (both STT and TTS):
   - Open HACS in Home Assistant
   - Go to **Integrations**
   - Find and download:
     - **OpenAI Whisper Cloud** (fabio-garavini/ha-openai-whisper-stt-api)
     - **OpenAI TTS** (sfortis/openai_tts)
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
