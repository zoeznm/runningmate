import secrets


struct = wiz.model("struct")
security = wiz.model("security")


def _require_admin(action):
    security.require_admin(action)

def list():
    _require_admin("members.list")
    text = wiz.request.query("text", "")
    role = wiz.request.query("role", "")

    members = struct.user.list(text=text, role=role)

    # 아바타 컬러 추가
    colors = [
        "bg-indigo-100 text-indigo-700",
        "bg-pink-100 text-pink-700",
        "bg-green-100 text-green-700",
        "bg-amber-100 text-amber-700",
        "bg-cyan-100 text-cyan-700",
        "bg-violet-100 text-violet-700",
    ]
    for i, m in enumerate(members):
        m["avatarColor"] = colors[i % len(colors)]
        m["joined"] = str(m.get("created", ""))[:10]

    wiz.response.status(200, members)

def invite():
    _require_admin("members.invite")
    email = wiz.request.query("email", "")
    role = wiz.request.query("role", "viewer")

    if not email:
        wiz.response.status(400, message="이메일을 입력해주세요.")

    # 이미 존재하는지 확인
    existing = struct.user.db.get(email=email)
    if existing:
        wiz.response.status(400, message="이미 등록된 사용자입니다.")

    temporary_password = secrets.token_urlsafe(32)
    struct.user.create(dict(
        email=email,
        password=temporary_password,
        name=email.split("@")[0],
        role=role
    ))

    context = security.session_context()
    security.audit("members.invite", actor_id=context.get("id"), actor_role=context.get("role"), target=email, metadata={"role": role})
    wiz.response.status(200, message="초대 사용자를 생성했습니다. 비밀번호 재설정으로 초기 비밀번호를 설정해주세요.")

def remove():
    _require_admin("members.remove")
    id = wiz.request.query("id", "")
    if not id:
        wiz.response.status(400, message="ID가 필요합니다.")

    struct.user.db.delete(id=id)
    context = security.session_context()
    security.audit("members.remove", actor_id=context.get("id"), actor_role=context.get("role"), target=id)
    wiz.response.status(200)
