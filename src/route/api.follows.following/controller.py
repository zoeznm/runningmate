struct = wiz.model("struct")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request


def _profile_payload(user, viewer_id):
    profile = struct.user.public_profile(user, viewer_id)
    if not profile:
        return None

    stats_visible = bool(profile.get("is_public") or profile.get("is_me"))
    profile["stats_public"] = stats_visible
    profile["stats"] = running.public_user_stats(
        profile.get("id"),
        include_legacy=bool(profile.get("is_me")),
    ) if stats_visible else None
    profile["badges_public"] = stats_visible
    profile.update(running.public_badges(profile.get("id"), limit=5) if stats_visible else {
        "badges": [],
        "earned_badge_count": 0,
        "total_badge_count": 0,
        "achievement_rate": 0,
    })
    return profile


if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
elif not (session.get("id") or ""):
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
else:
    viewer_id = session.get("id") or ""
    ids = struct.follow.following_ids(viewer_id)
    users = struct.user.list_by_ids(ids)
    profiles = [
        profile for profile in (_profile_payload(user, viewer_id) for user in users)
        if profile
    ]

    wiz.response.json({
        "success": True,
        "data": profiles,
        "counts": struct.follow.counts(viewer_id),
    })
