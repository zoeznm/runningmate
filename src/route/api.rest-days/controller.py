import json


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
    if session is None:
        return ""
    return session.get("id") or ""


request = wiz.server.package.flask.request
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    wiz.response.json({"data": running.load_rest_days(user_id)})
elif request.method == "DELETE":
    payload = _request_payload()
    date = payload.get("date") if isinstance(payload, dict) else None
    if running.delete_rest_day(date, user_id):
        wiz.response.json({"success": True, "data": running.load_rest_days(user_id)})
    else:
        wiz.response.json({
            "success": False,
            "message": "해제할 휴식일을 찾지 못했습니다.",
            "data": running.load_rest_days(user_id),
        })
else:
    payload = _request_payload()
    date = payload.get("date") if isinstance(payload, dict) else None
    enabled = payload.get("rest", True) if isinstance(payload, dict) else True
    success, message, rows = running.set_rest_day(date, bool(enabled), user_id)
    wiz.response.json({
        "success": success,
        "message": message,
        "data": rows,
    })
