import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request


class OAuth:
    STATE_KEY = "runningmate.oauth"
    ENV_FILES = (
        os.environ.get("RUNNINGMATE_OAUTH_ENV_FILE", "/opt/app/config/oauth.env"),
    )

    PROVIDERS = {
        "naver": {
            "client_id": "NAVER_CLIENT_ID",
            "client_secret": "NAVER_CLIENT_SECRET",
            "authorize_url": "https://nid.naver.com/oauth2.0/authorize",
            "token_url": "https://nid.naver.com/oauth2.0/token",
            "profile_url": "https://openapi.naver.com/v1/nid/me",
            "scope": "",
        },
        "google": {
            "client_id": "GOOGLE_CLIENT_ID",
            "client_secret": "GOOGLE_CLIENT_SECRET",
            "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "profile_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "scope": "openid email profile",
        },
    }

    def __init__(self):
        self._load_env_files()

    def _load_env_files(self):
        for env_file in self.ENV_FILES:
            if not env_file or not os.path.exists(env_file):
                continue
            try:
                with open(env_file, "r", encoding="utf-8") as fp:
                    for line in fp:
                        key, _, value = line.strip().partition("=")
                        if key and value and key not in os.environ:
                            os.environ[key] = value.strip().strip('"').strip("'")
            except Exception:
                continue

    def _flask(self):
        return wiz.server.package.flask

    def _request(self):
        return self._flask().request

    def _session(self):
        return self._flask().session

    def _base_url(self):
        configured = os.environ.get("RUNNINGMATE_PUBLIC_BASE_URL")
        if configured:
            return configured.rstrip("/")

        try:
            security = wiz.model("security")
            if security.oauth_require_public_base_url():
                return ""
        except Exception:
            pass

        request = self._request()
        scheme = str(request.headers.get("X-Forwarded-Proto") or request.scheme or "https").split(",")[0].strip()
        host = str(request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
        return f"{scheme}://{host}".rstrip("/")

    def _redirect_uri(self, provider):
        provider = str(provider or "").strip().upper()
        configured = (
            os.environ.get(f"{provider}_REDIRECT_URI")
            or os.environ.get("RUNNINGMATE_OAUTH_REDIRECT_URI")
            or os.environ.get("OAUTH_REDIRECT_URI")
        )
        if configured:
            redirect_uri = configured.rstrip("/")
        else:
            base_url = self._base_url()
            redirect_uri = f"{base_url}/access" if base_url else ""

        if not redirect_uri:
            return ""
        try:
            security = wiz.model("security")
            if not security.url_host_allowed(redirect_uri):
                return ""
        except Exception:
            pass
        return redirect_uri

    def _provider(self, provider):
        provider = str(provider or "").strip().lower()
        if provider not in self.PROVIDERS:
            return None
        config = dict(self.PROVIDERS[provider])
        config["provider"] = provider
        config["client_id_value"] = os.environ.get(config["client_id"], "").strip()
        config["client_secret_value"] = os.environ.get(config["client_secret"], "").strip()
        return config

    def _log(self, provider, message, detail=""):
        try:
            wiz.model("security").safe_log(f"OAuth:{provider}", message, detail)
        except Exception:
            pass

    def _error_redirect(self, message="social_login_failed"):
        message = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(message or "social_login_failed"))[:80]
        query = urllib.parse.urlencode({"social_error": message})
        wiz.response.redirect(f"/access?{query}")

    def _json_request(self, url, data=None, headers=None, method=None):
        encoded = None
        request_headers = dict(headers or {})
        if data is not None:
            encoded = urllib.parse.urlencode(data).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
            method = method or "POST"

        req = urllib.request.Request(url, data=encoded, headers=request_headers, method=method or "GET")
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"http_{error.code}:{body[:300]}")
        return json.loads(body)

    def start(self, provider):
        try:
            wiz.model("security").auth_headers()
        except Exception:
            pass
        config = self._provider(provider)
        if not config or not config["client_id_value"] or not config["client_secret_value"]:
            self._error_redirect("social_config_missing")
            return

        redirect_uri = self._redirect_uri(config["provider"])
        if not redirect_uri:
            self._error_redirect("social_redirect_invalid")
            return

        state = secrets.token_urlsafe(24)
        self._session()[self.STATE_KEY] = {
            "provider": config["provider"],
            "state": state,
            "created_at": int(time.time()),
        }

        params = {
            "response_type": "code",
            "client_id": config["client_id_value"],
            "redirect_uri": redirect_uri,
            "state": state,
        }
        if config["scope"]:
            params["scope"] = config["scope"]

        wiz.response.redirect(f"{config['authorize_url']}?{urllib.parse.urlencode(params)}")

    def _verify_state(self, provider, state):
        saved = self._session().get(self.STATE_KEY) or {}
        created_at = int(saved.get("created_at") or 0)
        expected_state = str(saved.get("state") or "")
        actual_state = str(state or "")
        if saved.get("provider") != provider or not expected_state or not secrets.compare_digest(expected_state, actual_state):
            return False
        try:
            ttl = wiz.model("security").oauth_state_ttl_seconds()
        except Exception:
            ttl = 600
        if created_at and int(time.time()) - created_at > ttl:
            return False
        return True

    def _saved_provider(self):
        saved = self._session().get(self.STATE_KEY) or {}
        return str(saved.get("provider") or "").strip().lower()

    def _token(self, config, code, state):
        data = {
            "grant_type": "authorization_code",
            "client_id": config["client_id_value"],
            "client_secret": config["client_secret_value"],
            "code": code,
        }
        if config["provider"] == "naver":
            data["state"] = state
        else:
            data["redirect_uri"] = self._redirect_uri(config["provider"])
        return self._json_request(config["token_url"], data=data)

    def _profile(self, config, access_token):
        payload = self._json_request(
            config["profile_url"],
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if config["provider"] == "naver":
            source = payload.get("response") or {}
            return {
                "provider": "naver",
                "provider_user_id": str(source.get("id") or ""),
                "email": source.get("email") or "",
                "name": source.get("name") or source.get("nickname") or "",
                "profile_image": source.get("profile_image") or "",
                "email_verified": bool(source.get("email")),
            }

        return {
            "provider": "google",
            "provider_user_id": str(payload.get("sub") or ""),
            "email": payload.get("email") or "",
            "name": payload.get("name") or "",
            "profile_image": payload.get("picture") or "",
            "email_verified": bool(payload.get("email_verified")),
        }

    def callback(self, provider=None):
        try:
            wiz.model("security").auth_headers()
        except Exception:
            pass
        request = self._request()
        provider = str(provider or self._saved_provider() or "").strip().lower()
        config = self._provider(provider)
        if not config:
            self._error_redirect("social_provider_invalid")
            return

        if request.args.get("error"):
            error = str(request.args.get("error") or "social_denied")
            description = str(request.args.get("error_description") or "")
            self._log(config["provider"], "provider_denied", f"{error} {description}".strip())
            self._error_redirect(error)
            return

        code = str(request.args.get("code") or "").strip()
        state = str(request.args.get("state") or "").strip()
        if not code or not self._verify_state(config["provider"], state):
            self._session().pop(self.STATE_KEY, None)
            self._log(config["provider"], "state_invalid", f"code={bool(code)} state={bool(state)}")
            self._error_redirect("social_state_invalid")
            return

        try:
            try:
                token = self._token(config, code, state)
            except Exception as error:
                self._log(config["provider"], "token_failed", error)
                self._error_redirect("social_token_failed")
                return

            access_token = token.get("access_token")
            if not access_token:
                raise RuntimeError("missing_access_token")

            try:
                profile = self._profile(config, access_token)
            except Exception as error:
                self._log(config["provider"], "profile_failed", error)
                self._error_redirect("social_profile_failed")
                return

            if not profile.get("provider_user_id"):
                self._log(config["provider"], "profile_missing_id")
                self._error_redirect("social_profile_missing")
                return
            if config["provider"] == "google" and profile.get("email") and not profile.get("email_verified"):
                self._log(config["provider"], "email_not_verified")
                self._error_redirect("google_email_not_verified")
                return

            struct = wiz.model("struct")
            auth = wiz.model("auth")
            session = wiz.model("portal/season/session").use()
            user = struct.user.find_or_create_social_user(profile)
            session.set(**auth.session_payload(user))
            self._session().pop(self.STATE_KEY, None)
            wiz.response.redirect("/dashboard")
        except Exception as error:
            if error.__class__.__name__ == "ResponseException":
                raise
            self._log(config["provider"], "callback_failed", error)
            self._error_redirect("social_login_failed")


Model = OAuth()
