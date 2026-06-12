import datetime
import json


session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")


def _request_payload():
    raw = wiz.server.package.flask.request.get_data(as_text=True)
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


def _date_value(value):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _profile_response(user):
    if not user:
        return {"success": False, "message": "사용자를 찾을 수 없습니다."}

    return {
        "success": True,
        "data": {
            "id": user.get("id"),
            "username": user.get("username") or "",
            "email": user.get("email"),
            "name": user.get("display_name") or user.get("name") or "",
            "display_name": user.get("display_name") or user.get("name") or "",
            "gender": struct.user.normalize_gender(user.get("gender")),
            "mobile": user.get("mobile") or "",
            "role": user.get("role") or "user",
            "running_start_date": str(user.get("running_start_date") or "")[:10],
            "profile_image": user.get("profile_image") or "",
            "onboarded": bool(user.get("onboarded")),
            "is_public": bool(user.get("is_public", True)),
        },
    }


def _current_user():
    user_id = session.get("id")
    if not user_id:
        return None
    return struct.user.get(id=user_id)


request = wiz.server.package.flask.request
user = _current_user()

if user is None:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")
elif request.method == "GET":
    wiz.response.json(_profile_response(user))
elif request.method == "PATCH":
    payload = _request_payload()
    fields = {}

    if "name" in payload:
        name = str(payload.get("name") or "").strip()
        if not name:
            wiz.response.status(400, success=False, message="이름을 입력해주세요.")
        fields["name"] = name[:50]

    if "mobile" in payload:
        fields["mobile"] = str(payload.get("mobile") or "").strip()[:20]

    if "gender" in payload or "sex" in payload:
        gender = struct.user.normalize_gender(payload.get("gender") or payload.get("sex"))
        if not gender:
            wiz.response.status(400, success=False, message="성별을 확인해주세요.")
        fields["gender"] = gender

    if "running_start_date" in payload or "runningStartDate" in payload:
        running_start_date = _date_value(payload.get("running_start_date") or payload.get("runningStartDate"))
        if running_start_date is None:
            wiz.response.status(400, success=False, message="러닝 시작일을 확인해주세요.")
        fields["running_start_date"] = running_start_date

    if "profile_image" in payload or "profileImage" in payload:
        profile_image = str(payload.get("profile_image") or payload.get("profileImage") or "")
        if len(profile_image) > 2 * 1024 * 1024:
            wiz.response.status(400, success=False, message="프로필 사진 용량이 너무 큽니다.")
        fields["profile_image"] = profile_image

    if "onboarded" in payload:
        fields["onboarded"] = _bool_value(payload.get("onboarded"))

    if "is_public" in payload or "isPublic" in payload:
        fields["is_public"] = _bool_value(payload.get("is_public") if "is_public" in payload else payload.get("isPublic"))

    if not fields:
        wiz.response.json(_profile_response(user))

    struct.user.update_profile(user.get("id"), **fields)
    updated = struct.user.get(id=user.get("id"))
    if updated:
        session.set(
            name=updated.get("name"),
            gender=updated.get("gender") or "",
            onboarded=bool(updated.get("onboarded")),
        )
    wiz.response.json(_profile_response(updated))
else:
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
