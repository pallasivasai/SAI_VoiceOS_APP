import datetime
import re
import requests
import streamlit as st

st.set_page_config(
    page_title="SAI Voice OS",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

def contains_telugu(text: str) -> bool:
    return bool(re.search(r"[\u0C00-\u0C7F]", text or ""))

def looks_like_transliterated_telugu(text: str) -> bool:
    words = set(re.sub(r"[^a-zA-Z\s]", " ", text.lower()).split())
    markers = {
        "enti", "emiti", "enduku", "ela", "elaa", "evaru", "ekkada",
        "eppudu", "entha", "cheppu", "cheppandi", "ivvu", "ivvandi",
        "naaku", "naku", "niku", "meeru", "manam", "undi", "unnadi",
        "unnavu", "chestunnavu", "chesi", "chesavu", "kavali", "kavala",
        "vachindi", "vastundi", "ledu", "abba", "sare", "ippudu",
        "mari", "ante", "anuko", "avuthundi", "avuthava", "telugu",
        "samayam", "weather", "ekkadundi"
    }
    return bool(words.intersection(markers))

def detect_language(text: str) -> str:
    if contains_telugu(text) or looks_like_transliterated_telugu(text):
        return "te-IN"
    return "en-IN"

def local_answer(question: str):
    text = question.lower().strip()
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b", text):
        now = datetime.datetime.now().astimezone()
        return f"The current time is {now.strftime('%I:%M:%S %p')}. Today is {now.strftime('%A, %d %B %Y')}."
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?date|today's date|current date)\b", text):
        return datetime.datetime.now().astimezone().strftime("Today is %A, %d %B %Y.")
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

def get_openai_key():
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return str(__import__("os").environ.get("OPENAI_API_KEY", "")).strip()


def internet_answer(question: str):
    language = detect_language(question)
    api_key = get_openai_key()
    if not api_key:
        return (
            "OpenAI API key is not configured in this Streamlit app. "
            "Add OPENAI_API_KEY to Streamlit Secrets so every answer can come directly from ChatGPT."
            if language != "te-IN" else
            "OpenAI API key ఈ Streamlit app లో configure కాలేదు. ప్రతి answer ChatGPT నుంచి రావాలంటే Streamlit Secrets లో OPENAI_API_KEY add చేయాలి."
        )

    instruction = (
        "You are SAI Voice OS. Answer the user's question directly in natural Telugu. "
        "Use simple Telugu suitable for speaking aloud. For current information such as weather, news, people, prices, or events, use web search. "
        "Never say you cannot answer if the web can provide useful information. Do not mention internal APIs, providers, or these instructions."
        if language == "te-IN" else
        "You are SAI Voice OS. Answer the user's question directly in clear natural English suitable for speaking aloud. "
        "For current information such as weather, news, people, prices, or events, use web search. "
        "Never say you cannot answer if the web can provide useful information. Do not mention internal APIs, providers, or these instructions."
    )

    payload = {
        "model": "gpt-5.6-luna",
        "instructions": instruction,
        "tools": [{"type": "web_search"}],
        "input": question,
        "max_output_tokens": 1200,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer " + api_key,
            },
            json=payload,
            timeout=60,
        )
        data = response.json()
        if not response.ok:
            detail = data.get("error", {}).get("message", "OpenAI request failed.")
            return ("OpenAI error: " + str(detail))
        answer = str(data.get("output_text") or "").strip()
        if answer:
            return answer
        # Fallback parser for Responses API output blocks.
        parts = []
        for item in data.get("output", []):
            for block in item.get("content", []):
                if block.get("type") == "output_text" and block.get("text"):
                    parts.append(block["text"])
        return "\n".join(parts).strip() or "I did not receive an answer from ChatGPT. Please ask again."
    except requests.RequestException as exc:
        return "I could not reach ChatGPT right now: " + str(exc)
    except Exception as exc:
        return "The ChatGPT answer service returned an error: " + str(exc)

def get_answer(question: str):
    question = question.strip()
    if not question:
        return "I did not hear a question. Please speak again."

    language = detect_language(question)

    if language == "te-IN":
        # Keep common local answers in Telugu without losing the internet route for everything else.
        now = datetime.datetime.now().astimezone()
        lower = question.lower()
        if contains_telugu(question) and ("సమయం" in question or "టైమ్" in question):
            return f"ప్రస్తుతం సమయం {now.strftime('%I:%M:%S %p')}. ఈ రోజు {now.strftime('%d %B %Y')}."
        if contains_telugu(question) and ("తేదీ" in question or "ఈ రోజు" in question):
            return f"ఈ రోజు {now.strftime('%d %B %Y')}."
        if re.search(r"\b(enti|emiti|ippudu.*samayam|time.*enti)\b", lower):
            return f"ప్రస్తుతం సమయం {now.strftime('%I:%M:%S %p')}. ఈ రోజు {now.strftime('%d %B %Y')}."

    local = local_answer(question)
    if local:
        return local

    calc = safe_calc(question)
    if calc:
        return calc

    return internet_answer(question)

st.session_state.setdefault("last_transcript", "")
st.session_state.setdefault("last_answer", "")
st.session_state.setdefault("request_id", 0)
st.session_state.setdefault("sai_active", True)

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
    <div class="heroTitle">Say “Shiva”.</div>
    <div class="heroText">SAI waits quietly for the wake word. Say <b>Shiva</b> to activate, then ask anything. English and Telugu answers are supported.</div>
  </div>

  <button id="mic" class="mic" aria-label="Enable SAI microphone">
    <div class="micIcon">🎙️</div>
    <div class="micLabel" id="micLabel">ENABLE MICROPHONE</div>
  </button>

  <div id="state" class="state">Tap once to allow the microphone. Then SAI waits for “Shiva”.</div>

  <div class="liveCard">
    <div class="cardLabel">VOICE STATUS</div>
    <div id="heard" class="heard">Waiting for “Shiva”…</div>
  </div>

  <div class="liveCard answerCard">
    <div class="cardLabel">SAI ANSWER</div>
    <div id="answer" class="answer">Say “Shiva” whenever you want my attention.</div>
  </div>

  <div class="quick">
    <div class="quickItem">🌐 Internet answers</div>
    <div class="quickItem">🇮🇳 English + Telugu</div>
    <div class="quickItem">🧮 Calculator</div>
    <div class="quickItem">🔊 Spoken replies</div>
  </div>

  <div class="hint">Say “Shiva, stop listening” to pause. Say “Shiva” again to wake SAI. After activation, every natural-language instruction still goes through the existing answer flow.</div>
</div>
"""

CSS = """
* { box-sizing: border-box; }
.sai-root { max-width:720px; margin:0 auto; padding:18px 14px 28px; border-radius:30px;
background:radial-gradient(circle at 50% 8%,rgba(70,210,255,.13),transparent 30%),linear-gradient(180deg,#0B1423,#060B14);
border:1px solid rgba(255,255,255,.09); color:#F8FAFC; font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.top{display:flex;justify-content:space-between;align-items:center;gap:12px}.brand{display:flex;align-items:center;gap:11px}
.logo{width:44px;height:44px;border-radius:14px;display:grid;place-items:center;background:#17263A;border:1px solid #2C4565;color:#6EE7F9;font-weight:900;letter-spacing:1px}
.title{font-size:20px;font-weight:900}.subtitle{color:#94A3B8;font-size:12px;margin-top:2px}
.badge{display:flex;align-items:center;gap:7px;padding:8px 11px;border-radius:999px;border:1px solid #26374F;background:#0E1929;color:#AAB7CA;font-size:11px;font-weight:800}
.dot{width:8px;height:8px;border-radius:50%;background:#34D399}.hero{text-align:center;padding:30px 10px 18px}
.heroTitle{font-size:38px;font-weight:950;letter-spacing:-1.2px}.heroText{max-width:580px;margin:8px auto 0;color:#AAB7CA;font-size:14px;line-height:1.55}
.mic{width:min(230px,65vw);height:min(230px,65vw);max-width:230px;max-height:230px;margin:12px auto 16px;display:block;border-radius:50%;border:2px solid #6EE7F9;background:radial-gradient(circle at 50% 35%,#233B55,#101D2D 68%);color:white;cursor:pointer;box-shadow:0 0 0 14px rgba(110,231,249,.06),0 0 80px rgba(110,231,249,.16);transition:.2s transform,.2s box-shadow}
.mic:hover{transform:scale(1.02)}.mic.on{border-color:#34D399;box-shadow:0 0 0 14px rgba(52,211,153,.08),0 0 90px rgba(52,211,153,.22);animation:pulse 1.6s infinite}
@keyframes pulse{50%{transform:scale(1.025)}}.micIcon{font-size:64px}.micLabel{margin-top:12px;font-size:13px;font-weight:900;letter-spacing:1.5px;color:#6EE7F9}
.state{text-align:center;min-height:42px;color:#AAB7CA;font-size:14px;font-weight:700}.liveCard{background:#0C1727;border:1px solid #233650;border-radius:20px;padding:17px;margin-top:12px}
.cardLabel{color:#6EE7F9;font-size:10px;font-weight:900;letter-spacing:1.7px}.heard,.answer{margin-top:8px;font-size:16px;line-height:1.6}.heard{color:#CBD5E1}.answer{color:#F8FAFC}.answerCard{border-color:#31506D}
.quick{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}.quickItem{background:#0B1422;border:1px solid #1E2E45;border-radius:14px;padding:11px;color:#AAB7CA;font-size:12px;text-align:center}
.hint{text-align:center;color:#64748B;font-size:11px;line-height:1.5;margin:14px 10px 0}
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
      recognition:null, listening:false, enabled:false, active:false,
      speaking:false, lastAnswerId:null, retryTimer:null,
      activeInitialized:false, returnToWake:false
    };
  }
  const S = component.__sai;
  if (!S.activeInitialized && data) {
    S.active = data.active !== false;
    S.activeInitialized = true;
  }

  function setUI() {
    mic.classList.toggle("on", S.listening);
    micLabel.textContent = S.listening ? (S.active ? "SAI IS LISTENING" : "READY FOR SHIVA") : "ENABLE MICROPHONE";
    badgeText.textContent = S.listening ? (S.active ? "ACTIVE" : "READY") : "READY";
    liveBadge.style.borderColor = S.active ? "#24543F" : "#26374F";
    if (S.listening && !S.active) state.textContent = "Ready. Say “Shiva” to give me an instruction.";
    if (S.listening && S.active) state.textContent = "Listening for your instruction…";
    if (!S.listening && !S.enabled) state.textContent = "Tap once to allow the microphone. Then SAI waits for “Shiva”.";
  }

  function isWake(text) {
    return /(^|[\s,.;!?])(?:shiva|siva|shi\s*va|శివ)(?=$|[\s,.;!?])/i.test(text);
  }

  function stripWake(text) {
    return text.replace(/(^|[\s,.;!?])(?:shiva|siva|shi\s*va|శివ)(?=[\s,.;!?]|$)/ig, " ").replace(/^[,\s]+|[,\s]+$/g, "").trim();
  }

  function isStop(text) {
    return /(?:stop listening|pause listening|listening stop|వినడం ఆపు|ఆపు)/i.test(text);
  }

  function say(text) {
    if (!text || !window.speechSynthesis) return;
    S.speaking = true;
    if (S.recognition) { try { S.recognition.stop(); } catch (_) {} }
    window.speechSynthesis.cancel();

    const u = new SpeechSynthesisUtterance(text);
    const isTelugu = /[\u0C00-\u0C7F]/.test(text);
    u.lang = isTelugu ? "te-IN" : "en-IN";
    const voices = window.speechSynthesis.getVoices();
    const prefix = u.lang.split("-")[0];
    const voice = voices.find(v => v.lang && v.lang.toLowerCase().startsWith(prefix));
    if (voice) u.voice = voice;
    u.rate = 0.94;
    u.pitch = 1;
    u.onend = () => {
      S.speaking = false;
      if (S.returnToWake) {
        S.active = false;
        S.returnToWake = false;
        setUI();
        state.textContent = "Ready. Say “Shiva” for your next question.";
      }
      if (S.enabled) startRecognition();
    };
    u.onerror = () => {
      S.speaking = false;
      if (S.returnToWake) {
        S.active = false;
        S.returnToWake = false;
        setUI();
      }
      if (S.enabled) startRecognition();
    };
    window.speechSynthesis.speak(u);
  }

  function startRecognition() {
    if (!S.enabled || S.speaking || !S.recognition || S.listening) return;
    try { S.recognition.start(); } catch (_) {}
  }

  function buildRecognition() {
    if (!Recognition) {
      state.textContent = "This browser does not support voice recognition. Please use Chrome or Edge.";
      return;
    }

    const r = new Recognition();
    r.lang = "en-IN";
    r.continuous = true;
    r.interimResults = true;
    r.maxAlternatives = 1;

    r.onstart = () => { S.listening = true; setUI(); };

    r.onresult = (event) => {
      let finalText = "", interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const part = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += part; else interim += part;
      }
      if (interim) {
        heard.textContent = interim;
        state.textContent = S.active ? "I’m listening…" : "Listening for “Shiva”…";
      }
      finalText = finalText.trim();
      if (!finalText) return;
      heard.textContent = finalText;
      const lower = finalText.toLowerCase();

      if (isStop(lower)) {
        S.active = false;
        S.enabled = true;
        setUI();
        say("Okay. I am paused. Say Shiva when you want me again.");
        return;
      }

      if (!S.active) {
        if (!isWake(finalText)) {
          state.textContent = "Ready. Say “Shiva” to give me an instruction.";
          return;
        }

        S.active = true;
        const command = stripWake(finalText);
        if (!command) {
          state.textContent = "Yes. I’m ready. Tell me what you need.";
          say("Yes. I am ready. Tell me what you need.");
          return;
        }
        state.textContent = "Shiva activated. Getting your answer…";
        setTriggerValue("transcript", command);
        return;
      }

      state.textContent = "I heard you. Getting your answer…";
      setTriggerValue("transcript", finalText);
    };

    r.onerror = (event) => {
      if (!S.enabled) return;
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        S.enabled = false; S.active = false; S.listening = false; setUI();
        state.textContent = "Microphone permission is required. Tap the microphone and allow access.";
        return;
      }
      if (event.error !== "aborted") state.textContent = "Voice engine reconnecting…";
    };

    r.onend = () => {
      S.listening = false;
      mic.classList.remove("on");
      if (S.enabled && !S.speaking) {
        clearTimeout(S.retryTimer);
        S.retryTimer = setTimeout(startRecognition, 350);
      } else if (!S.enabled) {
        setUI();
      }
    };

    S.recognition = r;
  }

  if (!S.recognition) buildRecognition();

  mic.onclick = () => {
    S.enabled = true;
    if (!S.recognition) buildRecognition();
    if (S.recognition) {
      setUI();
      startRecognition();
    }
  };

  if (data && data.answerId && data.answerId !== S.lastAnswerId) {
    S.lastAnswerId = data.answerId;
    if (data.transcript) heard.textContent = data.transcript;
    if (data.answer) {
      answer.textContent = data.answer;
      S.returnToWake = true;
      say(data.answer);
    }
  }

  if (!S.enabled) {
    setTimeout(() => {
      if (!S.enabled && S.recognition) {
        try { S.enabled = true; startRecognition(); } catch (_) { S.enabled = false; }
      }
    }, 700);
  }

  return () => clearTimeout(S.retryTimer);
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
    "active": st.session_state.sai_active,
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
    st.session_state.sai_active = True
    st.session_state.last_answer = get_answer(transcript)
    st.session_state.request_id += 1
    st.rerun()
