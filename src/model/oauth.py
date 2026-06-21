import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
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
        "apple": {
            "client_id": "APPLE_CLIENT_ID",
            "client_secret": "APPLE_CLIENT_SECRET",
            "authorize_url": "https://appleid.apple.com/auth/authorize",
            "token_url": "https://appleid.apple.com/auth/token",
            "profile_url": "",
            "scope": "name email",
            "response_mode": "form_post",
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
        client_secret_key = config.get("client_secret")
        config["client_secret_value"] = os.environ.get(client_secret_key, "").strip() if client_secret_key else ""
        return config

    def _log(self, provider, message, detail=""):
        try:
            wiz.model("security").safe_log(f"OAuth:{provider}", message, detail)
        except Exception:
            pass

    def _native_client_requested(self):
        try:
            request = self._request()
            value = (
                request.values.get("client")
                or request.values.get("native")
                or request.args.get("client")
                or request.args.get("native")
                or ""
            )
        except Exception:
            value = ""
        return str(value or "").strip().lower() in ("native", "ios", "app", "capacitor", "1", "true")

    def _native_redirect_url(self, params):
        return f"runmate://oauth/callback?{urllib.parse.urlencode(params)}"

    def _error_redirect(self, message="social_login_failed", native=None):
        message = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(message or "social_login_failed"))[:80]
        query = urllib.parse.urlencode({"social_error": message})
        if native is None:
            native = self._native_client_requested()
        if native:
            wiz.response.redirect(self._native_redirect_url({"social_error": message}))
            return
        wiz.response.redirect(f"/access?{query}")

    def _state_secret(self):
        try:
            secret = self._flask().current_app.config.get("SECRET_KEY")
            if secret:
                return str(secret)
        except Exception:
            pass
        return (
            os.environ.get("RUNNINGMATE_OAUTH_STATE_SECRET")
            or os.environ.get("WIZ_SECRET_KEY")
            or os.environ.get("FLASK_SECRET_KEY")
            or os.environ.get("SECRET_KEY")
            or "runningmate-oauth-state"
        )

    def _sign_state(self, payload):
        raw = self._jwt_json(payload)
        signature = hmac.new(self._state_secret().encode("utf-8"), raw.encode("ascii"), hashlib.sha256).digest()
        return f"{raw}.{self._b64url(signature)}"

    def _signed_state(self, provider, client="web"):
        return self._sign_state({
            "client": "native" if str(client or "").strip().lower() == "native" else "web",
            "iat": int(time.time()),
            "nonce": secrets.token_urlsafe(18),
            "provider": provider,
        })

    def _signed_state_payload(self, provider, state):
        try:
            raw, signature = str(state or "").rsplit(".", 1)
            expected = hmac.new(self._state_secret().encode("utf-8"), raw.encode("ascii"), hashlib.sha256).digest()
            if not secrets.compare_digest(self._b64url(expected), signature):
                return None
            padding = "=" * ((4 - len(raw) % 4) % 4)
            payload = json.loads(base64.urlsafe_b64decode((raw + padding).encode("ascii")).decode("utf-8"))
            if str(payload.get("provider") or "") != provider:
                return None
            created_at = int(payload.get("iat") or 0)
            try:
                ttl = wiz.model("security").oauth_state_ttl_seconds()
            except Exception:
                ttl = 600
            if not created_at or int(time.time()) - created_at > ttl:
                return None
            return payload
        except Exception:
            return None

    def _verify_signed_state(self, provider, state):
        return bool(self._signed_state_payload(provider, state))

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

    def _b64url(self, value):
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    def _jwt_json(self, value):
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return self._b64url(raw)

    def _decode_jwt_payload(self, token):
        parts = str(token or "").split(".")
        if len(parts) < 2:
            raise RuntimeError("jwt_payload_missing")
        payload = parts[1]
        padding = "=" * ((4 - len(payload) % 4) % 4)
        return json.loads(base64.urlsafe_b64decode((payload + padding).encode("ascii")).decode("utf-8"))

    def _der_length(self, data, offset):
        if offset >= len(data):
            raise RuntimeError("der_length_missing")
        first = data[offset]
        offset += 1
        if first < 0x80:
            return first, offset
        size = first & 0x7F
        if size == 0 or size > 4 or offset + size > len(data):
            raise RuntimeError("der_length_invalid")
        length = int.from_bytes(data[offset:offset + size], "big")
        return length, offset + size

    def _der_integer(self, data, offset):
        if offset >= len(data) or data[offset] != 0x02:
            raise RuntimeError("der_integer_missing")
        length, offset = self._der_length(data, offset + 1)
        value = data[offset:offset + length].lstrip(b"\x00") or b"\x00"
        return value, offset + length

    def _ecdsa_der_to_raw(self, signature):
        if not signature or signature[0] != 0x30:
            raise RuntimeError("ecdsa_signature_invalid")
        length, offset = self._der_length(signature, 1)
        end = offset + length
        if end > len(signature):
            raise RuntimeError("ecdsa_signature_truncated")
        r, offset = self._der_integer(signature, offset)
        s, offset = self._der_integer(signature, offset)
        return r[-32:].rjust(32, b"\x00") + s[-32:].rjust(32, b"\x00")

    def _apple_private_key_path(self):
        return os.environ.get("APPLE_PRIVATE_KEY_PATH", "").strip().strip('"').strip("'")

    def _apple_config_ready(self):
        if os.environ.get("APPLE_CLIENT_SECRET", "").strip():
            return True
        return all([
            os.environ.get("APPLE_TEAM_ID", "").strip(),
            os.environ.get("APPLE_KEY_ID", "").strip(),
            self._apple_private_key_path(),
            os.path.exists(self._apple_private_key_path()),
        ])

    def _apple_client_secret(self, config):
        if config.get("client_secret_value"):
            return config["client_secret_value"]
        team_id = os.environ.get("APPLE_TEAM_ID", "").strip()
        key_id = os.environ.get("APPLE_KEY_ID", "").strip()
        key_path = self._apple_private_key_path()
        client_id = config["client_id_value"]
        if not team_id or not key_id or not key_path or not os.path.exists(key_path):
            raise RuntimeError("apple_config_missing")

        now = int(time.time())
        header = {"alg": "ES256", "kid": key_id, "typ": "JWT"}
        payload = {
            "aud": "https://appleid.apple.com",
            "exp": now + 86400 * 180,
            "iat": now,
            "iss": team_id,
            "sub": client_id,
        }
        signing_input = f"{self._jwt_json(header)}.{self._jwt_json(payload)}"
        try:
            result = subprocess.run(
                ["openssl", "dgst", "-sha256", "-sign", key_path],
                input=signing_input.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=8,
                check=False,
            )
        except Exception as error:
            raise RuntimeError(f"apple_client_secret_sign_error:{error}")
        if result.returncode != 0:
            raise RuntimeError("apple_client_secret_sign_failed")
        signature = self._ecdsa_der_to_raw(result.stdout)
        return f"{signing_input}.{self._b64url(signature)}"

    def start(self, provider):
        try:
            wiz.model("security").auth_headers()
        except Exception:
            pass
        config = self._provider(provider)
        if not config or not config["client_id_value"]:
            self._error_redirect("social_config_missing")
            return
        if config["provider"] == "apple":
            if not self._apple_config_ready():
                self._error_redirect("social_config_missing")
                return
        elif not config["client_secret_value"]:
            self._error_redirect("social_config_missing")
            return

        redirect_uri = self._redirect_uri(config["provider"])
        if not redirect_uri:
            self._error_redirect("social_redirect_invalid")
            return

        client = "native" if self._native_client_requested() else "web"
        state = self._signed_state(config["provider"], client)
        self._session()[self.STATE_KEY] = {
            "client": client,
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
        if config.get("response_mode"):
            params["response_mode"] = config["response_mode"]

        wiz.response.redirect(f"{config['authorize_url']}?{urllib.parse.urlencode(params)}")

    def _verify_state(self, provider, state):
        saved = self._session().get(self.STATE_KEY) or {}
        created_at = int(saved.get("created_at") or 0)
        expected_state = str(saved.get("state") or "")
        actual_state = str(state or "")
        if saved.get("provider") != provider or not expected_state or not secrets.compare_digest(expected_state, actual_state):
            return self._verify_signed_state(provider, actual_state)
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

    def _callback_client(self, provider, state):
        saved = self._session().get(self.STATE_KEY) or {}
        client = str(saved.get("client") or "").strip().lower()
        if client:
            return client
        payload = self._signed_state_payload(provider, state) or {}
        return str(payload.get("client") or "web").strip().lower()

    def _token(self, config, code, state):
        data = {
            "grant_type": "authorization_code",
            "client_id": config["client_id_value"],
            "code": code,
        }
        if config["provider"] == "apple":
            data["client_secret"] = self._apple_client_secret(config)
            data["redirect_uri"] = self._redirect_uri(config["provider"])
        elif config["provider"] == "naver":
            data["client_secret"] = config["client_secret_value"]
            data["state"] = state
        else:
            data["client_secret"] = config["client_secret_value"]
            data["redirect_uri"] = self._redirect_uri(config["provider"])
        return self._json_request(config["token_url"], data=data)

    def _profile(self, config, access_token=None, token=None, request_values=None):
        if config["provider"] == "apple":
            token = token or {}
            claims = self._decode_jwt_payload(token.get("id_token"))
            if claims.get("iss") != "https://appleid.apple.com":
                raise RuntimeError("apple_issuer_invalid")
            audience = claims.get("aud")
            if isinstance(audience, list):
                audience_valid = config["client_id_value"] in audience
            else:
                audience_valid = audience == config["client_id_value"]
            if not audience_valid:
                raise RuntimeError("apple_audience_invalid")
            if int(claims.get("exp") or 0) and int(claims.get("exp") or 0) + 300 < int(time.time()):
                raise RuntimeError("apple_token_expired")

            user_info = {}
            raw_user = ""
            try:
                raw_user = (request_values or {}).get("user") or ""
            except Exception:
                raw_user = ""
            if raw_user:
                try:
                    user_info = json.loads(raw_user)
                except Exception:
                    user_info = {}

            name = ""
            name_info = user_info.get("name") if isinstance(user_info, dict) else None
            if isinstance(name_info, dict):
                name = " ".join(
                    [str(name_info.get("firstName") or "").strip(), str(name_info.get("lastName") or "").strip()]
                ).strip()
            email_verified = claims.get("email_verified")
            if isinstance(email_verified, str):
                email_verified = email_verified.lower() == "true"

            return {
                "provider": "apple",
                "provider_user_id": str(claims.get("sub") or ""),
                "email": claims.get("email") or (user_info.get("email") if isinstance(user_info, dict) else "") or "",
                "name": name,
                "profile_image": "",
                "email_verified": bool(email_verified),
            }

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
        request_values = request.values
        provider = str(provider or self._saved_provider() or "").strip().lower()
        config = self._provider(provider)
        if not config:
            self._error_redirect("social_provider_invalid")
            return

        state = str(request_values.get("state") or "").strip()
        native_client = self._callback_client(config["provider"], state) == "native"

        if request_values.get("error"):
            error = str(request_values.get("error") or "social_denied")
            description = str(request_values.get("error_description") or "")
            self._log(config["provider"], "provider_denied", f"{error} {description}".strip())
            self._error_redirect(error, native_client)
            return

        code = str(request_values.get("code") or "").strip()
        if not code or not self._verify_state(config["provider"], state):
            self._session().pop(self.STATE_KEY, None)
            self._log(config["provider"], "state_invalid", f"code={bool(code)} state={bool(state)}")
            self._error_redirect("social_state_invalid", native_client)
            return

        try:
            try:
                token = self._token(config, code, state)
            except Exception as error:
                self._log(config["provider"], "token_failed", error)
                self._error_redirect("social_token_failed", native_client)
                return

            access_token = token.get("access_token")
            if not access_token and config["provider"] != "apple":
                raise RuntimeError("missing_access_token")

            try:
                profile = self._profile(config, access_token, token, request_values)
            except Exception as error:
                self._log(config["provider"], "profile_failed", error)
                self._error_redirect("social_profile_failed", native_client)
                return

            if not profile.get("provider_user_id"):
                self._log(config["provider"], "profile_missing_id")
                self._error_redirect("social_profile_missing", native_client)
                return
            if config["provider"] in ("google", "apple") and profile.get("email") and not profile.get("email_verified"):
                self._log(config["provider"], "email_not_verified")
                self._error_redirect(f"{config['provider']}_email_not_verified", native_client)
                return

            struct = wiz.model("struct")
            auth = wiz.model("auth")
            session = wiz.model("portal/season/session").use()
            user = struct.user.find_or_create_social_user(profile)
            session.set(**auth.session_payload(user))
            self._session().pop(self.STATE_KEY, None)
            if native_client:
                tokens = auth.issue_tokens(user)
                wiz.response.redirect(self._native_redirect_url({
                    "oauth_access_token": tokens.get("access_token") or "",
                    "oauth_refresh_token": tokens.get("refresh_token") or "",
                    "oauth_token_type": tokens.get("token_type") or "Bearer",
                    "oauth_expires_in": tokens.get("expires_in") or "",
                    "oauth_refresh_expires_in": tokens.get("refresh_expires_in") or "",
                    "oauth_provider": config["provider"],
                }))
                return
            wiz.response.redirect("/dashboard")
        except Exception as error:
            if error.__class__.__name__ == "ResponseException":
                raise
            self._log(config["provider"], "callback_failed", error)
            self._error_redirect("social_login_failed", native_client)


Model = OAuth()
