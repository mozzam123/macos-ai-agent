from pathlib import Path

import sounddevice as sd
from scipy.io.wavfile import write

from app.config import SAMPLE_RATE, RECORDING_DURATION

CHANNELS = 1


def record_audio(
    output_path: str = "recording.wav",
    duration: int = RECORDING_DURATION,
) -> Path:
    """Record microphone audio and save it as a WAV file."""

    path = Path(output_path)

    print(f"Listening for {duration} seconds...")

    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )

    sd.wait()

    write(
        path,
        SAMPLE_RATE,
        audio,
    )

    return path
