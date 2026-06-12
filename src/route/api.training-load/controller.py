try:
    running = wiz.model("runningmate")
except Exception:
    running = None

try:
    auth = wiz.model("auth")
except Exception:
    auth = None

try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None


def _current_user_id():
    try:
        session_user_id = session.get("id") if session is not None else ""
    except Exception:
        session_user_id = ""
    if session_user_id:
        return session_user_id

    if auth is None:
        return ""

    try:
        request = wiz.server.package.flask.request
        header = str(request.headers.get("Authorization") or "")
    except Exception:
        header = ""

    if not header.lower().startswith("bearer "):
        return ""

    token = header.split(" ", 1)[1].strip()
    verified, error = auth.verify_token(token, token_type="access")
    if error or not verified:
        return ""

    user = verified.get("user") or {}
    try:
        if session is not None:
            session.set(**auth.session_payload(user))
    except Exception:
        pass

    return user.get("id") or verified.get("claims", {}).get("sub") or ""


def _empty_training_load(message="회복 지표는 안전 구간이야."):
    return {
        "streak": 0,
        "weekly_increase_pct": None,
        "recommend_rest": False,
        "reason": message,
        "reasons": [],
        "current_week_distance_km": 0,
        "previous_week_distance_km": 0,
        "recent_avg_heart_rate": None,
        "baseline_avg_heart_rate": None,
        "heart_rate_delta_bpm": None,
        "negative_condition_streak": 0,
        "status": "safe",
        "status_label": "안전",
    }


def _response_payload(data, message="", success=True):
    if not isinstance(data, dict):
        data = _empty_training_load()

    payload = {
        "success": success,
        "data": data,
    }
    payload.update(data)
    if message:
        payload["message"] = message
    return payload


user_id = _current_user_id()
if not user_id:
    wiz.response.status(
        401,
        **_response_payload(
            _empty_training_load("로그인 후 훈련 부하를 계산할게."),
            "로그인이 필요합니다.",
            success=False,
        ),
    )
else:
    message = ""
    try:
        anchor_date = wiz.request.query("date", "")
    except Exception:
        anchor_date = ""

    try:
        if running is None:
            raise RuntimeError("runningmate model is unavailable")
        rows = running.load_runs(include_media=False, user_id=user_id)
        data = running.training_load(anchor_date, rows=rows)
    except Exception:
        message = "훈련 부하를 계산하지 못했습니다."
        data = _empty_training_load("러닝 기록이 쌓이면 훈련 부하를 계산할게.")

    wiz.response.json(_response_payload(data, message))
