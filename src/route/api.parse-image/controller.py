import base64
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time
import uuid


running = wiz.model("runningmate")
security = wiz.model("security")
session = wiz.model("portal/season/session").use()

if not session.get("id"):
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

DEFAULT_VISION_MODEL = "gpt-5.4-mini"
DEFAULT_IMAGE_DETAIL = "high"
DEFAULT_CODEX_TIMEOUT = 180
DEFAULT_AI_IMAGE_PARSE_COOLDOWN_SECONDS = 30
DEFAULT_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS = 300
DEFAULT_AI_IMAGE_PARSE_RATE_MAX_REQUESTS = 5
DEFAULT_AI_IMAGE_PARSE_MONTHLY_LIMIT = 35
DEFAULT_OPENAI_RETRY_MAX = 2
DEFAULT_OPENAI_BACKOFF_BASE_SECONDS = 0.8
DEFAULT_OPENAI_BACKOFF_MAX_SECONDS = 8
ENV_FILE = os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", "/opt/app/config/openai.env")
UPLOAD_DIR = os.environ.get("RUNNINGMATE_UPLOAD_DIR", "/opt/app/data/run_images")
DEFAULT_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
IMAGE_MIME_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/heic": ".heic",
    "image/heif": ".heif",
}

PROMPT = """
러닝 앱 캡처 이미지에서 러닝 기록을 추출해 JSON만 반환해.
이미지를 먼저 OCR로 읽고, 화면에 보이는 총 러닝 거리와 날짜를 가장 우선해서 판단해.
필드:
- date: YYYY-MM-DD
- distance_km: float. 화면의 총 러닝 거리 값만 km 단위 숫자로 반환해. 예: "3.24 km"는 3.24, "3.08 km"는 3.08. 소수점 둘째 자리를 반올림하거나 줄이지 마. 페이스, 시간, 칼로리, 고도, 걸음 수를 거리로 쓰지 마.
- avg_pace: MM'SS" 형식
- duration: HH:MM:SS 형식
- calories: int
- avg_heart_rate: int
- cadence: int
- elevation_gain: float 또는 null
- raw_text: OCR로 읽은 주요 텍스트를 한 줄 문자열로 요약
읽을 수 없는 필드는 null로 반환해.
반환값은 설명 없이 순수 JSON 객체 하나여야 해.
"""

CODEX_PROMPT = PROMPT + """
이미지에 러닝 기록이 없거나 값을 확신할 수 없으면 해당 필드는 null로 둬.
최종 답변에는 JSON 객체만 출력해.
"""


def _json_payload():
    raw = wiz.server.package.flask.request.get_data(as_text=True)
    if not raw:
        return {}

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data.get("data") if isinstance(data.get("data"), dict) else data
    except Exception:
        return {}

    return {}


def _uploaded_file():
    files = wiz.server.package.flask.request.files
    if not files:
        return None

    return files.get("image") or files.get("file") or next(iter(files.values()), None)


def _target_date():
    request = wiz.server.package.flask.request
    value = (
        request.form.get("target_date")
        or request.form.get("date")
        or request.args.get("target_date")
        or request.args.get("date")
    )
    if not value:
        return None

    return running.normalize_run({"date": value}).get("date")


def _image_extension(file_storage):
    ext = os.path.splitext(file_storage.filename or "")[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return ext

    return IMAGE_MIME_EXTENSIONS.get(file_storage.mimetype or "", ".png")


def _max_upload_bytes():
    try:
        return max(1024, int(os.environ.get("RUNNINGMATE_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES)))
    except Exception:
        return DEFAULT_MAX_UPLOAD_BYTES


def _uploaded_size(file_storage):
    content_length = getattr(file_storage, "content_length", None)
    if content_length:
        try:
            return int(content_length)
        except Exception:
            pass

    stream = getattr(file_storage, "stream", None)
    if not stream:
        return 0

    try:
        position = stream.tell()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(position)
        return size
    except Exception:
        _rewind_file(file_storage)
        return 0


def _read_header(file_storage, size=32):
    stream = getattr(file_storage, "stream", None)
    if not stream:
        return b""

    try:
        position = stream.tell()
        stream.seek(0)
        header = stream.read(size)
        stream.seek(position)
        return header or b""
    except Exception:
        _rewind_file(file_storage)
        return b""


def _looks_like_supported_image(file_storage):
    ext = _image_extension(file_storage)
    mimetype = str(file_storage.mimetype or "").lower()
    header = _read_header(file_storage)

    if ext in {".jpg", ".jpeg"} or mimetype == "image/jpeg":
        return header.startswith(b"\xff\xd8\xff")
    if ext == ".png" or mimetype == "image/png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".gif" or mimetype == "image/gif":
        return header.startswith((b"GIF87a", b"GIF89a"))
    if ext == ".webp" or mimetype == "image/webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    if ext in {".heic", ".heif"} or mimetype in {"image/heic", "image/heif"}:
        return b"ftyp" in header[:16] and any(brand in header[:32] for brand in (b"heic", b"heif", b"mif1", b"msf1"))
    return False


def _validate_upload(file_storage):
    ext = os.path.splitext(file_storage.filename or "")[1].lower()
    mimetype = str(file_storage.mimetype or "").lower()
    if ext not in IMAGE_EXTENSIONS and mimetype not in IMAGE_MIME_EXTENSIONS:
        return _error_payload("지원하지 않는 이미지 형식입니다.", "unsupported_image_type")

    size = _uploaded_size(file_storage)
    if size > _max_upload_bytes():
        return _error_payload("이미지 파일이 너무 큽니다.", "image_too_large")

    if not _looks_like_supported_image(file_storage):
        return _error_payload("이미지 파일 형식을 확인하지 못했습니다.", "invalid_image_file")

    return None


def _rewind_file(file_storage):
    try:
        file_storage.stream.seek(0)
    except Exception:
        pass


def _delete_file(path):
    if not path:
        return

    try:
        os.unlink(path)
    except Exception:
        pass


def _persist_uploaded_image(file_storage):
    validation_error = _validate_upload(file_storage)
    if validation_error:
        _rewind_file(file_storage)
        return None, None, validation_error

    temp_path = None
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        incoming_dir = security.upload_incoming_dir(UPLOAD_DIR)
        filename = f"{uuid.uuid4().hex}{_image_extension(file_storage)}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        temp_path = os.path.join(incoming_dir, f"{filename}.upload")
        file_storage.save(temp_path)
        scan_ok, scan_error = security.scan_upload_file(temp_path)
        if not scan_ok:
            _delete_file(temp_path)
            _rewind_file(file_storage)
            return None, None, _error_payload(scan_error, "malware_scan_failed")
        os.replace(temp_path, filepath)
        _rewind_file(file_storage)
        return filepath, f"/api/run-images/{filename}", None
    except Exception:
        _delete_file(temp_path)
        _rewind_file(file_storage)
        return None, None, _error_payload("업로드 이미지를 저장하지 못했습니다.", "image_store_failed")


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


def _env_int(name, default):
    _load_env_file()
    try:
        return max(0, int(os.environ.get(name, default)))
    except Exception:
        return default


def _env_float(name, default):
    _load_env_file()
    try:
        return max(0.0, float(os.environ.get(name, default)))
    except Exception:
        return default


def _current_user_id():
    return session.get("id") or ""


def _image_parse_rate_limits():
    return (
        _env_int("RUNNINGMATE_AI_IMAGE_PARSE_COOLDOWN_SECONDS", DEFAULT_AI_IMAGE_PARSE_COOLDOWN_SECONDS),
        _env_int("RUNNINGMATE_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS", DEFAULT_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS),
        _env_int("RUNNINGMATE_AI_IMAGE_PARSE_RATE_MAX_REQUESTS", DEFAULT_AI_IMAGE_PARSE_RATE_MAX_REQUESTS),
    )


def _reserve_image_parse_rate_limit():
    cooldown_seconds, window_seconds, max_requests = _image_parse_rate_limits()
    return running.reserve_ai_rate_limit(
        _current_user_id(),
        action="image_parse",
        cooldown_seconds=cooldown_seconds,
        window_seconds=window_seconds,
        max_requests=max_requests,
    )


def _image_parse_monthly_limit():
    return _env_int("RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT", DEFAULT_AI_IMAGE_PARSE_MONTHLY_LIMIT)


def _reserve_image_parse_usage():
    return running.reserve_ai_usage(
        _current_user_id(),
        action="image_parse",
        daily_limit=0,
        monthly_limit=_image_parse_monthly_limit(),
    )


def _image_parse_usage_message(usage):
    if usage and usage.get("reason") == "monthly_limit":
        limit = usage.get("monthly_limit") or _image_parse_monthly_limit()
        return f"이번 달 이미지 파싱 {limit}회를 모두 사용했습니다. 다음 달에 다시 이용해주세요."
    return (usage or {}).get("message") or "이미지 파싱 사용량 제한에 도달했습니다."


def _extract_json(text):
    text = str(text or "").strip()
    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def _ai_provider():
    _load_env_file()
    return str(os.environ.get("RUNNINGMATE_AI_PROVIDER") or "openai").strip().lower()


def _codex_timeout():
    try:
        return max(30, int(os.environ.get("RUNNINGMATE_CODEX_TIMEOUT", DEFAULT_CODEX_TIMEOUT)))
    except Exception:
        return DEFAULT_CODEX_TIMEOUT


def _error_payload(message, code=None):
    payload = {"message": message}
    if code:
        payload["error_code"] = code
    return payload


def _error_http_status(error):
    if not isinstance(error, dict):
        return 200

    code = error.get("error_code")
    if code in {
        "missing_api_key",
        "invalid_api_key",
        "insufficient_quota",
        "model_not_found",
        "api_forbidden",
        "openai_error",
    }:
        return 503
    if code in {"rate_limited", "usage_limited"}:
        return 429
    return 200


def _openai_error_fields(exc):
    status_code = getattr(exc, "status_code", None)
    code = getattr(exc, "code", None)
    message = ""
    body = getattr(exc, "body", None)

    if isinstance(body, dict):
        error = body.get("error") if isinstance(body.get("error"), dict) else body
        code = code or error.get("code") or error.get("type")
        message = str(error.get("message") or "")

    return status_code, code, message, f"{message} {exc}"


def _openai_is_quota_error(exc):
    _status_code, code, _message, error_text = _openai_error_fields(exc)
    return code == "insufficient_quota" or "insufficient_quota" in error_text or "exceeded your current quota" in error_text


def _openai_error_payload(exc):
    status_code, code, message, error_text = _openai_error_fields(exc)

    error_text = f"{message} {exc}"
    if code == "insufficient_quota" or "insufficient_quota" in error_text or "exceeded your current quota" in error_text:
        return _error_payload(
            "OpenAI API 모드에서 크레딧 또는 월 사용 한도가 부족해 이미지 파싱을 실행하지 못했습니다. Billing에서 크레딧을 충전하거나 RUNNINGMATE_AI_PROVIDER=codex로 Codex CLI 모드를 사용해주세요.",
            "insufficient_quota",
        )

    if status_code == 429:
        return _error_payload(
            "OpenAI API 요청 한도에 잠시 걸렸습니다. 자동 재시도 후에도 처리하지 못했으니 잠시 후 다시 시도해주세요.",
            "rate_limited",
        )

    if status_code == 401:
        return _error_payload(
            "OpenAI API 키가 올바르지 않거나 사용할 수 없습니다. 새 API 키로 교체해주세요.",
            "invalid_api_key",
        )

    if code == "model_not_found" or "does not have access to model" in error_text:
        return _error_payload(
            "OpenAI 이미지 파싱 모델에 접근할 수 없습니다. RUNNINGMATE_VISION_MODEL을 현재 프로젝트에서 사용 가능한 모델로 설정해주세요.",
            "model_not_found",
        )

    if status_code == 403:
        return _error_payload(
            "OpenAI API 접근 권한이 없습니다. 프로젝트/조직 권한과 지역 또는 IP 제한 설정을 확인해주세요.",
            "api_forbidden",
        )

    if status_code in (500, 502, 503, 504):
        return _error_payload(
            "OpenAI 서버가 일시적으로 응답하지 않습니다. 자동 재시도 후에도 실패했습니다. 잠시 후 다시 시도해주세요.",
            "openai_unavailable",
        )

    return _error_payload(
        "이미지 파싱 중 OpenAI API 오류가 발생했습니다. API 키, 결제 상태, 모델 설정을 확인해주세요.",
        code or "openai_error",
    )


def _openai_retry_after_seconds(exc):
    headers = getattr(getattr(exc, "response", None), "headers", None) or getattr(exc, "headers", None)
    if not headers:
        return None

    for key in ("retry-after", "Retry-After"):
        try:
            value = headers.get(key)
        except Exception:
            value = None
        if value is None:
            continue
        try:
            return max(0.0, float(value))
        except Exception:
            return None
    return None


def _openai_retry_max():
    return _env_int("RUNNINGMATE_OPENAI_RETRY_MAX", DEFAULT_OPENAI_RETRY_MAX)


def _openai_backoff_delay(attempt, exc):
    max_delay = _env_float("RUNNINGMATE_OPENAI_BACKOFF_MAX_SECONDS", DEFAULT_OPENAI_BACKOFF_MAX_SECONDS)
    retry_after = _openai_retry_after_seconds(exc)
    if retry_after is not None:
        return min(max_delay, retry_after)

    base = _env_float("RUNNINGMATE_OPENAI_BACKOFF_BASE_SECONDS", DEFAULT_OPENAI_BACKOFF_BASE_SECONDS)
    return min(max_delay, (base * (2 ** max(0, attempt))) + random.uniform(0, base))


def _openai_should_retry(exc):
    if _openai_is_quota_error(exc):
        return False
    return getattr(exc, "status_code", None) in (429, 500, 502, 503, 504)


def _openai_call_with_retries(call):
    attempt = 0
    retry_max = _openai_retry_max()
    while True:
        try:
            return call()
        except Exception as exc:
            if attempt >= retry_max or not _openai_should_retry(exc):
                raise
            time.sleep(_openai_backoff_delay(attempt, exc))
            attempt += 1


def _run_codex(prompt, image_path=None):
    codex = shutil.which("codex")
    if not codex:
        return None, _error_payload("서버에 Codex CLI가 설치되어 있지 않습니다.", "codex_unavailable")

    output = tempfile.NamedTemporaryFile(delete=False)
    output.close()
    command = [
        codex,
        "exec",
        "--cd",
        "/tmp",
        "--skip-git-repo-check",
        "--ephemeral",
        "--color",
        "never",
        "-o",
        output.name,
    ]
    if image_path:
        command.extend(["--image", image_path])
    command.extend(["--", prompt])

    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            input="",
            timeout=_codex_timeout(),
        )
        if result.returncode != 0:
            return None, _error_payload("Codex 실행에 실패했습니다. 서버의 Codex 로그인 상태를 확인해주세요.", "codex_error")
        with open(output.name, "r", encoding="utf-8") as fp:
            text = fp.read().strip()
        if not text and result.stdout:
            text = result.stdout.strip()
        if not text:
            return None, _error_payload("Codex 응답이 비어 있습니다.", "codex_empty")
        return text, None
    except subprocess.TimeoutExpired:
        return None, _error_payload("Codex 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.", "codex_timeout")
    except Exception:
        return None, _error_payload("Codex 실행 중 오류가 발생했습니다.", "codex_error")
    finally:
        try:
            os.unlink(output.name)
        except Exception:
            pass


def _parse_with_codex(image_path):
    text, error = _run_codex(CODEX_PROMPT, image_path)
    if error:
        return None, error

    parsed = _extract_json(text)
    if not parsed:
        return None, _error_payload("Codex가 이미지에서 러닝 JSON을 만들지 못했습니다.", "codex_parse_empty")
    return parsed, None


def _parse_with_openai(image_path, content_type):
    _load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, _error_payload(
            "OpenAI API 키가 설정되어 있지 않습니다. 개인 Codex 계정 직접 연결이 아니라 OPENAI_API_KEY 환경 변수로 연결해주세요.",
            "missing_api_key",
        )

    try:
        from openai import OpenAI

        with open(image_path, "rb") as fp:
            encoded = base64.b64encode(fp.read()).decode("ascii")
        image_url = f"data:{content_type};base64,{encoded}"
        client_kwargs = {"api_key": api_key}
        if os.environ.get("OPENAI_BASE_URL"):
            client_kwargs["base_url"] = os.environ.get("OPENAI_BASE_URL")

        client = OpenAI(**client_kwargs)
        response = _openai_call_with_retries(
            lambda: client.responses.create(
                model=os.environ.get("RUNNINGMATE_VISION_MODEL", DEFAULT_VISION_MODEL),
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": PROMPT},
                            {
                                "type": "input_image",
                                "image_url": image_url,
                                "detail": os.environ.get("RUNNINGMATE_IMAGE_DETAIL", DEFAULT_IMAGE_DETAIL),
                            },
                        ],
                    }
                ],
            )
        )
        parsed = _extract_json(getattr(response, "output_text", ""))
        if not parsed:
            return None, _error_payload("이미지에서 러닝 데이터를 읽지 못했습니다.", "parse_empty")
        return parsed, None
    except Exception as exc:
        return None, _openai_error_payload(exc)


def _audit_image_parse(success, metadata=None):
    _load_env_file()
    payload = dict(metadata or {})
    payload["provider"] = _ai_provider()
    payload["model"] = os.environ.get("RUNNINGMATE_VISION_MODEL", DEFAULT_VISION_MODEL)
    security.audit(
        "image_parse",
        actor_id=_current_user_id(),
        actor_role=session.get("role") or "",
        success=success,
        metadata=payload,
    )


file_storage = _uploaded_file()
target_date = _target_date()
if file_storage:
    stored_path, image_url, store_error = _persist_uploaded_image(file_storage)
    if store_error:
        security.audit("image_upload", actor_id=_current_user_id(), actor_role=session.get("role") or "", success=False, metadata=store_error)
        store_error["success"] = False
        wiz.response.json(store_error)
    else:
        security.audit("image_upload", actor_id=_current_user_id(), actor_role=session.get("role") or "", target=image_url, success=True, metadata={"target_date": target_date})
        rate_limit = _reserve_image_parse_rate_limit()
        if not rate_limit.get("allowed"):
            _delete_file(stored_path)
            wiz.response.status(
                429,
                success=False,
                message=rate_limit.get("message") or "AI 이미지 파싱 요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
                error_code="rate_limited",
                rate_limit=rate_limit,
            )
        else:
            usage = _reserve_image_parse_usage()
            if not usage.get("allowed"):
                _delete_file(stored_path)
                wiz.response.status(
                    429,
                    success=False,
                    message=_image_parse_usage_message(usage),
                    error_code=usage.get("reason") or "usage_limited",
                    usage=usage,
                )
            else:
                if _ai_provider() == "codex":
                    parsed, error = _parse_with_codex(stored_path)
                else:
                    parsed, error = _parse_with_openai(stored_path, file_storage.mimetype or "image/png")
                if error:
                    if isinstance(error, dict):
                        _audit_image_parse(False, {"error_code": error.get("error_code"), "message": error.get("message")})
                    else:
                        _audit_image_parse(False, {"message": str(error)})
                    _delete_file(stored_path)
                    if isinstance(error, dict):
                        error["success"] = False
                        error["usage"] = usage
                        status_code = _error_http_status(error)
                        if status_code >= 400:
                            wiz.response.status(status_code, **error)
                        else:
                            wiz.response.json(error)
                    else:
                        wiz.response.json({"success": False, "message": error, "usage": usage})
                else:
                    data = running.normalize_run(parsed)
                    if target_date:
                        data["date"] = target_date
                    if not data.get("date") or data.get("distance_km") is None:
                        _delete_file(stored_path)
                        wiz.response.json({
                            "success": False,
                            "message": "날짜와 거리 값을 확인하지 못했습니다.",
                            "usage": usage,
                        })
                    else:
                        data["raw_parsed_json"] = parsed
                        data["image_url"] = image_url
                        _audit_image_parse(True, {"target_date": data.get("date")})
                        wiz.response.json({"success": True, "data": data, "usage": usage})
else:
    data = running.normalize_run(_json_payload())
    if data.get("date") or data.get("distance_km") is not None:
        wiz.response.json({"success": True, "data": data})
    else:
        wiz.response.json({
            "success": False,
            "message": "파싱할 이미지 또는 러닝 JSON 데이터가 필요합니다.",
        })
