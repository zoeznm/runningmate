auth = wiz.model("auth")
running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
request = wiz.server.package.flask.request


INITIAL_RUN_FIELDS = [
    "id",
    "date",
    "distance_km",
    "avg_pace",
    "duration",
    "run_type",
    "calories",
    "avg_heart_rate",
    "cadence",
    "elevation_gain",
    "water_before_ml",
    "water_after_ml",
    "journal",
    "is_public",
    "user_id",
    "created_at",
]


def _limit():
    try:
        value = int(wiz.request.query("limit", 60) or 60)
    except Exception:
        return 60
    return max(1, min(value, 120))


def _filter_fields(row):
    return {field: row.get(field) for field in INITIAL_RUN_FIELDS}


if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")

user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

user = struct.user.get(id=user_id)
if not user:
    session.clear()
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

limit = _limit()
runs = running.load_runs(include_media=False, user_id=user_id)
visible_runs = [_filter_fields(row) for row in runs[:limit]]
has_media_history = any(row.get("image_url") for row in runs)

wiz.response.json({
    "success": True,
    "data": {
        "profile": auth.public_user(user),
        "runs": visible_runs,
        "run_count": len(runs),
        "run_limit": limit,
        "has_more_runs": len(runs) > len(visible_runs),
        "has_media_history": has_media_history,
    },
})
