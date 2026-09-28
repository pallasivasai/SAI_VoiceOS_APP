import re
from tools.google import search_google
from tools.system import calculate, local_answer
from tools.weather import answer_weather

def is_telugu(text: str) -> bool:
    return bool(re.search(r"[\u0C00-\u0C7F]", text or ""))
def is_weather(text: str) -> bool:
    return bool(re.search(r"\b(weather|temperature|rain|forecast|climate|humidity)\b|వాతావరణం|వర్షం|ఉష్ణోగ్రత", text, re.I))
def stop_requested(text: str) -> bool:
    return bool(re.search(r"stop listening|pause listening|listening stop|వినడం ఆపు|ఆపు", text or "", re.I))
def answer(question: str) -> str:
    local = local_answer(question)
    if local: return local
    calc = calculate(question)
    if calc: return calc
    if is_weather(question): return answer_weather(question, "te-IN" if is_telugu(question) else "en-IN")
    return search_google(question, "te-IN" if is_telugu(question) else "en-IN")
