import os
from pathlib import Path

from dotenv import load_dotenv


APP_NAME = "macOS AI Agent"
DATA_DIR = Path(
    os.environ.get(
        "MACOS_AI_AGENT_DATA_DIR",
        Path.home() / "Library" / "Application Support" / APP_NAME,
    )
).expanduser()

# Store mutable user data outside the .app bundle. The bundle can be replaced
# during upgrades, while this directory remains writable and persistent.
DATA_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = DATA_DIR / ".env"
CHECKPOINTS_FILE = DATA_DIR / "checkpoints.db"
ALIASES_FILE = DATA_DIR / "aliases.json"
RECENT_MEMORY_FILE = DATA_DIR / "recent_memory.json"
RECORDING_FILE = DATA_DIR / "recording.wav"

# A packaged app loads secrets only from its user-owned support directory.
# The fallback keeps the source checkout convenient during development.
load_dotenv(ENV_FILE)
if not ENV_FILE.exists():
    load_dotenv()

MAX_RECORDING_DURATION = 15
SILENCE_DURATION = 1.2
SILENCE_THRESHOLD = 500

WHISPER_MODEL = "whisper-large-v3"
OLLAMA_MODEL = "qwen3:8b"

SAMPLE_RATE = 16000

HOTKEY = "<ctrl>+<alt>+<space>"
GROQ_MODEL = "openai/gpt-oss-20b"
