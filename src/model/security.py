import datetime
import hashlib
import hmac
import json
import os
import re
import shlex
import shutil
import subprocess
import time
import urllib.parse


class Security:
    UPLOAD_URL_PREFIXES = ("/api/run-images/", "/api/run-media/")
    SENSITIVE_KEYS = {
        "access_token", "refresh_token", "id_token", "token", "authorization", "api_key",
        "apikey", "secret", "client_secret", "password", "password_hash", "current_password",
        "new_password", "confirm_password", "journal", "diary", "raw_text", "raw_parsed_json",
        "content", "message_body", "developer_token", "user_token",
    }
    EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
    JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
    API_KEY_RE = re.compile(r"\b(?:sk|rk|pk|sess|org|proj)-[A-Za-z0-9_-]{12,}\b")
    BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{12,}")
    PARAM_SECRET_RE = re.compile(
        r"(?i)\b(access_token|refresh_token|id_token|client_secret|api_key|admin_token|token|code|password)=([^&\s]+)"
    )

    def _bool(self, name, default=False):
        value = os.environ.get(name)
        if value is None:
            return default
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    def public_base_url(self):
        return str(os.environ.get("RUNNINGMATE_PUBLIC_BASE_URL") or "").strip().rstrip("/")

    def allowed_origins(self):
        raw = os.environ.get("RUNNINGMATE_ALLOWED_ORIGINS") or self.public_base_url()
        origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip() and item.strip() != "*"]
        for native_origin in ("capacitor://localhost", "ionic://localhost"):
            if native_origin not in origins:
                origins.append(native_origin)
        return origins

    def allowed_hosts(self):
        hosts = set()
        for origin in self.allowed_origins():
            try:
                parsed = urllib.parse.urlparse(origin)
                if parsed.netloc:
                    hosts.add(parsed.netloc.lower())
            except Exception:
                pass
        return hosts

    def url_host_allowed(self, url):
        try:
            parsed = urllib.parse.urlparse(str(url or ""))
        except Exception:
            return False
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return False
        hosts = self.allowed_hosts()
        return not hosts or parsed.netloc.lower() in hosts

    def auth_headers(self):
        try:
            wiz.response.headers.set(**{
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "same-origin",
            })
        except Exception:
            pass

    def bearer_token(self):
        try:
            request = wiz.server.package.flask.request
            header = str(request.headers.get("Authorization") or "").strip()
        except Exception:
            return ""

        if not header.lower().startswith("bearer "):
            return ""
        return header.split(" ", 1)[1].strip()

    def bind_bearer_session(self, session=None):
        try:
            session = session or wiz.model("portal/season/session").use()
            if session.get("id"):
                return session.get("id")
        except Exception:
            return ""

        token = self.bearer_token()
        if not token:
            return ""

        try:
            auth = wiz.model("auth")
            verified, error = auth.verify_token(token, token_type="access")
            if error or not verified:
                return ""

            user = verified.get("user")
            if not user:
                return ""

            session.set(**auth.session_payload(user))
            return str(user.get("id") or "")
        except Exception:
            return ""

    def _sensitive_key(self, key):
        normalized = re.sub(r"[^a-z0-9]+", "_", str(key or "").strip().lower()).strip("_")
        if normalized in self.SENSITIVE_KEYS:
            return True
        return any(part in normalized for part in ("token", "secret", "password", "api_key", "apikey", "journal", "diary"))

    def mask_email(self, value):
        text = str(value or "")
        if "@" not in text:
            return text
        local, _, domain = text.partition("@")
        if not local or not domain:
            return "<redacted-email>"
        return f"{local[:1]}***@{domain}"

    def _mask_text(self, value, max_length=1000):
        text = str(value or "")
        text = self.BEARER_RE.sub("Bearer <redacted>", text)
        text = self.JWT_RE.sub("<redacted-token>", text)
        text = self.API_KEY_RE.sub("<redacted-api-key>", text)
        text = self.PARAM_SECRET_RE.sub(lambda match: f"{match.group(1)}=<redacted>", text)
        text = self.EMAIL_RE.sub(lambda match: self.mask_email(match.group(0)), text)
        if max_length and len(text) > max_length:
            text = text[:max_length] + "...<truncated>"
        return text

    def mask_sensitive(self, value, max_length=1000):
        if isinstance(value, dict):
            masked = {}
            for key, item in value.items():
                if self._sensitive_key(key):
                    masked[key] = "<redacted>"
                else:
                    masked[key] = self.mask_sensitive(item, max_length=max_length)
            return masked
        if isinstance(value, list):
            return [self.mask_sensitive(item, max_length=max_length) for item in value[:100]]
        if isinstance(value, tuple):
            return tuple(self.mask_sensitive(item, max_length=max_length) for item in value[:100])
        if isinstance(value, str):
            return self._mask_text(value, max_length=max_length)
        return value

    def safe_log(self, scope, message, detail=""):
        text = f"[{self._mask_text(scope, 80)}] {self._mask_text(message, 300)}"
        if detail:
            text = f"{text} - {self._mask_text(detail, 800)}"
        try:
            print(text, flush=True)
        except Exception:
            pass

    def audit_log_path(self):
        return os.environ.get("RUNNINGMATE_AUDIT_LOG_FILE", "/opt/app/data/security_audit.jsonl")

    def audit(self, event, actor_id="", actor_role="", target="", success=True, metadata=None):
        row = {
            "ts": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            "event": self._mask_text(event, 120),
            "actor_id": self._mask_text(actor_id, 120),
            "actor_role": self._mask_text(actor_role, 40),
            "target": self._mask_text(target, 200),
            "success": bool(success),
            "metadata": self.mask_sensitive(metadata or {}, max_length=500),
        }
        path = self.audit_log_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "a", encoding="utf-8") as fp:
                fp.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            try:
                os.chmod(path, 0o600)
            except Exception:
                pass
        except Exception:
            pass
        return row

    def session_context(self, session=None):
        try:
            session = session or wiz.model("portal/season/session").use()
            return {
                "id": str(session.get("id") or ""),
                "role": str(session.get("role") or ""),
                "email": str(session.get("email") or ""),
            }
        except Exception:
            return {"id": "", "role": "", "email": ""}

    def is_admin_session(self, session=None):
        context = self.session_context(session)
        return context.get("role") == "admin"

    def require_admin(self, action="admin_access", session=None):
        context = self.session_context(session)
        ok = context.get("role") == "admin"
        self.audit(
            action,
            actor_id=context.get("id"),
            actor_role=context.get("role"),
            success=ok,
            metadata={"email": context.get("email")},
        )
        if ok:
            return True
        wiz.response.status(403, success=False, message="관리자 권한이 필요합니다.")

    def oauth_require_public_base_url(self):
        return self._bool("RUNNINGMATE_OAUTH_REQUIRE_PUBLIC_BASE_URL", False)

    def oauth_state_ttl_seconds(self):
        try:
            return max(60, min(3600, int(os.environ.get("RUNNINGMATE_OAUTH_STATE_TTL_SECONDS", 600))))
        except Exception:
            return 600

    def _secret(self):
        secret = (
            os.environ.get("RUNNINGMATE_FILE_URL_SECRET")
            or os.environ.get("RUNNINGMATE_JWT_SECRET")
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

        return hashlib.sha256(b"runningmate-local-file-url-secret").digest()

    def upload_url_ttl_seconds(self):
        try:
            return max(60, min(3600, int(os.environ.get("RUNNINGMATE_UPLOAD_URL_TTL_SECONDS", 600))))
        except Exception:
            return 600

    def local_upload_url_path(self, url):
        text = str(url or "").strip()
        if not text:
            return ""

        try:
            parsed = urllib.parse.urlparse(text)
            path = parsed.path or text.split("?", 1)[0]
        except Exception:
            path = text.split("?", 1)[0]

        return path if path.startswith(self.UPLOAD_URL_PREFIXES) else ""

    def _upload_url_signature(self, path, expires):
        message = f"{path}.{int(expires)}".encode("utf-8")
        return hmac.new(self._secret(), message, hashlib.sha256).hexdigest()

    def sign_upload_url(self, url, ttl_seconds=None):
        path = self.local_upload_url_path(url)
        if not path:
            return url

        try:
            ttl = int(ttl_seconds if ttl_seconds is not None else self.upload_url_ttl_seconds())
        except Exception:
            ttl = self.upload_url_ttl_seconds()
        ttl = max(60, min(3600, ttl))
        expires = int(time.time()) + ttl
        signature = self._upload_url_signature(path, expires)
        return f"{path}?exp={expires}&sig={signature}"

    def verify_upload_url_signature(self, url_or_path, expires, signature):
        path = self.local_upload_url_path(url_or_path)
        if not path:
            return False

        try:
            expires = int(expires)
        except Exception:
            return False
        if expires < int(time.time()):
            return False

        expected = self._upload_url_signature(path, expires)
        return bool(signature and hmac.compare_digest(str(signature), expected))

    def upload_scan_mode(self):
        if self._bool("RUNNINGMATE_AV_SCAN_DISABLED", False):
            return "disabled"

        mode = str(os.environ.get("RUNNINGMATE_AV_SCAN_MODE") or "permissive").strip().lower()
        if mode in {"disabled", "off", "false", "0", "none"}:
            return "disabled"
        if mode in {"permissive", "optional", "warn"}:
            return "permissive"
        return "required"

    def upload_scan_timeout_seconds(self):
        try:
            return max(1, min(300, int(os.environ.get("RUNNINGMATE_AV_SCAN_TIMEOUT_SECONDS", 30))))
        except Exception:
            return 30

    def upload_incoming_dir(self, root):
        incoming_dir = os.path.join(root, ".incoming")
        os.makedirs(incoming_dir, exist_ok=True)
        try:
            os.chmod(incoming_dir, 0o700)
        except Exception:
            pass
        return incoming_dir

    def _resolve_command(self, value):
        try:
            command = shlex.split(str(value or ""))
        except Exception:
            return None
        if not command:
            return None

        executable = command[0]
        if os.path.isabs(executable):
            if os.path.isfile(executable) and os.access(executable, os.X_OK):
                return command
            return None

        resolved = shutil.which(executable)
        if not resolved:
            return None
        return [resolved] + command[1:]

    def _upload_scan_command(self):
        custom = os.environ.get("RUNNINGMATE_AV_SCANNER")
        if custom:
            return self._resolve_command(custom)

        clamdscan = shutil.which("clamdscan")
        if clamdscan:
            return [clamdscan, "--fdpass", "--no-summary"]

        clamscan = shutil.which("clamscan")
        if clamscan:
            return [clamscan, "--no-summary"]

        return None

    def _append_scan_path(self, command, path):
        if any("{path}" in item for item in command):
            return [item.replace("{path}", path) for item in command]
        return command + [path]

    def scan_upload_file(self, path):
        mode = self.upload_scan_mode()
        if mode == "disabled":
            return True, ""
        if not path or not os.path.isfile(path):
            return False, "업로드 파일을 검사하지 못했습니다."

        command = self._upload_scan_command()
        if not command:
            if mode == "permissive":
                return True, ""
            return False, "서버 악성 파일 스캔 엔진이 준비되지 않았습니다."

        try:
            result = subprocess.run(
                self._append_scan_path(command, path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.upload_scan_timeout_seconds(),
                check=False,
            )
        except subprocess.TimeoutExpired:
            if mode == "permissive":
                return True, ""
            return False, "악성 파일 스캔 시간이 초과되었습니다."
        except Exception:
            if mode == "permissive":
                return True, ""
            return False, "업로드 파일을 검사하지 못했습니다."

        output = b" ".join([result.stdout or b"", result.stderr or b""]).upper()
        if result.returncode == 0 and b"FOUND" not in output:
            return True, ""
        if result.returncode == 1 or b"FOUND" in output:
            return False, "악성 파일로 의심되어 업로드가 차단되었습니다."
        if mode == "permissive":
            return True, ""
        return False, "업로드 파일 악성 검사에 실패했습니다."


Model = Security()
