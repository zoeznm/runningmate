import os
import re

fs = wiz.project.fs(os.path.join("config", "pwa"))
swjs = fs.read("sw.js", "")
swjs = re.sub(
    r'const CACHE_VERSION = "[^"]+";',
    'const CACHE_VERSION = "runningmate-pwa-v64-access-modal-polish";',
    swjs,
    count=1,
)
flask = wiz.server.package.flask
response = flask.Response(swjs, content_type="text/javascript; charset=utf-8")
response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
wiz.response.response(response)
