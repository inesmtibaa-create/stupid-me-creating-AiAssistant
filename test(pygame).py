from gtts import gTTS
import pygame

tts = gTTS("Bonjour le monde", lang="fr")
tts.save("audio.mp3")

pygame.mixer.init()
pygame.mixer.music.load("audio.mp3")
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    pass    