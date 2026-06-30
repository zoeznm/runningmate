import json
import os
import random
import re
import select
import shutil
import subprocess
import tempfile
import time


running = wiz.model("runningmate")

try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None

try:
    security = wiz.model("security")
except Exception:
    security = None

if session is not None and security is not None:
    try:
        security.bind_bearer_session(session)
    except Exception:
        pass

ENV_FILE = os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", "/opt/app/config/openai.env")
DEFAULT_CODEX_TIMEOUT = 180
DEFAULT_CHAT_MODEL = "gpt-5.4-mini"
DEFAULT_MAX_CHAT_MESSAGE_CHARS = 1200
DEFAULT_AI_CHAT_DAILY_LIMIT = 5
DEFAULT_AI_CHAT_MONTHLY_LIMIT = 120
DEFAULT_AI_CHAT_ADMIN_DAILY_LIMIT = 100
DEFAULT_AI_CHAT_ADMIN_MONTHLY_LIMIT = 2000
DEFAULT_AI_CHAT_COOLDOWN_SECONDS = 10
DEFAULT_AI_CHAT_RATE_WINDOW_SECONDS = 60
DEFAULT_AI_CHAT_RATE_MAX_REQUESTS = 6
DEFAULT_OPENAI_RETRY_MAX = 2
DEFAULT_OPENAI_BACKOFF_BASE_SECONDS = 0.8
DEFAULT_OPENAI_BACKOFF_MAX_SECONDS = 8


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


def _ai_provider():
    _load_env_file()
    return str(os.environ.get("RUNNINGMATE_AI_PROVIDER") or "openai").strip().lower()


def _codex_timeout():
    try:
        return max(30, int(os.environ.get("RUNNINGMATE_CODEX_TIMEOUT", DEFAULT_CODEX_TIMEOUT)))
    except Exception:
        return DEFAULT_CODEX_TIMEOUT


def _chat_model():
    _load_env_file()
    return os.environ.get("RUNNINGMATE_CHAT_MODEL") or os.environ.get("RUNNINGMATE_VISION_MODEL", DEFAULT_CHAT_MODEL)


def _max_chat_message_chars():
    try:
        return max(100, int(os.environ.get("RUNNINGMATE_MAX_CHAT_MESSAGE_CHARS", DEFAULT_MAX_CHAT_MESSAGE_CHARS)))
    except Exception:
        return DEFAULT_MAX_CHAT_MESSAGE_CHARS


def _current_user():
    if session is None:
        return {"id": "", "name": "나", "role": ""}
    return {
        "id": session.get("id") or "",
        "name": session.get("name") or "나",
        "role": session.get("role") or "",
    }


def _current_user_id():
    return _current_user().get("id") or ""


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


def _chat_usage_limits():
    role = str(_current_user().get("role") or "").strip().lower()
    if role == "admin":
        return (
            _env_int("RUNNINGMATE_AI_CHAT_ADMIN_DAILY_LIMIT", DEFAULT_AI_CHAT_ADMIN_DAILY_LIMIT),
            _env_int("RUNNINGMATE_AI_CHAT_ADMIN_MONTHLY_LIMIT", DEFAULT_AI_CHAT_ADMIN_MONTHLY_LIMIT),
        )
    return (
        _env_int("RUNNINGMATE_AI_CHAT_DAILY_LIMIT", DEFAULT_AI_CHAT_DAILY_LIMIT),
        _env_int("RUNNINGMATE_AI_CHAT_MONTHLY_LIMIT", DEFAULT_AI_CHAT_MONTHLY_LIMIT),
    )


def _reserve_chat_usage():
    daily_limit, monthly_limit = _chat_usage_limits()
    return running.reserve_ai_usage(
        _current_user_id(),
        action="chat",
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
    )


def _chat_usage_status():
    daily_limit, monthly_limit = _chat_usage_limits()
    return running.ai_usage_status(
        _current_user_id(),
        action="chat",
        daily_limit=daily_limit,
        monthly_limit=monthly_limit,
    )


def _chat_rate_limits():
    return (
        _env_int("RUNNINGMATE_AI_CHAT_COOLDOWN_SECONDS", DEFAULT_AI_CHAT_COOLDOWN_SECONDS),
        _env_int("RUNNINGMATE_AI_CHAT_RATE_WINDOW_SECONDS", DEFAULT_AI_CHAT_RATE_WINDOW_SECONDS),
        _env_int("RUNNINGMATE_AI_CHAT_RATE_MAX_REQUESTS", DEFAULT_AI_CHAT_RATE_MAX_REQUESTS),
    )


def _reserve_chat_rate_limit():
    cooldown_seconds, window_seconds, max_requests = _chat_rate_limits()
    return running.reserve_ai_rate_limit(
        _current_user_id(),
        action="chat",
        cooldown_seconds=cooldown_seconds,
        window_seconds=window_seconds,
        max_requests=max_requests,
    )


def _message_error(message):
    if not message:
        return "질문을 입력해주세요."
    if len(message) > _max_chat_message_chars():
        return "질문이 너무 깁니다. 핵심 내용만 짧게 입력해주세요."
    return None


def _normalize_pacer_persona(value):
    persona = str(value or "").strip().lower()
    return persona if persona in {"balanced", "coach", "gentle", "strict"} else "balanced"


def _pacer_persona_instruction(persona):
    persona = _normalize_pacer_persona(persona)
    if persona == "coach":
        return "페이서 페르소나는 코치형이야. 목표, 거리, 강도, 다음 액션을 구조적으로 제안하고 말끝은 단정하되 과장하지 마."
    if persona == "gentle":
        return "페이서 페르소나는 다정형이야. 사용자의 부담을 낮추고 회복과 지속성을 우선해서 부드럽게 격려해."
    if persona == "strict":
        return "페이서 페르소나는 엄격형이야. 핑계와 미루기를 줄이도록 단호하게 말하되, 모욕하거나 죄책감을 주지 마."
    return "페이서 페르소나는 밸런스형이야. 기록과 컨디션을 함께 보고 실용적인 선택지를 균형 있게 제안해."


def _request_streaming(payload):
    value = payload.get("stream")
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _ndjson(event, **payload):
    payload["event"] = event
    return json.dumps(payload, ensure_ascii=False, default=str) + "\n"


def _chunk_text(text, size=8):
    buf = ""
    for char in str(text or ""):
        buf += char
        if len(buf) >= size or char in ".!?\n。！？":
            yield buf
            buf = ""
    if buf:
        yield buf


def _stream_text(text):
    for chunk in _chunk_text(text):
        yield _ndjson("delta", text=chunk)
        time.sleep(0.015)


def _run_codex(prompt):
    codex = shutil.which("codex")
    if not codex:
        return None, "서버에 Codex CLI가 설치되어 있지 않습니다."

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
        "--",
        prompt,
    ]

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
            return None, "Codex 실행에 실패했습니다. 서버의 Codex 로그인 상태를 확인해주세요."
        with open(output.name, "r", encoding="utf-8") as fp:
            text = fp.read().strip()
        if not text and result.stdout:
            text = result.stdout.strip()
        if not text:
            return None, "Codex 응답이 비어 있습니다."
        return text, None
    except subprocess.TimeoutExpired:
        return None, "Codex 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    except Exception:
        return None, "Codex 실행 중 오류가 발생했습니다."
    finally:
        try:
            os.unlink(output.name)
        except Exception:
            pass


def _safe_context_value(loader, fallback):
    try:
        return loader()
    except Exception:
        return fallback


def _chat_run_summary(row):
    source = row if isinstance(row, dict) else {}
    return {
        "date": source.get("date"),
        "distance_km": source.get("distance_km"),
        "avg_pace": source.get("avg_pace"),
        "duration": source.get("duration"),
        "run_type": source.get("run_type"),
        "calories": source.get("calories"),
        "avg_heart_rate": source.get("avg_heart_rate"),
        "cadence": source.get("cadence"),
        "elevation_gain": source.get("elevation_gain"),
        "water_before_ml": source.get("water_before_ml"),
        "water_after_ml": source.get("water_after_ml"),
        "journal": source.get("journal"),
    }


def _chat_journal_summary(row):
    source = row if isinstance(row, dict) else {}
    return {
        "date": source.get("date"),
        "distance_km": source.get("distance_km"),
        "avg_pace": source.get("avg_pace"),
        "journal": source.get("journal"),
    }


def _month_context():
    user_id = _current_user_id()
    rows = running.runs_for_month(user_id=user_id)
    if not rows:
        return None

    total = round(sum(row.get("distance_km") or 0 for row in rows), 2)
    pace_rows = [row for row in rows if running.pace_to_seconds(row.get("avg_pace"))]
    avg_pace = "-"
    if pace_rows:
        seconds = sum(running.pace_to_seconds(row.get("avg_pace")) for row in pace_rows) / len(pace_rows)
        avg_pace = running.seconds_to_pace(seconds)

    heart_rates = [row.get("avg_heart_rate") for row in rows if row.get("avg_heart_rate")]
    avg_heart = round(sum(heart_rates) / len(heart_rates)) if heart_rates else None
    latest = _chat_run_summary(rows[0])
    hydration = _safe_context_value(lambda: running.hydration_context(user_id=user_id), {})
    year_month = str(latest.get("date") or "")[:7]

    return {
        "total": total,
        "count": len(rows),
        "avg_pace": avg_pace,
        "avg_heart": avg_heart,
        "latest": latest,
        "hydration": hydration,
        "goals": _safe_context_value(lambda: running.goals_context(year_month, user_id=user_id), {}),
    }


def _codex_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    return _run_codex(_chat_prompt(message, cycle_enabled, pacer_persona))


def _chat_context(cycle_enabled=False):
    user_id = _current_user_id()
    rows = _safe_context_value(lambda: running.runs_for_month(user_id=user_id), [])
    context = {
        "month_summary": _safe_context_value(lambda: _month_context(), None),
        "recent_runs": [_chat_run_summary(row) for row in rows[:8]],
        "recent_journals": [
            _chat_journal_summary(row)
            for row in _safe_context_value(lambda: running.recent_journals(3, user_id=user_id), [])
        ],
        "weight_context": _safe_context_value(lambda: running.running_weight_context(user_id=user_id), {}),
        "hydration_context": _safe_context_value(lambda: running.hydration_context(user_id=user_id), {}),
        "goals_context": _safe_context_value(lambda: running.goals_context(user_id=user_id), {}),
        "ranking_context": _safe_context_value(lambda: running.ranking_context(_current_user()), {}),
        "social_cheer_context": _safe_context_value(lambda: running.social_cheer_context(_current_user().get("id")), {}),
        "training_load": _safe_context_value(
            lambda: running.training_load(rows=running.load_runs(include_media=False, user_id=user_id)),
            {},
        ),
    }
    if cycle_enabled:
        context["cycle_context"] = _safe_context_value(lambda: running.cycle_context(user_id=user_id), {})
    return context


def _chat_prompt(message, cycle_enabled=False, pacer_persona="balanced"):
    cycle_instruction = ""
    if cycle_enabled:
        cycle_instruction = "사용자가 설정에서 생리주기 연동을 켠 경우에만 cycle_context를 참고해. 주기 단계와 운동 강도 조언은 단정하지 말고, 개인차와 컨디션 우선을 짧게 언급해."
    persona_instruction = _pacer_persona_instruction(pacer_persona)
    return f"""
너는 러닝메이트 앱의 한국어 러닝 코치 '페이서'야.
사용자의 러닝 기록 컨텍스트와 질문을 보고 짧고 실용적으로 답해.
{persona_instruction}
모르는 값은 지어내지 말고, 데이터가 없으면 업로드를 안내해.
체중 데이터가 있으면 러닝량과 함께 참고하되, 무리한 감량이나 극단적인 식단을 권하지 말고 건강한 페이스와 회복을 강조해.
최근 수분 데이터가 있으면 러닝 전/후 섭취량을 참고해. 8km 이상 긴 러닝인데 수분 기록이 거리 대비 적거나 없으면 "오늘 8km 뛰었는데 물 조금 부족했던 거 같아"처럼 짧고 자연스럽게 보충 조언을 해.
목표 데이터가 있으면 거리, 횟수, 시간, 평균 페이스 목표별 진행률과 남은 값을 자연스럽게 알려줘. 예: "이번달 횟수 목표까지 3번 남았어."
랭킹 데이터가 있으면 순위, 1위와의 거리 차이, 추격 문구를 자연스럽게 한 문장으로 언급할 수 있어.
social_cheer_context에 친구 반응/댓글이 있으면 "친구들이 응원했어!"처럼 짧게 언급할 수 있어.
훈련 부하 데이터(training_load)에는 연속 러닝 일수, 주간 거리 증가율, 최근 3회 평균 심박, 최근 컨디션 흐름이 들어 있어. 사용자가 "오늘 뛸까?", "쉬어야 할까?", "러닝해도 돼?"처럼 묻거나 training_load.recommend_rest가 true이면 이 값을 먼저 평가해. 휴식을 권할 때는 "이번주 벌써 28km 뛰었고 지난주보다 35% 늘었어. 부상 위험 있으니 하루 쉬자"처럼 수치와 이유를 짧게 설명해.
{cycle_instruction}
최종 답변은 한국어 문장만 출력해. 마크다운 표나 코드블록은 쓰지 마.

러닝 데이터:
{json.dumps(_chat_context(cycle_enabled), ensure_ascii=False, default=str)}

최근 일기 3개는 사용자의 컨디션과 맥락을 이해하는 참고 자료야.
예: "어제 일기에 무릎 아프다고 했는데 오늘은 괜찮아?"처럼 일기 내용과 러닝 기록을 연결해 자연스럽게 대화해.

사용자 질문:
{message}
"""


def _codex_event_delta(event):
    event_type = str(event.get("type") or "")
    if "delta" not in event_type:
        return None

    for key in ("delta", "text"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value

    item = event.get("item")
    if isinstance(item, dict):
        for key in ("delta", "text"):
            value = item.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _codex_completed_text(event):
    if event.get("type") != "item.completed":
        return None

    item = event.get("item")
    if isinstance(item, dict) and item.get("type") == "agent_message":
        text = item.get("text")
        if isinstance(text, str) and text:
            return text
    return None


def _stream_codex_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    codex = shutil.which("codex")
    if not codex:
        yield _ndjson("error", message="서버에 Codex CLI가 설치되어 있지 않습니다.")
        return

    command = [
        codex,
        "exec",
        "--json",
        "--cd",
        "/tmp",
        "--skip-git-repo-check",
        "--ephemeral",
        "--color",
        "never",
        "--",
        _chat_prompt(message, cycle_enabled, pacer_persona),
    ]

    process = None
    emitted_delta = False
    emitted_text = False
    deadline = time.time() + _codex_timeout()

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        while process.stdout:
            if time.time() > deadline:
                process.kill()
                yield _ndjson("error", message="Codex 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.")
                return

            if process.poll() is None:
                ready, _, _ = select.select([process.stdout], [], [], 0.5)
                if not ready:
                    continue
                line = process.stdout.readline()
            else:
                line = process.stdout.readline()
                if not line:
                    break

            if not line:
                continue

            try:
                event = json.loads(line)
            except Exception:
                continue

            delta = _codex_event_delta(event)
            if delta:
                emitted_delta = True
                emitted_text = True
                yield _ndjson("delta", text=delta)
                continue

            completed = _codex_completed_text(event)
            if completed and not emitted_delta:
                emitted_text = True
                for chunk in _stream_text(completed):
                    yield chunk

        returncode = process.wait()
        if returncode != 0 and not emitted_text:
            yield _ndjson("error", message="Codex 실행에 실패했습니다. 서버의 Codex 로그인 상태를 확인해주세요.")
    except Exception:
        if process and process.poll() is None:
            process.kill()
        yield _ndjson("error", message="Codex 실행 중 오류가 발생했습니다.")


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


def _openai_error_message(exc):
    status_code, code, message, error_text = _openai_error_fields(exc)

    error_text = f"{message} {exc}"
    if code == "insufficient_quota" or "insufficient_quota" in error_text or "exceeded your current quota" in error_text:
        return "OpenAI API 크레딧 또는 월 사용 한도가 부족해 AI 채팅을 실행하지 못했습니다."
    if status_code == 429:
        return "OpenAI API 요청 한도에 잠시 걸렸습니다. 자동 재시도 후에도 처리하지 못했으니 잠시 후 다시 시도해주세요."
    if status_code == 401:
        return "OpenAI API 키가 올바르지 않거나 사용할 수 없습니다."
    if code == "model_not_found" or "does not have access to model" in error_text:
        return "OpenAI 채팅 모델에 접근할 수 없습니다. RUNNINGMATE_CHAT_MODEL을 현재 프로젝트에서 사용 가능한 모델로 설정해주세요."
    if status_code == 400:
        if code in {"context_length_exceeded", "string_above_max_length"} or "maximum context length" in error_text:
            return "AI에 보낼 러닝 데이터가 너무 커서 답변을 만들지 못했습니다. 컨텍스트를 줄인 뒤 다시 시도해주세요."
        if message:
            return f"OpenAI 요청을 처리하지 못했습니다: {message}"
    if status_code == 403:
        return "OpenAI API 접근 권한이 없습니다. 프로젝트/조직 권한과 지역 또는 IP 제한 설정을 확인해주세요."
    if status_code in (500, 502, 503, 504):
        return "OpenAI 서버가 일시적으로 응답하지 않습니다. 자동 재시도 후에도 실패했습니다. 잠시 후 다시 시도해주세요."
    return "AI 채팅 중 OpenAI API 오류가 발생했습니다."


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


def _local_fallback_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    try:
        return _shape_local_reply(_reply(message, cycle_enabled), pacer_persona), None
    except Exception:
        return "지금 일부 러닝 데이터를 불러오지 못했어. 질문을 조금 짧게 다시 보내주면 기본 기록 기준으로 답해볼게.", None


def _chat_prompt_or_fallback(message, cycle_enabled=False, pacer_persona="balanced"):
    try:
        return _chat_prompt(message, cycle_enabled, pacer_persona), None
    except Exception:
        fallback, _error = _local_fallback_reply(message, cycle_enabled, pacer_persona)
        return "", fallback


def _stream_openai_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    _load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        yield _ndjson("error", message="OpenAI API 키가 설정되어 있지 않습니다.")
        return

    try:
        from openai import OpenAI

        client_kwargs = {"api_key": api_key}
        if os.environ.get("OPENAI_BASE_URL"):
            client_kwargs["base_url"] = os.environ.get("OPENAI_BASE_URL")

        client = OpenAI(**client_kwargs)
        attempt = 0
        retry_max = _openai_retry_max()
        prompt, fallback_reply = _chat_prompt_or_fallback(message, cycle_enabled, pacer_persona)
        if fallback_reply:
            for chunk in _stream_text(fallback_reply):
                yield chunk
            return

        while True:
            emitted_text = False
            try:
                with client.responses.stream(
                    model=_chat_model(),
                    input=prompt,
                ) as stream:
                    for event in stream:
                        event_type = str(getattr(event, "type", "") or "")
                        if event_type == "response.output_text.delta":
                            delta = getattr(event, "delta", "")
                            if delta:
                                emitted_text = True
                                yield _ndjson("delta", text=delta)
                        elif event_type in {"response.error", "response.failed"}:
                            error = getattr(event, "error", None) or getattr(getattr(event, "response", None), "error", None)
                            if error:
                                yield _ndjson("error", message=str(getattr(error, "message", "") or error))
                                return

                    if not emitted_text:
                        final_response = stream.get_final_response()
                        final_text = str(getattr(final_response, "output_text", "") or "")
                        for chunk in _stream_text(final_text):
                            emitted_text = True
                            yield chunk

                if not emitted_text:
                    yield _ndjson("error", message="답변을 만들지 못했어.")
                return
            except Exception as exc:
                if emitted_text or attempt >= retry_max or not _openai_should_retry(exc):
                    yield _ndjson("error", message=_openai_error_message(exc))
                    return
                time.sleep(_openai_backoff_delay(attempt, exc))
                attempt += 1
    except Exception as exc:
        yield _ndjson("error", message=_openai_error_message(exc))


def _openai_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    _load_env_file()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None, "OpenAI API 키가 설정되어 있지 않습니다."

    try:
        from openai import OpenAI

        client_kwargs = {"api_key": api_key}
        if os.environ.get("OPENAI_BASE_URL"):
            client_kwargs["base_url"] = os.environ.get("OPENAI_BASE_URL")

        client = OpenAI(**client_kwargs)
        prompt, fallback_reply = _chat_prompt_or_fallback(message, cycle_enabled, pacer_persona)
        if fallback_reply:
            return fallback_reply, None
        response = _openai_call_with_retries(
            lambda: client.responses.create(
                model=_chat_model(),
                input=prompt,
            )
        )
        text = str(getattr(response, "output_text", "") or "").strip()
        if not text:
            return None, "답변을 만들지 못했어."
        return text, None
    except Exception as exc:
        return None, _openai_error_message(exc)


def _shape_local_reply(reply, pacer_persona="balanced"):
    persona = _normalize_pacer_persona(pacer_persona)
    text = str(reply or "").strip()
    if not text:
        return text
    if persona == "coach":
        return f"계획은 이렇게 가자. {text}"
    if persona == "gentle":
        return f"괜찮아, 천천히 보자. {text}"
    if persona == "strict":
        return f"미루지 말고 바로 정리하자. {text}"
    return text


def _stream_local_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    for chunk in _stream_text(_shape_local_reply(_reply(message, cycle_enabled), pacer_persona)):
        yield chunk


def _chat_reply(message, cycle_enabled=False, pacer_persona="balanced"):
    provider = _ai_provider()
    if provider == "codex":
        return _codex_reply(message, cycle_enabled, pacer_persona)
    if provider == "openai":
        return _openai_reply(message, cycle_enabled, pacer_persona)
    return _shape_local_reply(_reply(message, cycle_enabled), pacer_persona), None


def _is_rest_question(message):
    normalized = re.sub(r"\s+", "", str(message or ""))
    return any(keyword in normalized for keyword in (
        "오늘뛸까",
        "오늘뛰",
        "뛰어도",
        "러닝해도",
        "달려도",
        "쉬어야",
        "휴식",
        "오버트레이닝",
    ))


def _training_load_reply(training_load):
    reason = training_load.get("reason") or "훈련 부하를 확인했어."
    streak = training_load.get("streak") or 0
    current_week = training_load.get("current_week_distance_km") or 0
    weekly_increase_pct = training_load.get("weekly_increase_pct")
    recent_heart = training_load.get("recent_avg_heart_rate")
    heart_delta = training_load.get("heart_rate_delta_bpm")
    negative_condition_streak = training_load.get("negative_condition_streak") or 0

    details = []
    if weekly_increase_pct is not None and current_week:
        details.append(f"이번주 벌써 {running.km_text(current_week)} 뛰었고 지난주보다 {round(weekly_increase_pct)}% 늘었어")
    if streak >= 5:
        details.append(f"{streak}일 연속 달렸어")
    if recent_heart and heart_delta and heart_delta > 0:
        details.append(f"최근 3회 평균 심박이 {recent_heart}bpm으로 평소보다 {heart_delta}bpm 높아")
    if negative_condition_streak >= 2:
        details.append(f"최근 컨디션이 {negative_condition_streak}회 연속 좋지 않았어")

    detail = details[0] if details else reason
    if training_load.get("recommend_rest"):
        return f"오늘은 쉬는 게 좋아. {detail}. 부상 위험이 올라갈 수 있으니 하루 회복하자."
    if training_load.get("status") == "caution":
        return f"뛰어도 되지만 강도는 낮추자. {reason} 가볍게 시작하고 컨디션이 나쁘면 바로 멈추자."
    return f"오늘은 무리 신호가 크지 않아. {reason} 가볍게 뛰고 몸이 무거우면 회복주로 바꾸자."


def _event_payload(raw):
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _stream_reply(message, session_id=None, cycle_enabled=False, chat_day=None, pacer_persona="balanced"):
    yield _ndjson("start")
    error = _message_error(message)
    if error:
        yield _ndjson("error", message=error)
        yield _ndjson("done")
        return

    usage_status = _chat_usage_status()
    if not usage_status.get("allowed"):
        yield _ndjson("error", message=usage_status.get("message") or "페이서 AI 사용량 제한에 도달했어.", usage=usage_status)
        yield _ndjson("done", usage=usage_status)
        return

    rate_limit = _reserve_chat_rate_limit()
    if not rate_limit.get("allowed"):
        yield _ndjson(
            "error",
            message=rate_limit.get("message") or "AI 요청이 너무 많아 잠시 후 다시 시도해주세요.",
            usage=usage_status,
            rate_limit=rate_limit,
        )
        yield _ndjson("done", usage=usage_status, rate_limit=rate_limit)
        return

    usage = _reserve_chat_usage()
    if not usage.get("allowed"):
        yield _ndjson("error", message=usage.get("message") or "페이서 AI 사용량 제한에 도달했어.", usage=usage)
        yield _ndjson("done", usage=usage)
        return

    reply_parts = []
    error_message = ""
    provider = _ai_provider()
    if provider == "codex":
        events = _stream_codex_reply(message, cycle_enabled, pacer_persona)
    elif provider == "openai":
        events = _stream_openai_reply(message, cycle_enabled, pacer_persona)
    else:
        events = _stream_local_reply(message, cycle_enabled, pacer_persona)

    for event in events:
        payload = _event_payload(event)
        event_type = payload.get("event")
        text = payload.get("text")
        if event_type == "delta" and isinstance(text, str):
            reply_parts.append(text)
        elif event_type == "message" and isinstance(text, str):
            reply_parts = [text]
        elif event_type == "error":
            error_message = str(payload.get("message") or "AI 채팅 중 오류가 발생했어.")
        yield event

    reply = "".join(reply_parts).strip() or error_message
    session = running.save_chat_exchange(session_id, message, reply, _current_user().get("id"), chat_day=chat_day) if reply else None
    yield _ndjson("done", session=session, session_id=(session or {}).get("id"), usage=usage)


def _respond_stream(message, session_id=None, cycle_enabled=False, chat_day=None, pacer_persona="balanced"):
    flask = wiz.server.package.flask
    response = flask.Response(
        flask.stream_with_context(_stream_reply(message, session_id, cycle_enabled, chat_day, pacer_persona)),
        content_type="application/x-ndjson; charset=utf-8",
    )
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return wiz.response.response(response)


def _reply(message, cycle_enabled=False):
    context = _month_context()
    user_id = _current_user_id()
    goals_context = running.goals_context(user_id=user_id)
    ranking_context = running.ranking_context(_current_user())
    social_context = running.social_cheer_context(_current_user().get("id"))
    training_load = running.training_load(rows=running.load_runs(include_media=False, user_id=user_id))
    if context and _is_rest_question(message):
        return _training_load_reply(training_load)

    if "목표" in message:
        if (goals_context.get("goals") or []):
            return goals_context.get("summary") or "이번달 목표 진행 상황을 확인했어."
        return "이번달 목표가 아직 없어. 목표 화면에서 거리, 횟수, 시간, 평균 페이스를 따로 설정할 수 있어."

    if "랭킹" in message or "순위" in message:
        if ranking_context.get("my_rank"):
            return ranking_context.get("motivation_text") or f"현재 내 순위는 {ranking_context.get('my_rank')}위야."
        return "랭킹 참여를 켜고 친구 기록이 쌓이면 이번주 거리 순위를 알려줄게."

    if "응원" in message or "댓글" in message or "좋아요" in message:
        if social_context.get("reaction_count") or social_context.get("comment_count"):
            return social_context.get("summary") or "친구들이 내 기록을 응원했어."
        return "아직 친구 응원 데이터는 없어. 공개 기록이 피드에 보이면 친구들이 반응과 댓글을 남길 수 있어."

    if not context:
        return "아직 기록이 없어서 분석할 데이터가 없어. 캡처를 업로드하면 페이스와 심박 흐름을 같이 봐줄게."

    latest = context["latest"]
    if cycle_enabled and any(keyword in message for keyword in ("주기", "생리", "난포", "배란", "황체")):
        cycle = running.cycle_context(user_id=user_id)
        summary = cycle.get("summary") or {}
        current = summary.get("current_phase_label")
        next_start = summary.get("next_start_date")
        if not cycle.get("enabled"):
            return "주기 연동 기록이 아직 없어. 설정을 켠 뒤 시작일과 종료일을 남기면 러닝 강도 조언에 참고할게."
        if current:
            next_text = f" 다음 예상 시작일은 {next_start}로 보고 있어." if next_start else ""
            return f"입력한 기록 기준 현재는 {current}야.{next_text} 컨디션 개인차가 크니 오늘 강도는 몸 상태를 우선해서 조절하자."
        return "주기 기록은 있지만 오늘 단계는 아직 확인하기 어려워. 최근 컨디션과 수면을 우선해서 강도를 낮춰도 좋아."

    if "심박" in message:
        if context["avg_heart"]:
            return f"이번달 평균 심박은 {context['avg_heart']}bpm이야. 최근 기록과 비교해서 높아지는 날은 페이스를 조금 낮춰보자."
        return "아직 심박 데이터가 있는 기록이 없어. 심박이 보이는 캡처를 추가하면 같이 봐줄게."

    if "이번주" in message:
        weekly = running.weekly_stats(user_id=user_id)
        return weekly.get("distanceFooter") or "이번주 기록을 아직 계산하지 못했어."

    if "체중" in message or "몸무게" in message or "감량" in message:
        weight_context = running.running_weight_context(user_id=user_id)
        summary = weight_context.get("weight_summary") or {}
        latest = summary.get("latest")
        start = summary.get("start")
        month = weight_context.get("this_month") or {}
        if not latest:
            return "아직 체중 기록이 없어. 오늘 체중을 남기면 러닝량과 함께 변화 흐름을 봐줄게."
        if start and latest.get("date") != start.get("date") and summary.get("change_kg") is not None:
            change = summary.get("change_kg")
            direction = "감량" if change < 0 else "증가" if change > 0 else "유지"
            return f"최근 체중은 {latest.get('weight_kg')}kg이고 시작 대비 {change:+.1f}kg {direction} 흐름이야. 이번달 러닝은 {month.get('run_distance_km', 0)}km야. 무리한 감량보다 수면과 회복이 유지되는 페이스로 보자."
        return f"최근 체중은 {latest.get('weight_kg')}kg이야. 기록이 더 쌓이면 러닝량과 변화량을 같이 분석해줄게."

    if "수분" in message or "물" in message:
        hydration = running.hydration_context(user_id=user_id)
        stats = hydration.get("stats") or {}
        latest_low = hydration.get("latest_long_run_low_hydration")
        if not stats.get("loggedRunCount"):
            return "아직 수분 기록이 없어. 업로드할 때 러닝 전후 물 섭취량을 같이 남기면 장거리 때 충분했는지 봐줄게."
        if latest_low:
            return f"최근 {latest_low.get('distance_km')}km 러닝은 수분 기록이 {latest_low.get('water_total_ml')}ml라 조금 부족했던 거 같아. 긴 러닝 전후로 물을 나눠 마시는 패턴을 남겨보자."
        return f"이번달 수분 기록 기준 러닝당 평균 {stats.get('averageMlPerRun', 0)}ml, 거리 대비 {stats.get('mlPerKm', 0)}ml/km 정도야."

    if "이번달" in message or "페이스" in message:
        return f"이번달은 {context['count']}회, 총 {context['total']}km를 달렸고 평균 페이스는 {context['avg_pace']}/km야."

    if "오늘" in message or "최근" in message:
        hydration = (context.get("hydration") or {}).get("latest_long_run_low_hydration")
        if hydration and latest.get("date") == hydration.get("date"):
            return f"최근 기록은 {latest.get('date')} {running.km_text(latest.get('distance_km'))}, 페이스 {latest.get('avg_pace') or '-'}야. 오늘 {latest.get('distance_km')}km 뛰었는데 물이 조금 부족했던 거 같아."
        return f"최근 기록은 {latest.get('date')} {running.km_text(latest.get('distance_km'))}, 페이스 {latest.get('avg_pace') or '-'}야."

    return f"현재 기록 기준으로 이번달 총 {context['total']}km를 달렸어. 최근 5개 기록을 기준으로 페이스와 컨디션 흐름을 같이 볼게."


request = wiz.server.package.flask.request
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    wiz.response.json({
        "success": True,
        "data": running.load_chat_sessions(user_id=user_id),
        "usage": _chat_usage_status(),
    })
elif request.method == "DELETE":
    payload = _payload()
    session_id = str(
        payload.get("id")
        or payload.get("session_id")
        or wiz.request.query("id", "")
        or wiz.request.query("session_id", "")
        or ""
    ).strip()

    if running.delete_chat_session(session_id, user_id=user_id):
        wiz.response.json({
            "success": True,
            "data": running.load_chat_sessions(user_id=user_id),
            "usage": _chat_usage_status(),
        })
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 대화를 찾지 못했습니다.",
            "data": running.load_chat_sessions(user_id=user_id),
            "usage": _chat_usage_status(),
        })
else:
    payload = _payload()
    message = str(payload.get("message") or "").strip()
    session_id = str(payload.get("session_id") or "").strip() or None
    chat_day = running._date(payload.get("client_date"))
    cycle_enabled = str(payload.get("cycle_enabled") or "").strip().lower() in {"1", "true", "yes", "y"}
    pacer_persona = _normalize_pacer_persona(payload.get("pacer_persona"))

    if _request_streaming(payload):
        _respond_stream(message, session_id, cycle_enabled, chat_day, pacer_persona)
    else:
        message_error = _message_error(message)
        if message_error:
            wiz.response.json({"success": False, "message": message_error})
        else:
            usage_status = _chat_usage_status()
            if not usage_status.get("allowed"):
                wiz.response.status(
                    429,
                    success=False,
                    message=usage_status.get("message") or "페이서 AI 사용량 제한에 도달했어.",
                    usage=usage_status,
                )
            else:
                rate_limit = _reserve_chat_rate_limit()
                if not rate_limit.get("allowed"):
                    wiz.response.status(
                        429,
                        success=False,
                        message=rate_limit.get("message") or "AI 요청이 너무 많아 잠시 후 다시 시도해주세요.",
                        usage=usage_status,
                        rate_limit=rate_limit,
                    )
                else:
                    usage = _reserve_chat_usage()
                    if not usage.get("allowed"):
                        wiz.response.status(
                            429,
                            success=False,
                            message=usage.get("message") or "페이서 AI 사용량 제한에 도달했어.",
                            usage=usage,
                        )
                    else:
                        reply, error = _chat_reply(message, cycle_enabled, pacer_persona)
                        if error:
                            session = running.save_chat_exchange(session_id, message, error, user_id, chat_day=chat_day)
                            wiz.response.json({
                                "success": False,
                                "message": error,
                                "session_id": (session or {}).get("id"),
                                "session": session,
                                "usage": usage,
                            })
                        else:
                            session = running.save_chat_exchange(session_id, message, reply, user_id, chat_day=chat_day)
                            wiz.response.json({
                                "success": True,
                                "reply": reply,
                                "session_id": (session or {}).get("id"),
                                "session": session,
                                "usage": usage,
                            })
