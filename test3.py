from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from gtts import gTTS
import pygame
import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import os
import time

load_dotenv("key.env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Modèles à essayer en ordre
MODELS = [
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-3-1b-it:free",
]

print("⏳ Chargement de Whisper...")
stt_model = whisper.load_model("base")
print("✅ Whisper prêt !\n")

def speak(text: str):
    print(f"🔊 Abdou : {text}")
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except:
        pass
    tts = gTTS(text, lang="fr")
    tts.save("audio.mp3")
    pygame.mixer.init()
    pygame.mixer.music.load("audio.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.unload()
    pygame.mixer.quit()

def listen() -> str:
    duration = 5
    sample_rate = 16000
    print("🎤 Je t'écoute...")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32"
    )
    sd.wait()

    volume = np.abs(audio).mean()
    print(f"📊 Volume détecté : {volume:.4f}")

    if volume < 0.001:
        print("❌ Je n'ai rien entendu... Parle plus fort !")
        return ""

    print("✅ Je t'ai entendu ! Traitement...")
    audio_flat = audio.flatten()
    result = stt_model.transcribe(audio_flat, language="fr")  # ← forcer français
    text = result["text"].strip()
    print(f"👂 Tu as dit : '{text}'")
    return text

def ask_llm(messages, retries=3) -> str:
    """Essaie plusieurs modèles si rate limit"""
    for model in MODELS:
        for attempt in range(retries):
            try:
                print(f"🧠 Essai avec {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                return response.choices[0].message.content
            except Exception as e:
                if "429" in str(e):
                    print(f"⚠️ Rate limit sur {model}, attente 3s...")
                    time.sleep(3)
                else:
                    print(f"❌ Erreur : {e}")
                    break
    return "Désolé, tous les modèles sont occupés. Réessaie dans quelques secondes."

# ── Main ──
now = datetime.now()
SYSTEM_PROMPT = f"""
Tu es Abdou, un assistant vocal sympa.
Tu réponds en français, de façon courte (1-2 phrases).
Tu comprends tout, même les fautes d'orthographe.
Tu ne dis JAMAIS "je n'ai pas compris".
Date : {now.strftime("%d/%m/%Y")} | Heure : {now.strftime("%H:%M")}
"""

history = []
print("🤖 Abdou est prêt !\n")
speak("Bonjour ! Je suis Abdou, je vous écoute !")

while True:
    print("\n─────────────────────")
    mode = input("Mode → v (voix) / t (texte) / quit : ").strip().lower()

    if mode == "quit":
        speak("Au revoir !")
        break
    elif mode == "v":
        user_input = listen()
        if not user_input:
            continue
    elif mode == "t":
        user_input = input("Toi : ").strip()
        if not user_input:
            continue
    else:
        continue

    history.append({"role": "user", "content": user_input})

    reply = ask_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        *history
    ])

    history.append({"role": "assistant", "content": reply})
    speak(reply)