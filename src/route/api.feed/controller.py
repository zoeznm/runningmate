struct = wiz.model("struct")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request


def _current_user_id():
    return session.get("id") or ""


def _profiles_by_id(user_ids, viewer_id):
    users = struct.user.list_by_ids(user_ids)
    profiles = {}
    for user in users:
        profile = struct.user.public_profile(user, viewer_id)
        if profile:
            profiles[profile.get("id")] = profile
    return profiles


if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
elif not _current_user_id():
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
else:
    viewer_id = _current_user_id()
    following_ids = struct.follow.following_ids(viewer_id)
    profiles = _profiles_by_id(following_ids, viewer_id)
    limit = wiz.request.query("limit", 30)
    wiz.response.json({
        "success": True,
        "data": running.signed_upload_payload(running.feed(viewer_id, following_ids, profiles, limit=limit)),
        "following_count": len(following_ids),
    })
