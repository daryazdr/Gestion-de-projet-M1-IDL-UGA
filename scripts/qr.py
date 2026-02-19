from pathlib import Path

import qrcode


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_QR_DIR = BASE_DIR / "docs" / "qr"


def creer_qr(url: str, nom_fichier: str, dossier_output=None) -> str:
    """
    Cree un QR code a partir d'une URL.
    """
    try:
        output_dir = Path(dossier_output) if dossier_output else DEFAULT_QR_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        chemin_qr = output_dir / f"{nom_fichier}.png"
        img = qrcode.make(url)
        img.save(chemin_qr)

        print(f"QR code crée : {chemin_qr}")
        return str(chemin_qr)

    except Exception as e:
        print("Erreur création QR :", e)
        return None
