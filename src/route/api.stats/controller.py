running = wiz.model("runningmate")
session = wiz.model("portal/season/session").use()

user_id = session.get("id")
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

wiz.response.json(running.stats(wiz.request.query("year_month", ""), user_id=user_id))
