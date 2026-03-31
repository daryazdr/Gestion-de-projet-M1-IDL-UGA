## Gestion-de-projet-M1-IDL-UGA

Projet de Master 1 Industrie de la langue, UGA (2025-2026).

Automatisation de la traduction et de l'accessibilité de protocoles médicaux pour patientes allophones atteintes de diabète gestationnel, avec simplification FALC et audio multilingue.

## Contexte du projet

# Problématique
Le service d'endocrinologie de l'Hôpital Nord de Marseille accueille régulièrement des patientes allophones atteintes de diabète gestationnel. La barrière linguistique, combinée à la complexité des termes médicaux, met en danger l'autonomie des patientes pour réaliser des gestes techniques (injections, mesures glycémiques), comprendre et appliquer les protocoles diététiques et assurer un suivi médical sécurisé.

# Solution proposée

Pipeline automatisé qui transforme les protocoles médicaux français en documents multilingues accessibles.

## Fonctionnement actuel

Le programme principal est `scripts/main.py`.

Pipeline:
1. Lecture du document d'entree (`.txt`, `.pdf`, `.docx`).
2. Simplification FALC.
3. Traductions multilingues.
4. Generation des audios.
5. Upload GitHub Pages de l'audio et QR + page HTML player.
7. Generation de documents finaux: 1 DOCX par version de texte (FALC + traductions choisies).

En pratique, avec FALC + 4 langues, on obtient 5 DOCX pour chaque fiche.

## Formats d'entree supportes

- `.txt`
- `.pdf`
- `.docx`

## Player HTML et QR

Pour chaque audio, le script cree une page player HTML avec:
- gros boutons pictogrammes (Play, Pause, -5s, +5s)
- bouton Pause en rouge
- titre adapte a la langue (ex: russe)

Le QR code et le lien dans le document pointent vers cette page HTML player.

## Structure du projet

protocoles-multilingues/
├── scripts/               # Code source
│   ├── main.py           # Pipeline principal
│   ├── falc.py           # Simplification FALC
│   ├── traduction.py     # Traductions
│   ├── generer_audio.py  # Text-to-Speech
│   ├── upload_audio.py   # GitHub Pages
│   ├── qr.py             # QR codes
│   └── docx_builder.py   # Documents Word
│
├── docs/                  # Données et résultats
│   ├── input/            # Documents originaux
│   ├── falc/             # Textes simplifiés
│   ├── traductions/      # Traductions
│   ├── audio/            # Fichiers MP3
│   ├── qr/               # QR codes
│   └── docx/             # Documents finaux
│
├── config.py             # Configuration
├── requirements.txt      # Dépendances
└── README.md            # Documentation

## Installation

# Cloner le repository
git clone https://github.com/VOTRE_USERNAME/protocoles-multilingues.git
cd protocoles-multilingues

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# Installer dépendances
pip install -r requirements.txt

## Prérequis

Python 3.8+
Git
Compte GitHub (pour hébergement audio)

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

## Remarques

- Le programme contient des pauses de verification manuelle pour certaines etapes.
- Si un format n'est pas lisible, verifier encodage/fichier source.