import json


running = wiz.model("runningmate")

try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None


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


def _fields():
    raw_fields = wiz.request.query("fields", "") or ""
    return [field.strip() for field in raw_fields.split(",") if field.strip()]


def _truthy(value, default=False):
    text = str(value if value is not None else "").strip().lower()
    if not text:
        return default
    return text in ("1", "true", "yes", "y", "on")


def _include_media():
    return _truthy(wiz.request.query("include_media", ""), True)


def _should_sign_payload(fields, include_media):
    if include_media or not fields:
        return True
    return any(field in ("image_url", "media", "media_url") for field in fields)


def _filter_fields(row, fields):
    if not fields:
        return row
    return {field: row.get(field) for field in fields}


def _current_user():
    if session is None or not session.get("id"):
        return None

    return {
        "id": session.get("id"),
        "name": session.get("name") or "나",
    }


def _filtered_runs(user_id):
    rows = running.load_runs(include_media=_include_media(), user_id=user_id)
    year_month = wiz.request.query("year_month", "")
    if year_month:
        rows = [row for row in rows if str(row.get("date") or "").startswith(year_month)]

    limit = wiz.request.query("limit", "")
    if limit:
        try:
            rows = rows[:max(0, int(limit))]
        except Exception:
            pass

    fields = _fields()
    return [_filter_fields(row, fields) for row in rows]


request = wiz.server.package.flask.request
current_user = _current_user()
if current_user is None:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    fields = _fields()
    include_media = _include_media()
    rows = _filtered_runs(current_user.get("id"))
    if _should_sign_payload(fields, include_media):
        rows = running.signed_upload_payload(rows)
    wiz.response.json({"data": rows})
elif request.method == "DELETE":
    payload = _request_payload()
    run_id = payload.get("id") if isinstance(payload, dict) else None
    if running.delete_run(run_id, current_user.get("id")):
        wiz.response.json({"success": True})
    else:
        wiz.response.json({
            "success": False,
            "message": "삭제할 러닝 기록을 찾지 못했습니다.",
        })
else:
    payload = _request_payload()
    if isinstance(payload, dict) and not payload.get("user_id") and not payload.get("userId"):
        payload["user_id"] = current_user.get("id")
    saved, errors = running.save_run(payload)
    if errors:
        wiz.response.json({
            "success": False,
            "message": "필수 러닝 기록 필드가 부족합니다.",
            "fields": errors,
        })
    else:
        wiz.response.json({
            "success": True,
            "data": running.signed_upload_payload(saved),
            "newly_earned_badges": running.award_badges(current_user.get("id")),
        })
