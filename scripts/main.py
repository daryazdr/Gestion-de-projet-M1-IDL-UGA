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
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire le fichier texte: {path}")


def enregistrer_image_unique(
    image_bytes, extension, nom_base, prefixe, index, hashes, images
):
    if not image_bytes:
        return

    image_hash = hashlib.sha1(image_bytes).hexdigest()
    if image_hash in hashes:
        return

    hashes.add(image_hash)
    ext = (extension or "png").lower()
    image_path = EXTRACTED_IMG_DIR / f"{nom_base}_{prefixe}_{index}.{ext}"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    images.append(str(image_path))


def lire_pdf(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(path))
    textes = []
    images = []
    hashes_images = set()
    compteur = 1

    for page_index, page in enumerate(doc, start=1):
        textes.append(page.get_text())

        # Methode 1: extraction originale via xref (meilleure qualite)
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                image_info = doc.extract_image(xref)
                image_bytes = image_info.get("image")
                extension = image_info.get("ext", "png")
                enregistrer_image_unique(
                    image_bytes,
                    extension,
                    nom_base,
                    f"pdf_p{page_index}",
                    compteur,
                    hashes_images,
                    images,
                )
                compteur += 1
            except Exception:
                pass

        # Methode 2: images inline (certaines images ne sont pas dans get_images)
        try:
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 1:
                    continue
                image_bytes = block.get("image")
                extension = block.get("ext", "png")
                enregistrer_image_unique(
                    image_bytes,
                    extension,
                    nom_base,
                    f"pdf_inline_p{page_index}",
                    compteur,
                    hashes_images,
                    images,
                )
                compteur += 1
        except Exception:
            pass

    doc.close()
    return "\n\n".join(textes).strip(), images


def lire_docx(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = Document(str(path))
    texte = "\n".join(p.text for p in doc.paragraphs if p.text).strip()

    images = []
    image_id = 1
    for rel in doc.part.rels.values():
        if "image" not in rel.reltype:
            continue

        blob = rel.target_part.blob
        content_type = rel.target_part.content_type
        extension = content_type.split("/")[-1]
        image_path = EXTRACTED_IMG_DIR / f"{nom_base}_docx_{image_id}.{extension}"

        with open(image_path, "wb") as f:
            f.write(blob)

        images.append(str(image_path))
        image_id += 1

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
    with open(path, "w", encoding="utf-8") as f:
        f.write(texte)


def pause_verification(etape, fichiers):
    print(f"\nVerification manuelle, etape : {etape}")
    for fichier in fichiers:
        print(f"Fichier : {fichier}")
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

    # 1) Lecture du document source (txt/pdf/docx)
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
    documents = []

    # Document FALC
    nom_audio_falc = f"{nom_base}_falc_microsoft"
    audio_falc_path = generer_audio(texte_falc, "fr", nom_audio_falc)
    falc_url = upload_github_pages(audio_falc_path) if audio_falc_path else None
    falc_qr_path = creer_qr(falc_url, nom_audio_falc) if falc_url else None

    if audio_falc_path:
        fichiers_audio_qr.append(audio_falc_path)
    if falc_qr_path:
        fichiers_audio_qr.append(falc_qr_path)

    documents.append(
        {
            "doc_id": f"{nom_base}_falc",
            "section": {
                "titre": "Texte FALC (FR)",
                "texte": texte_falc,
                "qr_path": falc_qr_path,
                "audio_url": falc_url,
                "langue": "fr",
            },
        }
    )

    # Documents traductions (service choisi)
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

    # 6) Un DOCX par texte (normalement 5)
    fichiers_docx = []
    for doc_info in documents:
        docx_path = creer_docx(doc_info["doc_id"], [doc_info["section"]], images_source)
        if docx_path:
            fichiers_docx.append(docx_path)

    if not fichiers_docx:
        print("Echec creation DOCX")
        return

    if not pause_verification("DOCX editable", fichiers_docx):
        return

    # 7) Un PDF final par DOCX
    fichiers_pdf = []
    for docx_path in fichiers_docx:
        pdf_path = exporter_docx_vers_pdf(docx_path)
        if pdf_path:
            fichiers_pdf.append(pdf_path)

    if fichiers_pdf:
        pause_verification("PDF final", fichiers_pdf)

    print("\nPipeline termine pour :", nom_base)


if __name__ == "__main__":
    entree = DATA_DIR / "input" / "surveillance.pdf"
    traiter_fiche(entree)
