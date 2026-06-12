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


def _current_user():
    if session is None:
        return None

    user_id = session.get("id") or ""
    if not user_id:
        return None
    return {
        "id": user_id,
        "username": session.get("username") or "",
        "email": session.get("email") or "",
        "name": session.get("name") or "나",
        "display_name": session.get("display_name") or session.get("name") or "나",
    }


def _filtered_challenges(rows):
    status = str(wiz.request.query("status", "") or "").strip()
    if not status:
        return rows

    if status == "joined":
        return [row for row in rows if row.get("viewer_joined") and row.get("status") != "ended"]
    if status == "recruiting":
        return [row for row in rows if row.get("status") != "ended"]
    if status == "owned":
        return [row for row in rows if row.get("viewer_owned")]
    if status == "ended":
        return [row for row in rows if row.get("status") == "ended"]
    return rows


def _summary(rows):
    return {
        "joined": len([row for row in rows if row.get("viewer_joined") and row.get("status") != "ended"]),
        "recruiting": len([row for row in rows if row.get("status") != "ended"]),
        "owned": len([row for row in rows if row.get("viewer_owned")]),
        "ended": len([row for row in rows if row.get("status") == "ended"]),
    }


request = wiz.server.package.flask.request
user = _current_user()
if user is None:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    rows = running.load_challenges(user)
    wiz.response.json({
        "success": True,
        "data": _filtered_challenges(rows),
        "summary": _summary(rows),
    })
elif request.method == "POST":
    challenge, message = running.create_challenge(_request_payload(), user)
    if challenge:
        rows = running.load_challenges(user)
        wiz.response.json({
            "success": True,
            "data": challenge,
            "challenges": rows,
            "summary": _summary(rows),
        })
    else:
        wiz.response.json({
            "success": False,
            "message": message or "챌린지를 만들지 못했습니다.",
            "data": None,
        })
else:
    wiz.response.json({"success": False, "message": "지원하지 않는 요청입니다."})
