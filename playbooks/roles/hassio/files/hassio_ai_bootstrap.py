import json
import os
from datetime import datetime, timezone
from uuid import uuid4

PATH = "/config/.storage/core.config_entries"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def to_int(name: str, default: int) -> int:
    try:
        return int(float(os.getenv(name, str(default))))
    except Exception:
        return default


def to_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def gen_id() -> str:
    return uuid4().hex[:26].upper()


def find_entry(entries: list[dict], domain: str):
    for item in entries:
        if item.get("domain") == domain:
            return item
    return None


with open(PATH, "r", encoding="utf-8") as config_entries_file:
    root = json.load(config_entries_file)

entries = root.setdefault("data", {}).setdefault("entries", [])
changed = False

backup_path = f"{PATH}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
with open(backup_path, "w", encoding="utf-8") as backup_file:
    json.dump(root, backup_file, ensure_ascii=False, separators=(",", ":"))

home_agent_entry = find_entry(entries, "home_agent")
if home_agent_entry is None:
    home_agent_entry = {
        "created_at": now_iso(),
        "data": {},
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "home_agent",
        "entry_id": gen_id(),
        "minor_version": 1,
        "modified_at": now_iso(),
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "Home Agent",
        "unique_id": None,
        "version": 1,
    }
    entries.append(home_agent_entry)
    changed = True

home_agent_data = home_agent_entry.setdefault("data", {})
home_agent_options = home_agent_entry.setdefault("options", {})

desired_home_agent_data = {
    "llm_api_key": "",
    "llm_base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:8080/v1"),
    "llm_keep_alive": "-1",
    "llm_max_tokens": to_int("HOME_AGENT_MAX_TOKENS", 220),
    "llm_model": os.getenv("HOME_AGENT_MODEL", "ministral-3:3b"),
    "llm_temperature": to_float("HOME_AGENT_TEMPERATURE", 0.5),
    "name": "Home Agent",
    "thinking_enabled": to_bool("HOME_AGENT_THINKING_ENABLED", False),
}
for key, value in desired_home_agent_data.items():
    if home_agent_data.get(key) != value:
        home_agent_data[key] = value
        changed = True

desired_home_agent_options = {
    "context_mode": os.getenv("CONTEXT_MODE", "vector_db"),
    "context_format": os.getenv("CONTEXT_FORMAT", "json"),
    "debug_logging": to_bool("DEBUG_LOGGING", False),
    "streaming_enabled": to_bool("STREAMING_ENABLED", True),
    "history_enabled": to_bool("HISTORY_ENABLED", True),
    "history_max_messages": to_int("HISTORY_MAX_MESSAGES", 4),
    "history_max_tokens": to_int("HISTORY_MAX_TOKENS", 8000),
    "max_context_tokens": to_int("MAX_CONTEXT_TOKENS", 30000),
    "direct_entities": "",
    "compression_level": "high",
    "preserve_recent_messages": 2,
    "memory_context_top_k": 2,
    "vector_db_enabled": True,
    "vector_db_host": os.getenv("CHROMADB_HOST", "127.0.0.1"),
    "vector_db_port": to_int("CHROMADB_PORT", 8001),
    "vector_db_collection": os.getenv("VECTOR_DB_COLLECTION", "home_entities"),
    "vector_db_top_k": to_int("VECTOR_DB_TOP_K", 3),
    "vector_db_similarity_threshold": to_float("VECTOR_DB_SIMILARITY_THRESHOLD", 250.0),
    "vector_db_embedding_provider": os.getenv("VECTOR_DB_EMBEDDING_PROVIDER", "ollama"),
    "vector_db_embedding_base_url": os.getenv("VECTOR_DB_EMBEDDING_BASE_URL", "http://127.0.0.1:11434"),
    "vector_db_embedding_model": os.getenv("VECTOR_DB_EMBEDDING_MODEL", "nomic-embed-text"),
}
for key, value in desired_home_agent_options.items():
    if home_agent_options.get(key) != value:
        home_agent_options[key] = value
        changed = True

tts_entry = find_entry(entries, "openai_tts")
if tts_entry is None:
    tts_entry = {
        "created_at": now_iso(),
        "data": {},
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "openai_tts",
        "entry_id": gen_id(),
        "minor_version": 1,
        "modified_at": now_iso(),
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": "OpenAI TTS (127.0.0.1)",
        "unique_id": f"openai_tts_{uuid4().hex[:16]}",
        "version": 2,
    }
    entries.append(tts_entry)
    changed = True

tts_data = tts_entry.setdefault("data", {})
if tts_data.get("api_key") != "":
    tts_data["api_key"] = ""
    changed = True
tts_url = os.getenv("TTS_URL", "http://127.0.0.1:8000/v1/audio/speech")
if tts_data.get("url") != tts_url:
    tts_data["url"] = tts_url
    changed = True
if not tts_data.get("unique_id"):
    tts_data["unique_id"] = f"openai_tts_{uuid4().hex[:16]}"
    changed = True

subentries = tts_entry.setdefault("subentries", [])
profile = None
for subentry in subentries:
    if subentry.get("subentry_type") == "profile":
        profile = subentry
        break
if profile is None:
    profile = {
        "data": {},
        "subentry_id": gen_id(),
        "subentry_type": "profile",
        "title": os.getenv("TTS_PROFILE_TITLE", "Speaches.ia"),
        "unique_id": None,
    }
    subentries.append(profile)
    changed = True

profile_data = profile.setdefault("data", {})
desired_profile_data = {
    "chime": False,
    "chime_sound": "threetone.mp3",
    "extra_payload": None,
    "instructions": None,
    "model": os.getenv("TTS_MODEL", "tts-1"),
    "normalize_audio": False,
    "profile_name": os.getenv("TTS_PROFILE_NAME", "defaut"),
    "speed": to_float("TTS_SPEED", 1.0),
    "voice": os.getenv("TTS_VOICE", "upmc"),
}
for key, value in desired_profile_data.items():
    if profile_data.get(key) != value:
        profile_data[key] = value
        changed = True
if not profile_data.get("unique_id"):
    profile_data["unique_id"] = str(uuid4())
    changed = True
desired_profile_title = os.getenv("TTS_PROFILE_TITLE", "Speaches.ia")
if profile.get("title") != desired_profile_title:
    profile["title"] = desired_profile_title
    changed = True

whisper_entry = find_entry(entries, "openai_whisper_cloud")
if whisper_entry is None:
    whisper_entry = {
        "created_at": now_iso(),
        "data": {},
        "disabled_by": None,
        "discovery_keys": {},
        "domain": "openai_whisper_cloud",
        "entry_id": gen_id(),
        "minor_version": 3,
        "modified_at": now_iso(),
        "options": {},
        "pref_disable_new_entities": False,
        "pref_disable_polling": False,
        "source": "user",
        "subentries": [],
        "title": os.getenv("WHISPER_NAME", "Speaches.ia"),
        "unique_id": None,
        "version": 1,
    }
    entries.append(whisper_entry)
    changed = True

whisper_data = whisper_entry.setdefault("data", {})
desired_whisper_data = {
    "api_key": os.getenv("WHISPER_API_KEY") or None,
    "custom_provider": True,
    "name": os.getenv("WHISPER_NAME", "Speaches.ia"),
    "url": os.getenv("WHISPER_URL", "http://127.0.0.1:8000/v1/audio/transcriptions"),
}
for key, value in desired_whisper_data.items():
    if whisper_data.get(key) != value:
        whisper_data[key] = value
        changed = True

whisper_options = whisper_entry.setdefault("options", {})
desired_whisper_options = {
    "model": os.getenv("WHISPER_MODEL", "whisper-1"),
    "prompt": os.getenv("WHISPER_PROMPT", ""),
    "temperature": to_float("WHISPER_TEMPERATURE", 0.0),
}
for key, value in desired_whisper_options.items():
    if whisper_options.get(key) != value:
        whisper_options[key] = value
        changed = True
desired_whisper_title = os.getenv("WHISPER_NAME", "Speaches.ia")
if whisper_entry.get("title") != desired_whisper_title:
    whisper_entry["title"] = desired_whisper_title
    changed = True

for domain_name in ("home_agent", "openai_tts", "openai_whisper_cloud"):
    entry = find_entry(entries, domain_name)
    if not entry:
        continue
    if entry.get("source") != "user":
        entry["source"] = "user"
        changed = True
    if entry.get("pref_disable_new_entities") is None:
        entry["pref_disable_new_entities"] = False
        changed = True
    if entry.get("pref_disable_polling") is None:
        entry["pref_disable_polling"] = False
        changed = True
    if "disabled_by" not in entry:
        entry["disabled_by"] = None
        changed = True

if changed:
    for domain_name in ("home_agent", "openai_tts", "openai_whisper_cloud"):
        entry = find_entry(entries, domain_name)
        if entry:
            entry["modified_at"] = now_iso()

    with open(PATH, "w", encoding="utf-8") as config_entries_file:
        json.dump(root, config_entries_file, ensure_ascii=False, separators=(",", ":"))

print(f"changed={changed}")
print(f"backup={backup_path}")
