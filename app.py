import datetime
import os
import html
import re
from urllib.parse import quote_plus, urlparse, parse_qs, unquote
import requests
import streamlit as st

try:
    import google.generativeai as genai
except ImportError:
    genai = None
from zoneinfo import ZoneInfo

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
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time|what is time|samayam|time ippudu|ippudu time)\b", text):
        now = datetime.datetime.now(ZoneInfo("Asia/Kolkata"))
        return f"The current time in India is {now.strftime('%I:%M:%S %p')}. Today is {now.strftime('%A, %d %B %Y')}."
    if re.search(r"\b(what(?:'s| is)?\s+(?:the\s+)?date|today's date|current date|today date|ee roju date)\b", text):
        return datetime.datetime.now(ZoneInfo("Asia/Kolkata")).strftime("Today is %A, %d %B %Y.")
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

def _google_result_text(raw_html: str, language: str) -> str:
    page = html.unescape(raw_html)

    def tag_text(tag_id: str):
        patterns = [
            rf'<(?:div|span)[^>]+id=[\"\']{re.escape(tag_id)}[\"\'][^>]*>(.*?)</(?:div|span)>',
            rf'<(?:div|span)[^>]+class=[\"\'][^\"\']*{re.escape(tag_id)}[^\"\']*[\"\'][^>]*>(.*?)</(?:div|span)>',
        ]
        for pattern in patterns:
            match = re.search(pattern, page, flags=re.I | re.S)
            if match:
                value = re.sub(r"<[^>]+>", " ", match.group(1))
                return re.sub(r"\s+", " ", html.unescape(value)).strip()
        return ""

    weather_location = tag_text("wob_loc")
    weather_time = tag_text("wob_dts")
    weather_condition = tag_text("wob_dc")
    weather_temp = tag_text("wob_tm")
    weather_humidity = tag_text("wob_hm")
    weather_wind = tag_text("wob_ws")
    if weather_condition or weather_temp:
        parts = [p for p in [weather_location, weather_time, weather_condition] if p]
        if weather_temp:
            parts.append(f"{weather_temp} degrees Celsius")
        if weather_humidity:
            parts.append(f"Humidity {weather_humidity}")
        if weather_wind:
            parts.append(f"Wind {weather_wind}")
        return "Current weather: " + ". ".join(parts) + "."

    # Google answer/knowledge panels and featured snippets.
    answer_patterns = [
        r'data-attrid="(?:wa:/description|description)"[^>]*>(.*?)</div>',
        r'class="[^"]*(?:VwiC3b|yXK7lf)[^"]*"[^>]*>(.*?)</div>',
    ]

    def clean(fragment: str) -> str:
        fragment = re.sub(r"<script.*?</script>", " ", fragment, flags=re.I | re.S)
        fragment = re.sub(r"<style.*?</style>", " ", fragment, flags=re.I | re.S)
        fragment = re.sub(r"<[^>]+>", " ", fragment)
        fragment = html.unescape(fragment)
        return re.sub(r"\s+", " ", fragment).strip()

    answers = []
    for pattern in answer_patterns:
        for match in re.findall(pattern, page, flags=re.I | re.S):
            text = clean(match)
            if len(text) >= 35 and text not in answers:
                answers.append(text)
            if len(answers) >= 3:
                break
        if len(answers) >= 3:
            break

    # Normal Google result snippets.
    titles = []
    for match in re.findall(r"<h3[^>]*>(.*?)</h3>", page, flags=re.I | re.S):
        title = clean(match)
        if title and title not in titles:
            titles.append(title)

    snippets = []
    for match in re.findall(r'class="[^"]*(?:VwiC3b|yXK7lf)[^"]*"[^>]*>(.*?)</div>', page, flags=re.I | re.S):
        text = clean(match)
        if len(text) >= 35 and text not in snippets:
            snippets.append(text)
        if len(snippets) >= 5:
            break

    if answers:
        return answers[0]

    if snippets:
        parts = []
        for i, snippet in enumerate(snippets[:3]):
            title = titles[i] if i < len(titles) else ""
            parts.append(f"{title}: {snippet}" if title else snippet)
        prefix = "Google search results: " if language != "te-IN" else "Google search results: "
        return prefix + " ".join(parts)

    # Last-resort visible text extraction from Google's response.
    visible = clean(page)
    visible = re.sub(r"Google Search.*?Sign in", " ", visible, flags=re.I)
    if len(visible) > 1200:
        visible = visible[:1200]
    return visible

def _secret(name: str, default: str = "") -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except Exception:
        return default


GEMINI_API_KEY = _secret("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3.5-flash-lite"


def gemini_answer(question: str) -> str:
    """Generate the voice answer with the same free Gemini Flash-Lite setup as SAI-RAG."""
    language = detect_language(question)
    if not GEMINI_API_KEY:
        return (
            "Gemini API key is missing. Please add GEMINI_API_KEY under Streamlit Secrets."
            if language != "te-IN"
            else
            "Gemini API key set cheyyaledu. Streamlit Secrets lo GEMINI_API_KEY add cheyyandi."
        )
    if genai is None:
        return "Gemini library is not installed. Please restart the Streamlit app."

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        system = (
            "You are SAI, a voice-first accessibility assistant for blind users. "
            "Answer naturally, clearly and concisely because your answer will be spoken aloud. "
            "Do not mention Google Search, Streamlit, APIs, or internal implementation unless the user asks. "
            "If the user speaks Telugu or Telugu transliteration, answer in Telugu. "
            "If the user speaks English, answer in English."
        )
        response = model.generate_content(
            [system, question],
            generation_config={
                "temperature": 0.4,
                "max_output_tokens": 512,
            },
        )
        answer = (getattr(response, "text", "") or "").strip()
        return answer or "Gemini did not return a readable answer."
    except Exception as exc:
        print(f"[SAI] Gemini error: {exc}")
        return (
            "I could not get an answer from Gemini right now. Please try again."
            if language != "te-IN"
            else
            "Gemini nundi answer ippudu raledu. Malli try cheyyandi."
        )


def internet_answer(question: str):
    # Kept as a compatibility wrapper. All normal knowledge answers now come from Gemini.
    return gemini_answer(question)
def reverse_geocode(lat, lon):
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 10},
            headers={"User-Agent": "SAI-Voice-OS/1.0"},
            timeout=8,
        )
        response.raise_for_status()
        address = response.json().get("address", {})
        return (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("village")
            or address.get("county")
        )
    except Exception:
        return None

def extract_weather_place(question: str):
    """Return an explicitly named weather location, if the user supplied one."""
    text = re.sub(r"\s+", " ", question.strip())
    patterns = [
        r"\b(?:weather|temperature|rain|forecast|climate|humidity)\s+(?:in|at|near|for)\s+([A-Za-z][A-Za-z .'-]{1,50}?)(?:\s+(?:now|today|right now|please))?$",
        r"^([A-Za-z][A-Za-z .'-]{1,50}?)\s+(?:weather|temperature|forecast|climate)$",
        r"^what(?:'s| is)?\s+(?:the\s+)?(?:weather|temperature)(?:\s+(?:now|today|right now))?\s+(?:in|at|near|for)\s+([A-Za-z][A-Za-z .'-]{1,50}?)(?:\s+(?:now|today|right now))?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            place = match.group(1).strip(" ,.-")
            if place and place.lower() not in {"now", "today", "right now"}:
                return place
    return None

def get_answer(question: str, location=None):
    question = question.strip()
    if not question:
        return "I did not hear a question. Please speak again."

    # Shiva/wake-word behavior stays unchanged. Normal knowledge answers use Gemini Flash-Lite.
    local = local_answer(question)
    if local:
        return local

    calc = safe_calc(question)
    if calc:
        return calc

    weather_query = bool(re.search(r"\b(weather|temperature|rain|forecast|climate|humidity)\b", question, re.I))
    if weather_query:
        explicit_place = extract_weather_place(question)
        if explicit_place:
            question = f"weather in {explicit_place}"
        elif location:
            try:
                lat = float(location.get("lat"))
                lon = float(location.get("lon"))
                place = reverse_geocode(lat, lon)
                if place:
                    question = f"weather in {place}"
            except Exception:
                pass
        else:
            language = detect_language(question)
            return (
                "మీరు ఏ location లో weather కావాలనుకుంటున్నారు? City or area చెప్పండి."
                if language == "te-IN"
                else
                "I don't have your location permission. Which city or area would you like the weather for?"
            )

    return gemini_answer(question)


st.session_state.setdefault("last_transcript", "")
st.session_state.setdefault("last_answer", "")
st.session_state.setdefault("request_id", 0)
st.session_state.setdefault("sai_active", True)
st.session_state.setdefault("last_location", None)
st.session_state.setdefault("last_voice_event_id", 0)
st.session_state.setdefault("awaiting_weather_location", False)

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
    <div class="heroText">SAI waits quietly for <b>Shiva</b>. After activation, SAI stays ready for every next command. Gemini answers naturally and speaks the response back to you.</div>
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
    <div class="quickItem">✨ Gemini Flash-Lite answers</div>
    <div class="quickItem">🇮🇳 English + Telugu</div>
    <div class="quickItem">🧮 Calculator</div>
    <div class="quickItem">🔊 Spoken replies</div>
  </div>

  <div class="hint">Say “Shiva” to activate SAI. After activation, ask as many questions as you want. Say “Shiva, stop listening” to pause.</div>
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
  const { parentElement, data, setStateValue, setTriggerValue } = component;
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
      activeInitialized:false, returnToWake:false, location:null,
      lastFinalText:"", lastProcessedAt:0, pendingQuestion:"", awaitingWeatherLocation:false, pausedByUser:false
    };
  }
  const S = component.__sai;
  if (!S.activeInitialized && data) {
    S.active = data.active !== false;
    S.location = data.location || null;
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

  function isWeatherQuestion(text) {
    return /\b(weather|temperature|rain|forecast|climate|humidity)\b|\b(వాతావరణం|వర్షం|ఉష్ణోగ్రత)\b/i.test(text);
  }

  function hasExplicitWeatherLocation(text) {
    if (!isWeatherQuestion(text)) return false;
    return /\b(?:weather|temperature|rain|forecast|climate|humidity)\s+(?:in|at|near|for)\s+[A-Za-z][A-Za-z .'-]{1,50}/i.test(text)
      || /^[A-Za-z][A-Za-z .'-]{1,50}\s+(?:weather|temperature|forecast|climate)$/i.test(text);
  }

  function sendVoiceEvent(question, location) {
    setTriggerValue("voice_event", JSON.stringify({
      id: Date.now(),
      transcript: question || "",
      location: location || null
    }));
  }

  // Weather location handling is permission-aware:
  // explicit locations never request browser geolocation; otherwise ask for
  // permission first, and if denied, ask the user for a city/location.
  function requestLocationIfNeeded() {
    if (!navigator.geolocation) {
      const message = "I cannot access your location. Which location's weather would you like?";
      S.awaitingWeatherLocation = true;
      S.pendingQuestion = "";
      state.textContent = message;
      say(message);
      return;
    }
    if (!isWeatherQuestion(S.pendingQuestion || "")) return;
    if (hasExplicitWeatherLocation(S.pendingQuestion || "")) {
      state.textContent = "Searching Google for that location's weather…";
      sendVoiceEvent(S.pendingQuestion, null);
      S.pendingQuestion = "";
      return;
    }
    state.textContent = "Getting your current location and checking the weather…";
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        S.location = {lat: pos.coords.latitude, lon: pos.coords.longitude};
        setTriggerValue("voice_event", JSON.stringify({id: Date.now(), transcript: S.pendingQuestion || "", location: S.location}));
        S.pendingQuestion = "";
      },
      () => {
        const message = "I do not have location permission. Which location's weather would you like?";
        S.awaitingWeatherLocation = true;
        S.pendingQuestion = "";
        state.textContent = message;
        S.active = true;
        S.pausedByUser = false;
        setUI();
        say(message);
      },
      {enableHighAccuracy:true, timeout:10000, maximumAge:0}
    );
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
      S.returnToWake = false;
      S.active = !S.pausedByUser;
      setUI();
      state.textContent = S.active ? "Listening for your next instruction…" : "Paused. Say “Shiva” when you want me again.";
      if (S.enabled && S.active) startRecognition();
    };
    u.onerror = () => {
      S.speaking = false;
      S.returnToWake = false;
      S.active = !S.pausedByUser;
      setUI();
      state.textContent = S.active ? "Listening for your next instruction…" : "Paused. Say “Shiva” when you want me again.";
      if (S.enabled && S.active) startRecognition();
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
        S.pausedByUser = true;
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
        S.pausedByUser = false;
        S.awaitingWeatherLocation = false;
        const command = stripWake(finalText);
        if (!command) {
          state.textContent = "Yes. I’m ready. Tell me what you need.";
          say("Yes. I am ready. Tell me what you need.");
          return;
        }
        state.textContent = "Shiva activated. Getting your answer…";
        if (isWeatherQuestion(command)) {
          S.pendingQuestion = command;
          S.location = null;
          S.awaitingWeatherLocation = false;
          state.textContent = hasExplicitWeatherLocation(command)
            ? "Searching Google for that location's weather…"
            : "Getting your current location and checking the weather…";
          requestLocationIfNeeded();
        } else {
          setTriggerValue("voice_event", JSON.stringify({id: Date.now(), transcript: command, location: null}));
        }
        return;
      }

      const cleaned = stripWake(finalText);
      S.pausedByUser = false;
      if (!cleaned) {
        S.active = true;
        setUI();
        state.textContent = "Yes. I am ready. Tell me what you need.";
        say("Yes. I am ready. Tell me what you need.");
        return;
      }

      // If location permission was unavailable, the next spoken phrase is treated
      // as the requested weather location, then the complete weather question is
      // sent to Gemini. The user does not need to say Shiva again.
      if (S.awaitingWeatherLocation) {
        S.awaitingWeatherLocation = false;
        S.pendingQuestion = "";
        const weatherLocation = stripWake(cleaned).replace(/^(?:in|at|near|for)\s+/i, "").trim();
        if (!weatherLocation) {
          state.textContent = "Please tell me the city or location.";
          say("Please tell me the city or location.");
          S.awaitingWeatherLocation = true;
          return;
        }
        const weatherQuestion = "What is the weather today in " + weatherLocation + "?";
        heard.textContent = weatherQuestion;
        state.textContent = "Checking the weather with Gemini…";
        setTriggerValue("voice_event", JSON.stringify({id: Date.now(), transcript: weatherQuestion, location: null}));
        return;
      }

      if (cleaned === S.lastFinalText && (Date.now() - S.lastProcessedAt) < 1200) return;
      S.lastFinalText = cleaned;
      S.lastProcessedAt = Date.now();
      state.textContent = "I heard you. Getting your answer…";

      if (isWeatherQuestion(cleaned)) {
        S.pendingQuestion = cleaned;
        S.location = null;
        S.awaitingWeatherLocation = false;
        state.textContent = hasExplicitWeatherLocation(cleaned)
          ? "Searching Google for that location's weather…"
          : "Getting your current location for the weather…";
        requestLocationIfNeeded();
      } else {
        setTriggerValue("voice_event", JSON.stringify({id: Date.now(), transcript: cleaned, location: null}));
      }
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

  if (data && data.location) S.location = data.location;

  if (data && data.answerId && data.answerId !== S.lastAnswerId) {
    S.lastAnswerId = data.answerId;
    if (data.transcript) heard.textContent = data.transcript;
    if (data.answer) {
      answer.textContent = data.answer;
      const asksForWeatherLocation =
        /which (?:city|area|location).*weather/i.test(data.answer) ||
        /don't have your location permission/i.test(data.answer) ||
        /ఏ location.*weather|city or area చెప్పండి/i.test(data.answer);

      if (asksForWeatherLocation) {
        S.active = true;
        S.pausedByUser = false;
        S.awaitingWeatherLocation = true;
        state.textContent = "Tell me the city or area. You do not need to say Shiva again.";
      }

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
    "location": st.session_state.last_location,
}

result = voice_component(
    data=data,
    key="sai_voice_component",
    on_transcript_change=lambda: None,
    on_voice_event_change=lambda: None,
    width="stretch",
    height="content",
)

voice_event = getattr(result, "voice_event", None)
if voice_event:
    try:
        import json
        event = json.loads(voice_event) if isinstance(voice_event, str) else voice_event
    except Exception:
        event = {}

    event_id = int(event.get("id") or 0)
    transcript = (event.get("transcript") or "").strip()
    location = event.get("location")
    if location:
        st.session_state.last_location = location

    if transcript and event_id != st.session_state.last_voice_event_id:
        st.session_state.last_voice_event_id = event_id

        # Server-side follow-up state: when SAI has just asked for a weather
        # location, the very next spoken phrase is the location. This survives
        # Streamlit reruns and does not require saying Shiva again.
        if st.session_state.awaiting_weather_location:
            weather_location = transcript.strip()
            weather_location = re.sub(
                r"^(?:in|at|near|for)\\s+",
                "",
                weather_location,
                flags=re.I,
            ).strip()
            transcript = f"What is the weather today in {weather_location}?"
            st.session_state.awaiting_weather_location = False

        st.session_state.last_transcript = transcript
        st.session_state.sai_active = True
        st.session_state.last_answer = get_answer(transcript, st.session_state.last_location)

        # If the backend had to ask for a location, keep the follow-up mode
        # alive until the next spoken location arrives.
        st.session_state.awaiting_weather_location = bool(
            re.search(r"which (?:city|area|location).*weather", st.session_state.last_answer, re.I)
            or re.search(r"don't have your location permission", st.session_state.last_answer, re.I)
            or re.search(r"ఏ location.*weather|city or area చెప్పండి", st.session_state.last_answer, re.I)
        )

        st.session_state.request_id += 1
        st.rerun()
