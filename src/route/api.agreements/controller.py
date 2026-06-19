import json


session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
request = wiz.server.package.flask.request


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


def _response(status_code, payload):
    if status_code >= 400:
        wiz.response.status(status_code, **payload)
    wiz.response.json(payload)


def _current_user_id():
    return session.get("id")


def _status():
    user_id = _current_user_id()
    return {
        "success": True,
        "data": struct.agreement.status(user_id),
    }


if request.method == "GET":
    wiz.response.json(_status())
elif not _current_user_id():
    _response(401, {"success": False, "message": "로그인이 필요합니다."})
else:
    user_id = _current_user_id()
    payload = _payload()

    if request.method == "POST":
        terms_agreed = _bool_value(payload.get("terms_agreed") or payload.get("termsAgreed"))
        privacy_agreed = _bool_value(payload.get("privacy_agreed") or payload.get("privacyAgreed"))
        age_confirmed = _bool_value(payload.get("age_confirmed") or payload.get("ageConfirmed"))
        marketing_optin = _bool_value(payload.get("marketing_optin") or payload.get("marketingOptin"))
        location_info_agreed = _bool_value(payload.get("location_info_agreed") or payload.get("locationInfoAgreed"))
        photo_access_agreed = _bool_value(payload.get("photo_access_agreed") or payload.get("photoAccessAgreed"))

        if not terms_agreed or not privacy_agreed or not age_confirmed:
            _response(400, {"success": False, "message": "필수 동의 항목을 모두 체크해주세요."})
        else:
            struct.agreement.record(
                user_id,
                marketing_optin=marketing_optin,
                location_info_agreed=location_info_agreed,
                photo_access_agreed=photo_access_agreed,
                agreed_at=payload.get("agreed_at") or payload.get("agreedAt"),
                terms_version=payload.get("terms_version") or payload.get("termsVersion"),
                privacy_version=payload.get("privacy_version") or payload.get("privacyVersion"),
            )
            wiz.response.json(_status())

    elif request.method == "PATCH":
        latest = struct.agreement.latest(user_id)
        current = struct.agreement.current()
        marketing_optin = _bool_value(payload.get("marketing_optin") or payload.get("marketingOptin"))
        location_info_agreed = (latest or {}).get("location_info_agreed", False)
        photo_access_agreed = (latest or {}).get("photo_access_agreed", False)

        struct.agreement.record(
            user_id,
            marketing_optin=marketing_optin,
            location_info_agreed=location_info_agreed,
            photo_access_agreed=photo_access_agreed,
            terms_version=(latest or {}).get("terms_version") or current["terms"]["version"],
            privacy_version=(latest or {}).get("privacy_version") or current["privacy"]["version"],
        )
        wiz.response.json(_status())

    else:
        _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})
