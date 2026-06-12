import os
fs = wiz.project.fs(os.path.join("config", "pwa"))
swjs = fs.read("sw.js", "")
flask = wiz.server.package.flask
response = flask.Response(swjs, content_type="text/javascript; charset=utf-8")
response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
wiz.response.response(response)
