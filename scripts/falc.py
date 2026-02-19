import os
from groq import Groq
from config import GROQ_API_KEY


def construire_prompt_falc(texte_original: str) -> str:
    return f"""
Tu es expert en simplification FALC (Facile à Lire et à Comprendre).

Règles de simplification :
    - Phrases courtes. Chaque phrase nouvelle commence sur une nouvelle ligne.
    - 1 idée par phrase. Chaque phrase termine par un point.
    - Vocabulaire simple et courant
    - Éviter métaphores, abréviations, initiales, acronymes, les expliquer si utilisées dans le texte, 
    pas en note de bas de page
    - Expliquer termes médicaux et concepts difficiles
    - S'adresser directement aux personnes en utilisant des mots comme « vous »
    - Utiliser des phrases positives plutôt que la négation
    - Utiliser des phrases actives plutôt que des phrases passives
    - Le style, la police, la mise en forme et le type d'écriture sont identiques tout au long du texte
    - Les pages sont numérotées (de la manière suivante : « page 2 sur 4 »)

Simplifie ce texte et :
- Garde TOUTES les informations médicales, ne supprime rien
- Ne change pas le sens médical
- Reste précis sur les consignes de santé
- Ne jamais modifier les valeurs numériques, unités, posologies

Texte à simplifier :
{texte_original}
"""


def simplifier_falc(texte_original: str) -> str:
    """
    Simplifie un texte médical en FALC avec Groq.
    Retourne le texte simplifié ou None en cas d'erreur.
    """

    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = construire_prompt_falc(texte_original)

        # Appel
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant spécialisé en simplification FALC pour des textes médicaux.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )

        # Récupération du texte généré
        texte_simplifie = response.choices[0].message.content
        return texte_simplifie

    except Exception as e:
        print("Erreur simplification FALC :", e)
        return None
