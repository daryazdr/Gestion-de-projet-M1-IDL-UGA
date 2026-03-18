import time
from typing import Dict

import deepl
import requests

from config import (
    DEEPL_API_KEY,
    MICROSOFT_TRANSLATOR_KEY,
    MICROSOFT_TRANSLATOR_REGION,
)


LANGUES_PAR_DEFAUT = ["en", "ru", "ar", "tr"]
LANGUES_DEEPL = {
    "en": "EN-GB",
    "ru": "RU",
    "ar": "AR",
    "tr": "TR",
}
MICROSOFT_ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate"
PAUSE_ENTRE_APPELS = 1

translator_deepl = deepl.Translator(DEEPL_API_KEY)


def pause_courte():
    time.sleep(PAUSE_ENTRE_APPELS)


def traduire_deepl(texte: str, langue_cible: str) -> str:
    """Traduit un texte avec DeepL."""
    try:
        langue = LANGUES_DEEPL.get(langue_cible.lower())
        if not langue:
            print("Langue non supportee :", langue_cible)
            return None

        result = translator_deepl.translate_text(
            texte,
            target_lang=langue,
            preserve_formatting=True,
        )
        return result.text
    except Exception as e:
        print("Erreur DeepL :", e)
        return None


def traduire_microsoft(texte: str, langue_cible: str) -> str:
    """Traduit un texte avec Microsoft Translator."""
    try:
        params = {
            "api-version": "3.0",
            "from": "fr",
            "to": langue_cible.lower(),
        }
        headers = {
            "Ocp-Apim-Subscription-Key": MICROSOFT_TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": MICROSOFT_TRANSLATOR_REGION,
            "Content-type": "application/json",
        }
        body = [{"text": texte}]

        response = requests.post(
            MICROSOFT_ENDPOINT,
            params=params,
            headers=headers,
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()[0]["translations"][0]["text"]
    except Exception as e:
        print("Erreur Microsoft Translator :", e)
        return None


def traduire_texte_complet(texte: str, langues=None) -> Dict:
    """Traduit un texte avec DeepL et Microsoft pour comparaison."""
    if langues is None:
        langues = LANGUES_PAR_DEFAUT

    traductions = {}

    for langue in langues:
        print(f"\nTraduction en {langue.upper()}")
        traductions[langue] = {}

        print(" DeepL...")
        traductions[langue]["deepl"] = traduire_deepl(texte, langue)
        pause_courte()

        print(" Microsoft...")
        traductions[langue]["microsoft"] = traduire_microsoft(texte, langue)
        pause_courte()

    return traductions
