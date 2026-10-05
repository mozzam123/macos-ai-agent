from groq import Groq

from app.config import WHISPER_MODEL


client = Groq()


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file using Groq Whisper."""

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=WHISPER_MODEL,
            response_format="json",
            language="en",
            temperature=0.0,
        )

    return transcription.text.strip()
