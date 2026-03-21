# test_micro.py
import sounddevice as sd
import soundfile as sf
import numpy as np

print("🎤 Parle pendant 3 secondes...")

# Enregistrer
duration = 3
sample_rate = 16000
audio = sd.rec(
    int(duration * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="float32"
)
sd.wait()
print(" Enregistrement terminé !")

# Sauvegarder
sf.write("test_micro.wav", audio, sample_rate)
print(" Sauvegardé dans test_micro.wav")

# Vérifier le volume
volume = np.abs(audio).mean()
print(f" Volume détecté : {volume:.4f}")

if volume > 0.001:
    print(" Micro fonctionne ! L'IA t'entend !")
else:
    print(" Micro trop silencieux ou pas branché !")