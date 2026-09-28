# SAI Voice OS

SAI Voice OS is a voice-first accessibility assistant designed around a JARVIS-style hands-free interaction model for blind users.

## Two modes

### 1. Native desktop voice engine — JARVIS-style

The primary voice architecture is now a local Python desktop process:

    Microphone → Shiva wake detection → local STT → intent/tools → Google Search → TTS → next question

Behavior:

- Say **Shiva** → SAI wakes.
- SAI says **Yes. I am listening.**
- Ask a question.
- SAI answers aloud.
- SAI stays active for follow-up questions; Shiva is not required after every answer.
- Say **Shiva, stop listening** or **stop listening** → SAI sleeps.
- Say **Shiva** again → SAI wakes again.

The native engine does not require Chrome or Streamlit for voice interaction.

See DESKTOP_SETUP.md for Windows installation and configuration.

### 2. Optional Streamlit HUD

app.py remains the browser-based visual HUD and can still be deployed on Streamlit Community Cloud. It is not required by the native voice engine.

## Current desktop components

- main.py — long-running SAI state machine.
- core/audio.py — microphone capture and speech endpointing.
- core/wake.py — Shiva wake engine with custom OpenWakeWord support and local Whisper fallback.
- core/stt.py — faster-whisper local speech-to-text.
- core/tts.py — local Windows TTS through pyttsx3/SAPI.
- core/assistant.py — command routing and continuous conversation policy.
- tools/google.py — Google Search result extraction.
- tools/weather.py — weather location parsing and Google weather lookup.
- tools/system.py — time, date, and safe calculator.
- models/shiva.onnx — optional custom Shiva OpenWakeWord model; binary model files are intentionally not committed.

## Installation

Windows / Python 3.11 or 3.12:

    py -3.11 -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements-desktop.txt
    python main.py

The first faster-whisper run downloads the selected speech model. The default is small. For a lighter CPU machine, set SAI_WHISPER_MODEL=base.

For a supported NVIDIA GPU, configure SAI_WHISPER_DEVICE=cuda and SAI_WHISPER_COMPUTE=float16.

## Shiva wake word

For the final low-power always-on behavior, train a dedicated OpenWakeWord model for Shiva and place it at models/shiva.onnx. OpenWakeWord supports custom wake-word models and streaming local inference. Until that model is added, SAI uses a functional local faster-whisper fallback to detect Shiva in short microphone chunks.

Do not commit private voice recordings, downloaded model weights, API keys, or .venv.
