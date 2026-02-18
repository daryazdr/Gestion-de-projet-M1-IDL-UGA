import os
from groq import Groq
from config import GROQ_API_KEY


def construire_prompt_falc(texte_original: str) -> str:
    return f"""
Tu es expert en simplification FALC (Facile à Lire et à Comprendre).

Règles de simplification :
    - Phrases courtes. Chaque phrase nouvelle commence sur une nouvelle ligne
    - Un mot n'est jamais coupé en fin de ligne [⇒ pas de tiret (-) en fin de ligne]
    - Des points (puces ou numéros) sont utilisés pour lister des thèmes ou idées dans une même phrase
    - 1 idée par phrase
    - Vocabulaire simple et courant
    - Vocabulaire constant : utiliser le même mot pour parler de la même chose, tout au long du document
    - Éviter métaphores, abréviations, initiales, acronymes, les expliquer si utilisées dans le texte, 
    pas en note de bas de page
    - Expliquer termes médicaux et concepts difficiles, les expliquer si utilisées dans le texte, 
    pas en note de bas de page
    - Les titres sont courts et annoncent clairement ce qui va suivre
    - S'adresser directement aux personnes en utilisant des mots comme « vous »
    - Utiliser des phrases positives plutôt que négatives (ex. : préférer « Vous devriez rester jusqu’à 
    la fin de la réunion » plutôt que « Vous ne devriez pas partir avant la fin de la réunion »)
    - Utiliser des phrases actives plutôt que des phrases passives (ex. : « Le médecin vous enverra une 
    lettre » plutôt que « Vous recevrez une lettre envoyée par le médecin »)
    - Le texte est toujours aligné à gauche ; il n'est jamais justifié
    - Le texte est aéré (à larges interlignes et à espacement suffisant entre les caractères), 
    avec de larges marges (le texte ne doit pas avoir l'air à l'étroit dans la page)
    - Le texte est sans italique, sans lettrines, sans police à caractères à empattement, 
    à contour ou à ombre portée, et, si possible, sans caractères spéciaux tels que \, &, <, § ou #
    - La ponctuation est simple. Les caractères doivent au moins avoir la taille 14 de la police Arial 
    et bien se détacher sur le fond et ne pas être soulignés
    - Les mots entièrement en majuscules sont à éviter
    - Le style, la police, la mise en forme et le type d'écriture sont identiques tout au long du texte, 
    qui ne doit pas être trop long
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
