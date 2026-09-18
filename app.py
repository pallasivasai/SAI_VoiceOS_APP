import streamlit as st
import datetime
import re
import requests
import speech_recognition as sr
import streamlit.components.v1 as components
import json

st.set_page_config(
    page_title="SAI Voice OS",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background:#050812;
    color:#F8FAFC;
}
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:760px; padding:1rem 1rem 3rem; }

.sai-shell {
    background:linear-gradient(180deg,#0D1627,#09101D);
    border:1px solid #22304A;
    border-radius:30px;
    padding:28px 22px 24px;
    box-shadow:0 24px 70px rgba(0,0,0,.35);
}

.title {
    text-align:center;
    font-size:2.25rem;
    font-weight:900;
    margin:0;
}
.sub {
    text-align:center;
    color:#A9B5C9;
    font-size:1rem;
    margin:.45rem 0 1.25rem;
}
.voice-guide {
    text-align:center;
    color:#6EE7F9;
    font-weight:800;
    font-size:1rem;
    margin-bottom:1rem;
}
.help {
    background:#111C2E;
    border:1px solid #2B3B57;
    border-radius:18px;
    padding:15px 17px;
    margin:12px 0 16px;
    line-height:1.55;
    font-size:1rem;
}
.answer {
    background:#0D1728;
    border:1px solid #2A3B59;
    border-radius:20px;
    padding:20px;
    margin-top:18px;
    line-height:1.7;
    font-size:1.08rem;
}
.small {
    color:#93A2B9;
    font-size:.9rem;
    line-height:1.5;
    margin-top:12px;
}
div[data-testid="stAudioInput"] {
    margin-top:.5rem;
}
button[kind="secondary"] {
    border-radius:16px !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sai-shell">
  <div class="title">SAI Voice OS</div>
  <div class="sub">Voice-first assistant designed for people who should not need to type.</div>
  <div class="voice-guide">🎙️ TAP • SPEAK • LISTEN</div>
  <div class="help">
    <b>How to use SAI:</b><br>
    Tap the microphone and simply speak your question.
    SAI converts your speech to text, gets an answer from the internet,
    and reads the answer aloud.
  </div>
</div>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

def local_answer(q: str):
    text = q.lower().strip()

    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b", text):
        now = datetime.datetime.now().astimezone()
        return (
            f"The current time is {now.strftime('%I:%M:%S %p')}. "
            f"Today is {now.strftime('%A, %d %B %Y')}."
        )

    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?date|today's date|current date)\b", text):
        return datetime.datetime.now().astimezone().strftime(
            "Today is %A, %d %B %Y."
        )

    return None

def safe_calc(q: str):
    expr = q.lower()
    for prefix in ["calculate", "solve", "what is"]:
        expr = expr.replace(prefix, "")

    expr = (
        expr.replace("multiplied by", "*")
        .replace("divided by", "/")
        .replace("plus", "+")
        .replace("minus", "-")
        .replace("times", "*")
        .strip()
    )

    if re.fullmatch(r"[0-9\s+\-*/().%]+", expr) and any(c.isdigit() for c in expr):
        try:
            return f"The answer is {eval(expr, {'__builtins__': {}}, {})}."
        except Exception:
            return None
    return None

def answer_from_internet(question: str):
    endpoint = "https://jgubunffqfyapurxpoih.supabase.co/functions/v1/sai-claude"

    try:
        response = requests.post(
            endpoint,
            headers={
                "Content-Type": "application/json",
                "apikey": "public-web-client",
            },
            json={
                "question": question,
                "language": "en-IN",
                "timezone": (
                    datetime.datetime.now().astimezone().tzinfo.key
                    if hasattr(datetime.datetime.now().astimezone().tzinfo, "key")
                    else "Asia/Kolkata"
                ),
            },
            timeout=45,
        )

        if not response.ok:
            return (
                "I could not get the internet answer right now. "
                f"The answer service returned status {response.status_code}."
            )

        data = response.json()

        if data.get("answer"):
            return data["answer"]

        return "The internet answer service responded, but it did not return an answer."

    except requests.RequestException:
        return "I could not reach the internet answer service right now. Please try again."
    except Exception:
        return "The answer service returned an unexpected response. Please try again."

def answer(question: str):
    question = question.strip()

    if not question:
        return "I did not hear your question. Please tap the microphone and speak again."

    local = local_answer(question)
    if local:
        return local

    calc = safe_calc(question)
    if calc:
        return calc

    return answer_from_internet(question)

def transcribe(audio_value):
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.5

    try:
        with sr.AudioFile(audio_value) as source:
            audio = recognizer.record(source)

        return recognizer.recognize_google(audio, language="en-IN")

    except (sr.UnknownValueError, sr.RequestError):
        return ""
    except Exception:
        return ""

# Native Streamlit microphone: blind-user-first, no keyboard typing required.
audio = st.audio_input(
    "SAI microphone — tap to speak",
    sample_rate=16000,
    key="sai_microphone",
    help="Tap the microphone, speak naturally, then tap stop when you finish.",
)

if audio is not None:
    with st.spinner("SAI is listening, understanding, and finding your answer…"):
        question = transcribe(audio)

        if not question:
            result = (
                "I could not understand the speech. "
                "Please tap the microphone and speak again."
            )
        else:
            result = answer(question)

        st.session_state.history.append(
            (question or "[speech not understood]", result)
        )

if st.session_state.history:
    q, a = st.session_state.history[-1]

    st.markdown(
        f"""
        <div class="answer">
          <b>You said:</b> {q}<br><br>
          <b>SAI:</b> {a}
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(
        f"""
        <script>
        const text = {json.dumps(a)};
        if (window.speechSynthesis) {{
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "en-IN";
            utterance.rate = 0.95;
            utterance.pitch = 1;
            window.speechSynthesis.speak(utterance);
        }}
        </script>
        """,
        height=1,
    )

    st.markdown(
        """
        <div class="small">
          SAI is voice-first: there is intentionally no text box.
          Tap the microphone, speak, and SAI will respond with an internet-backed answer and read it aloud.
        </div>
        """,
        unsafe_allow_html=True,
    )
