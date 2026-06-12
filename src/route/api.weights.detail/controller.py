running = wiz.model("runningmate")
try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None
request = wiz.server.package.flask.request


def _current_user_id():
    if session is None:
        return ""
    return session.get("id") or ""

segment = wiz.request.match("/api/weights/<date>")
date = getattr(segment, "date", "") if segment is not None else ""
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "DELETE":
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
            "message": "삭제할 체중 기록을 찾지 못했습니다.",
            "weights": running.load_weights(user_id=user_id),
            "settings": running.load_weight_settings(user_id=user_id),
        })
else:
    log = next((row for row in running.load_weights(user_id=user_id) if row.get("date") == date), None)
    if log:
        wiz.response.json({"success": True, "data": log})
    else:
        wiz.response.json({
            "success": False,
            "message": "체중 기록을 찾지 못했습니다.",
        })
