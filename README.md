# Gestion-de-projet-M1-IDL-UGA

Projet de Master 1 IDL (2025-2026).

Objectif: rendre des documents medicaux plus accessibles (FALC, traductions, audio, QR, documents finaux).

## Fonctionnement actuel

Le programme principal est `scripts/main.py`.

Pipeline:
1. Lecture du document d'entree (`.txt`, `.pdf`, `.docx`, `.doc`).
2. Simplification FALC.
3. Traductions multilingues.
4. Generation des audios.
5. Upload GitHub Pages de l'audio + page HTML player.
6. Generation des QR codes (QR -> page HTML player, pas vers le mp3 direct).
7. Generation de documents finaux:
- 1 DOCX par version de texte (FALC + traductions choisies).
- puis 1 PDF par DOCX.

En pratique, avec FALC + 4 langues, on obtient 5 DOCX puis 5 PDF.

## Formats d'entree supportes

- `.txt`
- `.pdf`
- `.docx`
- `.doc`

### Note pour le format `.doc`

Le `.doc` est converti automatiquement en `.docx` via Microsoft Word (Windows).
Prerequis:
- Microsoft Word installe
- `pywin32` installe

## Player HTML et QR

Pour chaque audio, le script cree une page player HTML avec:
- gros boutons pictogrammes (Play, Pause, -5s, +5s)
- bouton Pause en rouge
- titre adapte a la langue (ex: russe)

Le QR code et le lien dans le document pointent vers cette page HTML player.

## Arborescence de sortie (dossier `docs/`)

- `docs/falc/` : textes FALC
- `docs/traductions/` : textes traduits
- `docs/audio/` : fichiers audio
- `docs/qr/` : QR codes
- `docs/docx/` : DOCX finaux
- `docs/pdf/` : PDF finaux
- `docs/images_extraites/` : images extraites des documents source
- `docs/player/` : pages HTML player publiees sur GitHub Pages (via repo)

## Installation

Depuis la racine du projet:

```powershell
pip install -r scripts/requirements.txt
```

## Configuration

Completer `scripts/config.py` avec vos cles/API:
- `GROQ_API_KEY`
- `DEEPL_API_KEY`
- `MICROSOFT_TRANSLATOR_KEY`
- `MICROSOFT_TRANSLATOR_REGION`
- `GITHUB_TOKEN`
- `GITHUB_REPO` (format `owner/repo` ou URL GitHub)
- `GITHUB_PAGES_BASE_URL`

Le code utilise la branche `main` et publie les contenus dans `docs/` pour GitHub Pages.

## Lancer le pipeline complet

```powershell
python scripts/main.py
```

Le fichier d'entree est defini en bas de `scripts/main.py`.

## Scripts de test utiles

### Test upload + QR (sans pipeline complet)

```powershell
python scripts/test2.py
```

### Test generation DOCX + PDF a partir des fichiers deja generes

```powershell
python scripts/test3.py
```

## Remarques

- Le programme contient des pauses de verification manuelle pour certaines etapes.
- Les pauses apres "traductions" et apres generation des PDF ont ete retirees.
- Si un format n'est pas lisible, verifier encodage/fichier source.