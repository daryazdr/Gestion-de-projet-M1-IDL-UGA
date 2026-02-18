import base64
from pathlib import Path

import requests

try:
    import config
except Exception:
    config = None


GITHUB_TOKEN = getattr(config, "GITHUB_TOKEN", "") if config else ""
GITHUB_REPO = getattr(config, "GITHUB_REPO", "") if config else ""
GITHUB_PAGES_BASE_URL = getattr(config, "GITHUB_PAGES_BASE_URL", "") if config else ""


def upload_github_pages(chemin_fichier):
    """
    Envoie un fichier audio vers la branche gh-pages via l'API GitHub.
    Retourne l'URL publique GitHub Pages.
    """
    if not GITHUB_TOKEN or not GITHUB_REPO or not GITHUB_PAGES_BASE_URL:
        print(
            "Config GitHub manquante: GITHUB_TOKEN, GITHUB_REPO, GITHUB_PAGES_BASE_URL"
        )
        return None

    fichier = Path(chemin_fichier)
    if not fichier.exists():
        print("Fichier introuvable:", chemin_fichier)
        return None

    contenu_base64 = base64.b64encode(fichier.read_bytes()).decode("utf-8")
    chemin_repo = f"audio/{fichier.name}"
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{chemin_repo}"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # Si le fichier existe deja, on recupere son SHA pour l'ecraser
    sha = None
    response_get = requests.get(api_url, headers=headers, timeout=30)
    if response_get.status_code == 200:
        sha = response_get.json().get("sha")

    payload = {
        "message": f"upload audio {fichier.name}",
        "content": contenu_base64,
        "branch": "gh-pages",
    }
    if sha:
        payload["sha"] = sha

    response_put = requests.put(api_url, headers=headers, json=payload, timeout=60)
    if response_put.status_code not in [200, 201]:
        print("Erreur upload GitHub:", response_put.status_code, response_put.text)
        return None

    url_publique = f"{GITHUB_PAGES_BASE_URL.rstrip('/')}/{chemin_repo}"
    print("Upload GitHub Pages OK:", url_publique)
    return url_publique
