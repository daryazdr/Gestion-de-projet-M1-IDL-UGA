from googletrans import Translator
import deepl
from typing import Dict
import time
from config import DEEPL_API_KEY


translator_google = Translator()
translator_deepl = deepl.Translator(DEEPL_API_KEY)


def traduire_deepl(texte: str, langue_cible: str) -> str:
    """
    Traduit un texte avec DeepL.
    langue_cible : 'en', 'ru', 'ar', 'tr'
    """
    try:
        # Mapping des codes langues
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


def traduire_google(texte: str, langue_cible: str) -> str:
    """
    Traduit un texte avec Google Translate.
    """
    try:
        # Google Translate utilise des codes langues standard
        result = translator_google.translate(
            texte, src="fr", dest=langue_cible.lower()  # source français
        )
        return result.text

    except Exception as e:
        print("Erreur Google Translate :", e)
        return None


def traduire_texte_complet(texte: str, langues=None) -> Dict:
    """
    Traduit un texte avec DeepL et Google pour comparaison.
    """
    if langues is None:
        langues = ["en", "ru", "ar", "tr"]

    traductions = {}

    for langue in langues:
        print(f"\nTraduction en {langue.upper()}")

        traductions[langue] = {}

        print("  → DeepL...")
        trad_deepl = traduire_deepl(texte, langue)
        traductions[langue]["deepl"] = trad_deepl

        time.sleep(1)

        print("  → Google...")
        trad_google = traduire_google(texte, langue)
        traductions[langue]["google"] = trad_google

        time.sleep(1)

    return traductions
