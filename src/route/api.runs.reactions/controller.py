import json


struct = wiz.model("struct")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request
security = wiz.model("security")
security.bind_bearer_session(session)


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


def _run_id():
    segment = wiz.request.match("/api/runs/<run_id>/reactions")
    return getattr(segment, "run_id", "") if segment is not None else ""


def _actor_profile(viewer_id):
    user = struct.user.get(id=viewer_id)
    return struct.user.public_profile(user, viewer_id) or {"id": viewer_id, "name": "러너", "profile_image": ""}


def _profiles_for_run(run, viewer_id, actor=None):
    ids = {
        run.get("user_id") or run.get("userId"),
        viewer_id,
    }
    for reaction in running.load_run_reactions():
        if reaction.get("run_id") == run.get("id"):
            ids.add(reaction.get("user_id"))
    for comment in running.load_run_comments():
        if comment.get("run_id") == run.get("id"):
            ids.add(comment.get("user_id"))

    profiles = {}
    for user in struct.user.list_by_ids([user_id for user_id in ids if user_id]):
        profile = struct.user.public_profile(user, viewer_id)
        if profile:
            profiles[profile.get("id")] = profile
    if actor:
        profiles[actor.get("id")] = actor
    return profiles


def _can_view_run(run, viewer_id):
    owner_id = run.get("user_id") or run.get("userId")
    if not owner_id:
        return False
    if owner_id == viewer_id:
        return True
    if run.get("is_public") is False:
        return False
    if owner_id not in struct.follow.following_ids(viewer_id):
        return False
    owner = struct.user.get(id=owner_id)
    profile = struct.user.public_profile(owner, viewer_id)
    return bool(not profile or profile.get("is_public", True))


viewer_id = _current_user_id()
run_id = _run_id()
run = running.run_detail(run_id)

if request.method not in ("GET", "POST", "DELETE"):
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
elif not viewer_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif not run:
    wiz.response.status(404, success=False, message="러닝 기록을 찾지 못했습니다.")
elif not _can_view_run(run, viewer_id):
    wiz.response.status(403, success=False, message="공개된 친구 기록만 응원할 수 있습니다.")
else:
    payload = _payload()
    reaction_type = payload.get("type") or wiz.request.query("type", "")
    actor = _actor_profile(viewer_id)

    if request.method == "GET":
        profiles = _profiles_for_run(run, viewer_id, actor)
        social = running.run_social_state(run_id, viewer_id, profiles)
        wiz.response.json({
            "success": True,
            "data": social,
            "social": social,
        })
    elif request.method == "POST":
        item, message = running.save_run_reaction(
            run_id,
            viewer_id,
            reaction_type,
            user_name=actor.get("name"),
            profile_image=actor.get("profile_image"),
        )
        if message:
            wiz.response.status(400, success=False, message=message)
        else:
            profiles = _profiles_for_run(run, viewer_id, actor)
            wiz.response.json({
                "success": True,
                "data": item,
                "social": running.run_social_state(run_id, viewer_id, profiles),
            })
    else:
        deleted = running.delete_run_reaction(run_id, viewer_id, reaction_type)
        profiles = _profiles_for_run(run, viewer_id, actor)
        wiz.response.json({
            "success": True,
            "deleted": deleted,
            "social": running.run_social_state(run_id, viewer_id, profiles),
        })
