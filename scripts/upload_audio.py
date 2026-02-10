import os
import dropbox
from config import DROPBOX_TOKEN


def upload_dropbox(chemin_fichier: str) -> str:
    """
    Upload un fichier audio sur Dropbox et retourne l'URL publique.
    """
    try:
        if not os.path.exists(chemin_fichier):
            print("Fichier introuvable :", chemin_fichier)
            return None

        dbx = dropbox.Dropbox(DROPBOX_TOKEN)

        nom_fichier = os.path.basename(chemin_fichier)
        chemin_dropbox = f"/audio/{nom_fichier}"

        with open(chemin_fichier, "rb") as f:
            dbx.files_upload(
                f.read(), chemin_dropbox, mode=dropbox.files.WriteMode.overwrite
            )

        shared_link = dbx.sharing_create_shared_link_with_settings(chemin_dropbox)
        url = shared_link.url.replace("dl=0", "dl=1")

        print(f"Upload Dropbox : {nom_fichier}")
        return url

    except Exception as e:
        print("Erreur upload Dropbox :", e)
        return None
