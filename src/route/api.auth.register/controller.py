import json


auth = wiz.model("auth")
session = wiz.model("portal/season/session").use()
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


def _bool_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return False


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
    user_struct = struct.user
    username_ok, username, username_message = user_struct.validate_username(payload.get("username", ""))
    email = user_struct.normalize_email(payload.get("email", ""))
    password = str(payload.get("password") or "")
    confirm_password = str(payload.get("confirm_password") or payload.get("confirmPassword") or "")
    name = str(payload.get("name") or payload.get("display_name") or payload.get("displayName") or "").strip()
    gender = user_struct.normalize_gender(payload.get("gender") or payload.get("sex") or "")

    if not username_ok:
        _response(400, {"success": False, "message": username_message})
    if user_struct.username_exists(username):
        _response(409, {"success": False, "message": "이미 사용 중인 아이디야"})
    if email:
        email_ok, email, email_message = user_struct.validate_email(email)
        if not email_ok:
            _response(400, {"success": False, "message": email_message})
        if user_struct.email_exists(email):
            _response(409, {"success": False, "message": "이미 사용 중인 이메일이야"})
    if not name:
        _response(400, {"success": False, "message": "이름을 입력해주세요."})
    if not gender:
        _response(400, {"success": False, "message": "성별을 선택해주세요."})
    if not password:
        _response(400, {"success": False, "message": "비밀번호를 입력해주세요."})
    if len(password) < 8:
        _response(400, {"success": False, "message": "비밀번호는 8자 이상이어야 합니다."})
    if confirm_password and password != confirm_password:
        _response(400, {"success": False, "message": "비밀번호가 일치하지 않습니다."})

    previous_count = user_struct.count()
    try:
        database = user_struct.db.orm._meta.database
        database.connect(reuse_if_open=True)
        with database.atomic():
            if user_struct.username_exists(username):
                _response(409, {"success": False, "message": "이미 사용 중인 아이디야"})
            if email and user_struct.email_exists(email):
                _response(409, {"success": False, "message": "이미 사용 중인 이메일이야"})

            user_id = user_struct.create({
                "username": username,
                "email": email,
                "password": password,
                "name": name[:50],
                "display_name": name[:50],
                "gender": gender,
                "role": "user",
            })

            if _bool_value(payload.get("terms_agreed")) or _bool_value(payload.get("termsAgreed")):
                struct.agreement.record(
                    user_id,
                    marketing_optin=_bool_value(payload.get("marketing_optin") or payload.get("marketingOptin")),
                    location_info_agreed=_bool_value(payload.get("location_info_agreed") or payload.get("locationInfoAgreed")),
                    photo_access_agreed=_bool_value(payload.get("photo_access_agreed") or payload.get("photoAccessAgreed")),
                    agreed_at=payload.get("agreed_at") or payload.get("agreedAt"),
                    terms_version=payload.get("terms_version") or payload.get("termsVersion"),
                    privacy_version=payload.get("privacy_version") or payload.get("privacyVersion"),
                )
    except ApiResponse:
        raise
    except Exception as error:
        text = str(error).lower()
        if "username" in text or "duplicate" in text or "unique" in text:
            _response(409, {"success": False, "message": "이미 사용 중인 아이디야"})
        _response(500, {"success": False, "message": "회원가입 중 오류가 발생했습니다."})

    user = user_struct.get(id=user_id)
    if previous_count == 0:
        try:
            wiz.model("runningmate").assign_legacy_records(user_id)
        except Exception:
            pass

    tokens = auth.issue_tokens(user)
    session.set(**auth.session_payload(user))
    wiz.response.json({"success": True, "data": tokens, **tokens})
except ApiResponse as response:
    _send_response(response.status_code, response.payload)
