from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
WAKE_MODEL = MODELS_DIR / "shiva.onnx"
SAMPLE_RATE = int(os.getenv("SAI_SAMPLE_RATE", "16000"))
CHANNELS = 1
WAKE_CHUNK_SECONDS = float(os.getenv("SAI_WAKE_CHUNK_SECONDS", "2.0"))
MAX_COMMAND_SECONDS = float(os.getenv("SAI_MAX_COMMAND_SECONDS", "12"))
SILENCE_SECONDS = float(os.getenv("SAI_SILENCE_SECONDS", "1.15"))
MIN_SPEECH_SECONDS = float(os.getenv("SAI_MIN_SPEECH_SECONDS", "0.25"))
RMS_THRESHOLD = float(os.getenv("SAI_RMS_THRESHOLD", "0.012"))
WHISPER_MODEL = os.getenv("SAI_WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("SAI_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE = os.getenv("SAI_WHISPER_COMPUTE", "int8")
WAKE_THRESHOLD = float(os.getenv("SAI_WAKE_THRESHOLD", "0.55"))
TTS_RATE = int(os.getenv("SAI_TTS_RATE", "175"))
GOOGLE_TIMEOUT = int(os.getenv("SAI_GOOGLE_TIMEOUT", "15"))
