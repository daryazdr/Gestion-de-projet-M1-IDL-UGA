import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / "docs" / "pdf"


def creer_pdf(nom_base, sections):
    """
    Cree un PDF avec sections contenant:
    - titre
    - texte
    - qr_path
    - audio_url

    Le QR pointe seulement vers l'audio de la section.
    """
    try:
        PDF_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = PDF_DIR / f"{nom_base}_complet.pdf"

        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        largeur, hauteur = A4

        for i, section in enumerate(sections):
            if i > 0:
                c.showPage()

            titre = section.get("titre", "")
            texte = section.get("texte", "")
            qr_path = section.get("qr_path")
            audio_url = section.get("audio_url")

            # Titre
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, hauteur - 40, titre)

            # QR en haut a droite
            if qr_path and Path(qr_path).exists():
                taille_qr = 100
                x_qr = largeur - taille_qr - 40
                y_qr = hauteur - taille_qr - 50
                c.drawImage(
                    ImageReader(qr_path), x_qr, y_qr, width=taille_qr, height=taille_qr
                )
                c.setFont("Helvetica", 10)
                c.drawCentredString(x_qr + taille_qr / 2, y_qr - 12, "scanne-moi")

            # Lien audio texte (si pas de scan)
            if audio_url:
                c.setFont("Helvetica", 9)
                c.drawString(40, hauteur - 58, f"Lien audio: {audio_url}")

            # Corps du texte
            y = hauteur - 90
            c.setFont("Helvetica", 10)
            for ligne in texte.splitlines():
                blocs = textwrap.wrap(ligne, width=100) if ligne.strip() else [""]
                for bloc in blocs:
                    if y < 50:
                        c.showPage()
                        y = hauteur - 50
                        c.setFont("Helvetica", 10)
                    c.drawString(40, y, bloc)
                    y -= 13

        c.save()
        print("PDF cree:", pdf_path)
        return str(pdf_path)
    except Exception as e:
        print("Erreur creation PDF:", e)
        return None

