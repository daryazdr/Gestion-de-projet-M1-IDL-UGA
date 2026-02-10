import os
from gtts import gTTS


def generer_audio(
    texte: str, langue: str, nom_fichier: str, dossier_output="data/audio"
) -> str:
    """
    Génère un fichier audio avec gTTS.
    Retourne le chemin du fichier audio.
    """
    try:
        os.makedirs(dossier_output, exist_ok=True)

        print(f"Génération audio {langue.upper()}...")
        tts = gTTS(text=texte, lang=langue, slow=True)

        chemin_fichier = os.path.join(dossier_output, f"{nom_fichier}.mp3")
        tts.save(chemin_fichier)

        print(f"Audio créé : {chemin_fichier}")
        return chemin_fichier

    except Exception as e:
        print("Erreur audio :", e)
        return None
