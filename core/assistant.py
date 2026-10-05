import re
from collections import deque
from core.gemini import ask_gemini
from tools.system import calculate, local_answer


def is_telugu(text: str) -> bool:
    return bool(re.search(r"[\u0C00-\u0C7F]", text or ""))


def is_weather(text: str) -> bool:
    return bool(
        re.search(
            r"\b(weather|temperature|rain|forecast|climate|humidity)\b|వాతావరణం|వర్షం|ఉష్ణోగ్రత",
            text or "",
            re.I,
        )
    )


def stop_requested(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:stop listening|pause listening|listening stop)\b|వినడం ఆపు|ఆపు",
            text or "",
            re.I,
        )
    )


def wake_requested(text: str) -> bool:
    normalized = " ".join((text or "").lower().split())
    return bool(
        re.search(
            r"(^|\s)(?:shiva|siva|shi\s*va|sheeva|sheva|seeva|శివ)(?=\s|$)",
            normalized,
            re.I,
        )
    )


def clean_wake(text: str) -> str:
    return re.sub(
        r"(^|[\s,.;!?])(?:shiva|siva|shi\s*va|sheeva|sheva|seeva|శివ)(?=[\s,.;!?]|$)",
        " ",
        text or "",
        flags=re.I,
    ).strip()


class Conversation:
    """Persistent multi-turn conversation state for the native SAI voice engine."""

    def __init__(self, max_turns: int = 10):
        self.history = deque(maxlen=max_turns * 2)

    def answer(self, question: str) -> str:
        question = question.strip()
        if not question:
            return "I did not hear you. Please say that again."

        local = local_answer(question)
        if local:
            self._remember(question, local)
            return local

        calc = calculate(question)
        if calc:
            self._remember(question, calc)
            return calc

        language = "te-IN" if is_telugu(question) else "en-IN"
        context = list(self.history)
        answer = ask_gemini(
            question,
            language=language,
            history=context,
        )
        self._remember(question, answer)
        return answer

    def _remember(self, question: str, answer: str):
        self.history.append(("user", question))
        self.history.append(("assistant", answer))


_default = Conversation()


def answer(question: str) -> str:
    return _default.answer(question)
