import requests
import deepl
from typing import Dict
import time
from config import DEEPL_API_KEY, MICROSOFT_TRANSLATOR_KEY, MICROSOFT_TRANSLATOR_REGION


translator_deepl = deepl.Translator(DEEPL_API_KEY)


def traduire_deepl(texte: str, langue_cible: str) -> str:
    """
    Traduit un texte avec DeepL.
    langue_cible : 'en', 'ru', 'ar', 'tr'
    """
    try:
        langue_map = {
            "en": "EN-GB",
            "ru": "RU",
            "ar": "AR",
            "tr": "TR",
        }

        langue = langue_map.get(langue_cible.lower())
        if not langue:
            print("Langue non supportée :", langue_cible)
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
    """
    Traduit un texte avec Microsoft Translator (Azure).
    """
    try:
        endpoint = "https://api.cognitive.microsofttranslator.com/translate"
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
            endpoint, params=params, headers=headers, json=body, timeout=30
        )
        response.raise_for_status()
        return response.json()[0]["translations"][0]["text"]

    except Exception as e:
        print("Erreur Microsoft Translator :", e)
        return None


def traduire_texte_complet(texte: str, langues=None) -> Dict:
    """
    Traduit un texte avec DeepL et Microsoft pour comparaison.
    """
    if langues is None:
        langues = ["en", "ru", "ar", "tr"]

    traductions = {}

    for langue in langues:
        print(f"\nTraduction en {langue.upper()}")

        traductions[langue] = {}

        print(" DeepL...")
        trad_deepl = traduire_deepl(texte, langue)
        traductions[langue]["deepl"] = trad_deepl

        time.sleep(1)

        print(" Microsoft...")
        trad_ms = traduire_microsoft(texte, langue)
        traductions[langue]["microsoft"] = trad_ms

        time.sleep(1)

    return traductions
