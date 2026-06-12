session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request
security = wiz.model("security")
security.auth_headers()

if request.method != "POST":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")

context = security.session_context(session)
security.audit("auth.logout", actor_id=context.get("id"), actor_role=context.get("role"), target=context.get("id"))
session.clear()
wiz.response.json({"success": True})
