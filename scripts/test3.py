from pathlib import Path

from docx_builder import creer_docx, exporter_docx_vers_pdf


BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"

# Change seulement ces 2 variables si besoin
NOM_BASE = "surveillance"
SERVICE = "deepl"  # deepl ou microsoft


def lire_texte(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def path_image_source(nom_base):
    images_dir = DOCS_DIR / "images_extraites"
    if not images_dir.exists():
        return []

    # Garde les images du document en cours
    images = sorted(images_dir.glob(f"{nom_base}_*"))
    return [str(p) for p in images]


def construire_documents_test(nom_base, service):
    falc_txt = DOCS_DIR / "falc" / f"{nom_base}_falc.txt"

    documents = [
        {
            "doc_id": f"{nom_base}_falc_test",
            "section": {
                "titre": "Texte FALC (FR)",
                "texte": lire_texte(falc_txt),
                "qr_path": str(DOCS_DIR / "qr" / f"{nom_base}_falc_microsoft.png"),
                "audio_url": f"(test) https://.../player/{nom_base}_falc_microsoft.html",
                "langue": "fr",
            },
        }
    ]

    for langue in ["en", "ru", "ar", "tr"]:
        txt_path = DOCS_DIR / "traductions" / f"{nom_base}_{langue}_{service}.txt"
        documents.append(
            {
                "doc_id": f"{nom_base}_{langue}_{service}_test",
                "section": {
                    "titre": f"Traduction {langue.upper()} ({service})",
                    "texte": lire_texte(txt_path),
                    "qr_path": str(DOCS_DIR / "qr" / f"{nom_base}_{langue}_{service}.png"),
                    "audio_url": f"(test) https://.../player/{nom_base}_{langue}_{service}.html",
                    "langue": langue,
                },
            }
        )

    return documents


def main():
    documents = construire_documents_test(NOM_BASE, SERVICE)
    images_source = path_image_source(NOM_BASE)

    fichiers_docx = []
    for doc_info in documents:
        texte = doc_info["section"]["texte"].strip()
        if not texte:
            print("Texte manquant, document ignore:", doc_info["doc_id"])
            continue

        docx_path = creer_docx(doc_info["doc_id"], [doc_info["section"]], images_source)
        if docx_path:
            fichiers_docx.append(docx_path)

    if not fichiers_docx:
        print("Aucun DOCX cree")
        return

    print("\nDOCX crees:")
    for p in fichiers_docx:
        print("-", p)

    fichiers_pdf = []
    for docx_path in fichiers_docx:
        pdf_path = exporter_docx_vers_pdf(docx_path)
        if pdf_path:
            fichiers_pdf.append(pdf_path)

    print("\nPDF crees:")
    for p in fichiers_pdf:
        print("-", p)


if __name__ == "__main__":
    main()