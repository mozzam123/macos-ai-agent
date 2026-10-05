import os
from dotenv import load_dotenv


load_dotenv()


WHISPER_MODEL = "whisper-large-v3"
OLLAMA_MODEL = "qwen3:8b"

RECORDING_DURATION = 10
SAMPLE_RATE = 16000

HOTKEY = "<ctrl>+<alt>+<space>"
GROQ_MODEL = "openai/gpt-oss-20b"
