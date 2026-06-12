import json


auth = wiz.model("auth")
running = wiz.model("runningmate")
try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None


def _request_payload():
    raw = wiz.server.package.flask.request.get_data(as_text=True)
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


def _save_weight_settings_payload(payload, user_id):
    try:
        settings, message = running.save_weight_settings(payload, user_id=user_id)
    except Exception:
        settings = None
        message = "목표 체중을 저장하지 못했습니다."

    if settings:
        return {
            "success": True,
            "data": settings,
            "settings": settings,
        }

    try:
        current_settings = running.load_weight_settings(user_id=user_id)
    except Exception:
        current_settings = {
            "target_weight_kg": None,
            "updated_at": "",
            "user_id": user_id,
        }

    return {
        "success": False,
        "message": message or "목표 체중을 저장하지 못했습니다.",
        "settings": current_settings,
    }


request = wiz.server.package.flask.request
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    period = wiz.request.query("period", "3m")
    wiz.response.json({
        "success": True,
        "data": running.load_weights(period, user_id=user_id),
        "summary": running.weight_summary(period, user_id=user_id),
        "settings": running.load_weight_settings(user_id=user_id),
    })
elif request.method == "PATCH":
    payload = _request_payload()
    wiz.response.json(_save_weight_settings_payload(payload, user_id))
elif request.method == "DELETE":
    payload = _request_payload()
    date = payload.get("date") if isinstance(payload, dict) else None
    if running.delete_weight(date, user_id):
        wiz.response.json({
            "success": True,
            "data": None,
            "weights": running.load_weights(user_id=user_id),
            "summary": running.weight_summary("3m", user_id=user_id),
            "settings": running.load_weight_settings(user_id=user_id),
        })
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 체중 기록 날짜가 올바르지 않습니다.",
            "weights": running.load_weights(user_id=user_id),
            "settings": running.load_weight_settings(user_id=user_id),
        })
else:
    payload = _request_payload()
    if isinstance(payload, dict) and (
        payload.get("mode") in ("target_weight", "weight_settings")
        or "target_weight_kg" in payload
        or "targetWeightKg" in payload
        or "target_weight" in payload
    ):
        wiz.response.json(_save_weight_settings_payload(payload, user_id))
    else:
        if isinstance(payload, dict) and not payload.get("user_id") and not payload.get("userId"):
            payload["user_id"] = user_id
        log, message = running.save_weight(payload)
        if log:
            wiz.response.json({
                "success": True,
                "data": log,
                "weights": running.load_weights(user_id=user_id),
                "summary": running.weight_summary("3m", user_id=user_id),
                "settings": running.load_weight_settings(user_id=user_id),
            })
        else:
            wiz.response.json({
                "success": False,
                "message": message or "체중 기록을 저장하지 못했습니다.",
                "weights": running.load_weights(user_id=user_id),
                "settings": running.load_weight_settings(user_id=user_id),
            })
