import datetime
import json
import re
import requests
import streamlit as st

st.set_page_config(
    page_title="SAI Voice OS",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# SAI backend
# -----------------------------
SAI_ENDPOINT = "https://jgubunffqfyapurxpoih.supabase.co/functions/v1/sai-claude"

def local_answer(question: str):
    text = question.lower().strip()

    if re.search(
        r"\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b",
        text,
    ):
        now = datetime.datetime.now().astimezone()
        return (
            f"The current time is {now.strftime('%I:%M:%S %p')}. "
            f"Today is {now.strftime('%A, %d %B %Y')}."
        )

    if re.search(
        r"\b(what(?:'s| is)?\s+(?:the\s+)?date|today's date|current date)\b",
        text,
    ):
        return datetime.datetime.now().astimezone().strftime(
            "Today is %A, %d %B %Y."
        )

    return None

def safe_calc(question: str):
    expr = question.lower()
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

def internet_answer(question: str):
    try:
        tz = datetime.datetime.now().astimezone().tzinfo
        timezone = tz.key if hasattr(tz, "key") else "Asia/Kolkata"

        response = requests.post(
            SAI_ENDPOINT,
            headers={
                "Content-Type": "application/json",
                "apikey": "public-web-client",
            },
            json={
                "question": question,
                "language": "en-IN",
                "timezone": timezone,
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

        return "The internet answer service did not return an answer."

    except requests.RequestException:
        return "I could not reach the internet answer service right now. Please try again."
    except Exception:
        return "The SAI answer service returned an unexpected response."

def get_answer(question: str):
    question = question.strip()
    if not question:
        return "I did not hear a question. Please speak again."

    local = local_answer(question)
    if local:
        return local

    calc = safe_calc(question)
    if calc:
        return calc

    # All other natural-language requests use the internet-backed SAI service.
    return internet_answer(question)

# -----------------------------
# Session state
# -----------------------------
st.session_state.setdefault("last_transcript", "")
st.session_state.setdefault("last_answer", "")
st.session_state.setdefault("request_id", 0)

# -----------------------------
# Always-on voice component
# -----------------------------
HTML = """
<div class="sai-root">
  <div class="top">
    <div class="brand">
      <div class="logo">SAI</div>
      <div>
        <div class="title">SAI Voice OS</div>
        <div class="subtitle">Voice-first accessibility assistant</div>
      </div>
    </div>
    <div id="liveBadge" class="badge"><span class="dot"></span><span id="badgeText">READY</span></div>
  </div>

  <div class="hero">
    <div class="heroTitle">Just speak.</div>
    <div class="heroText">No typing. No text box. SAI keeps listening and answers your questions aloud.</div>
  </div>

  <button id="mic" class="mic" aria-label="Enable SAI microphone">
    <div class="micIcon">🎙️</div>
    <div class="micLabel" id="micLabel">ENABLE MICROPHONE</div>
  </button>

  <div id="state" class="state">Tap once to start SAI. After that, listening stays on.</div>

  <div class="liveCard">
    <div class="cardLabel">I HEARD</div>
    <div id="heard" class="heard">Waiting for your voice…</div>
  </div>

  <div class="liveCard answerCard">
    <div class="cardLabel">SAI ANSWER</div>
    <div id="answer" class="answer">Your answer will appear here and be spoken aloud.</div>
  </div>

  <div class="quick">
    <div class="quickItem">🌐 Internet answers</div>
    <div class="quickItem">⏰ Time & date</div>
    <div class="quickItem">🧮 Calculator</div>
    <div class="quickItem">🔊 Spoken replies</div>
  </div>

  <div class="hint">Say “SAI, stop listening” if you need to pause. Say “SAI, start listening” to resume.</div>
</div>
"""

CSS = """
* { box-sizing: border-box; }
.sai-root {
  max-width: 720px;
  margin: 0 auto;
  padding: 18px 14px 28px;
  border-radius: 30px;
  background:
    radial-gradient(circle at 50% 8%, rgba(70,210,255,.13), transparent 30%),
    linear-gradient(180deg,#0B1423,#060B14);
  border: 1px solid rgba(255,255,255,.09);
  color: #F8FAFC;
  font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.top {
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:12px;
}
.brand { display:flex; align-items:center; gap:11px; }
.logo {
  width:44px; height:44px; border-radius:14px;
  display:grid; place-items:center;
  background:#17263A; border:1px solid #2C4565;
  color:#6EE7F9; font-weight:900; letter-spacing:1px;
}
.title { font-size:20px; font-weight:900; }
.subtitle { color:#94A3B8; font-size:12px; margin-top:2px; }
.badge {
  display:flex; align-items:center; gap:7px;
  padding:8px 11px; border-radius:999px;
  border:1px solid #26374F; background:#0E1929;
  color:#AAB7CA; font-size:11px; font-weight:800;
}
.dot { width:8px; height:8px; border-radius:50%; background:#34D399; }
.hero { text-align:center; padding:30px 10px 18px; }
.heroTitle { font-size:38px; font-weight:950; letter-spacing:-1.2px; }
.heroText { max-width:560px; margin:8px auto 0; color:#AAB7CA; font-size:14px; line-height:1.55; }
.mic {
  width:min(230px,65vw); height:min(230px,65vw);
  max-width:230px; max-height:230px;
  margin:12px auto 16px; display:block;
  border-radius:50%; border:2px solid #6EE7F9;
  background:radial-gradient(circle at 50% 35%,#233B55,#101D2D 68%);
  color:white; cursor:pointer;
  box-shadow:0 0 0 14px rgba(110,231,249,.06),0 0 80px rgba(110,231,249,.16);
  transition:.2s transform,.2s box-shadow;
}
.mic:hover { transform:scale(1.02); }
.mic.on {
  border-color:#34D399;
  box-shadow:0 0 0 14px rgba(52,211,153,.08),0 0 90px rgba(52,211,153,.22);
  animation:pulse 1.6s infinite;
}
@keyframes pulse { 50% { transform:scale(1.025); } }
.micIcon { font-size:64px; }
.micLabel { margin-top:12px; font-size:13px; font-weight:900; letter-spacing:1.5px; color:#6EE7F9; }
.state { text-align:center; min-height:42px; color:#AAB7CA; font-size:14px; font-weight:700; }
.liveCard {
  background:#0C1727; border:1px solid #233650;
  border-radius:20px; padding:17px; margin-top:12px;
}
.cardLabel { color:#6EE7F9; font-size:10px; font-weight:900; letter-spacing:1.7px; }
.heard,.answer { margin-top:8px; font-size:16px; line-height:1.6; }
.heard { color:#CBD5E1; }
.answer { color:#F8FAFC; }
.answerCard { border-color:#31506D; }
.quick { display:grid; grid-template-columns:1fr 1fr; gap:9px; margin-top:12px; }
.quickItem {
  background:#0B1422; border:1px solid #1E2E45;
  border-radius:14px; padding:11px; color:#AAB7CA;
  font-size:12px; text-align:center;
}
.hint { text-align:center; color:#64748B; font-size:11px; line-height:1.5; margin:14px 10px 0; }
"""

JS = """
export default function(component) {
  const { parentElement, data, setTriggerValue } = component;
  const mic = parentElement.querySelector("#mic");
  const micLabel = parentElement.querySelector("#micLabel");
  const state = parentElement.querySelector("#state");
  const heard = parentElement.querySelector("#heard");
  const answer = parentElement.querySelector("#answer");
  const badgeText = parentElement.querySelector("#badgeText");
  const liveBadge = parentElement.querySelector("#liveBadge");

  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!component.__sai) {
    component.__sai = {
      recognition: null,
      listening: false,
      enabled: false,
      speaking: false,
      lastAnswerId: null,
      retryTimer: null
    };
  }

  const S = component.__sai;

  function setUI(on, message) {
    S.listening = on;
    mic.classList.toggle("on", on);
    micLabel.textContent = on ? "SAI IS LISTENING" : "ENABLE MICROPHONE";
    badgeText.textContent = on ? "LISTENING" : "READY";
    liveBadge.style.borderColor = on ? "#24543F" : "#26374F";
    state.textContent = message || (on
      ? "Listening continuously. Speak naturally."
      : "Tap once to start SAI. After that, listening stays on.");
  }

  function say(text) {
    if (!text || !window.speechSynthesis) return;

    S.speaking = true;
    if (S.recognition) {
      try { S.recognition.stop(); } catch (_) {}
    }

    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-IN";
    u.rate = 0.94;
    u.pitch = 1;

    u.onend = () => {
      S.speaking = false;
      if (S.enabled) startRecognition();
    };
    u.onerror = () => {
      S.speaking = false;
      if (S.enabled) startRecognition();
    };

    window.speechSynthesis.speak(u);
  }

  function startRecognition() {
    if (!S.enabled || S.speaking || !S.recognition || S.listening) return;

    try {
      S.recognition.start();
    } catch (_) {
      // Browser can report "already started"; onend will recover.
    }
  }

  function buildRecognition() {
    if (!Recognition) {
      setUI(false, "This browser does not support voice recognition. Please use Chrome or Edge.");
      return;
    }

    const r = new Recognition();
    r.lang = "en-IN";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 1;

    r.onstart = () => {
      setUI(true, "Listening continuously. Speak naturally.");
    };

    r.onresult = (event) => {
      let finalText = "";
      let interim = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const part = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += part;
        else interim += part;
      }

      if (interim) {
        heard.textContent = interim;
        state.textContent = "I’m listening…";
      }

      finalText = finalText.trim();
      if (!finalText) return;

      heard.textContent = finalText;
      state.textContent = "I heard you. Getting your answer…";

      const lower = finalText.toLowerCase();
      if (/\b(sai[, ]*)?\s*stop listening\b/i.test(lower)) {
        S.enabled = false;
        try { r.stop(); } catch (_) {}
        setUI(false, "SAI is paused. Tap the microphone to resume.");
        say("Okay. SAI listening is paused.");
        return;
      }

      if (/\b(sai[, ]*)?\s*start listening\b/i.test(lower)) {
        S.enabled = true;
        startRecognition();
        return;
      }

      setTriggerValue("transcript", finalText);
    };

    r.onerror = (event) => {
      if (!S.enabled) return;

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        S.enabled = false;
        setUI(false, "Microphone permission is required. Tap the microphone and allow access.");
        return;
      }

      if (event.error !== "aborted") {
        state.textContent = "Voice engine reconnecting…";
      }
    };

    r.onend = () => {
      S.listening = false;
      mic.classList.remove("on");

      if (S.enabled && !S.speaking) {
        clearTimeout(S.retryTimer);
        S.retryTimer = setTimeout(startRecognition, 350);
      } else if (!S.enabled) {
        setUI(false, "SAI is paused. Tap the microphone to resume.");
      }
    };

    S.recognition = r;
  }

  if (!S.recognition) buildRecognition();

  mic.onclick = () => {
    S.enabled = true;
    if (!S.recognition) buildRecognition();
    if (S.recognition) {
      setUI(true, "Starting microphone…");
      startRecognition();
    }
  };

  if (data && data.answerId && data.answerId !== S.lastAnswerId) {
    S.lastAnswerId = data.answerId;
    if (data.transcript) heard.textContent = data.transcript;
    if (data.answer) {
      answer.textContent = data.answer;
      say(data.answer);
    }
  }

  // Try to start automatically. Browsers may require one initial user gesture.
  if (!S.enabled) {
    setTimeout(() => {
      if (!S.enabled && S.recognition) {
        try {
          S.enabled = true;
          startRecognition();
        } catch (_) {
          S.enabled = false;
        }
      }
    }, 700);
  }

  return () => {
    clearTimeout(S.retryTimer);
  };
}
"""

voice_component = st.components.v2.component(
    "sai_always_on_voice",
    html=HTML,
    css=CSS,
    js=JS,
    isolate_styles=True,
)

data = {
    "transcript": st.session_state.last_transcript,
    "answer": st.session_state.last_answer,
    "answerId": st.session_state.request_id,
}

result = voice_component(
    data=data,
    key="sai_voice_component",
    on_transcript_change=lambda: None,
    width="stretch",
    height="content",
)

transcript = getattr(result, "transcript", None)

if transcript and transcript != st.session_state.last_transcript:
    st.session_state.last_transcript = transcript
    st.session_state.last_answer = get_answer(transcript)
    st.session_state.request_id += 1
    st.rerun()
