import json


running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request


def _payload():
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
    return session.get("id") or ""


viewer_id = _current_user_id()

if request.method not in ("GET", "PATCH"):
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
elif not viewer_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif request.method == "GET":
    wiz.response.json({
        "success": True,
        "data": running.load_notifications(viewer_id, limit=wiz.request.query("limit", 50)),
    })
else:
    payload = _payload()
    wiz.response.json({
        "success": True,
        "data": running.mark_notifications_read(viewer_id, payload.get("id") or payload.get("notification_id")),
    })
