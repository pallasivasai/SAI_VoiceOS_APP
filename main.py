import time
from core.audio import record_command, record_wake_chunk
from core.assistant import answer, stop_requested
from core.config import WAKE_CHUNK_SECONDS
from core.stt import transcribe
from core.tts import Speaker
from core.wake import WakeDetector

class SAI:
    def __init__(self):
        self.speaker = Speaker()
        self.wake = WakeDetector(transcribe)
        self.active = False
    def startup(self):
        print("\nSAI Voice OS\n----------------")
        if self.wake.using_custom_model:
            print("Wake engine: custom Shiva openWakeWord model")
        else:
            print("Wake engine: local Whisper Shiva fallback")
            print("For true low-power Shiva wake detection, add models/shiva.onnx.")
        print("Say 'Shiva' to start. After activation, keep talking naturally. Say 'Shiva, stop listening' to sleep.\n")
        self.speaker.say("SAI is ready. Say Shiva when you need me.")
    def sleep_loop(self):
        self.active = False
        while not self.active:
            try:
                audio = record_wake_chunk(WAKE_CHUNK_SECONDS)
                if self.wake.detect(audio):
                    self.active = True
                    self.speaker.say("Yes. I am ready. Tell me what you need.")
                    return
            except KeyboardInterrupt: raise
            except Exception as exc:
                print(f"[SAI] Wake loop error: {exc}")
                time.sleep(1)
    def active_loop(self):
        while self.active:
            try:
                print("[SAI] Listening...")
                text = transcribe(record_command())
                print(f"YOU: {text or '[no speech]'}")
                if not text:
                    self.speaker.say("I did not hear you. Please say that again.")
                    continue
                if stop_requested(text):
                    self.active = False
                    self.speaker.say("Okay. I am paused. Say Shiva when you want me again.")
                    return
                self.speaker.say(answer(text))
                # Deliberately remain active after every answer.
            except KeyboardInterrupt: raise
            except Exception as exc:
                print(f"[SAI] Active loop error: {exc}")
                self.speaker.say("I had a problem with that request. Please try again.")
    def run(self):
        self.startup()
        while True:
            self.sleep_loop()
            self.active_loop()

if __name__ == "__main__":
    try: SAI().run()
    except KeyboardInterrupt: print("\nSAI Voice OS stopped.")
