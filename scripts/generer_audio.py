import asyncio
from pathlib import Path

import edge_tts


BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "docs" / "audio"


VOIX = {
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-JennyNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ar": "ar-SA-HamedNeural",
    "tr": "tr-TR-EmelNeural",
}


def generer_audio(texte, langue, nom_fichier):
    """Cree un MP3 avec Microsoft Edge TTS."""
    try:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        voix = VOIX.get(langue.lower(), VOIX["fr"])
        sortie = AUDIO_DIR / f"{nom_fichier}.mp3"

        async def sauvegarder_audio():
            tts = edge_tts.Communicate(texte, voix)
            await tts.save(str(sortie))

        asyncio.run(sauvegarder_audio())

        print("Audio crée:", sortie)
        return str(sortie)
    except Exception as e:
        print("Erreur generation audio:", e)
        return None
