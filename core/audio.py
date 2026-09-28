import time
from collections import deque
import numpy as np
import sounddevice as sd
from .config import CHANNELS, MAX_COMMAND_SECONDS, MIN_SPEECH_SECONDS, RMS_THRESHOLD, SAMPLE_RATE, SILENCE_SECONDS

def rms(audio: np.ndarray) -> float:
    if audio.size == 0:
        return 0.0
    data = audio.astype(np.float32)
    return float(np.sqrt(np.mean(np.square(data)) + 1e-12))

def record_command() -> np.ndarray:
    block = int(SAMPLE_RATE * 0.10)
    pre_roll = deque(maxlen=4)
    chunks = []
    started = False
    speech_time = 0.0
    silence_time = 0.0
    start = time.monotonic()
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", blocksize=block) as stream:
        while time.monotonic() - start < MAX_COMMAND_SECONDS:
            data, _ = stream.read(block)
            mono = np.asarray(data[:, 0], dtype=np.float32).copy()
            level = rms(mono)
            pre_roll.append(mono)
            if level >= RMS_THRESHOLD:
                if not started:
                    started = True
                    chunks.extend(list(pre_roll))
                chunks.append(mono)
                speech_time += block / SAMPLE_RATE
                silence_time = 0.0
            elif started:
                chunks.append(mono)
                silence_time += block / SAMPLE_RATE
                if silence_time >= SILENCE_SECONDS and speech_time >= MIN_SPEECH_SECONDS:
                    break
    if not chunks:
        return np.empty(0, dtype=np.float32)
    return np.concatenate(chunks).astype(np.float32)

def record_wake_chunk(seconds: float) -> np.ndarray:
    frames = max(1, int(SAMPLE_RATE * seconds))
    audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32")
    sd.wait()
    return np.asarray(audio[:, 0], dtype=np.float32)
