import json


struct = wiz.model("struct")
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


def _response(status_code, payload):
    if status_code >= 400:
        wiz.response.status(status_code, **payload)
    wiz.response.json(payload)


if request.method != "POST":
    _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})
else:
    payload = _payload()
    token = payload.get("token") or payload.get("reset_token") or payload.get("resetToken")
    new_password = payload.get("newPassword") or payload.get("new_password") or payload.get("password")

    ok, message = struct.user.reset_password_with_token(token, str(new_password or ""))
    if ok:
        _response(200, {"success": True, "message": "비밀번호가 재설정되었습니다. 새 비밀번호로 로그인해주세요."})
    else:
        _response(400, {"success": False, "message": message or "비밀번호 재설정에 실패했습니다."})
