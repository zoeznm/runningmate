running = wiz.model("runningmate")

try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None


def _current_user_id():
    if session is None:
        return ""
    return session.get("id") or ""


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


def _summary(rows):
    return {
        "joined": len([row for row in rows if row.get("viewer_joined") and row.get("status") != "ended"]),
        "recruiting": len([row for row in rows if row.get("status") != "ended"]),
        "owned": len([row for row in rows if row.get("viewer_owned")]),
        "ended": len([row for row in rows if row.get("status") == "ended"]),
    }


request = wiz.server.package.flask.request
segment = wiz.request.match("/api/challenges/<challenge_id>")
challenge_id = getattr(segment, "challenge_id", "") if segment is not None else ""
user_id = _current_user_id()
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    user = _current_user()
    if user is None:
        wiz.response.status(401, success=False, message="로그인이 필요합니다.")
    challenge = running.challenge_detail(challenge_id, user)
    if challenge:
        wiz.response.json({"success": True, "data": challenge})
    else:
        wiz.response.json({
            "success": False,
            "message": "챌린지를 찾지 못했습니다.",
            "data": None,
        })
elif request.method == "DELETE":
    user = _current_user()
    if user is None:
        wiz.response.status(401, success=False, message="로그인이 필요합니다.")
    challenge, message = running.delete_challenge(challenge_id, user)
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
            "message": message or "챌린지를 삭제하지 못했습니다.",
            "data": None,
        })
else:
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
