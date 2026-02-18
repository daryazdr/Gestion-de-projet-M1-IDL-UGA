import asyncio
from pathlib import Path

import edge_tts


BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_DIR = BASE_DIR / "docs" / "audio"


VOIX = {
    "fr": "fr-FR-DeniseNeural",
    "en": "en-US-JennyNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ar": "ar-EG-SalmaNeural",
    "tr": "tr-TR-EmelNeural",
}


def generer_audio(texte, langue, nom_fichier):
    """
    Cree un mp3 avec Microsoft Edge TTS.
    """
    try:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        voix = VOIX.get(langue.lower(), VOIX["fr"])
        sortie = AUDIO_DIR / f"{nom_fichier}.mp3"

        async def _run():
            tts = edge_tts.Communicate(texte, voix)
            await tts.save(str(sortie))

        asyncio.run(_run())

        print("Audio cree:", sortie)
        return str(sortie)
    except Exception as e:
        print("Erreur generation audio:", e)
        return None

