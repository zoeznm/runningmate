running = wiz.model("runningmate")
try:
    session = wiz.model("portal/season/session").use()
except Exception:
    session = None

user_id = session.get("id") if session is not None else ""
if not user_id:
    wiz.response.status(401, success=False, message="로그인이 필요합니다.")

summary = running.badges_summary(user_id)
wiz.response.json({
    "success": True,
    "data": summary.get("data", []),
    "earned_count": summary.get("earned_count", 0),
    "total_count": summary.get("total_count", 0),
    "achievement_rate": summary.get("achievement_rate", 0),
    "user_badges": summary.get("user_badges", []),
})
