struct = wiz.model("struct")
session = wiz.model("portal/season/session").use()

def get():
    user_id = session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    user = struct.user.get(id=user_id)
    if user is None:
        wiz.response.status(404, message="사용자를 찾을 수 없습니다.")

    wiz.response.status(200, user)

def update_profile():
    user_id = session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    name = wiz.request.query("name", "")
    mobile = wiz.request.query("mobile", "")
    is_public = wiz.request.query("is_public", None)

    if not name:
        wiz.response.status(400, message="이름을 입력해주세요.")

    fields = dict(name=name, mobile=mobile)
    if is_public is not None:
        fields["is_public"] = str(is_public).strip().lower() in ("1", "true", "yes", "y", "on")

    struct.user.update_profile(user_id, **fields)

    # 세션도 갱신
    session.set(name=name)

    wiz.response.status(200)

def change_password():
    user_id = session.get("id")
    if not user_id:
        wiz.response.status(401, message="로그인이 필요합니다.")

    current_password = wiz.request.query("current_password", "")
    new_password = wiz.request.query("new_password", "")

    if not current_password:
        wiz.response.status(400, message="현재 비밀번호를 입력해주세요.")
    if not new_password:
        wiz.response.status(400, message="새 비밀번호를 입력해주세요.")

    ok, message, _meta = struct.user.change_password_with_policy(user_id, current_password, new_password)
    if not ok:
        wiz.response.status(400, message=message or "비밀번호 변경에 실패했습니다.")

    session.set(password_changed_at=struct.user.password_session_version(user_id))

    wiz.response.status(200)
