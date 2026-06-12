import json


session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
request = wiz.server.package.flask.request
security = wiz.model("security")
security.auth_headers()


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


def _bool_value(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return default


def _response(status_code, payload):
    if status_code >= 400:
        wiz.response.status(status_code, **payload)
    wiz.response.json(payload)


if request.method != "PATCH":
    _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})

user_id = session.get("id")
if not user_id:
    _response(401, {"success": False, "message": "로그인이 필요합니다."})

payload = _payload()
current_password = payload.get("currentPassword") or payload.get("current_password") or ""
new_password = payload.get("newPassword") or payload.get("new_password") or ""
invalidate_sessions = _bool_value(payload.get("invalidateOtherSessions"), True)

ok, message, meta = struct.user.change_password_with_policy(
    user_id,
    str(current_password or ""),
    str(new_password or ""),
    invalidate_sessions=invalidate_sessions,
)

if not ok:
    status_code = 429 if meta.get("locked_until") else 400
    security.audit("auth.password_change", actor_id=user_id, actor_role=session.get("role") or "", target=user_id, success=False, metadata=meta)
    _response(status_code, {"success": False, "message": message or "비밀번호 변경에 실패했습니다.", "data": meta})

if invalidate_sessions:
    session.set(password_changed_at=meta.get("password_changed_at") or struct.user.password_session_version(user_id))

security.audit("auth.password_change", actor_id=user_id, actor_role=session.get("role") or "", target=user_id, success=True, metadata={"invalidate_sessions": invalidate_sessions})
_response(200, {
    "success": True,
    "message": "비밀번호가 변경됐어",
    "data": {
        "other_sessions_invalidated": bool(invalidate_sessions),
    },
})
