from pathlib import Path

from docx import Document
from docx.shared import Inches
from docx2pdf import convert


BASE_DIR = Path(__file__).resolve().parent.parent
DOCX_DIR = BASE_DIR / "docs" / "docx"
PDF_DIR = BASE_DIR / "docs" / "pdf"


LABELS_PAR_LANGUE = {
    "fr": {
        "qr": "QR lecteur audio:",
        "lien": "Lien lecteur audio:",
    },
    "ru": {
        "qr": "QR аудиоплеера:",
        "lien": "Ссылка на аудиоплеер:",
    },
    "en": {
        "qr": "Audio player QR:",
        "lien": "Audio player link:",
    },
    "ar": {
        "qr": "رمز QR لمشغل الصوت:",
        "lien": "رابط مشغل الصوت:",
    },
    "tr": {
        "qr": "Ses oynatici QR kodu:",
        "lien": "Ses oynatici baglantisi:",
    },
}


def labels_pour_langue(langue):
    return LABELS_PAR_LANGUE.get((langue or "fr").lower(), LABELS_PAR_LANGUE["fr"])


def creer_docx(nom_base, sections, images_source=None):
    """
    Cree un DOCX editable.
    sections: liste de dictionnaires avec:
    - titre
    - texte
    - qr_path
    - audio_url
    - langue (fr, ru, en, ar, tr)
    """
    try:
        DOCX_DIR.mkdir(parents=True, exist_ok=True)
        docx_path = DOCX_DIR / f"{nom_base}.docx"

        doc = Document()

        for section in sections:
            titre = section.get("titre", "")
            texte = section.get("texte", "")
            qr_path = section.get("qr_path")
            audio_url = section.get("audio_url")
            langue = section.get("langue", "fr")
            labels = labels_pour_langue(langue)

            doc.add_heading(titre, level=1)

            for ligne in texte.splitlines():
                doc.add_paragraph(ligne if ligne.strip() else "")

            if qr_path and Path(qr_path).exists():
                doc.add_paragraph(labels["qr"])
                doc.add_picture(str(qr_path), width=Inches(1.5))

            if audio_url:
                doc.add_paragraph(f"{labels['lien']} {audio_url}")

        if images_source:
            doc.add_page_break()
            doc.add_heading("Images du document source", level=1)
            for image_path in images_source:
                image_file = Path(image_path)
                if not image_file.exists():
                    continue
                doc.add_paragraph(image_file.name)
                doc.add_picture(str(image_file), width=Inches(5.5))

        doc.save(str(docx_path))
        print("DOCX cree:", docx_path)
        return str(docx_path)

    except Exception as e:
        print("Erreur creation DOCX:", e)
        return None


def exporter_docx_vers_pdf(docx_path):
    """
    Exporte un DOCX en PDF.
    Requiert Microsoft Word (docx2pdf sur Windows).
    """
    try:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        docx_file = Path(docx_path)
        pdf_path = PDF_DIR / f"{docx_file.stem}.pdf"

        convert(str(docx_file), str(pdf_path))
        print("PDF final cree:", pdf_path)
        return str(pdf_path)

    except Exception as e:
        print("Erreur export DOCX -> PDF:", e)
        return None
