import hashlib
import unicodedata
from pathlib import Path

import fitz
from docx import Document

from docx_builder import creer_docx
from falc import simplifier_falc
from generer_audio import generer_audio
from qr import creer_qr
from traduction import traduire_texte_complet
from upload_audio import upload_github_pages, upload_github_pages_multi


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "docs"
EXTRACTED_IMG_DIR = DATA_DIR / "images_extraites"
SERVICES_AUDIO = ["deepl", "microsoft"]


TITRES_SECTIONS = {
    "eviter": {
        "fr": "ALIMENTS A EVITER",
        "en": "FOODS TO AVOID",
        "ru": "\u041f\u0420\u041e\u0414\u0423\u041a\u0422\u042b, \u041a\u041e\u0422\u041e\u0420\u042b\u0425 \u0421\u041b\u0415\u0414\u0423\u0415\u0422 \u0418\u0417\u0411\u0415\u0413\u0410\u0422\u042c",
        "ar": "\u0627\u0644\u0623\u0637\u0639\u0645\u0629 \u0627\u0644\u062a\u064a \u064a\u062c\u0628 \u062a\u062c\u0646\u0628\u0647\u0627",
        "tr": "KACINILMASI GEREKEN GIDALAR",
    },
    "conseilles": {
        "fr": "ALIMENTS CONSEILLES",
        "en": "RECOMMENDED FOODS",
        "ru": "\u0420\u0415\u041a\u041e\u041c\u0415\u041d\u0414\u0423\u0415\u041c\u042b\u0415 \u041f\u0420\u041e\u0414\u0423\u041a\u0422\u042b",
        "ar": "\u0627\u0644\u0623\u0637\u0639\u0645\u0629 \u0627\u0644\u0645\u0648\u0635\u0649 \u0628\u0647\u0627",
        "tr": "ONERILEN GIDALAR",
    },
    "journee_type": {
        "fr": "JOURNEE TYPE",
        "en": "TYPICAL DAY",
        "ru": "\u0422\u0418\u041f\u0418\u0427\u041d\u042b\u0419 \u0414\u0415\u041d\u042c",
        "ar": "\u064a\u0648\u0645 \u0646\u0645\u0648\u0630\u062c\u064a",
        "tr": "ORNEK GUN",
    },
}


def lire_txt(path):
    for encodage in ("utf-8", "cp1252", "latin-1"):
        try:
            return Path(path).read_text(encoding=encodage)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Impossible de lire le fichier texte: {path}")


def ajouter_image_unique(image_bytes, out_path, seen_hashes, images):
    if not image_bytes:
        return

    image_hash = hashlib.sha1(image_bytes).hexdigest()
    if image_hash in seen_hashes:
        return

    seen_hashes.add(image_hash)
    out_path.write_bytes(image_bytes)
    images.append(str(out_path))


def extraire_images_pdf(doc, page, page_num, nom_base, index, seen_hashes, images):
    for img in page.get_images(full=True):
        try:
            info = doc.extract_image(img[0])
            extension = info.get("ext", "png")
            out_path = (
                EXTRACTED_IMG_DIR / f"{nom_base}_pdf_p{page_num}_{index}.{extension}"
            )
            ajouter_image_unique(info.get("image"), out_path, seen_hashes, images)
            index += 1
        except Exception:
            pass

    try:
        blocks = page.get_text("dict").get("blocks", [])
    except Exception:
        return index

    for block in blocks:
        if block.get("type") != 1:
            continue
        extension = block.get("ext", "png")
        out_path = (
            EXTRACTED_IMG_DIR / f"{nom_base}_pdf_inline_p{page_num}_{index}.{extension}"
        )
        ajouter_image_unique(block.get("image"), out_path, seen_hashes, images)
        index += 1

    return index


def lire_pdf(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(path))
    textes = []
    images = []
    seen_hashes = set()
    index = 1

    for page_num, page in enumerate(doc, start=1):
        textes.append(page.get_text())
        index = extraire_images_pdf(
            doc,
            page,
            page_num,
            nom_base,
            index,
            seen_hashes,
            images,
        )

    doc.close()
    return "\n\n".join(textes).strip(), images


def lire_docx(path, nom_base):
    EXTRACTED_IMG_DIR.mkdir(parents=True, exist_ok=True)

    doc = Document(str(path))
    texte = "\n".join(
        paragraph.text for paragraph in doc.paragraphs if paragraph.text
    ).strip()

    images = []
    index = 1
    for relation in doc.part.rels.values():
        if "image" not in relation.reltype:
            continue
        extension = relation.target_part.content_type.split("/")[-1]
        image_path = EXTRACTED_IMG_DIR / f"{nom_base}_docx_{index}.{extension}"
        image_path.write_bytes(relation.target_part.blob)
        images.append(str(image_path))
        index += 1

    return texte, images


def convertir_doc_en_docx(path_doc):
    """Convertit un fichier .doc en .docx avec Microsoft Word."""
    try:
        import win32com.client
    except Exception as e:
        raise RuntimeError(
            "Lecture .doc: installez pywin32 (pip install pywin32) et Microsoft Word"
        ) from e

    path_doc = Path(path_doc).resolve()
    path_docx = path_doc.with_name(f"{path_doc.stem}_converted.docx")

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = None

    try:
        doc = word.Documents.Open(str(path_doc))
        doc.SaveAs(str(path_docx), FileFormat=16)
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()

    return path_docx


def lire_document(path):
    path = Path(path)
    suffix = path.suffix.lower()
    nom_base = path.stem

    lecteurs = {
        ".txt": lambda: (lire_txt(path), []),
        ".pdf": lambda: lire_pdf(path, nom_base),
        ".docx": lambda: lire_docx(path, nom_base),
        ".doc": lambda: lire_docx(convertir_doc_en_docx(path), nom_base),
    }

    if suffix not in lecteurs:
        raise ValueError("Format non supporte. Utilisez .txt, .pdf, .docx ou .doc")

    return lecteurs[suffix]()


def ecrire_fichier(texte, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(texte, encoding="utf-8")


def pause_verification(etape, fichiers):
    print(f"\nVerification manuelle, etape : {etape}")
    for fichier in fichiers:
        print(f"Fichier : {fichier}")
    reponse = input("Appuyez sur Entree pour continuer (ou tapez q pour arreter) : ")
    return reponse.strip().lower() != "q"


def demander_service():
    while True:
        service = input("\nService pour les audios de traduction (deepl/microsoft) : ")
        service = service.strip().lower()
        if service in SERVICES_AUDIO:
            return service
        print("Choix invalide. Ecrivez deepl ou microsoft.")


def type_document(nom_base):
    return "diete" if nom_base.lower().startswith("diete") else "standard"


def normaliser_texte_pour_recherche(texte):
    texte = texte.replace("\xa0", " ")
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(
        caractere for caractere in texte if not unicodedata.combining(caractere)
    )
    return texte.upper()


def trouver_position_titre(texte_original, titre_recherche):
    texte_norm = normaliser_texte_pour_recherche(texte_original)
    titre_norm = normaliser_texte_pour_recherche(titre_recherche)
    return texte_norm.find(titre_norm)


def decouper_sections_diete(texte):

    texte_lower = texte.lower()

    # mots clés pour trouver les sections
    mots_interdits = ["interdits", "éviter", "eviter"]
    mots_conseilles = ["conseillés", "conseilles", "recommandés", "recommandes"]
    mots_journee = ["journée", "journee", "repas"]

    def trouver_position(mots):
        for mot in mots:
            pos = texte_lower.find(mot)
            if pos != -1:
                return pos
        return -1

    pos1 = trouver_position(mots_interdits)
    pos2 = trouver_position(mots_conseilles)
    pos3 = trouver_position(mots_journee)

    if -1 in [pos1, pos2, pos3]:
        print("Impossible de trouver les 3 sections dans le document diete.")
        return None

    positions = sorted([pos1, pos2, pos3])
    pos1, pos2, pos3 = positions

    return [
        {"cle": "eviter", "texte": texte[pos1:pos2].strip()},
        {"cle": "conseilles", "texte": texte[pos2:pos3].strip()},
        {"cle": "journee_type", "texte": texte[pos3:].strip()},
    ]


def generer_audio_seul(texte, langue, nom_audio):
    return generer_audio(texte, langue, nom_audio)


def generer_qr_depuis_audio(audio_path, nom_audio):
    player_url = upload_github_pages(audio_path) if audio_path else None
    qr_path = creer_qr(player_url, nom_audio) if player_url else None
    return player_url, qr_path


def traduire_sections_diete(sections):
    resultat = {}

    for section in sections:
        traductions_section = traduire_texte_complet(section["texte"])
        if not traductions_section:
            continue

        for langue, versions in traductions_section.items():
            resultat.setdefault(langue, {"deepl": [], "microsoft": []})

            for service in SERVICES_AUDIO:
                texte_traduit = versions.get(service)
                if not texte_traduit:
                    continue
                resultat[langue][service].append(
                    {"cle": section["cle"], "texte": texte_traduit}
                )

    return resultat


def sauvegarder_traductions_standard(nom_base, traductions):
    for langue, versions in traductions.items():
        for service, texte in versions.items():
            if not texte:
                continue
            out_path = DATA_DIR / "traductions" / f"{nom_base}_{langue}_{service}.txt"
            ecrire_fichier(texte, out_path)


def sauvegarder_traductions_diete(nom_base, traductions):
    for langue, versions in traductions.items():
        for service, sections in versions.items():
            if not sections:
                continue
            texte_complet = "\n\n".join(
                section["texte"] for section in sections if section["texte"]
            )
            out_path = DATA_DIR / "traductions" / f"{nom_base}_{langue}_{service}.txt"
            ecrire_fichier(texte_complet, out_path)


def sauvegarder_traductions(nom_base, doc_type, traductions):
    if doc_type == "diete":
        sauvegarder_traductions_diete(nom_base, traductions)
    else:
        sauvegarder_traductions_standard(nom_base, traductions)


def construire_document_falc(nom_base, texte_falc, qr_falc, url_falc):
    return {
        "doc_id": f"{nom_base}_falc",
        "sections": [
            {
                "titre": "Texte FALC (FR)",
                "texte": texte_falc,
                "qr_path": qr_falc,
                "audio_url": url_falc,
                "langue": "fr",
            }
        ],
    }


def construire_document_standard(nom_base, langue, service, texte, qr_path, audio_url):
    return {
        "doc_id": f"{nom_base}_{langue}_{service}",
        "sections": [
            {
                "titre": f"Traduction {langue.upper()} ({service})",
                "texte": texte,
                "qr_path": qr_path,
                "audio_url": audio_url,
                "langue": langue,
            }
        ],
    }


def construire_documents_standard(
    nom_base, traductions, choix_service, fichiers_audio_qr
):
    documents = []

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
            construire_document_standard(
                nom_base,
                langue,
                choix_service,
                texte_final,
                qr_path,
                audio_url,
            )
        )

    return documents


def creer_section_doc_diete(cle, langue, texte_section):
    sous_titre = TITRES_SECTIONS[cle].get(langue, TITRES_SECTIONS[cle]["fr"])
    return {
        "titre": sous_titre,
        "texte": texte_section,
        "qr_path": None,
        "audio_url": None,
        "langue": langue,
    }


def construire_documents_diete(nom_base, traductions, choix_service, fichiers_audio_qr):
    documents = []

    for langue, versions in traductions.items():
        sections_traduites = versions.get(choix_service)
        if not sections_traduites:
            continue

        sections_html = []
        sections_doc = []

        for section in sections_traduites:
            cle = section["cle"]
            texte_section = section["texte"]
            sous_titre = TITRES_SECTIONS[cle].get(langue, TITRES_SECTIONS[cle]["fr"])
            nom_audio = f"{nom_base}_{langue}_{choix_service}_{cle}"

            audio_path = generer_audio(texte_section, langue, nom_audio)
            if audio_path:
                fichiers_audio_qr.append(audio_path)
                sections_html.append({"titre": sous_titre, "audio_path": audio_path})

            sections_doc.append(creer_section_doc_diete(cle, langue, texte_section))

        if not sections_html:
            continue

        page_url = upload_github_pages_multi(
            sections_html,
            nom_page=f"{nom_base}_{langue}_{choix_service}",
            langue=langue,
        )

        qr_path = None
        if page_url:
            qr_path = creer_qr(page_url, f"{nom_base}_{langue}_{choix_service}")
            if qr_path:
                fichiers_audio_qr.append(qr_path)

        for section_doc in sections_doc:
            section_doc["qr_path"] = qr_path
            section_doc["audio_url"] = page_url

        documents.append(
            {
                "doc_id": f"{nom_base}_{langue}_{choix_service}",
                "sections": sections_doc,
            }
        )

    return documents


def preparer_traductions(doc_type, texte_original):
    if doc_type != "diete":
        return traduire_texte_complet(texte_original)

    sections_fr = decouper_sections_diete(texte_original)
    if not sections_fr:
        print("Echec decoupage diete")
        return None

    return traduire_sections_diete(sections_fr)


def creer_tous_les_docx(documents, images_source):
    fichiers_docx = []

    for document in documents:
        docx_path = creer_docx(document["doc_id"], document["sections"], images_source)
        if docx_path:
            fichiers_docx.append(docx_path)

    return fichiers_docx


def traiter_fiche(chemin_fiche):
    chemin_fiche = Path(chemin_fiche)
    nom_base = chemin_fiche.stem
    print(f"Traitement de : {chemin_fiche}")

    texte_original, images_source = lire_document(chemin_fiche)
    doc_type = type_document(nom_base)

    print("\nSimplification FALC...")
    texte_falc = simplifier_falc(texte_original)
    if not texte_falc:
        print("Echec simplification FALC")
        return

    falc_path = DATA_DIR / "falc" / f"{nom_base}_falc.txt"
    ecrire_fichier(texte_falc, falc_path)
    if not pause_verification("FALC", [str(falc_path)]):
        return

    print("\nTraductions multilingues...")
    traductions = preparer_traductions(doc_type, texte_original)
    if not traductions:
        print("Echec traductions")
        return

    sauvegarder_traductions(nom_base, doc_type, traductions)

    choix_service = demander_service()

    print("\nGeneration des audios")
    fichiers_audio_qr = []

    nom_audio_falc = f"{nom_base}_falc_microsoft"
    audio_falc = generer_audio_seul(texte_falc, "fr", nom_audio_falc)
    audios_generes = []
    if audio_falc:
        audios_generes.append(audio_falc)

    if not pause_verification("audios", audios_generes):
        return

    print("\nGeneration des QRs")

    url_falc, qr_falc = generer_qr_depuis_audio(audio_falc, nom_audio_falc)

    fichiers_audio_qr = []
    if audio_falc:
        fichiers_audio_qr.append(audio_falc)
    if qr_falc:
        fichiers_audio_qr.append(qr_falc)

    if not pause_verification("QRc", fichiers_audio_qr):
        return

    documents = [construire_document_falc(nom_base, texte_falc, qr_falc, url_falc)]

    if doc_type == "diete":
        documents.extend(
            construire_documents_diete(
                nom_base,
                traductions,
                choix_service,
                fichiers_audio_qr,
            )
        )
    else:
        documents.extend(
            construire_documents_standard(
                nom_base,
                traductions,
                choix_service,
                fichiers_audio_qr,
            )
        )

    if not pause_verification("audios et QR", fichiers_audio_qr):
        return

    fichiers_docx = creer_tous_les_docx(documents, images_source)
    if not fichiers_docx:
        print("Echec creation DOCX")
        return

    if not pause_verification("DOCX editable", fichiers_docx):
        return

    print("\nPipeline termine pour :", nom_base)


if __name__ == "__main__":
    entree = DATA_DIR / "input" / "diete.doc"
    traiter_fiche(entree)
