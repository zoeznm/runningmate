import json
import hmac
import os
import re
import shutil
import subprocess
import tempfile
import time


DEFAULT_VISION_MODEL = "gpt-5.4-mini"
ENV_FILE = os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", "/opt/app/config/openai.env")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
DEVICE_CODE_RE = re.compile(r"\b[A-Z0-9]{4,5}-[A-Z0-9]{4,6}\b")
security = wiz.model("security")


def _load_env_file():
    if not ENV_FILE or not os.path.exists(ENV_FILE):
        return

    try:
        with open(ENV_FILE, "r", encoding="utf-8") as fp:
            for line in fp:
                key, _, value = line.strip().partition("=")
                if key and value:
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


def _request_token():
    request = wiz.server.package.flask.request
    auth = str(request.headers.get("Authorization") or "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return str(
        request.headers.get("X-Runningmate-Admin-Token")
        or request.args.get("admin_token")
        or ""
    ).strip()


def _is_admin_session():
    return security.is_admin_session()


def _is_admin_request():
    if _is_admin_session():
        return True

    expected = os.environ.get("RUNNINGMATE_ADMIN_TOKEN", "").strip()
    token = _request_token()
    return bool(expected and token and hmac.compare_digest(expected, token))


def _same_origin_request():
    request = wiz.server.package.flask.request
    origin = str(request.headers.get("Origin") or "").rstrip("/")
    referer = str(request.headers.get("Referer") or "").rstrip("/")
    scheme = str(request.headers.get("X-Forwarded-Proto") or request.scheme or "http").split(",")[0].strip()
    host_name = str(request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
    host = f"{scheme}://{host_name}".rstrip("/")

    if origin and origin != host:
        return False
    if not origin and referer and not referer.startswith(host + "/"):
        return False
    return True


def _deny_admin():
    context = security.session_context()
    security.audit("ai_config.admin_denied", actor_id=context.get("id"), actor_role=context.get("role"), success=False)
    flask = wiz.server.package.flask
    response = flask.Response(
        json.dumps({"success": False, "message": "관리자 권한이 필요합니다."}, ensure_ascii=False),
        status=403,
        content_type="application/json; charset=utf-8",
    )
    return wiz.response.response(response)


def _configured(codex_status=None):
    if _ai_provider() == "codex":
        status = codex_status or _codex_status()
        return bool(status.get("available") and status.get("authenticated"))
    return bool(os.environ.get("OPENAI_API_KEY"))


def _model():
    if _ai_provider() == "codex":
        return os.environ.get("RUNNINGMATE_CODEX_MODEL", "codex-cli")
    return os.environ.get("RUNNINGMATE_CHAT_MODEL") or os.environ.get("RUNNINGMATE_VISION_MODEL", DEFAULT_VISION_MODEL)


def _ai_provider():
    return str(os.environ.get("RUNNINGMATE_AI_PROVIDER") or "openai").strip().lower()


def _codex_available():
    return bool(shutil.which("codex"))


def _clean_output(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", "ignore")
    return ANSI_RE.sub("", str(text or "")).strip()


def _run_codex(args, input_text="", timeout=12):
    codex = shutil.which("codex")
    if not codex:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": "Codex CLI not found",
        }

    try:
        result = subprocess.run(
            [codex, *args],
            check=False,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout,
        )
        return {
            "returncode": result.returncode,
            "stdout": _clean_output(result.stdout),
            "stderr": _clean_output(result.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": 124,
            "stdout": _clean_output(getattr(exc, "stdout", "") or ""),
            "stderr": "Codex command timed out",
        }
    except Exception as exc:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(exc),
        }


def _codex_status():
    if not _codex_available():
        return {
            "available": False,
            "authenticated": False,
            "status": "Codex CLI 없음",
            "message": "서버에 Codex CLI가 설치되어 있지 않습니다.",
        }

    result = _run_codex(["login", "status"], timeout=6)
    status_text = result.get("stdout") or result.get("stderr") or ""
    authenticated = result.get("returncode") == 0 and "Logged in" in status_text
    return {
        "available": True,
        "authenticated": authenticated,
        "status": status_text or ("로그인 상태 확인 실패" if result.get("returncode") else "로그인 상태 확인 완료"),
        "message": "Codex 로그인이 활성화되어 있습니다." if authenticated else "Codex 로그인을 갱신해야 합니다.",
    }


def _device_auth_payload(output):
    text = _clean_output(output)
    url_match = re.search(r"https://auth\.openai\.com/[^\s]+", text)
    code_match = DEVICE_CODE_RE.search(text)

    if not url_match or not code_match:
        return None

    return {
        "auth_url": url_match.group(0),
        "user_code": code_match.group(0),
        "expires_in_minutes": 15,
    }


def _start_device_auth():
    codex = shutil.which("codex")
    if not codex:
        return None, None

    log = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="runningmate-codex-login-",
        suffix=".log",
        delete=False,
    )
    log_path = log.name
    process = subprocess.Popen(
        [codex, "login", "--device-auth"],
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    log.close()

    deadline = time.time() + 8
    output = ""
    while time.time() < deadline:
        time.sleep(0.35)
        try:
            with open(log_path, "r", encoding="utf-8") as fp:
                output = fp.read()
        except Exception:
            output = ""

        device = _device_auth_payload(output)
        if device:
            device["auth_session_pid"] = process.pid
            return device, process

        if process.poll() is not None:
            break

    return None, process


def _refresh_codex_login():
    _load_env_file()
    if not _codex_available():
        return {
            "success": False,
            "message": "서버에 Codex CLI가 설치되어 있지 않습니다.",
            "codex_status": _codex_status(),
        }

    access_token = os.environ.get("CODEX_ACCESS_TOKEN", "").strip()
    if access_token:
        result = _run_codex(["login", "--with-access-token"], input_text=f"{access_token}\n", timeout=20)
        ok = result.get("returncode") == 0
        return {
            "success": ok,
            "message": "저장된 토큰으로 Codex 로그인을 갱신했습니다." if ok else "저장된 토큰으로 로그인 갱신에 실패했습니다.",
            "codex_status": _codex_status(),
        }

    device, process = _start_device_auth()
    if device:
        return {
            "success": True,
            "requires_action": True,
            "message": "새 Codex 인증 코드를 발급했습니다.",
            "codex_status": _codex_status(),
            **device,
        }

    ok = process is not None and process.poll() == 0
    return {
        "success": ok,
        "message": "Codex 로그인 갱신을 요청했습니다." if ok else "Codex 로그인 갱신을 시작하지 못했습니다.",
        "codex_status": _codex_status(),
    }


def _steps():
    if _ai_provider() == "codex":
        return [
            "AI 설정에서 로그인 갱신을 눌러 Codex 인증 코드를 발급한다.",
            "인증 페이지에서 같은 OpenAI 계정으로 로그인한다.",
            "상태 다시 확인을 눌러 연결을 확인한다.",
            "RUNNINGMATE_AI_PROVIDER=codex를 설정한다.",
        ]

    return [
        "OpenAI Platform에서 개인 API key를 만든다.",
        "서버 환경 변수 OPENAI_API_KEY에 그 키를 넣는다.",
        "선택: RUNNINGMATE_CHAT_MODEL과 RUNNINGMATE_VISION_MODEL로 채팅/이미지 파싱 모델을 각각 바꾼다.",
        "API 크레딧 또는 월 사용 한도를 확보한다.",
        "WIZ 서비스를 재시작한 뒤 업로드 탭에서 연결 상태를 확인한다.",
    ]


def _message(codex_mode, configured):
    if codex_mode:
        return "Codex CLI 로그인과 AI 채팅 백엔드가 연결되어 있습니다." if configured else "Codex 로그인 갱신이 필요합니다."
    return "OpenAI API 키가 연결되어 있습니다." if configured else "OpenAI API 키와 API 크레딧을 설정해야 합니다."


def _config_payload():
    provider = _ai_provider()
    codex_mode = provider == "codex"
    codex_status = _codex_status() if codex_mode else {
        "available": False,
        "authenticated": False,
        "status": "",
        "message": "",
    }
    configured = _configured(codex_status)

    return {
        "success": True,
        "configured": configured,
        "provider": "Codex CLI" if codex_mode else "OpenAI Responses API",
        "model": _model(),
        "codex_supported": _codex_available(),
        "codex_authenticated": bool(codex_status.get("authenticated")),
        "codex_status": "authenticated" if codex_status.get("authenticated") else "not_authenticated",
        "codex_status_message": codex_status.get("message", ""),
        "login_refresh_supported": codex_mode and _codex_available(),
        "mode": provider,
        "required_env": "OPENAI_API_KEY",
        "optional_env": ["RUNNINGMATE_AI_PROVIDER", "RUNNINGMATE_CHAT_MODEL", "RUNNINGMATE_VISION_MODEL", "RUNNINGMATE_IMAGE_DETAIL", "RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT", "RUNNINGMATE_CODEX_TIMEOUT", "RUNNINGMATE_ADMIN_TOKEN", "CODEX_ACCESS_TOKEN"],
        "setup_steps": _steps(),
        "message": _message(codex_mode, configured),
    }


_load_env_file()
request = wiz.server.package.flask.request
if request.method == "POST":
    if not _same_origin_request() or not _is_admin_request():
        _deny_admin()
    else:
        payload = _payload()
        action = str(payload.get("action") or "refresh_login").strip().lower()
        context = security.session_context()
        security.audit("ai_config.admin_action", actor_id=context.get("id"), actor_role=context.get("role"), metadata={"action": action})
        if action in {"refresh_login", "refresh-login", "login_refresh"}:
            result = _refresh_codex_login()
            result["config"] = _config_payload()
            wiz.response.json(result)
        else:
            wiz.response.json(_config_payload())
else:
    wiz.response.json(_config_payload())
