import re
import requests
from .google import search_google

def explicit_place(question: str):
    text = re.sub(r"\s+", " ", question.strip())
    patterns = [
        r"(?:weather|temperature|rain|forecast|climate|humidity)\s+(?:in|at|near|for)\s+([A-Za-z][A-Za-z .'-]{1,50}?)(?:\s+(?:now|today|right now))?$",
        r"^([A-Za-z][A-Za-z .'-]{1,50}?)\s+(?:weather|temperature|forecast|climate)$",
        r"what(?:'s| is)?\s+(?:the\s+)?(?:weather|temperature)(?:\s+(?:now|today|right now))?\s+(?:in|at|near|for)\s+([A-Za-z][A-Za-z .'-]{1,50}?)(?:\s+(?:now|today|right now))?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            place = match.group(1).strip(" ,.-")
            if place.lower() not in {"now", "today", "right now"}:
                return place
    return None

def current_ip_place():
    try:
        data = requests.get("https://ipapi.co/json/", timeout=7).json()
        return data.get("city") or data.get("region")
    except Exception:
        return None

def answer_weather(question: str, language="en-IN") -> str:
    place = explicit_place(question) or current_ip_place()
    query = f"weather in {place}" if place else question
    return search_google(query, language)
