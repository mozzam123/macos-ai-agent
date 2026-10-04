from pathlib import Path

from faster_whisper import WhisperModel

from app.config import WHISPER_MODEL

model = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8",
)


def transcribe_audio(audio_path: Path) -> str:
    """Transcribe an audio file locally using faster-whisper."""

    segments, _ = model.transcribe(
        str(audio_path),
        beam_size=5,
    )

    text = " ".join(segment.text.strip() for segment in segments)

    return text.strip()
