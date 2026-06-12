import os
import re


UPLOAD_DIR = os.environ.get("RUNNINGMATE_MEDIA_UPLOAD_DIR", "/opt/app/data/run_media")
FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.(?:jpg|jpeg|png|webp|gif|heic|heif|mp4|mov|webm|m4v)$")
running = wiz.model("runningmate")
security = wiz.model("security")
session = wiz.model("portal/season/session").use()


segment = wiz.request.match("/api/run-media/<path:filename>")
filename = getattr(segment, "filename", "") if segment is not None else ""
filename = os.path.basename(str(filename or ""))

if not FILENAME_RE.match(filename):
    wiz.response.abort(404)

root = os.path.realpath(UPLOAD_DIR)
filepath = os.path.realpath(os.path.join(root, filename))

if not filepath.startswith(root + os.sep) or not os.path.isfile(filepath):
    wiz.response.abort(404)

request = wiz.server.package.flask.request
upload_path = f"/api/run-media/{filename}"
signature_ok = security.verify_upload_url_signature(
    upload_path,
    request.args.get("exp"),
    request.args.get("sig"),
)
if not signature_ok and not running.can_access_upload_file("run-media", filename, session.get("id")):
    context = security.session_context(session)
    security.audit("file_access.denied", actor_id=context.get("id"), actor_role=context.get("role"), target=upload_path, success=False)
    wiz.response.abort(404)

wiz.response.headers.set(**{
    "Cache-Control": "private, max-age=300",
    "X-Content-Type-Options": "nosniff",
})
wiz.response.download(filepath, as_attachment=False)
