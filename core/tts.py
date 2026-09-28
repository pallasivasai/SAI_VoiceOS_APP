import threading
import pyttsx3
from .config import TTS_RATE

class Speaker:
    def __init__(self):
        self._lock = threading.Lock()
        self.engine = None
        self._init_engine()
    def _init_engine(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", TTS_RATE)
        except Exception as exc:
            print(f"[SAI] TTS initialization failed: {exc}")
            self.engine = None
    def say(self, text: str):
        if not text:
            return
        print(f"SAI: {text}")
        if self.engine is None:
            return
        with self._lock:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as exc:
                print(f"[SAI] TTS error: {exc}")
                self._init_engine()
