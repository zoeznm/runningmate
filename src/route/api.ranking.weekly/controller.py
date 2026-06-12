import json


running = wiz.model("runningmate")

try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None

try:
    struct = wiz.model("struct")
except Exception:
    struct = None


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


def _bool_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return False


def _current_user():
    user = {
        "id": "",
        "name": "나",
        "profile_image": "",
    }
    if session is not None:
        user["id"] = session.get("id") or ""
        user["name"] = session.get("name") or user["name"]

    if struct is not None and user.get("id"):
        try:
            row = struct.user.get(id=user.get("id"))
            if row:
                user["name"] = row.get("name") or user.get("name")
                user["profile_image"] = row.get("profile_image") or ""
        except Exception:
            pass

    return user


def _users():
    if struct is None:
        return []
    try:
        return struct.user.list()
    except Exception:
        return []


def _ranking_scope():
    scope = wiz.request.query("scope", "global")
    return "following" if scope == "following" else "global"


def _user_ids(users):
    ids = []
    for row in users or []:
        if not isinstance(row, dict):
            continue
        user_id = row.get("id") or row.get("user_id") or row.get("userId")
        if user_id:
            ids.append(str(user_id))
    return ids


def _following_ids(user_id):
    if struct is None or not user_id:
        return []
    try:
        return struct.follow.following_ids(user_id)
    except Exception:
        return []


def _follower_ids(user_id):
    if struct is None or not user_id:
        return []
    try:
        return struct.follow.follower_ids(user_id)
    except Exception:
        return []


def _ranking_target_user_ids(scope, viewer_id, users):
    if scope == "following":
        return _following_ids(viewer_id)

    ids = _user_ids(users)
    return ids if ids else None


def _ranking_for_request(user):
    users = _users()
    scope = _ranking_scope()
    user["following_ids"] = _following_ids(user.get("id"))
    user["follower_ids"] = _follower_ids(user.get("id"))
    return running.weekly_ranking(
        year_week=wiz.request.query("year_week", ""),
        period=wiz.request.query("period", "this_week"),
        viewer=user,
        users=users,
        target_user_ids=_ranking_target_user_ids(scope, user.get("id"), users),
        scope=scope,
    )


request = wiz.server.package.flask.request
user = _current_user()
if not user.get("id"):
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    wiz.response.json(_ranking_for_request(user))
elif request.method == "PATCH":
    payload = _request_payload()
    enabled = _bool_value(payload.get("ranking_enabled") if isinstance(payload, dict) else False)
    profile = running.set_ranking_participation(user.get("id"), enabled, user)
    wiz.response.json({
        "success": True,
        "data": profile,
        "ranking": _ranking_for_request(user).get("data"),
    })
else:
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
