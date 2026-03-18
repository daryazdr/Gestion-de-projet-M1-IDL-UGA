from groq import Groq

from config import GROQ_API_KEY


SYSTEM_MESSAGE = (
    "Tu es un assistant specialise en simplification FALC pour des textes medicaux."
)
MODEL_NAME = "llama-3.3-70b-versatile"


def construire_prompt_falc(texte_original: str) -> str:
    return f"""
Tu es expert en simplification FALC (Facile a Lire et a Comprendre).

Regles de simplification :
    - Phrases courtes. Chaque phrase nouvelle commence sur une nouvelle ligne.
    - 1 idee par phrase. Chaque phrase termine par un point.
    - Vocabulaire simple et courant.
    - Eviter metaphores, abreviations, initiales, acronymes.
    - Expliquer les termes medicaux et concepts difficiles.
    - S'adresser directement aux personnes avec des mots comme "vous".
    - Utiliser des phrases positives plutot que la negation.
    - Utiliser des phrases actives plutot que des phrases passives.
    - Garder une mise en forme coherente dans tout le texte.
    - Les pages sont numerotees (exemple : "page 2 sur 4").

Simplifie ce texte et :
- Garde TOUTES les informations medicales, ne supprime rien.
- Ne change pas le sens medical.
- Reste precis sur les consignes de sante.
- Ne jamais modifier les valeurs numeriques, unites, posologies.

Texte a simplifier :
{texte_original}
"""


def creer_client_groq() -> Groq:
    return Groq(api_key=GROQ_API_KEY)


def simplifier_falc(texte_original: str) -> str:
    """Simplifie un texte medical en FALC avec Groq."""
    try:
        client = creer_client_groq()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": construire_prompt_falc(texte_original)},
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Erreur simplification FALC :", e)
        return None
