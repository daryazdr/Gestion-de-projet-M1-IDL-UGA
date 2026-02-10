import os
import qrcode


def creer_qr(url: str, nom_fichier: str, dossier_output="data/qr") -> str:
    """
    Crée un QR code à partir d'une URL.
    """
    try:
        os.makedirs(dossier_output, exist_ok=True)

        chemin_qr = os.path.join(dossier_output, f"{nom_fichier}.png")
        img = qrcode.make(url)
        img.save(chemin_qr)

        print(f"QR code créé : {chemin_qr}")
        return chemin_qr

    except Exception as e:
        print("Erreur création QR :", e)
        return None
