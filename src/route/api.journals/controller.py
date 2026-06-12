running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()


page = wiz.request.query("page", "1")
limit = wiz.request.query("limit", "20")
user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

journals = running.journal_runs(page=page, limit=limit, user_id=user_id)

wiz.response.json({
    "success": True,
    "data": journals.get("items", []),
    "pagination": {
        "page": journals.get("page"),
        "limit": journals.get("limit"),
        "total": journals.get("total"),
        "has_more": journals.get("has_more"),
    },
})
