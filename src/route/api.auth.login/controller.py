import json


auth = wiz.model("auth")
session = wiz.model("portal/season/session").use()
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


class ApiResponse(Exception):
    def __init__(self, status_code, payload):
        super().__init__(payload.get("message") or "")
        self.status_code = status_code
        self.payload = payload


def _response(status_code, payload):
    raise ApiResponse(status_code, payload)


def _send_response(status_code, payload):
    flask = wiz.server.package.flask
    response = flask.Response(
        json.dumps(payload, ensure_ascii=False, default=auth._json_default),
        status=status_code,
        content_type="application/json; charset=utf-8",
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    wiz.response.response(response)


try:
    if request.method != "POST":
        _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})

    payload = _payload()
    identifier = payload.get("username") or payload.get("identifier") or payload.get("email") or ""
    password = payload.get("password") or ""

    if not identifier or not password:
        security.audit("auth.login", target=identifier, success=False, metadata={"reason": "missing_credentials"})
        _response(400, {"success": False, "message": "아이디와 비밀번호를 입력해주세요."})

    user, failure_reason = auth.authenticate_with_reason(identifier, password)
    if not user:
        security.audit("auth.login", target=identifier, success=False, metadata={
            "reason": "invalid_credentials",
            "detail": failure_reason or "invalid_credentials",
            "identifier_type": "email" if "@" in str(identifier or "") else "username",
        })
        _response(401, {"success": False, "message": "아이디 또는 비밀번호가 올바르지 않습니다."})

    tokens = auth.issue_tokens(user)
    session.set(**auth.session_payload(user))
    security.audit("auth.login", actor_id=user.get("id"), actor_role=user.get("role"), target=user.get("id"), success=True, metadata={
        "detail": failure_reason,
    } if failure_reason else {})
    _send_response(200, {"success": True, "data": tokens, **tokens})
except ApiResponse as response:
    _send_response(response.status_code, response.payload)
