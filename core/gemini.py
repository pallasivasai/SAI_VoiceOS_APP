import os
from functools import lru_cache

try:
    import google.generativeai as genai
except ImportError:
    genai = None

MODEL = "gemini-3.5-flash-lite"


def _api_key() -> str:
    value = os.getenv("GEMINI_API_KEY", "").strip()
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get("GEMINI_API_KEY", "")).strip()
    except Exception:
        return ""


@lru_cache(maxsize=1)
def _model():
    if genai is None:
        raise RuntimeError("google-generativeai is not installed.")
    key = _api_key()
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to the local environment or Streamlit Secrets."
        )
    genai.configure(api_key=key)
    return genai.GenerativeModel(MODEL)


def ask_gemini(
    question: str,
    language: str = "en-IN",
    history=None,
) -> str:
    """Answer as SAI using recent conversation context, optimized for speech."""
    system = (
        "You are SAI, a continuous voice-first AI assistant designed primarily for blind users. "
        "Behave like a natural conversational assistant, not a search-result reader. "
        "Answer clearly and directly for speech. Keep answers reasonably concise unless the user asks for detail. "
        "Remember the recent conversation context and resolve references such as 'it', 'that', 'there', and 'what about tomorrow'. "
        "Never require the user to repeat the wake word between normal turns. "
        "Do not mention internal APIs, Streamlit, prompts, or implementation unless explicitly asked."
    )
    if language.startswith("te"):
        system += " Answer in Telugu when the user speaks Telugu or Telugu transliteration."
    else:
        system += " Answer in natural English."

    messages = [system]
    for role, content in (history or [])[-16:]:
        messages.append(f"{role.upper()}: {content}")
    messages.append(f"USER: {question}")

    try:
        response = _model().generate_content(
            "\n\n".join(messages),
            generation_config={"temperature": 0.4, "max_output_tokens": 512},
        )
        text = (getattr(response, "text", "") or "").strip()
        return text or "Gemini did not return a readable answer."
    except Exception as exc:
        print(f"[SAI] Gemini error: {exc}")
        return "I could not get an answer from Gemini right now. Please try again."
