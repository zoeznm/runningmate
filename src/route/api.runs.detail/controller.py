import json


running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()
security = wiz.model("security")
security.bind_bearer_session(session)


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


segment = wiz.request.match("/api/runs/<run_id>")
run_id = getattr(segment, "run_id", "") if segment is not None else ""
request = wiz.server.package.flask.request
user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "PATCH":
    payload = _request_payload()
    editable_fields = (
        "date",
        "run_date",
        "runDate",
        "workout_date",
        "workoutDate",
        "distance_km",
        "distanceKm",
        "distance",
        "km",
        "avg_pace",
        "avgPace",
        "pace",
        "average_pace",
        "averagePace",
        "duration",
        "time",
        "elapsed_time",
        "elapsedTime",
        "moving_time",
        "movingTime",
        "run_type",
        "runType",
        "running_type",
        "runningType",
        "start_time",
        "startTime",
        "calories",
        "avg_heart_rate",
        "avgHeartRate",
        "heart_rate",
        "heartRate",
        "cadence",
        "elevation_gain",
        "elevationGain",
        "image_url",
        "imageUrl",
        "raw_parsed_json",
        "rawParsedJson",
        "journal",
        "water_before_ml",
        "waterBeforeMl",
        "water_before",
        "waterBefore",
        "before_water_ml",
        "beforeWaterMl",
        "water_after_ml",
        "waterAfterMl",
        "water_after",
        "waterAfter",
        "after_water_ml",
        "afterWaterMl",
        "is_public",
        "isPublic",
        "public",
        "privacy",
        "playlist_name",
        "playlistName",
        "music_playlist_name",
        "musicPlaylistName",
        "music_url",
        "musicUrl",
        "apple_music_url",
        "appleMusicUrl",
        "top_tracks",
        "topTracks",
        "music_tracks",
        "musicTracks",
    )
    if not isinstance(payload, dict) or not any(field in payload for field in editable_fields):
        wiz.response.json({
            "success": False,
            "message": "수정할 필드가 필요합니다.",
        })
    else:
        run, message = running.update_run(run_id, payload, user_id=user_id)
        if run:
            wiz.response.json({"success": True, "data": running.signed_upload_payload(run)})
        else:
            wiz.response.json({
                "success": False,
                "message": message or "러닝 기록을 수정하지 못했습니다.",
            })
else:
    run = running.run_detail(run_id, user_id=user_id)
    if run:
        wiz.response.json({"success": True, "data": running.signed_upload_payload(run)})
    else:
        wiz.response.json({
            "success": False,
            "message": "러닝 기록을 찾지 못했습니다.",
        })
