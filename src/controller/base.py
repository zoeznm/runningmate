import season
import datetime
import json
import os

request = wiz.server.package.flask.request

class Controller:
    def __init__(self):
        self.apply_cors_headers()
        if request.method == "OPTIONS":
            wiz.response.status(204)

        wiz.session = wiz.model("portal/season/session").use()
        sessiondata = wiz.session.get()
        wiz.response.data.set(session=sessiondata)

        lang = wiz.request.query("lang", None)
        if lang is not None:
            wiz.response.lang(lang)
            wiz.response.redirect(wiz.request.uri())

    def apply_cors_headers(self):
        origin = str(request.headers.get("Origin") or "").strip().rstrip("/")
        if not origin:
            return

        try:
            allowed = wiz.model("security").allowed_origins()
        except Exception:
            allowed = []

        if origin not in allowed:
            return

        try:
            wiz.response.headers.set(**{
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Requested-With",
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            })
        except Exception:
            pass

    def json_default(self, value):
        if isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value).replace('<', '&lt;').replace('>', '&gt;')
