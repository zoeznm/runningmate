import json


session = wiz.model("portal/season/session").use()
struct = wiz.model("struct")
running = wiz.model("runningmate")
request = wiz.server.package.flask.request
security = wiz.model("security")
security.auth_headers()


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


def _response(status_code, payload):
    if status_code >= 400:
        wiz.response.status(status_code, **payload)
    wiz.response.json(payload)


if request.method != "DELETE":
    _response(405, {"success": False, "message": "지원하지 않는 요청입니다."})

user_id = session.get("id")
if not user_id:
    _response(401, {"success": False, "message": "로그인이 필요합니다."})

user = struct.user.get(id=user_id)
if not user:
    session.clear()
    _response(401, {"success": False, "message": "사용자를 찾을 수 없습니다."})

payload = _payload()
confirm_text = str(payload.get("confirm_text") or payload.get("confirmText") or "").strip()
password = str(payload.get("password") or "")

if confirm_text and confirm_text != "삭제":
    _response(400, {"success": False, "message": "'삭제'를 정확히 입력해주세요."})
if not password and confirm_text != "삭제":
    _response(400, {"success": False, "message": "계정 삭제 확인이 필요합니다."})
if password and not struct.user.verify_password(user_id, password):
    security.audit("auth.account_delete", actor_id=user_id, actor_role=session.get("role") or "", target=user_id, success=False, metadata={"reason": "invalid_password"})
    _response(400, {"success": False, "message": "비밀번호가 올바르지 않습니다."})

snapshot = running.snapshot_account_data()
try:
    result = running.delete_account_data(user_id, include_legacy=True, delete_files=False)
    if not result.get("success"):
        raise RuntimeError(result.get("message") or "계정 데이터를 삭제하지 못했습니다.")

    summary = result.get("data") or {}
    file_cleanup = running.delete_account_files(summary.get("files") or [])
    if file_cleanup.get("failed"):
        raise RuntimeError("업로드 파일 삭제에 실패했습니다. 계정 삭제가 취소되었습니다.")

    summary["file_cleanup"] = file_cleanup
    if not struct.user.delete_account(user_id):
        raise RuntimeError("사용자를 찾을 수 없습니다.")

    security.audit("auth.account_delete", actor_id=user_id, actor_role=session.get("role") or "", target=user_id, success=True, metadata=summary)
    session.clear()
    wiz.response.json({
        "success": True,
        "message": "계정 삭제가 완료되었습니다.",
        "data": summary,
    })
except Exception as error:
    running.restore_account_data(snapshot)
    security.audit("auth.account_delete", actor_id=user_id, actor_role=session.get("role") or "", target=user_id, success=False, metadata={"error": str(error)})
    _response(500, {
        "success": False,
        "message": str(error) or "계정 삭제 중 오류가 발생해 변경 사항을 되돌렸습니다.",
    })
