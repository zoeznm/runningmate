oauth = wiz.model("oauth")
request = wiz.server.package.flask.request
wiz.model("security").auth_headers()

if request.method not in ("GET", "POST"):
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")

oauth.callback("apple")
