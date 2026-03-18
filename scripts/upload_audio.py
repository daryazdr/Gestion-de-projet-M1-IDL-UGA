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
GITHUB_PAGES_BRANCH = "gh-pages"

AUDIO_REPO_DIR = "audio"
PLAYER_REPO_DIR = "player"
AUDIO_WEB_DIR = "audio"
PLAYER_WEB_DIR = "player"

LANG_TITLES = {
    "fr": "Ecouter en francais",
    "ru": "\u041f\u0440\u043e\u0441\u043b\u0443\u0448\u0430\u0442\u044c \u043d\u0430 \u0440\u0443\u0441\u0441\u043a\u043e\u043c",
    "en": "Listen in English",
    "ar": "\u0627\u0644\u0627\u0633\u062a\u0645\u0627\u0639 \u0628\u0627\u0644\u0639\u0631\u0628\u064a\u0629",
    "tr": "Turkce dinleyin",
}


def normaliser_repo(repo):
    repo = (repo or "").strip()
    if "github.com/" in repo:
        repo = repo.split("github.com/", 1)[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return repo.strip("/")


def detecter_langue(nom_audio):
    tokens = nom_audio.lower().split("_")
    if "falc" in tokens:
        return "fr"
    for token in reversed(tokens):
        if token in LANG_TITLES:
            return token
    return "fr"


def titre_pour_langue(langue):
    return LANG_TITLES.get(langue, LANG_TITLES["fr"])


def url_github_pages(chemin_web):
    return f"{GITHUB_PAGES_BASE_URL.rstrip('/')}/{quote(chemin_web)}"


def construire_page_player(nom_audio, audio_url):
    titre = titre_pour_langue(detecter_langue(nom_audio))
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titre}</title>
  <style>
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; background:#eef4fb; font-family:Arial,sans-serif; }}
    .card {{ width:min(94vw,640px); background:#fff; border-radius:20px; padding:30px; text-align:center; box-shadow:0 14px 30px rgba(16,36,62,.15); }}
    .controls {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; margin-top:16px; }}
    button {{ min-height:96px; border:none; border-radius:16px; color:white; cursor:pointer; font-weight:700; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; }}
    .seek {{ background:#1761cc; }}
    .play {{ background:#1f7a3a; }}
    .pause {{ background:#c93131; }}
    .icon {{ font-size:2.2rem; line-height:1; }}
    .time {{ margin-top:16px; color:#2f4868; }}
  </style>
</head>
<body>
  <main class="card">
    <h1>{titre}</h1>
    <audio id="player" preload="metadata" src="{audio_url}"></audio>
    <div class="controls">
      <button class="seek" onclick="seek(-5)"><span class="icon">&#9194;</span><span>5 sec</span></button>
      <button class="seek" onclick="seek(5)"><span class="icon">&#9193;</span><span>5 sec</span></button>
      <button class="play" onclick="playAudio()"><span class="icon">&#9654;</span><span>Play</span></button>
      <button class="pause" onclick="pauseAudio()"><span class="icon">&#9208;</span><span>Pause</span></button>
    </div>
    <p class="time" id="time">00:00 / 00:00</p>
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

    function refreshTime() {{ timeEl.textContent = `${{fmt(player.currentTime)}} / ${{fmt(player.duration)}}`; }}
    function playAudio() {{ player.play(); }}
    function pauseAudio() {{ player.pause(); }}
    function seek(delta) {{
      const maxDuration = Number.isFinite(player.duration) ? player.duration : player.currentTime + delta;
      player.currentTime = Math.max(0, Math.min(maxDuration, player.currentTime + delta));
      refreshTime();
    }}

    player.addEventListener('timeupdate', refreshTime);
    player.addEventListener('loadedmetadata', refreshTime);
  </script>
</body>
</html>
"""


def construire_bloc_audio(section_id, titre, audio_url):
    return f"""
    <section class="audio-block">
      <h2>{titre}</h2>
      <audio id="player_{section_id}" preload="metadata" src="{audio_url}"></audio>
      <div class="controls">
        <button class="seek" onclick="seek('player_{section_id}', 'time_{section_id}', -5)">
          <span class="icon">&#9194;</span><span>5 sec</span>
        </button>
        <button class="seek" onclick="seek('player_{section_id}', 'time_{section_id}', 5)">
          <span class="icon">&#9193;</span><span>5 sec</span>
        </button>
        <button class="play" onclick="playAudio('player_{section_id}')">
          <span class="icon">&#9654;</span><span>Play</span>
        </button>
        <button class="pause" onclick="pauseAudio('player_{section_id}')">
          <span class="icon">&#9208;</span><span>Pause</span>
        </button>
      </div>
      <p class="time" id="time_{section_id}">00:00 / 00:00</p>
    </section>
    """


def construire_page_player_multi(nom_page, langue, sections):
    del nom_page
    titre_page = titre_pour_langue(langue)
    blocs_html = []

    for index, section in enumerate(sections, start=1):
        blocs_html.append(
            construire_bloc_audio(
                f"sec{index}",
                section["titre"],
                section["audio_url"],
            )
        )

    contenu_blocs = "\n".join(blocs_html)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titre_page}</title>
  <style>
    body {{ margin:0; background:#eef4fb; font-family:Arial,sans-serif; }}
    .wrapper {{ width:min(94vw,900px); margin:30px auto; }}
    .card {{ background:#fff; border-radius:20px; padding:30px; box-shadow:0 14px 30px rgba(16,36,62,.15); }}
    h1 {{ text-align:center; margin-top:0; }}
    .audio-block {{ margin-top:28px; padding-top:20px; border-top:1px solid #d9e2ef; }}
    .audio-block:first-of-type {{ border-top:none; padding-top:0; }}
    h2 {{ color:#16324f; }}
    .controls {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; margin-top:16px; }}
    button {{ min-height:96px; border:none; border-radius:16px; color:white; cursor:pointer; font-weight:700; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; }}
    .seek {{ background:#1761cc; }}
    .play {{ background:#1f7a3a; }}
    .pause {{ background:#c93131; }}
    .icon {{ font-size:2.2rem; line-height:1; }}
    .time {{ margin-top:16px; color:#2f4868; }}
  </style>
</head>
<body>
  <main class="wrapper">
    <div class="card">
      <h1>{titre_page}</h1>
      {contenu_blocs}
    </div>
  </main>

  <script>
    function getPlayer(playerId) {{
      return document.getElementById(playerId);
    }}

    function getTimeEl(timeId) {{
      return document.getElementById(timeId);
    }}

    function fmt(s) {{
      if (!Number.isFinite(s)) return '00:00';
      const m = Math.floor(s / 60).toString().padStart(2, '0');
      const sec = Math.floor(s % 60).toString().padStart(2, '0');
      return `${{m}}:${{sec}}`;
    }}

    function refreshTime(playerId, timeId) {{
      const player = getPlayer(playerId);
      const timeEl = getTimeEl(timeId);
      timeEl.textContent = `${{fmt(player.currentTime)}} / ${{fmt(player.duration)}}`;
    }}

    function playAudio(playerId) {{
      getPlayer(playerId).play();
    }}

    function pauseAudio(playerId) {{
      getPlayer(playerId).pause();
    }}

    function seek(playerId, timeId, delta) {{
      const player = getPlayer(playerId);
      const maxDuration = Number.isFinite(player.duration) ? player.duration : player.currentTime + delta;
      player.currentTime = Math.max(0, Math.min(maxDuration, player.currentTime + delta));
      refreshTime(playerId, timeId);
    }}

    window.addEventListener('load', function() {{
      const audios = document.querySelectorAll('audio');
      audios.forEach(function(audio) {{
        const playerId = audio.id;
        const timeId = playerId.replace('player_', 'time_');

        audio.addEventListener('timeupdate', function() {{
          refreshTime(playerId, timeId);
        }});

        audio.addEventListener('loadedmetadata', function() {{
          refreshTime(playerId, timeId);
        }});
      }});
    }});
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
    reponse_get = requests.get(
        api_url,
        headers=headers,
        params={"ref": GITHUB_PAGES_BRANCH},
        timeout=30,
    )
    if reponse_get.status_code == 200:
        sha = reponse_get.json().get("sha")

    payload = {
        "message": message,
        "content": base64.b64encode(contenu_bytes).decode("utf-8"),
        "branch": GITHUB_PAGES_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    return requests.put(api_url, headers=headers, json=payload, timeout=60)


def publier_fichier_github(repo_dir, web_dir, fichier, message):
    chemin_repo = f"{repo_dir}/{fichier.name}"
    reponse = github_put_file(
        normaliser_repo(GITHUB_REPO),
        chemin_repo,
        fichier.read_bytes(),
        message,
    )

    if reponse.status_code not in [200, 201]:
        print("Erreur upload GitHub:", reponse.status_code, reponse.text)
        return None

    return url_github_pages(f"{web_dir}/{fichier.name}")


def publier_audio_github(fichier):
    return publier_fichier_github(
        AUDIO_REPO_DIR,
        AUDIO_WEB_DIR,
        fichier,
        f"upload audio {fichier.name}",
    )


def publier_html_github(nom_html, html):
    chemin_repo = f"{PLAYER_REPO_DIR}/{nom_html}"
    reponse = github_put_file(
        normaliser_repo(GITHUB_REPO),
        chemin_repo,
        html.encode("utf-8"),
        f"upload player {nom_html}",
    )

    if reponse.status_code not in [200, 201]:
        print("Erreur upload player GitHub:", reponse.status_code, reponse.text)
        return None

    return url_github_pages(f"{PLAYER_WEB_DIR}/{nom_html}")


def verifier_config():
    repo = normaliser_repo(GITHUB_REPO)
    if not GITHUB_TOKEN or not repo or not GITHUB_PAGES_BASE_URL:
        print(
            "Config GitHub manquante: GITHUB_TOKEN, GITHUB_REPO, GITHUB_PAGES_BASE_URL"
        )
        return None
    return repo


def upload_github_pages(chemin_fichier):
    repo = verifier_config()
    if not repo:
        return None

    fichier = Path(chemin_fichier)
    if not fichier.exists():
        print("Fichier introuvable:", chemin_fichier)
        return None

    audio_url = publier_audio_github(fichier)
    if not audio_url:
        return None

    player_url = publier_html_github(
        f"{fichier.stem}.html",
        construire_page_player(fichier.stem, audio_url),
    )
    if not player_url:
        return None

    print("Upload GitHub Pages OK (player):", player_url)
    return player_url


def upload_github_pages_multi(sections, nom_page, langue):
    """Publie plusieurs audios sur une meme page GitHub Pages."""
    repo = verifier_config()
    if not repo:
        return None

    sections_publiques = []

    for section in sections:
        fichier = Path(section["audio_path"])
        if not fichier.exists():
            print("Fichier audio introuvable:", section["audio_path"])
            continue

        audio_url = publier_audio_github(fichier)
        if not audio_url:
            continue

        sections_publiques.append(
            {"titre": section["titre"], "audio_url": audio_url}
        )

    if not sections_publiques:
        print("Aucun audio publie pour la page multiple.")
        return None

    player_url = publier_html_github(
        f"{nom_page}.html",
        construire_page_player_multi(nom_page, langue, sections_publiques),
    )
    if not player_url:
        return None

    print("Upload GitHub Pages OK (multi player):", player_url)
    return player_url
