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


def _goal_type_from_request(payload):
    if isinstance(payload, dict):
        value = payload.get("goal_type") or payload.get("goalType") or payload.get("type")
        if value:
            return value
    return wiz.request.query("goal_type", "") or wiz.request.query("goalType", "") or wiz.request.query("type", "")


def _response(year_month, user_id):
    return {
        "success": True,
        "data": running.goals_for_month(year_month, user_id=user_id),
        "progress": running.goal_progress(year_month, user_id=user_id),
        "history": running.goal_history(user_id=user_id),
    }


segment = wiz.request.match("/api/goals/<year_month>")
year_month = getattr(segment, "year_month", "") if segment is not None else ""
request = wiz.server.package.flask.request
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    wiz.response.json(_response(year_month, user_id))
elif request.method == "PUT":
    payload = _request_payload()
    if isinstance(payload, dict) and isinstance(payload.get("goals"), list):
        _, message = running.replace_goals(year_month, payload.get("goals"), user_id)
        if message:
            wiz.response.json({"success": False, "message": message})
        else:
            wiz.response.json(_response(year_month, user_id))
    else:
        if isinstance(payload, dict) and not payload.get("user_id") and not payload.get("userId"):
            payload["user_id"] = user_id
        goal, message = running.save_goal(year_month, payload, user_id)
        if not goal:
            wiz.response.json({"success": False, "message": message or "목표를 저장하지 못했습니다."})
        else:
            wiz.response.json(_response(year_month, user_id))
elif request.method == "DELETE":
    payload = _request_payload()
    goal_type = _goal_type_from_request(payload)
    if running.delete_goal(year_month, goal_type, user_id):
        wiz.response.json(_response(year_month, user_id))
    else:
        body = _response(year_month, user_id)
        body["success"] = False
        body["message"] = "삭제할 목표를 찾지 못했습니다."
        wiz.response.json(body)
else:
    wiz.response.json({"success": False, "message": "지원하지 않는 요청입니다."})
