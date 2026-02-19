from pathlib import Path

from qr import creer_qr
from upload_audio import upload_github_pages


# Script de test simple (sans lancer main.py)
BASE_DIR = Path(__file__).resolve().parent.parent
AUDIO_TEST = BASE_DIR / "docs" / "audio" / "surveillance_ru_deepl.mp3"

if __name__ == "__main__":
    if not AUDIO_TEST.exists():
        print("Fichier audio introuvable:", AUDIO_TEST)
        raise SystemExit(1)

    print("Test upload de:", AUDIO_TEST)
    player_url = upload_github_pages(str(AUDIO_TEST))

    if not player_url:
        print("ECHEC upload")
        raise SystemExit(1)

    print("OK - URL player:", player_url)

    # QR qui pointe vers la page HTML player
    qr_nom = f"test_player_{AUDIO_TEST.stem}"
    qr_path = creer_qr(player_url, qr_nom)

    if qr_path:
        print("OK - QR cree:", qr_path)
    else:
        print("ECHEC creation QR")
