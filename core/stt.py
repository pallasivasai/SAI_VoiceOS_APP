from functools import lru_cache
import numpy as np
from faster_whisper import WhisperModel
from .config import WHISPER_COMPUTE, WHISPER_DEVICE, WHISPER_MODEL

@lru_cache(maxsize=1)
def get_model() -> WhisperModel:
    print(f"[SAI] Loading faster-whisper model: {WHISPER_MODEL}")
    return WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE)

def transcribe(audio: np.ndarray) -> str:
    if audio is None or audio.size == 0:
        return ""
    model = get_model()
    segments, _ = model.transcribe(audio, beam_size=1, best_of=1, temperature=0.0, vad_filter=True, condition_on_previous_text=False)
    return " ".join(seg.text.strip() for seg in segments if seg.text.strip()).strip()
