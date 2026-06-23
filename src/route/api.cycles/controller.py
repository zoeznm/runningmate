import json


auth = wiz.model("auth")
running = wiz.model("runningmate")
try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None
request = wiz.server.package.flask.request


def _request_payload():
    raw = request.get_data(as_text=True)
    if not raw:
        return wiz.request.query()

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}

    return {}


def _current_user_id():
    try:
        session_user_id = session.get("id") if session is not None else ""
    except Exception:
        session_user_id = ""
    if session_user_id:
        return session_user_id

    try:
        header = str(request.headers.get("Authorization") or "")
    except Exception:
        header = ""

    if not header.lower().startswith("bearer "):
        return ""

    token = header.split(" ", 1)[1].strip()
    try:
        verified, error = auth.verify_token(token, token_type="access")
    except Exception:
        verified, error = None, "invalid_token"
    if error or not verified:
        return ""

    user = verified.get("user") or {}
    try:
        if session is not None:
            session.set(**auth.session_payload(user))
    except Exception:
        pass

    return user.get("id") or verified.get("claims", {}).get("sub") or ""


def _has_cycle_consent(payload=None):
    payload = payload if isinstance(payload, dict) else {}
    header = str(request.headers.get("X-Cycle-Consent", "")).strip().lower()
    query = str(wiz.request.query("enabled", "") or "").strip().lower()
    body = str(payload.get("consent", "")).strip().lower()
    return header in ("1", "true", "yes", "y") or query in ("1", "true", "yes", "y") or body in ("1", "true", "yes", "y")


def _privacy_headers():
    try:
        wiz.response.headers["Cache-Control"] = "no-store"
    except Exception:
        pass


payload = _request_payload()
_privacy_headers()
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif not _has_cycle_consent(payload):
    if request.method == "GET":
        wiz.response.json({
            "success": True,
            "enabled": False,
            "data": [],
            "summary": {
                "average_cycle_days": 28,
                "average_period_days": 7,
                "next_start_date": None,
                "current_phase": None,
                "current_phase_label": None,
                "log_count": 0,
                "menstrual_log_count": 0,
            },
        })
    else:
        wiz.response.json({
            "success": False,
            "message": "주기 데이터 접근은 명시적 설정 동의가 필요합니다.",
        })
elif request.method == "GET":
    wiz.response.json({
        "success": True,
        "enabled": True,
        "data": running.load_cycles(user_id=user_id),
        "summary": running.cycle_summary(user_id=user_id),
    })
elif request.method == "DELETE":
    cycle_id = payload.get("id") if isinstance(payload, dict) else None
    delete_all = bool(payload.get("all") or payload.get("delete_all") or not cycle_id)
    if running.delete_cycle(cycle_id, delete_all=delete_all, user_id=user_id):
        wiz.response.json({
            "success": True,
            "data": running.load_cycles(user_id=user_id),
            "summary": running.cycle_summary(user_id=user_id),
        })
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 주기 기록을 찾지 못했습니다.",
            "data": running.load_cycles(user_id=user_id),
            "summary": running.cycle_summary(user_id=user_id),
        })
else:
    if isinstance(payload, dict) and not payload.get("user_id") and not payload.get("userId"):
        payload["user_id"] = user_id
    log, message = running.save_cycle(payload)
    if log:
        wiz.response.json({
            "success": True,
            "data": log,
            "cycles": running.load_cycles(user_id=user_id),
            "summary": running.cycle_summary(user_id=user_id),
        })
    else:
        wiz.response.json({
            "success": False,
            "message": message or "주기 기록을 저장하지 못했습니다.",
            "cycles": running.load_cycles(user_id=user_id),
            "summary": running.cycle_summary(user_id=user_id),
        })
