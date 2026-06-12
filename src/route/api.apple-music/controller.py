import base64
import json
import os
import subprocess
import tempfile
import time

import requests


ENV_FILE = os.environ.get("RUNNINGMATE_APPLE_MUSIC_ENV_FILE", "/opt/app/config/apple-music.env")
RECENT_TRACKS_URL = "https://api.music.apple.com/v1/me/recent/played/tracks"
MAX_DEVELOPER_TOKEN_SECONDS = 60 * 60 * 24 * 180


def _load_env_file():
    if not ENV_FILE or not os.path.exists(ENV_FILE):
        return

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as fp:
            for line in fp:
                key, _, value = line.strip().partition("=")
                if key and value and key not in os.environ:
                    os.environ[key] = value.strip().strip('"').strip("'")
    except Exception:
        return


def _payload():
    raw = wiz.server.package.flask.request.get_data(as_text=True)
    if not raw:
        return {}

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}

    return {}


def _session_user_id():
    try:
        session = wiz.model("portal/season/session").use()
        return session.get("id")
    except Exception:
        return None


def _env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return ""


def _b64url(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _read_der_length(data, index):
    first = data[index]
    index += 1
    if first < 0x80:
        return first, index
    count = first & 0x7F
    length = int.from_bytes(data[index:index + count], "big")
    return length, index + count


def _der_signature_to_raw(der):
    if not der or der[0] != 0x30:
        return None

    _, index = _read_der_length(der, 1)
    if index >= len(der) or der[index] != 0x02:
        return None
    r_length, index = _read_der_length(der, index + 1)
    r = der[index:index + r_length]
    index += r_length
    if index >= len(der) or der[index] != 0x02:
        return None
    s_length, index = _read_der_length(der, index + 1)
    s = der[index:index + s_length]

    r = r.lstrip(b"\x00").rjust(32, b"\x00")
    s = s.lstrip(b"\x00").rjust(32, b"\x00")
    if len(r) != 32 or len(s) != 32:
        return None
    return r + s


def _private_key_file():
    key_path = _env(
        "RUNNINGMATE_APPLE_MUSIC_PRIVATE_KEY_PATH",
        "APPLE_MUSIC_PRIVATE_KEY_PATH",
        "MUSICKIT_PRIVATE_KEY_PATH",
    )
    if key_path and os.path.exists(key_path):
        return key_path, None

    key_content = _env(
        "RUNNINGMATE_APPLE_MUSIC_PRIVATE_KEY",
        "APPLE_MUSIC_PRIVATE_KEY",
        "MUSICKIT_PRIVATE_KEY",
    )
    if not key_content:
        return "", None

    key_content = key_content.replace("\\n", "\n")
    temp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".p8", delete=False)
    temp.write(key_content)
    temp.close()
    os.chmod(temp.name, 0o600)
    return temp.name, temp.name


def _generated_developer_token():
    team_id = _env("RUNNINGMATE_APPLE_MUSIC_TEAM_ID", "APPLE_MUSIC_TEAM_ID", "MUSICKIT_TEAM_ID")
    key_id = _env("RUNNINGMATE_APPLE_MUSIC_KEY_ID", "APPLE_MUSIC_KEY_ID", "MUSICKIT_KEY_ID")
    key_path, temp_path = _private_key_file()
    if not team_id or not key_id or not key_path:
        return "", "Developer Token 설정이 필요합니다."

    now = int(time.time())
    ttl = _env("RUNNINGMATE_APPLE_MUSIC_TOKEN_TTL_SECONDS", "APPLE_MUSIC_TOKEN_TTL_SECONDS")
    try:
        ttl_seconds = min(MAX_DEVELOPER_TOKEN_SECONDS, max(60, int(ttl))) if ttl else MAX_DEVELOPER_TOKEN_SECONDS
    except Exception:
        ttl_seconds = MAX_DEVELOPER_TOKEN_SECONDS

    header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
    body = {"iss": team_id, "iat": now, "exp": now + ttl_seconds}
    signing_input = ".".join([
        _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64url(json.dumps(body, separators=(",", ":")).encode("utf-8")),
    ]).encode("ascii")

    try:
        result = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=signing_input,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return "", "Developer Token 서명에 실패했습니다."
        signature = _der_signature_to_raw(result.stdout)
        if not signature:
            return "", "Developer Token 서명을 변환하지 못했습니다."
        return f"{signing_input.decode('ascii')}.{_b64url(signature)}", ""
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except Exception:
                pass


def _developer_token():
    static_token = _env("RUNNINGMATE_APPLE_MUSIC_DEVELOPER_TOKEN", "APPLE_MUSIC_DEVELOPER_TOKEN", "MUSICKIT_DEVELOPER_TOKEN")
    if static_token:
        return static_token, ""
    return _generated_developer_token()


def _artwork_url(artwork):
    if not isinstance(artwork, dict):
        return ""
    url = str(artwork.get("url") or "").strip()
    if not url:
        return ""
    return url.replace("{w}", "160").replace("{h}", "160")


def _track(row):
    source = row if isinstance(row, dict) else {}
    attributes = source.get("attributes") if isinstance(source.get("attributes"), dict) else {}
    title = str(attributes.get("name") or "").strip()
    artist = str(attributes.get("artistName") or "").strip()
    if not title or not artist:
        return None

    return {
        "id": str(source.get("id") or f"{title}:{artist}"),
        "title": title,
        "artist": artist,
        "album": str(attributes.get("albumName") or "").strip(),
        "album_art_url": _artwork_url(attributes.get("artwork")),
        "url": str(attributes.get("url") or "").strip(),
    }


def _recent_tracks(user_token, developer_token):
    response = requests.get(
        RECENT_TRACKS_URL,
        headers={
            "Authorization": f"Bearer {developer_token}",
            "Music-User-Token": user_token,
        },
        timeout=12,
    )
    try:
        payload = response.json()
    except Exception:
        payload = {}

    if response.status_code == 401:
        return None, "Apple Music 권한을 다시 연결해야 합니다."
    if response.status_code == 403:
        return None, "Apple Music 구독 또는 미디어 라이브러리 권한이 필요합니다."
    if response.status_code == 404:
        return None, "최근 재생곡을 찾지 못했습니다."
    if response.status_code >= 400:
        return None, payload.get("detail") or payload.get("message") or "최근 재생곡을 불러오지 못했습니다."

    rows = payload.get("data") if isinstance(payload, dict) else []
    tracks = []
    for row in rows[:30] if isinstance(rows, list) else []:
        item = _track(row)
        if item:
            tracks.append(item)
    return tracks, ""


_load_env_file()
if not _session_user_id():
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

request = wiz.server.package.flask.request
developer_token, token_error = _developer_token()

if request.method == "GET":
    configured = bool(developer_token)
    wiz.response.json({
        "success": True,
        "configured": configured,
        "developer_token": developer_token if configured else "",
        "message": "Apple Music Developer Token 준비됨" if configured else token_error,
        "setup_steps": [
            "RUNNINGMATE_APPLE_MUSIC_TEAM_ID 설정",
            "RUNNINGMATE_APPLE_MUSIC_KEY_ID 설정",
            "RUNNINGMATE_APPLE_MUSIC_PRIVATE_KEY_PATH 또는 RUNNINGMATE_APPLE_MUSIC_DEVELOPER_TOKEN 설정",
        ] if not configured else [],
    })
else:
    data = _payload()
    user_token = str(
        data.get("user_token")
        or data.get("userToken")
        or request.headers.get("Music-User-Token")
        or ""
    ).strip()

    if not developer_token:
        wiz.response.json({"success": False, "message": token_error or "Developer Token 설정이 필요합니다."})
    elif not user_token:
        wiz.response.json({"success": False, "message": "Apple Music User Token이 필요합니다."})
    else:
        tracks, error = _recent_tracks(user_token, developer_token)
        if error:
            wiz.response.json({"success": False, "message": error, "data": []})
        else:
            wiz.response.json({"success": True, "data": tracks})
