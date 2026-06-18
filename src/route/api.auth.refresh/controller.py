import json


auth = wiz.model("auth")
session = wiz.model("portal/season/session").use()
request = wiz.server.package.flask.request
wiz.model("security").auth_headers()


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
    if status_code >= 400:
        wiz.response.status(status_code, **payload)
    else:
        wiz.response.json(payload)


try:
    if request.method != "POST":
        _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})

    payload = _payload()
    refresh_token = payload.get("refresh_token") or payload.get("refreshToken") or ""
    tokens, error = auth.refresh(refresh_token)
    if error:
        session.clear()
        _response(401, {"success": False, "message": "다시 로그인해주세요.", "code": error})

    session.set(**auth.session_payload(tokens.get("user")))
    wiz.response.json({"success": True, "data": tokens, **tokens})
except ApiResponse as response:
    _send_response(response.status_code, response.payload)
