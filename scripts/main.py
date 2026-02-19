import hashlib
from pathlib import Path

import fitz
from docx import Document

from falc import simplifier_falc
from traduction import traduire_texte_complet
from generer_audio import generer_audio
from upload_audio import upload_github_pages
from qr import creer_qr
from docx_builder import creer_docx, exporter_docx_vers_pdf


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "docs"
EXTRACTED_IMG_DIR = DATA_DIR / "images_extraites"


def lire_txt(path):
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return Path(path).read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire le fichier texte: {path}")


def ajouter_image_unique(image_bytes, extension, out_path, seen_hashes, images):
    if not image_bytes:
        return
    h = hashlib.sha1(image_bytes).hexdigest()
    if h in seen_hashes:
        return
    seen_hashes.add(h)
    out_path.write_bytes(image_bytes)
    images.append(str(out_path))


def lire_pdf(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(path))
    textes = []
    images = []
    seen_hashes = set()
    index = 1

    for page_num, page in enumerate(doc, start=1):
        textes.append(page.get_text())

        # Methode 1: images standard du PDF
        for img in page.get_images(full=True):
            try:
                info = doc.extract_image(img[0])
                ext = info.get("ext", "png")
                out = EXTRACTED_IMG_DIR / f"{nom_base}_pdf_p{page_num}_{index}.{ext}"
                ajouter_image_unique(info.get("image"), ext, out, seen_hashes, images)
                index += 1
            except Exception:
                pass

        # Methode 2: images inline (pas toujours detectees par get_images)
        try:
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 1:
                    continue
                ext = block.get("ext", "png")
                out = (
                    EXTRACTED_IMG_DIR
                    / f"{nom_base}_pdf_inline_p{page_num}_{index}.{ext}"
                )
                ajouter_image_unique(block.get("image"), ext, out, seen_hashes, images)
                index += 1
        except Exception:
            pass

    doc.close()
    return "\n\n".join(textes).strip(), images


def lire_docx(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = Document(str(path))
    texte = "\n".join(p.text for p in doc.paragraphs if p.text).strip()

    images = []
    i = 1
    for rel in doc.part.rels.values():
        if "image" not in rel.reltype:
            continue
        extension = rel.target_part.content_type.split("/")[-1]
        image_path = EXTRACTED_IMG_DIR / f"{nom_base}_docx_{i}.{extension}"
        image_path.write_bytes(rel.target_part.blob)
        images.append(str(image_path))
        i += 1

    return texte, images


def lire_document(path):
    path = Path(path)
    suffix = path.suffix.lower()
    nom_base = path.stem

    if suffix == ".txt":
        return lire_txt(path), []
    if suffix == ".pdf":
        return lire_pdf(path, nom_base)
    if suffix == ".docx":
        return lire_docx(path, nom_base)

    raise ValueError("Format non supporte. Utilisez .txt, .pdf ou .docx")


def ecrire_fichier(texte, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(texte, encoding="utf-8")


def pause_verification(etape, fichiers):
    print(f"\nVerification manuelle, etape : {etape}")
    for fichier in fichiers:
        print(f"Fichier : {fichier}")
    reponse = input("Appuyez sur Entree pour continuer (ou tapez q pour arreter) : ")
    return reponse.strip().lower() != "q"


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


def generer_audio_qr(texte, langue, nom_audio):
    audio_path = generer_audio(texte, langue, nom_audio)
    player_url = upload_github_pages(audio_path) if audio_path else None
    qr_path = creer_qr(player_url, nom_audio) if player_url else None
    return audio_path, player_url, qr_path


def traiter_fiche(chemin_fiche):
    chemin_fiche = Path(chemin_fiche)
    nom_base = chemin_fiche.stem
    print(f"Traitement de : {chemin_fiche}")

    # 1) Lecture
    texte_original, images_source = lire_document(chemin_fiche)

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

    # 3) Traductions (plus de pause ici)
    print("\nTraductions multilingues...")
    traductions = traduire_texte_complet(texte_original)
    if not traductions:
        print("Echec traductions")
        return

    for langue, versions in traductions.items():
        for service, texte in versions.items():
            if not texte:
                continue
            out_path = DATA_DIR / "traductions" / f"{nom_base}_{langue}_{service}.txt"
            ecrire_fichier(texte, out_path)

    # 4) Service audio
    choix_service = demander_service()

    # 5) Audios + QR
    print("\nGeneration des audios et QR...")
    fichiers_audio_qr = []
    documents = []

    # FALC
    nom_audio_falc = f"{nom_base}_falc_microsoft"
    audio_falc, url_falc, qr_falc = generer_audio_qr(texte_falc, "fr", nom_audio_falc)
    if audio_falc:
        fichiers_audio_qr.append(audio_falc)
    if qr_falc:
        fichiers_audio_qr.append(qr_falc)

    documents.append(
        {
            "doc_id": f"{nom_base}_falc",
            "section": {
                "titre": "Texte FALC (FR)",
                "texte": texte_falc,
                "qr_path": qr_falc,
                "audio_url": url_falc,
                "langue": "fr",
            },
        }
    )

    # Traductions
    for langue, versions in traductions.items():
        texte_final = versions.get(choix_service)
        if not texte_final:
            continue

        nom_audio = f"{nom_base}_{langue}_{choix_service}"
        audio_path, audio_url, qr_path = generer_audio_qr(
            texte_final, langue, nom_audio
        )
        if audio_path:
            fichiers_audio_qr.append(audio_path)
        if qr_path:
            fichiers_audio_qr.append(qr_path)

        documents.append(
            {
                "doc_id": f"{nom_base}_{langue}_{choix_service}",
                "section": {
                    "titre": f"Traduction {langue.upper()} ({choix_service})",
                    "texte": texte_final,
                    "qr_path": qr_path,
                    "audio_url": audio_url,
                    "langue": langue,
                },
            }
        )

    if not pause_verification("audios et QR", fichiers_audio_qr):
        return

    # 6) DOCX (1 fichier par langue)
    fichiers_docx = []
    for doc in documents:
        docx_path = creer_docx(doc["doc_id"], [doc["section"]], images_source)
        if docx_path:
            fichiers_docx.append(docx_path)

    if not fichiers_docx:
        print("Echec creation DOCX")
        return

    if not pause_verification("DOCX editable", fichiers_docx):
        return

    # 7) PDF finaux (plus de pause ici)
    fichiers_pdf = []
    for docx_path in fichiers_docx:
        pdf_path = exporter_docx_vers_pdf(docx_path)
        if pdf_path:
            fichiers_pdf.append(pdf_path)

    print("\nPDF crees:")
    for pdf in fichiers_pdf:
        print("-", pdf)

    print("\nPipeline termine pour :", nom_base)


if __name__ == "__main__":
    entree = DATA_DIR / "input" / "surveillance2.docx"
    traiter_fiche(entree)
