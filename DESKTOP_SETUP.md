# SAI Voice OS — native desktop mode

This is the new JARVIS-style voice engine. The Streamlit UI remains available, but it is no longer the core voice engine.

## Behavior

1. Start main.py.
2. SAI says it is ready and enters sleep mode.
3. Say Shiva.
4. SAI says Yes. I am listening.
5. Ask a question.
6. SAI answers through the speaker.
7. SAI immediately returns to listening for the next question — no Shiva required again.
8. Say Shiva, stop listening (or stop listening) to return to sleep mode.
9. Say Shiva again to wake it.

## Windows setup

Use Python 3.11 or 3.12 for smooth dependency compatibility.

    cd SAI_VoiceOS_APP
    py -3.11 -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements-desktop.txt
    python main.py

The first faster-whisper run downloads the selected speech model. The default is small; for a lighter CPU machine use environment variable SAI_WHISPER_MODEL=base.

For a capable NVIDIA GPU, use SAI_WHISPER_MODEL=medium, SAI_WHISPER_DEVICE=cuda, and SAI_WHISPER_COMPUTE=float16.

## Microphone

Allow Windows microphone access for Python. SAI captures audio directly from the local microphone; Chrome/Streamlit is not required.

## AI conversation

Normal questions are answered by Gemini Flash-Lite. SAI keeps recent conversation context so follow-up questions such as "what about tomorrow?" or "who created it?" can be understood without repeating the previous question. The native engine is the primary continuous voice path; Streamlit is optional.

## Weather

Weather questions go through the same Gemini conversation engine in native mode, so the user can ask a location directly and then continue with follow-up questions. The browser location workflow remains available in the optional Streamlit HUD.

## Wake-word model

For final low-power JARVIS-style behavior, train a dedicated OpenWakeWord model for Shiva and place it at models/shiva.onnx. The engine automatically uses it when present. Without it, the local Whisper fallback still provides a working Shiva trigger.

Do not commit private recordings, API keys, downloaded Whisper models, TTS models, or the .venv directory.
