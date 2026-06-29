running = wiz.model("runningmate")
security = wiz.model("security")
request = wiz.server.package.flask.request
session = wiz.model("portal/season/session").use()
security.bind_bearer_session(session)


def _uploaded_files():
    files = request.files
    if not files:
        return []

    selected = []
    for key in ("media", "files", "file", "image", "video"):
        selected.extend(files.getlist(key))

    if selected:
        return selected

    return list(files.values())


segment = wiz.request.match("/api/runs/<run_id>/media")
run_id = getattr(segment, "run_id", "") if segment is not None else ""
user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

if request.method == "GET":
    wiz.response.json({"success": True, "data": running.signed_upload_payload(running.media_for_run(run_id, user_id=user_id))})
elif request.method == "POST":
    saved = []
    errors = []
    for file_storage in _uploaded_files():
        item, error = running.save_run_media(run_id, file_storage, user_id=user_id)
        if item:
            saved.append(item)
            security.audit("file_upload", actor_id=user_id, actor_role=session.get("role") or "", target=item.get("media_url"), success=True, metadata={"run_id": run_id, "media_type": item.get("media_type")})
        if error:
            errors.append(error)
            security.audit("file_upload", actor_id=user_id, actor_role=session.get("role") or "", target=run_id, success=False, metadata={"error": error})

    if saved:
        wiz.response.json({
            "success": True,
            "data": running.signed_upload_payload(saved),
            "media": running.signed_upload_payload(running.media_for_run(run_id, user_id=user_id)),
            "errors": errors,
        })
    else:
        wiz.response.json({
            "success": False,
            "message": errors[0] if errors else "업로드할 사진/영상 파일이 필요합니다.",
        })
else:
    wiz.response.json({
        "success": False,
        "message": "지원하지 않는 요청입니다.",
    })
