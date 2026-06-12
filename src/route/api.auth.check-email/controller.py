struct = wiz.model("struct")
request = wiz.server.package.flask.request


if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
else:
    user = struct.user
    valid, email, message = user.validate_email(wiz.request.query("email", ""))
    available = False

    if valid:
        available = not user.email_exists(email)
        if not available:
            message = "이미 사용 중인 이메일이야"
        else:
            message = "사용 가능한 이메일이야"

    wiz.response.json({
        "available": bool(available),
        "email": email,
        "message": message,
    })
