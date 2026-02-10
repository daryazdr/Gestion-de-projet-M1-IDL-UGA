import os

from falc import simplifier_falc
from traduction import traduire_texte_complet
from generer_audio import generer_audio
from upload_audio import upload_dropbox
from qr import creer_qr


def lire_fichier(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def sauvegarder_fichier(texte, chemin):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)


def traiter_fiche(chemin_fiche):
    print(f"Traitement de : {chemin_fiche}")

    nom_base = os.path.splitext(os.path.basename(chemin_fiche))[0]

    # 1. Lire texte original
    texte_original = lire_fichier(chemin_fiche)

    # 2. Simplification FALC
    print("\nSimplification FALC en cours")
    texte_falc = simplifier_falc(texte_original)
    if not texte_falc:
        print("Échec simplification FALC — arrêt du pipeline.")
        return
    sauvegarder_fichier(texte_falc, f"data/falc/{nom_base}_falc.txt")

    # 3. Traductions (DeepL + Google)
    print("\nTraductions multilingues en cours")
    traductions = traduire_texte_complet(texte_falc)
    if not traductions:
        print("Échec traductions — arrêt du pipeline.")
        return

    # Sauvegarde des traductions
    for langue, versions in traductions.items():
        for service, texte in versions.items():
            if texte:
                sauvegarder_fichier(
                    texte, f"data/traductions/{nom_base}_{langue}_{service}.txt"
                )

    # 4. Choix humain (manuel)
    choix_service = (
        input("\nQuel service utiliser pour les audios ? (deepl/microsoft) : ")
        .strip()
        .lower()
    )

    # 5. Génération audio + QR codes
    print("\nGénération audio + QR codes en cours")
    for langue, versions in traductions.items():
        texte_final = versions.get(choix_service)

        if not texte_final:
            print(f"Pas de traduction {choix_service} pour {langue}")
            continue

        # Audio
        nom_audio = f"{nom_base}_{langue}_{choix_service}"
        audio_path = generer_audio(texte_final, langue, nom_audio)

        # Upload
        audio_url = upload_dropbox(audio_path)

        # QR code
        creer_qr(audio_url, f"{nom_base}_{langue}_{choix_service}")

    print("\nTraitement terminé pour :", nom_base)


if __name__ == "__main__":
    # Exemple : traiter une fiche

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    traiter_fiche(os.path.join(BASE_DIR, "data", "input", "diabete.txt"))
