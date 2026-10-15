from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write

from app.config import (
    MAX_RECORDING_DURATION,
    SAMPLE_RATE,
    SILENCE_DURATION,
    SILENCE_THRESHOLD,
)


CHANNELS = 1

# Process audio in small chunks.
CHUNK_DURATION = 0.1

CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


def record_audio(
    output_path: str = "recording.wav",
) -> Path:
    """
    Record microphone audio.

    Recording stops when:
    - speech has started, and
    - the user is silent for SILENCE_DURATION seconds,

    or when MAX_RECORDING_DURATION is reached.
    """

    path = Path(output_path)

    frames = []

    speech_started = False
    silent_chunks = 0

    required_silent_chunks = int(SILENCE_DURATION / CHUNK_DURATION)

    max_chunks = int(MAX_RECORDING_DURATION / CHUNK_DURATION)

    print("Listening...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=CHUNK_SIZE,
    ) as stream:

        for _ in range(max_chunks):
            audio_chunk, overflowed = stream.read(CHUNK_SIZE)

            if overflowed:
                print("Warning: audio input overflow.")

            frames.append(audio_chunk.copy())

            # -------------------------------------------------
            # Calculate volume level
            # -------------------------------------------------

            audio_level = np.sqrt(np.mean(audio_chunk.astype(np.float32) ** 2))

            # -------------------------------------------------
            # Speech detected
            # -------------------------------------------------

            if audio_level > SILENCE_THRESHOLD:
                speech_started = True
                silent_chunks = 0

            # -------------------------------------------------
            # Silence after speech
            # -------------------------------------------------

            elif speech_started:
                silent_chunks += 1

                if silent_chunks >= required_silent_chunks:
                    print("Speech finished.")

                    break

    if not frames:
        raise RuntimeError("No audio was recorded.")

    audio = np.concatenate(
        frames,
        axis=0,
    )

    write(
        path,
        SAMPLE_RATE,
        audio,
    )

    return path
