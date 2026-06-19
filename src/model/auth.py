import base64
import datetime
import hashlib
import hmac
import json
import os
import time


class Auth:
    ACCESS_TTL_SECONDS = 15 * 60
    REFRESH_TTL_SECONDS = 30 * 24 * 60 * 60

    def _secret(self):
        secret = (
            os.environ.get("RUNNINGMATE_JWT_SECRET")
            or os.environ.get("SECRET_KEY")
            or os.environ.get("FLASK_SECRET_KEY")
        )
        if secret:
            return str(secret).encode("utf-8")

        try:
            flask = wiz.server.package.flask
            app_secret = flask.current_app.config.get("SECRET_KEY")
            if app_secret:
                return str(app_secret).encode("utf-8")
        except Exception:
            pass

        return hashlib.sha256(b"runningmate-local-jwt-secret").digest()

    def _b64encode(self, payload):
        return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")

    def _b64decode(self, payload):
        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode((payload + padding).encode("ascii"))

    def _json_default(self, value):
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    def _public_datetime(self, value):
        if not value:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)[:19]

    def _encode(self, claims):
        header = {"alg": "HS256", "typ": "JWT"}
        header_part = self._b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_part = self._b64encode(json.dumps(claims, separators=(",", ":"), default=self._json_default).encode("utf-8"))
        message = f"{header_part}.{payload_part}".encode("ascii")
        signature = hmac.new(self._secret(), message, hashlib.sha256).digest()
        return f"{header_part}.{payload_part}.{self._b64encode(signature)}"

    def _decode(self, token):
        try:
            header_part, payload_part, signature_part = str(token or "").split(".")
        except ValueError:
            return None, "invalid_token"

        message = f"{header_part}.{payload_part}".encode("ascii")
        expected = hmac.new(self._secret(), message, hashlib.sha256).digest()
        try:
            actual = self._b64decode(signature_part)
        except Exception:
            return None, "invalid_signature"
        if not hmac.compare_digest(expected, actual):
            return None, "invalid_signature"

        try:
            claims = json.loads(self._b64decode(payload_part).decode("utf-8"))
        except Exception:
            return None, "invalid_payload"

        now = int(time.time())
        if int(claims.get("exp") or 0) <= now:
            return None, "expired_token"
        return claims, ""

    def _session_version(self, user_id):
        struct = wiz.model("struct")
        return struct.user.password_session_version(user_id)

    def _token_claims(self, user, token_type, ttl):
        now = int(time.time())
        user_id = user.get("id")
        return {
            "iss": "runningmate",
            "sub": user_id,
            "typ": token_type,
            "iat": now,
            "exp": now + int(ttl),
            "pwd": self._session_version(user_id),
        }

    def public_user(self, user):
        source = dict(user or {})
        source.pop("password", None)
        source.pop("password_hash", None)
        return {
            "id": source.get("id"),
            "username": source.get("username") or "",
            "email": source.get("email") or "",
            "name": source.get("display_name") or source.get("name") or "",
            "display_name": source.get("display_name") or source.get("name") or "",
            "gender": source.get("gender") or "",
            "mobile": source.get("mobile") or "",
            "role": source.get("role") or "user",
            "running_start_date": str(source.get("running_start_date") or "")[:10],
            "profile_image": source.get("profile_image") or "",
            "onboarded": bool(source.get("onboarded")),
            "is_public": bool(source.get("is_public", True)),
            "created_at": self._public_datetime(source.get("created_at") or source.get("created")),
        }

    def issue_tokens(self, user):
        access_token = self._encode(self._token_claims(user, "access", self.ACCESS_TTL_SECONDS))
        refresh_token = self._encode(self._token_claims(user, "refresh", self.REFRESH_TTL_SECONDS))
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.ACCESS_TTL_SECONDS,
            "refresh_expires_in": self.REFRESH_TTL_SECONDS,
            "user": self.public_user(user),
        }

    def verify_token(self, token, token_type="access"):
        claims, error = self._decode(token)
        if error:
            return None, error
        if claims.get("typ") != token_type:
            return None, "invalid_token_type"

        user_id = claims.get("sub")
        if not user_id:
            return None, "invalid_subject"

        struct = wiz.model("struct")
        user = struct.user.get(id=user_id)
        if not user:
            return None, "user_not_found"

        expected = struct.user.password_session_version(user_id)
        if expected and str(claims.get("pwd") or "") != expected:
            return None, "stale_token"

        return {
            "claims": claims,
            "user": user,
        }, ""

    def session_payload(self, user):
        public = self.public_user(user)
        return {
            "id": public.get("id"),
            "username": public.get("username"),
            "email": public.get("email"),
            "name": public.get("name"),
            "gender": public.get("gender"),
            "role": public.get("role"),
            "onboarded": bool(public.get("onboarded")),
            "password_changed_at": self._session_version(public.get("id")),
        }

    def authenticate(self, identifier, password):
        user, _reason = self.authenticate_with_reason(identifier, password)
        return user

    def authenticate_with_reason(self, identifier, password):
        struct = wiz.model("struct")
        authenticate = getattr(struct.user, "authenticate_with_reason", None)
        if authenticate is None:
            user = struct.user.authenticate(identifier, password)
            return user, "" if user else "invalid_credentials"
        return authenticate(identifier, password)

    def refresh(self, refresh_token):
        verified, error = self.verify_token(refresh_token, token_type="refresh")
        if error:
            return None, error
        return self.issue_tokens(verified.get("user")), ""


Model = Auth()
