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
    date = wiz.request.query("date", "")
    if date:
        wiz.response.json({"data": running.day_note(date, user_id)})
    else:
        wiz.response.json({"data": running.load_day_notes(user_id)})
elif request.method == "DELETE":
    payload = _request_payload()
    date = payload.get("date") if isinstance(payload, dict) else None
    if running.delete_day_note(date, user_id):
        wiz.response.json({"success": True, "data": None, "notes": running.load_day_notes(user_id)})
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 메모 날짜가 올바르지 않습니다.",
            "notes": running.load_day_notes(user_id),
        })
else:
    payload = _request_payload()
    date = payload.get("date") if isinstance(payload, dict) else None
    memo = payload.get("memo") if isinstance(payload, dict) else None
    success, message, note, rows = running.save_day_note(date, memo, user_id)
    wiz.response.json({
        "success": success,
        "message": message,
        "data": note,
        "notes": rows,
    })
