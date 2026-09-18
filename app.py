import streamlit as st
import datetime
import os
import re
import requests
import speech_recognition as sr
import streamlit.components.v1 as components

st.set_page_config(page_title="SAI Voice OS", page_icon="🎙️", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#070B14; color:#F8FAFC; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:680px; padding:2rem 1rem 3rem; }
.sai-card { background:#0D1422; border:1px solid #1F2937; border-radius:28px; padding:28px; box-shadow:0 18px 55px rgba(0,0,0,.30); }
.sai-title { font-size:2.1rem; font-weight:800; margin:0; }
.sai-sub { color:#94A3B8; margin:.35rem 0 1.5rem; }
.mic-help { text-align:center; color:#6EE7F9; font-size:1.1rem; font-weight:700; margin:.7rem 0 1.2rem; }
.answer { background:#101827; border:1px solid #243248; border-radius:18px; padding:20px; margin-top:18px; line-height:1.65; font-size:1.08rem; }
.small { color:#94A3B8; font-size:.9rem; }
div[data-testid="stAudioInput"] { margin-top:.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sai-card">
  <div class="sai-title">SAI Voice OS</div>
  <div class="sai-sub">Voice-first accessibility assistant</div>
  <div class="mic-help">🎙️ TAP THE MICROPHONE AND SPEAK</div>
</div>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

def local_answer(q: str):
    text = q.lower().strip()
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b", text):
        now = datetime.datetime.now().astimezone()
        return f"The current time is {now.strftime('%I:%M:%S %p')}. Today is {now.strftime('%A, %d %B %Y')}."
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?date|today's date|current date)\b", text):
        return datetime.datetime.now().astimezone().strftime("Today is %A, %d %B %Y.")
    return None

def safe_calc(q: str):
    expr = q.lower()
    for prefix in ["calculate", "solve", "what is"]:
        expr = expr.replace(prefix, "")
    expr = expr.replace("multiplied by","*").replace("divided by","/").replace("plus","+").replace("minus","-").replace("times","*")
    expr = expr.strip()
    if re.fullmatch(r"[0-9\s+\-*/().%]+", expr) and any(c.isdigit() for c in expr):
        try:
            return f"The answer is {eval(expr, {'__builtins__': {}}, {})}."
        except Exception:
            return None
    return None

def answer(question: str):
    question = question.strip()
    if not question:
        return "I did not hear a question. Please tap the microphone and try again."
    local = local_answer(question)
    if local:
        return local
    calc = safe_calc(question)
    if calc:
        return calc

    endpoint = st.secrets.get("SAI_CLAUDE_URL", os.getenv("SAI_CLAUDE_URL", ""))
    if endpoint:
        try:
            r = requests.post(
                endpoint,
                json={"question": question, "language":"en-IN",
                      "timezone":datetime.datetime.now().astimezone().tzinfo.key
                      if hasattr(datetime.datetime.now().astimezone().tzinfo, "key") else "Asia/Kolkata"},
                timeout=35
            )
            data = r.json()
            if r.ok and data.get("answer"):
                return data["answer"]
        except Exception:
            pass
    return "The SAI answer service is not connected yet. Please configure SAI_CLAUDE_URL in Streamlit Secrets."

def transcribe(audio_value):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_value) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="en-IN")
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""
    except Exception:
        return ""

# Streamlit's native browser microphone control: no keyboard typing is required.
audio = st.audio_input("SAI microphone", key="sai_microphone")

if audio is not None:
    with st.spinner("SAI is listening and understanding…"):
        question = transcribe(audio)
        if not question:
            result = "I could not understand the speech. Please tap the microphone and speak again."
        else:
            result = answer(question)
        st.session_state.history.append((question or "[speech not understood]", result))

if st.session_state.history:
    q, a = st.session_state.history[-1]
    st.markdown(f'<div class="answer"><b>SAI heard:</b> {q}<br><br><b>SAI:</b> {a}</div>', unsafe_allow_html=True)
    components.html(f"""
    <script>
      const text = {__import__("json").dumps(a)};
      if (window.speechSynthesis) {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = "en-IN";
        u.rate = 0.95;
        u.pitch = 1;
        window.speechSynthesis.speak(u);
      }}
    </script>
    """, height=1)
    st.markdown('<div class="small">SAI is voice-first: tap the microphone, speak, and the answer is read aloud. Text entry is intentionally not required.</div>', unsafe_allow_html=True)
