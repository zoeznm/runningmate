auth = wiz.model("auth")
session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
request = wiz.server.package.flask.request
security = wiz.model("security")
security.auth_headers()
security.bind_bearer_session(session)

if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")

user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

user = struct.user.get(id=user_id)
if not user:
    session.clear()
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

wiz.response.json({
    "success": True,
    "data": auth.public_user(user),
})
