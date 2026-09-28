from pathlib import Path
import numpy as np
from .config import WAKE_MODEL, WAKE_THRESHOLD

class WakeDetector:
    """Dedicated Shiva model when present; local Whisper fallback otherwise."""
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.model = None
        self.using_custom_model = False
        if Path(WAKE_MODEL).exists():
            try:
                from openwakeword.model import Model
                self.model = Model(wakeword_models=[str(WAKE_MODEL)], inference_framework="onnx")
                self.using_custom_model = True
                print(f"[SAI] Custom Shiva wake model loaded: {WAKE_MODEL}")
            except Exception as exc:
                print(f"[SAI] Could not load Shiva wake model: {exc}")

    @staticmethod
    def _is_shiva(text: str) -> bool:
        normalized = " ".join((text or "").lower().split())
        return any(word in normalized for word in ("shiva", "siva", "shi va", "శివ"))

    def detect(self, audio: np.ndarray) -> bool:
        if self.using_custom_model and self.model is not None:
            pcm = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
            scores = self.model.predict(pcm)
            if isinstance(scores, dict):
                score = max(scores.values()) if scores else 0.0
                return float(score) >= WAKE_THRESHOLD
        return self._is_shiva(self.transcriber(audio))
