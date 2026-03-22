from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime
from gtts import gTTS
import pygame
import sounddevice as sd
import numpy as np
import whisper
import os
import time

load_dotenv("key.env")

MODELS = ["openrouter/auto"]



class Assistante:

    def __init__(
        self,
        nom: str = "Abdou",
        duree_ecoute_s: float = 5.0,
        echantillon_hz: int = 16000,
        modele_whisper: str = "base",
    ):
        self.nom = nom
        self.duree_ecoute_s = duree_ecoute_s
        self.echantillon_hz = echantillon_hz
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        self.models = MODELS
        self.history: list[dict] = []

        now = datetime.now()
        self.system_prompt = f"""Tu es {nom}, un assistant vocal francophone.

LANGUE (priorité absolue) :
- Écris TOUTE ta réponse en français uniquement. Pas d'anglais, pas de mélange fr/en.
- Même si l'utilisateur parle anglais ou mélange les langues, tu réponds en français.
- Les seules exceptions : citations demandées, noms propres, ou si l'utilisateur exige explicitement une phrase en anglais.
- Style oral, naturel, 1 à 2 phrases courtes.

Comportement :
- Tu restes sympa et tu comprends les fautes ou l'oral mal transcrit.
- Tu ne dis jamais « je n'ai pas compris » ; tu réponds au mieux en français.

Contexte : {now.strftime("%d/%m/%Y")}, {now.strftime("%H:%M")}.
"""

        print("⏳ Chargement de Whisper...")
        self._stt = whisper.load_model(modele_whisper)
        print(f"✅ Whisper ({modele_whisper}) prêt !\n")

    def parler(self, texte: str) -> None:
        print(f"🔊 {self.nom} : {texte}")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass
        tts = gTTS(texte, lang="fr")
        tts.save("audio.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load("audio.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
        pygame.mixer.quit()

    def ecouter(self) -> str:
        print("🎤 Je t'écoute...")
        n = int(self.duree_ecoute_s * self.echantillon_hz)
        audio = sd.rec(
            n,
            samplerate=self.echantillon_hz,
            channels=1,
            dtype="float32",
        )
        sd.wait()

        volume = abs(audio).mean()
        print(f"📊 Volume détecté : {volume:.4f}")

        if volume < 0.001:
            print("❌ Je n'ai rien entendu... Parle plus fort !")
            return ""

        print("✅ Je t'ai entendu ! Traitement...")
        audio_plat = audio.flatten()
        resultat = self._stt.transcribe(audio_plat, language="fr")
        texte = resultat["text"].strip()
        print(f"👂 Tu as dit : '{texte}'")
        return texte

    def repondre_llm(self, retries: int = 3) -> str:
        for model in self.models:
            for _ in range(retries):
                try:
                    print(f"🧠 Essai avec {model}...")
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            *self.history,
                        ],
                    )
                    raw = response.choices[0].message.content
                    return (raw or "").strip()
                except Exception as e:
                    if "429" in str(e):
                        print(f"⚠️ Rate limit sur {model}, attente 3s...")
                        time.sleep(3)
                    else:
                        print(f"❌ Erreur : {e}")
                        break
        return "Désolé, tous les modèles sont occupés. Réessaie dans quelques secondes."

    def tour_voix(self) -> bool:
        """Un échange vocal. Retourne False si l'utilisateur veut arrêter (via logique appelante)."""
        entree = self.ecouter()
        if not entree:
            return True

        self.history.append({"role": "user", "content": entree})
        reponse = self.repondre_llm()
        self.history.append({"role": "assistant", "content": reponse})
        self.parler(reponse)
        return True

    def boucle(self) -> None:
        """Modes voix (v), texte (t), quit."""
        print(f"🤖 {self.nom} est prêt !\n")
        self.parler(f"Bonjour ! Je suis {self.nom}, je vous écoute !")

        while True:
            print("\n─────────────────────")
            mode = input("Mode → v (voix) / t (texte) / quit : ").strip().lower()

            if mode == "quit":
                self.parler("Au revoir !")
                break
            if mode == "v":
                self.tour_voix()
            elif mode == "t":
                entree = input("Toi : ").strip()
                if not entree:
                    continue
                self.history.append({"role": "user", "content": entree})
                reponse = self.repondre_llm()
                self.history.append({"role": "assistant", "content": reponse})
                self.parler(reponse)
            else:
                continue


if __name__ == "__main__":
    Assistante().boucle()
