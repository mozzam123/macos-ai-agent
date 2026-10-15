import os
from dotenv import load_dotenv


load_dotenv()

MAX_RECORDING_DURATION = 15
SILENCE_DURATION = 1.2
SILENCE_THRESHOLD = 500

WHISPER_MODEL = "whisper-large-v3"
OLLAMA_MODEL = "qwen3:8b"

SAMPLE_RATE = 16000

HOTKEY = "<ctrl>+<alt>+<space>"
GROQ_MODEL = "openai/gpt-oss-20b"
