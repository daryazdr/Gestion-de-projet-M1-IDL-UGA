from pathlib import Path

from falc import simplifier_falc
from traduction import traduire_texte_complet
from generer_audio import generer_audio
from upload_audio import upload_github_pages
from qr import creer_qr
from pdf import creer_pdf


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "docs"


def lire_fichier(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def ecrire_fichier(texte, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(texte)


def pause_verification(etape, fichiers):
    print(f"\nVerification manuelle - {etape}")
    for fichier in fichiers:
        print(f"  - {fichier}")
    reponse = (
        input("Appuyez sur Entree pour continuer (ou tapez q pour arreter) : ")
        .strip()
        .lower()
    )
    return reponse != "q"


def demander_service():
    while True:
        service = (
            input("\nService pour les audios de traduction (deepl/microsoft) : ")
            .strip()
            .lower()
        )
        if service in ["deepl", "microsoft"]:
            return service
        print("Choix invalide. Ecrivez deepl ou microsoft.")


def traiter_fiche(chemin_fiche):
    chemin_fiche = Path(chemin_fiche)
    print(f"Traitement de : {chemin_fiche}")

    nom_base = chemin_fiche.stem

    # 1) Texte original
    texte_original = lire_fichier(chemin_fiche)
    if not pause_verification("texte original", [str(chemin_fiche)]):
        return

    # 2) FALC
    print("\nSimplification FALC...")
    texte_falc = simplifier_falc(texte_original)
    if not texte_falc:
        print("Echec simplification FALC")
        return

    falc_path = DATA_DIR / "falc" / f"{nom_base}_falc.txt"
    ecrire_fichier(texte_falc, falc_path)
    if not pause_verification("FALC", [str(falc_path)]):
        return

    # 3) Traductions depuis texte original
    print("\nTraductions multilingues...")
    traductions = traduire_texte_complet(texte_original)
    if not traductions:
        print("Echec traductions")
        return

    fichiers_traduits = []
    for langue, versions in traductions.items():
        for service, texte in versions.items():
            if not texte:
                continue
            out_path = DATA_DIR / "traductions" / f"{nom_base}_{langue}_{service}.txt"
            ecrire_fichier(texte, out_path)
            fichiers_traduits.append(str(out_path))

    if not pause_verification("traductions", fichiers_traduits):
        return

    # 4) Choix service pour audios traduits
    choix_service = demander_service()

    # 5) Audios + upload GitHub Pages + QR
    print("\nGeneration des audios et QR...")
    fichiers_audio_qr = []

    # Audio FALC
    nom_audio_falc = f"{nom_base}_falc_microsoft"
    audio_falc_path = generer_audio(texte_falc, "fr", nom_audio_falc)
    falc_url = upload_github_pages(audio_falc_path) if audio_falc_path else None
    falc_qr_path = creer_qr(falc_url, nom_audio_falc) if falc_url else None

    if audio_falc_path:
        fichiers_audio_qr.append(audio_falc_path)
    if falc_qr_path:
        fichiers_audio_qr.append(falc_qr_path)

    # Audios traductions (service choisi)
    infos_traductions = []
    for langue, versions in traductions.items():
        texte_final = versions.get(choix_service)
        if not texte_final:
            print(f"Pas de traduction {choix_service} pour {langue}")
            continue

        nom_audio = f"{nom_base}_{langue}_{choix_service}"
        audio_path = generer_audio(texte_final, langue, nom_audio)
        audio_url = upload_github_pages(audio_path) if audio_path else None
        qr_path = creer_qr(audio_url, nom_audio) if audio_url else None

        if audio_path:
            fichiers_audio_qr.append(audio_path)
        if qr_path:
            fichiers_audio_qr.append(qr_path)

        infos_traductions.append(
            {
                "id": f"{langue}_{choix_service}",
                "titre": f"Traduction {langue.upper()} ({choix_service})",
                "texte": texte_final,
                "qr_path": qr_path,
                "audio_url": audio_url,
            }
        )

    if not pause_verification("audios et QR", fichiers_audio_qr):
        return

    # 6) PDFs finaux
    fichiers_pdf = []

    falc_sections = [
        {
            "titre": "Texte FALC (FR)",
            "texte": texte_falc,
            "qr_path": falc_qr_path,
            "audio_url": falc_url,
        }
    ]
    pdf_falc = creer_pdf(f"{nom_base}_falc", falc_sections)
    if pdf_falc:
        fichiers_pdf.append(pdf_falc)

    for info in infos_traductions:
        sections_trad = [
            {
                "titre": info["titre"],
                "texte": info["texte"],
                "qr_path": info["qr_path"],
                "audio_url": info["audio_url"],
            }
        ]
        pdf_trad = creer_pdf(f"{nom_base}_{info['id']}", sections_trad)
        if pdf_trad:
            fichiers_pdf.append(pdf_trad)

    if not pause_verification("PDFs", fichiers_pdf):
        return

    print("\nPipeline termine pour :", nom_base)


if __name__ == "__main__":
    entree = DATA_DIR / "input" / "diabete.txt"
    traiter_fiche(entree)

