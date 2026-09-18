import streamlit as st
import datetime
import math
import os
import re
import urllib.parse
import requests

st.set_page_config(page_title="SAI Voice OS", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#070B14; color:#F8FAFC; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:760px; padding-top:2rem; }
.sai-card { background:#0D1422; border:1px solid #1F2937; border-radius:24px; padding:28px; box-shadow:0 18px 55px rgba(0,0,0,.28); }
.sai-title { font-size:2rem; font-weight:800; margin-bottom:.2rem; }
.sai-sub { color:#94A3B8; margin-bottom:1.5rem; }
.answer { background:#101827; border:1px solid #243248; border-radius:18px; padding:20px; margin-top:16px; line-height:1.6; font-size:1.05rem; }
.small { color:#64748B; font-size:.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="sai-card"><div class="sai-title">SAI Voice OS</div><div class="sai-sub">Voice-first accessibility assistant</div>', unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []

def local_answer(q: str):
    text = q.lower().strip()
    if re.search(r'\b(what(?:\'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b', text):
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M:%S %p')}. Today is {now.strftime('%A, %d %B %Y')}."
    if re.search(r'\b(what(?:\'s| is)?\s+(?:the\s+)?date|today\'s date|current date)\b', text):
        return datetime.datetime.now().strftime("Today is %A, %d %B %Y.")
    return None

def safe_calc(q: str):
    expr = q.lower()
    for prefix in ["calculate", "what is", "solve"]:
        expr = expr.replace(prefix, "")
    expr = expr.replace("plus","+").replace("minus","-").replace("times","*").replace("multiplied by","*").replace("divided by","/")
    expr = expr.strip()
    if re.fullmatch(r'[0-9\s+\-*/().%]+', expr) and any(c.isdigit() for c in expr):
        try:
            return f"The answer is {eval(expr, {'__builtins__': {}}, {})}."
        except Exception:
            return None
    return None

def answer(question: str):
    if not question.strip():
        return "Please enter a question."
    local = local_answer(question)
    if local:
        return local
    calc = safe_calc(question)
    if calc:
        return calc

    # Optional external answer service. Configure SAI_CLAUDE_URL in Streamlit secrets.
    endpoint = st.secrets.get("SAI_CLAUDE_URL", os.getenv("SAI_CLAUDE_URL", ""))
    if endpoint:
        try:
            r = requests.post(endpoint, json={"question": question, "language":"en-IN",
                                               "timezone":datetime.datetime.now().astimezone().tzinfo.key if hasattr(datetime.datetime.now().astimezone().tzinfo,'key') else "Asia/Kolkata"}, timeout=30)
            data = r.json()
            if r.ok and data.get("answer"):
                return data["answer"]
        except Exception:
            pass

    return ("I can handle local time, date, and calculations here. For general questions, connect the "
            "SAI Claude answer service using SAI_CLAUDE_URL in Streamlit Secrets.")

st.markdown("### Ask SAI")
question = st.text_input("Type a question", placeholder="What is the time now?", label_visibility="collapsed")
if st.button("🎙️ Ask SAI", use_container_width=True):
    result = answer(question)
    st.session_state.history.append((question, result))

if st.session_state.history:
    q, a = st.session_state.history[-1]
    st.markdown(f'<div class="answer"><b>You:</b> {q}<br><br><b>SAI:</b> {a}</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Voice input can be added through a browser microphone component; this deployment is designed to be Streamlit Cloud friendly.</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
