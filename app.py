import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="SAI Voice OS", page_icon="🎙️", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] { background:#070B14; color:#F8FAFC; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:720px; padding:1.2rem .8rem 2rem; }
.sai-shell { background:#0D1422; border:1px solid #1F2937; border-radius:28px; padding:26px 22px; box-shadow:0 18px 55px rgba(0,0,0,.30); }
.sai-title { font-size:2.1rem; font-weight:800; }
.sai-sub { color:#94A3B8; margin-top:4px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sai-shell">
  <div class="sai-title">SAI Voice OS</div>
  <div class="sai-sub">Always-on voice-first accessibility assistant</div>
</div>
""", unsafe_allow_html=True)

components.html(r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
*{box-sizing:border-box} body{margin:0;background:#070B14;color:#F8FAFC;font-family:system-ui,-apple-system,Segoe UI,sans-serif}
.card{border:1px solid #1F2937;border-radius:24px;background:#0D1422;padding:22px;text-align:center}
.mic{width:112px;height:112px;border-radius:50%;border:2px solid #6EE7F9;background:#132334;color:#6EE7F9;font-size:46px;cursor:pointer;box-shadow:0 0 0 12px rgba(110,231,249,.07)}
.mic.listening{animation:pulse 1.5s infinite;background:#17384a}
@keyframes pulse{50%{box-shadow:0 0 0 22px rgba(110,231,249,.02),0 0 35px rgba(110,231,249,.28)}}
.status{margin:16px 0 8px;font-weight:800;color:#6EE7F9}.heard{color:#CBD5E1;min-height:28px}
.answer{margin-top:16px;text-align:left;padding:16px;border-radius:16px;background:#101827;border:1px solid #243248;line-height:1.55}
.note{color:#64748B;font-size:13px;margin-top:14px}
</style>
</head>
<body>
<div class="card">
<button id="mic" class="mic" aria-label="SAI microphone">🎙️</button>
<div id="status" class="status">STARTING SAI…</div>
<div id="heard" class="heard">Please allow microphone access.</div>
<div id="answer" class="answer">SAI is ready.</div>
<div class="note">SAI keeps listening and automatically restarts the voice engine when the browser ends a recognition session.</div>
</div>
<script>
(function(){
const R=window.SpeechRecognition||window.webkitSpeechRecognition;
const mic=document.getElementById("mic"),status=document.getElementById("status"),heard=document.getElementById("heard"),box=document.getElementById("answer");
const URL="https://jgubunffqfyapurxpoih.supabase.co/functions/v1/sai-claude";
let rec=null,shouldListen=true,starting=false,speaking=false;
function speak(t){if(!("speechSynthesis"in window))return;speaking=true;speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);u.lang="en-IN";u.rate=.95;u.onend=()=>{speaking=false;setTimeout(start,250)};u.onerror=()=>{speaking=false;setTimeout(start,250)};speechSynthesis.speak(u)}
function setStatus(t,l){status.textContent=t;mic.classList.toggle("listening",!!l)}
function isTime(t){return /\b(what(?:'s| is)?\s+(?:the\s+)?time|time\s+now|current\s+time|what time is it|tell me the time)\b/i.test(t)}
async function answer(q){
if(isTime(q)){const n=new Date(),tm=new Intl.DateTimeFormat("en-IN",{hour:"numeric",minute:"2-digit",second:"2-digit",hour12:true}).format(n),dt=new Intl.DateTimeFormat("en-IN",{weekday:"long",day:"numeric",month:"long",year:"numeric"}).format(n);return "The current time is "+tm+". Today is "+dt+"."}
setStatus("SEARCHING THE INTERNET…",false);box.textContent="Getting an answer from the internet…";
try{const r=await fetch(URL,{method:"POST",headers:{"Content-Type":"application/json","apikey":"public-web-client"},body:JSON.stringify({question:q,language:"en-IN",timezone:Intl.DateTimeFormat().resolvedOptions().timeZone||"Asia/Kolkata"})});const d=await r.json();if(!r.ok||!d.answer)throw Error(d.error||"failed");return d.answer}catch(e){return"I could not reach the internet answer service right now. Please try again."}}
async function process(q){q=(q||"").trim();if(!q)return;shouldListen=false;setStatus("THINKING…",false);heard.textContent="You said: "+q;const a=await answer(q);box.textContent=a;setStatus("ANSWERING…",false);speak(a);shouldListen=true}
function start(){if(!shouldListen||speaking||starting)return;if(!R){setStatus("BROWSER VOICE NOT SUPPORTED",false);box.textContent="Please use Chrome for SAI voice.";return}try{starting=true;rec.start()}catch(e){starting=false;setTimeout(start,700)}}
if(!R){setStatus("BROWSER VOICE NOT SUPPORTED",false);box.textContent="Please use Chrome for the SAI always-on voice interface."}
else{
rec=new R();rec.lang="en-IN";rec.continuous=true;rec.interimResults=true;rec.maxAlternatives=1;
rec.onstart=()=>{starting=false;setStatus("LISTENING — SPEAK ANYTIME",true)}
rec.onresult=async(e)=>{let t="";for(let i=e.resultIndex;i<e.results.length;i++){if(e.results[i].isFinal)t+=e.results[i][0].transcript;else heard.textContent="Hearing: "+e.results[i][0].transcript}if(t.trim())await process(t)}
rec.onerror=(e)=>{starting=false;if(e.error==="not-allowed"||e.error==="service-not-allowed"){shouldListen=false;setStatus("MICROPHONE PERMISSION NEEDED",false);box.textContent="Allow microphone access for this site, then refresh the page.";return}if(shouldListen&&!speaking){setStatus("RECONNECTING VOICE…",false);setTimeout(start,800)}}
rec.onend=()=>{starting=false;if(shouldListen&&!speaking)setTimeout(start,350)}
setTimeout(start,500);mic.addEventListener("click",()=>{shouldListen=true;start()})
}
})();
</script>
</body>
</html>
""", height=430, scrolling=False)
