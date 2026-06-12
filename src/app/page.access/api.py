session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")


def _bool_value(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return False


def login():
    email = wiz.request.query("username", "") or wiz.request.query("identifier", "") or wiz.request.query("email", "")
    password = wiz.request.query("password", "")

    if not email or not password:
        wiz.response.status(400, message="아이디와 비밀번호를 입력해주세요.")

    user = struct.user.authenticate(email, password)
    if user is None:
        wiz.response.status(401, message="이메일 또는 비밀번호가 올바르지 않습니다.")

    session.set(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        role=user['role'],
        onboarded=bool(user.get('onboarded')),
        password_changed_at=struct.user.password_session_version(user['id']),
    )
    wiz.response.status(200)


def signup():
    user_struct = struct.user
    username = wiz.request.query("username", "")
    username_ok, username, username_message = user_struct.validate_username(username)
    email = user_struct.normalize_email(wiz.request.query("email", ""))
    password = wiz.request.query("password", "")
    confirm_password = wiz.request.query("confirm_password", "")
    name = (wiz.request.query("name", "") or "").strip()
    gender = user_struct.normalize_gender(wiz.request.query("gender", "") or wiz.request.query("sex", ""))
    terms_agreed = _bool_value(wiz.request.query("terms_agreed", False))
    privacy_agreed = _bool_value(wiz.request.query("privacy_agreed", False))
    age_confirmed = _bool_value(wiz.request.query("age_confirmed", False))
    marketing_optin = _bool_value(wiz.request.query("marketing_optin", False))
    agreed_at = wiz.request.query("agreed_at", "")
    terms_version = wiz.request.query("terms_version", "")
    privacy_version = wiz.request.query("privacy_version", "")

    if not username_ok:
        return wiz.response.status(400, message=username_message)
    if user_struct.username_exists(username):
        return wiz.response.status(400, message="이미 사용 중인 아이디야")
    email_ok, email, email_message = user_struct.validate_email(email)
    if not email_ok:
        return wiz.response.status(400, message=email_message)
    if not name:
        return wiz.response.status(400, message="이름을 입력해주세요.")
    if not gender:
        return wiz.response.status(400, message="성별을 선택해주세요.")
    if not password:
        return wiz.response.status(400, message="비밀번호를 입력해주세요.")
    if len(password) < 8:
        return wiz.response.status(400, message="비밀번호는 8자 이상이어야 합니다.")
    if password != confirm_password:
        return wiz.response.status(400, message="비밀번호가 일치하지 않습니다.")
    if not terms_agreed or not privacy_agreed or not age_confirmed:
        return wiz.response.status(400, message="필수 동의 항목을 모두 체크해주세요.")

    if user_struct.email_exists(email):
        return wiz.response.status(400, message="이미 사용 중인 이메일이야")

    try:
        database = user_struct.db.orm._meta.database
        database.connect(reuse_if_open=True)
        with database.atomic():
            if user_struct.username_exists(username):
                return wiz.response.status(400, message="이미 사용 중인 아이디야")
            if user_struct.email_exists(email):
                return wiz.response.status(400, message="이미 사용 중인 이메일이야")

            user_id = user_struct.create({
                "username": username,
                "email": email,
                "password": password,
                "name": name[:50],
                "gender": gender,
                "role": "user",
            })
            struct.agreement.record(
                user_id,
                marketing_optin=marketing_optin,
                agreed_at=agreed_at,
                terms_version=terms_version,
                privacy_version=privacy_version,
            )
    except Exception as error:
        text = str(error).lower()
        if "email" in text:
            return wiz.response.status(400, message="이미 사용 중인 이메일이야")
        if "duplicate" in text or "duplicated" in text or "unique" in text:
            return wiz.response.status(400, message="이미 사용 중인 아이디야")
        return wiz.response.status(500, message="회원가입 중 오류가 발생했습니다.")

    user = user_struct.get(id=user_id)

    session.set(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        gender=user.get("gender") or "",
        role=user["role"],
        onboarded=bool(user.get("onboarded")),
        password_changed_at=user_struct.password_session_version(user["id"]),
    )
    wiz.response.status(200)
