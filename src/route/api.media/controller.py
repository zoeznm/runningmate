running = wiz.model("runningmate")
request = wiz.server.package.flask.request
session = wiz.model("portal/season/session").use()


segment = wiz.request.match("/api/media/<media_id>")
media_id = getattr(segment, "media_id", "") if segment is not None else ""
user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "DELETE":
    if running.delete_run_media(media_id, user_id=user_id):
        wiz.response.json({"success": True})
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 첨부 미디어를 찾지 못했습니다.",
        })
else:
    wiz.response.json({
        "success": False,
        "message": "지원하지 않는 요청입니다.",
    })
