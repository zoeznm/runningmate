import json


struct = wiz.model("struct")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request


def _current_user_id():
    return session.get("id") or ""


def _request_payload():
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


def _actor_name(user_id):
    profile = struct.user.public_profile(struct.user.get(id=user_id), user_id)
    return (profile or {}).get("name") or (profile or {}).get("display_id") or "러너"


def _find_user_by_code(code):
    return struct.user.get_by_friend_code(code)


viewer_id = _current_user_id()

if not viewer_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif request.method == "GET":
    user = struct.user.get(id=viewer_id)
    code = struct.user.get_friend_code(viewer_id)
    if not code:
        wiz.response.status(500, success=False, message="친구코드를 생성하지 못했어.")
    else:
        wiz.response.json({
            "success": True,
            "data": {
                "code": code,
                "display_name": (user or {}).get("display_name") or (user or {}).get("name") or "러너",
                "share_text": f"러닝메이트 친구코드 {code}",
            },
        })
elif request.method == "POST":
    payload = _request_payload()
    code = payload.get("code") or payload.get("friend_code") or payload.get("friendCode") or ""
    target = _find_user_by_code(code)
    if not target:
        wiz.response.status(404, success=False, message="친구코드를 확인하지 못했어.")
    else:
        target_id = target.get("id") or ""
        if target_id == viewer_id:
            wiz.response.status(400, success=False, message="내 코드는 추가할 수 없어.")
        else:
            was_following = struct.follow.is_following(viewer_id, target_id)
            _, message = struct.follow.follow(viewer_id, target_id)
            if message:
                wiz.response.status(400, success=False, message=message)
            else:
                if not was_following:
                    running.create_follow_notification(target_id, viewer_id, _actor_name(viewer_id))

                wiz.response.json({
                    "success": True,
                    "message": "런메이트를 추가했어.",
                    "data": _profile_payload(target_id, viewer_id),
                })
else:
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
