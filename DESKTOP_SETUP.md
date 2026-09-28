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

## Google answers

Normal questions are sent to Google Search and the readable result is spoken. There is no OpenAI API key and no Supabase dependency in this desktop voice path.

## Weather

- What is the weather in Guntur now? searches Google for Guntur weather; no current-location lookup is needed.
- What is the weather now? uses the machine's approximate IP-based city when available.
- The browser location permission workflow in app.py is still available for the optional Streamlit HUD.

## Wake-word model

For final low-power JARVIS-style behavior, train a dedicated OpenWakeWord model for Shiva and place it at models/shiva.onnx. The engine automatically uses it when present. Without it, the local Whisper fallback still provides a working Shiva trigger.

Do not commit private recordings, API keys, downloaded Whisper models, TTS models, or the .venv directory.
