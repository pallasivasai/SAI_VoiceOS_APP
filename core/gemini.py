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


def ask_gemini(question: str, language: str = "en-IN") -> str:
    system = (
        "You are SAI, a concise voice-first assistant for blind users. "
        "Answer naturally and clearly for speech. Do not use markdown unless needed. "
        "Prefer a direct answer over long explanations."
    )
    if language.startswith("te"):
        system += " Answer in Telugu when the user speaks Telugu."
    try:
        response = _model().generate_content(
            [system, question],
            generation_config={"temperature": 0.4, "max_output_tokens": 512},
        )
        text = (getattr(response, "text", "") or "").strip()
        return text or "Gemini did not return a readable answer."
    except Exception as exc:
        print(f"[SAI] Gemini error: {exc}")
        return "I could not get an answer from Gemini right now. Please try again."
