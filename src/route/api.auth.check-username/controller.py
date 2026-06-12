struct = wiz.model("struct")
request = wiz.server.package.flask.request


if request.method != "GET":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
else:
    user = struct.user
    valid, username, message = user.validate_username(wiz.request.query("username", ""))
    available = False

    if valid:
        available = not user.username_exists(username)
        if not available:
            message = "이미 사용 중인 아이디야"
        else:
            message = "사용 가능한 아이디야"

    wiz.response.json({
        "available": bool(available),
        "username": username,
        "message": message,
    })
