import base64
from pathlib import Path
from urllib.parse import quote

import requests

try:
    import config
except Exception:
    config = None


GITHUB_TOKEN = getattr(config, "GITHUB_TOKEN", "") if config else ""
GITHUB_REPO = getattr(config, "GITHUB_REPO", "") if config else ""
GITHUB_PAGES_BASE_URL = getattr(config, "GITHUB_PAGES_BASE_URL", "") if config else ""
GITHUB_PAGES_BRANCH = "main"

# GitHub Pages publie depuis main/docs
AUDIO_REPO_DIR = "docs/audio"
PLAYER_REPO_DIR = "docs/player"

# URL publique (sans docs/)
AUDIO_WEB_DIR = "audio"
PLAYER_WEB_DIR = "player"

LANG_PAGE_LABELS = {
    "ru": "Прослушать на русском",
    "fr": "Ecouter en francais",
    "en": "Listen in English",
    "ar": "الاستماع بالعربية",
    "tr": "Turkce dinleyin",
}


def normaliser_repo(repo):
    repo = (repo or "").strip()
    if not repo:
        return ""

    if repo.startswith("http://") or repo.startswith("https://"):
        repo = repo.rstrip("/")
        if repo.endswith(".git"):
            repo = repo[:-4]
        if "github.com/" in repo:
            repo = repo.split("github.com/", 1)[1]

    return repo.strip("/")


def detecter_langue_depuis_nom(nom_audio):
    tokens = nom_audio.lower().split("_")
    if "falc" in tokens:
        return "fr"

    for token in reversed(tokens):
        if token in LANG_PAGE_LABELS:
            return token

    return "fr"


def texte_titre_player(nom_audio):
    langue = detecter_langue_depuis_nom(nom_audio)
    return LANG_PAGE_LABELS.get(langue, LANG_PAGE_LABELS["fr"])


def construire_page_player(nom_audio, audio_url):
    titre_page = texte_titre_player(nom_audio)

    return f"""<!doctype html>
<html lang=\"fr\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{titre_page}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #f7f9fc, #e7eef8);
      font-family: Arial, sans-serif;
      color: #10243e;
    }}
    .card {{
      width: min(94vw, 640px);
      background: white;
      border-radius: 20px;
      padding: 30px;
      box-shadow: 0 14px 30px rgba(16, 36, 62, 0.15);
      text-align: center;
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: 1.6rem;
      word-break: break-word;
    }}
    .controls {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(2, 1fr);
      margin-top: 16px;
    }}
    button {{
      min-height: 96px;
      border: none;
      border-radius: 16px;
      cursor: pointer;
      color: white;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 6px;
      font-weight: 700;
    }}
    .icon {{
      font-size: 2.2rem;
      line-height: 1;
    }}
    .txt {{
      font-size: 1rem;
      line-height: 1;
    }}
    button.seek {{
      background: #1761cc;
    }}
    button.play {{
      background: #1f7a3a;
    }}
    button.pause {{
      background: #c93131;
    }}
    .time {{
      margin-top: 16px;
      font-size: 1.05rem;
      color: #2f4868;
    }}
  </style>
</head>
<body>
  <main class=\"card\">
    <h1>{titre_page}</h1>
    <audio id=\"player\" preload=\"metadata\" src=\"{audio_url}\"></audio>

    <div class=\"controls\">
      <button type=\"button\" class=\"seek\" aria-label=\"Reculer 5 secondes\" onclick=\"seek(-5)\">
        <span class=\"icon\">⏪</span>
        <span class=\"txt\">5 sec</span>
      </button>
      <button type=\"button\" class=\"seek\" aria-label=\"Avancer 5 secondes\" onclick=\"seek(5)\">
        <span class=\"icon\">⏩</span>
        <span class=\"txt\">5 sec</span>
      </button>
      <button type=\"button\" class=\"play\" aria-label=\"Lecture\" onclick=\"playAudio()\">
        <span class=\"icon\">▶</span>
        <span class=\"txt\">Play</span>
      </button>
      <button type=\"button\" class=\"pause\" aria-label=\"Pause\" onclick=\"pauseAudio()\">
        <span class=\"icon\">⏸</span>
        <span class=\"txt\">Pause</span>
      </button>
    </div>

    <p class=\"time\" id=\"time\">00:00 / 00:00</p>
  </main>

  <script>
    const player = document.getElementById('player');
    const timeEl = document.getElementById('time');

    function fmt(s) {{
      if (!Number.isFinite(s)) return '00:00';
      const m = Math.floor(s / 60).toString().padStart(2, '0');
      const sec = Math.floor(s % 60).toString().padStart(2, '0');
      return `${{m}}:${{sec}}`;
    }}

    function refreshTime() {{
      timeEl.textContent = `${{fmt(player.currentTime)}} / ${{fmt(player.duration)}}`;
    }}

    function playAudio() {{ player.play(); }}
    function pauseAudio() {{ player.pause(); }}
    function seek(delta) {{
      const maxDuration = Number.isFinite(player.duration) ? player.duration : player.currentTime + delta;
      const next = Math.max(0, Math.min(maxDuration, player.currentTime + delta));
      player.currentTime = next;
      refreshTime();
    }}

    player.addEventListener('timeupdate', refreshTime);
    player.addEventListener('loadedmetadata', refreshTime);
  </script>
</body>
</html>
"""


def github_put_file(repo, chemin_repo, contenu_bytes, message):
    api_url = f"https://api.github.com/repos/{repo}/contents/{chemin_repo}"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    sha = None
    response_get = requests.get(
        api_url,
        headers=headers,
        params={"ref": GITHUB_PAGES_BRANCH},
        timeout=30,
    )
    if response_get.status_code == 200:
        sha = response_get.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(contenu_bytes).decode("utf-8"),
        "branch": GITHUB_PAGES_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    return requests.put(api_url, headers=headers, json=payload, timeout=60)


def upload_github_pages(chemin_fichier):
    repo = normaliser_repo(GITHUB_REPO)

    if not GITHUB_TOKEN or not repo or not GITHUB_PAGES_BASE_URL:
        print("Config GitHub manquante: GITHUB_TOKEN, GITHUB_REPO, GITHUB_PAGES_BASE_URL")
        return None

    fichier = Path(chemin_fichier)
    if not fichier.exists():
        print("Fichier introuvable:", chemin_fichier)
        return None

    audio_repo_path = f"{AUDIO_REPO_DIR}/{fichier.name}"
    response_audio = github_put_file(
        repo,
        audio_repo_path,
        fichier.read_bytes(),
        f"upload audio {fichier.name}",
    )
    if response_audio.status_code not in [200, 201]:
        print("Erreur upload audio GitHub:", response_audio.status_code, response_audio.text)
        return None

    audio_web_path = f"{AUDIO_WEB_DIR}/{fichier.name}"
    audio_url_public = f"{GITHUB_PAGES_BASE_URL.rstrip('/')}/{quote(audio_web_path)}"

    player_filename = f"{fichier.stem}.html"
    player_repo_path = f"{PLAYER_REPO_DIR}/{player_filename}"
    html = construire_page_player(fichier.stem, audio_url_public)

    response_player = github_put_file(
        repo,
        player_repo_path,
        html.encode("utf-8"),
        f"upload player {player_filename}",
    )
    if response_player.status_code not in [200, 201]:
        print("Erreur upload player GitHub:", response_player.status_code, response_player.text)
        return None

    player_web_path = f"{PLAYER_WEB_DIR}/{player_filename}"
    player_url = f"{GITHUB_PAGES_BASE_URL.rstrip('/')}/{quote(player_web_path)}"
    print("Upload GitHub Pages OK (player):", player_url)
    return player_url