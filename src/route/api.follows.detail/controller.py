struct = wiz.model("struct")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request


def _current_user_id():
    return session.get("id") or ""


def _target_user_id():
    segment = wiz.request.match("/api/follows/<user_id>")
    return getattr(segment, "user_id", "") if segment is not None else ""


def _profile_content_visible(profile):
    return bool(profile.get("is_public") or profile.get("is_me") or profile.get("is_mutual"))


def _profile_payload(user_id, viewer_id):
    user = struct.user.get(id=user_id)
    profile = struct.user.public_profile(user, viewer_id)
    if not profile:
        return None

    stats_visible = _profile_content_visible(profile)
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


def _profiles_for_ids(user_ids, viewer_id):
    users = struct.user.list_by_ids(user_ids)
    profiles = []
    for user in users:
        profile = _profile_payload((user or {}).get("id"), viewer_id)
        if profile:
            profiles.append(profile)
    return profiles


def _profile_media(user_id, visible):
    if not visible:
        return []

    items = []
    for run in running.load_runs(include_media=True, user_id=user_id):
        if run.get("is_public") is False:
            continue
        for media in run.get("media") or []:
            if media.get("media_url"):
                items.append({
                    "media": media,
                    "run": run,
                })
    return items[:30]


def _actor_name(user_id):
    user = struct.user.get(id=user_id)
    profile = struct.user.public_profile(user, user_id)
    return (profile or {}).get("name") or (profile or {}).get("display_id") or "러너"


viewer_id = _current_user_id()
target_id = _target_user_id()

if not viewer_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif not target_id:
    wiz.response.status(400, success=False, message="사용자 ID가 필요합니다.")
else:
    if request.method == "GET":
        profile = _profile_payload(target_id, viewer_id)
        if not profile:
            wiz.response.status(404, success=False, message="사용자를 찾지 못했습니다.")
        else:
            lists_visible = _profile_content_visible(profile)
            wiz.response.json({
                "success": True,
                "data": running.signed_upload_payload({
                    "profile": profile,
                    "lists_public": lists_visible,
                    "following": _profiles_for_ids(struct.follow.following_ids(target_id), viewer_id) if lists_visible else [],
                    "followers": _profiles_for_ids(struct.follow.follower_ids(target_id), viewer_id) if lists_visible else [],
                    "media": _profile_media(target_id, lists_visible),
                }),
            })
    elif request.method == "POST":
        was_following = struct.follow.is_following(viewer_id, target_id)
        _, message = struct.follow.follow(viewer_id, target_id)
        if message:
            wiz.response.status(400, success=False, message=message)
        else:
            if not was_following:
                running.create_follow_notification(target_id, viewer_id, _actor_name(viewer_id))
            wiz.response.json({
                "success": True,
                "message": "팔로우했습니다.",
                "data": _profile_payload(target_id, viewer_id),
            })
    elif request.method == "DELETE":
        _, message = struct.follow.unfollow(viewer_id, target_id)
        if message:
            wiz.response.status(400, success=False, message=message)
        else:
            wiz.response.json({
                "success": True,
                "message": "언팔로우했습니다.",
                "data": _profile_payload(target_id, viewer_id),
            })
    else:
        wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
