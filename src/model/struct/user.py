# =============================================================================
# User Sub-Struct (사용자 비즈니스 로직)
# =============================================================================
# 사용 패턴:
#   struct = wiz.model("struct")
#   struct.user.authenticate("email@example.com", "hashed_password")
#   struct.user.get("user_id")
#   struct.user.list(text="검색어", role="admin")
#   struct.user.update_profile(user_id, name="새이름", mobile="010-...")
# =============================================================================

import datetime
import hashlib
import re
import secrets
import uuid
import bcrypt
import peewee as pw

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RESERVED_USERNAMES = {
    "admin", "administrator", "root", "api", "auth", "login", "logout",
    "signup", "register", "system", "support", "help", "user", "users",
    "me", "profile", "settings", "dashboard", "null", "undefined", "test",
}
PASSWORD_RESET_MINUTES = 30
PASSWORD_CHANGE_LOCK_THRESHOLD = 5
PASSWORD_CHANGE_LOCK_MINUTES = 10
FRIEND_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
FRIEND_CODE_LENGTH = 10

class User:
    def __init__(self, core):
        self.core = core
        self.db = core.orm.use("user")
        self.password_reset_db = core.orm.use("password_resets")
        self.social_db = core.orm.use("social_account")

    def _hash_password(self, password):
        """비밀번호 bcrypt 해시"""
        if isinstance(password, str):
            password = password.encode('utf-8')
        return bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode('utf-8')

    def _check_password(self, password, hashed):
        """비밀번호 검증"""
        if not password or not hashed:
            return False
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(hashed, str):
            hashed = hashed.encode('utf-8')
        try:
            return bcrypt.checkpw(password, hashed)
        except Exception:
            return False

    def _hash_reset_token(self, token):
        return hashlib.sha256(str(token or "").encode("utf-8")).hexdigest()

    def _parse_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.datetime.min.time())
        text = str(value or "").strip()
        if not text:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.datetime.strptime(text[:26], fmt)
            except Exception:
                pass
        return None

    def _format_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.datetime.min.time()).strftime("%Y-%m-%d %H:%M:%S")
        text = str(value or "").strip()
        if not text:
            return ""
        parsed = self._parse_datetime(text)
        if parsed:
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        return text[:19]

    def password_session_version(self, id):
        user = self.db.get(id=id)
        if user is None:
            return ""
        return self._format_datetime(user.get("password_changed_at"))

    def session_is_current(self, session_data):
        if not session_data:
            return True
        user_id = session_data.get("id") if isinstance(session_data, dict) else None
        if not user_id:
            return True

        user = self.db.get(id=user_id)
        if user is None:
            return False

        expected = self._format_datetime(user.get("password_changed_at"))
        if not expected:
            return True
        return str(session_data.get("password_changed_at") or "") == expected

    def normalize_username(self, username):
        return str(username or "").strip().lower()

    def normalize_email(self, email):
        return str(email or "").strip().lower()

    def normalize_gender(self, gender):
        text = str(gender or "").strip().lower()
        if text in ("male", "m", "man", "men", "남", "남자", "남성"):
            return "male"
        if text in ("female", "f", "woman", "women", "여", "여자", "여성"):
            return "female"
        return ""

    def validate_username(self, username):
        normalized = self.normalize_username(username)
        if not normalized:
            return False, normalized, "아이디를 입력해주세요."
        if not USERNAME_PATTERN.match(normalized):
            return False, normalized, "3~30자, 영문/숫자/언더스코어만"
        if normalized in RESERVED_USERNAMES:
            return False, normalized, "사용할 수 없는 아이디야"
        return True, normalized, ""

    def validate_email(self, email):
        normalized = self.normalize_email(email)
        if not normalized:
            return False, normalized, "이메일을 입력해주세요."
        if not EMAIL_PATTERN.match(normalized):
            return False, normalized, "올바른 이메일 형식이 아니야"
        return True, normalized, ""

    def normalize_friend_code(self, code):
        compact = "".join(ch for ch in str(code or "").strip().upper() if ch.isalnum())
        if compact.startswith("RM"):
            compact = compact[2:]
        return compact

    def format_friend_code(self, code):
        compact = self.normalize_friend_code(code)
        return f"RM-{compact}" if compact else ""

    def _random_friend_code(self):
        body = "".join(secrets.choice(FRIEND_CODE_ALPHABET) for _ in range(FRIEND_CODE_LENGTH))
        return f"RM-{body}"

    def friend_code_exists(self, code, exclude_id=""):
        formatted = self.format_friend_code(code)
        if not formatted:
            return False

        model = self.db.orm
        try:
            query = model.friend_code == formatted
            if exclude_id:
                query = query & (model.id != exclude_id)
            return model.select().where(query).exists()
        except Exception:
            existing = self.db.get(friend_code=formatted)
            return bool(existing and existing.get("id") != exclude_id)

    def _unique_friend_code(self, exclude_id=""):
        for _index in range(80):
            candidate = self._random_friend_code()
            if not self.friend_code_exists(candidate, exclude_id=exclude_id):
                return candidate
        for _index in range(20):
            candidate = f"RM-{secrets.token_hex(6).upper()}"
            if not self.friend_code_exists(candidate, exclude_id=exclude_id):
                return candidate
        raise RuntimeError("친구코드를 생성하지 못했습니다.")

    def get_friend_code(self, user_id):
        user = self.get(id=user_id)
        if not user:
            return ""

        current = self.format_friend_code(user.get("friend_code"))
        if current and not self.friend_code_exists(current, exclude_id=user_id):
            return current

        for _index in range(5):
            code = self._unique_friend_code(exclude_id=user_id)
            try:
                self.db.update({
                    "friend_code": code,
                    "updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }, id=user_id)
                return code
            except Exception:
                continue
        return ""

    def get_by_friend_code(self, code):
        formatted = self.format_friend_code(code)
        if not formatted:
            return None

        model = self.db.orm
        try:
            row = model.select().where(model.friend_code == formatted).first()
            return self._without_password(row)
        except Exception:
            return self._without_password(self.db.get(friend_code=formatted))

    def username_exists(self, username):
        normalized = self.normalize_username(username)
        if not normalized:
            return False

        model = self.db.orm
        try:
            query = pw.fn.LOWER(model.id) == normalized
            if hasattr(model, "username"):
                query = query | (pw.fn.LOWER(model.username) == normalized)
            return model.select().where(query).exists()
        except Exception:
            return self.db.get(username=normalized) is not None or self.db.get(id=normalized) is not None

    def email_exists(self, email):
        normalized = self.normalize_email(email)
        if not normalized:
            return False

        model = self.db.orm
        try:
            return model.select().where(pw.fn.LOWER(model.email) == normalized).exists()
        except Exception:
            return self.db.get(email=normalized) is not None

    def get_by_email(self, email, include_password=False):
        normalized = self.normalize_email(email)
        if not normalized:
            return None

        model = self.db.orm
        try:
            row = model.select().where(pw.fn.LOWER(model.email) == normalized).first()
            data = self._row_data(row)
        except Exception:
            data = self._row_data(self.db.get(email=normalized))

        if data and not include_password:
            data.pop("password", None)
            data.pop("password_hash", None)
        return data

    def get_by_username(self, username, include_password=False):
        normalized = self.normalize_username(username)
        if not normalized:
            return None

        model = self.db.orm
        try:
            query = pw.fn.LOWER(model.id) == normalized
            if hasattr(model, "username"):
                query = query | (pw.fn.LOWER(model.username) == normalized)
            row = model.select().where(query).first()
            data = self._row_data(row)
        except Exception:
            data = self._row_data(self.db.get(username=normalized) or self.db.get(id=normalized))

        if data and not include_password:
            data.pop("password", None)
            data.pop("password_hash", None)
        return data

    def get_by_identifier(self, identifier, include_password=False):
        value = str(identifier or "").strip()
        if not value:
            return None

        if "@" in value:
            user = self.get_by_email(value, include_password=include_password)
            if user:
                return user
        return self.get_by_username(value, include_password=include_password)

    def get_by_social_account(self, provider, provider_user_id):
        provider = str(provider or "").strip().lower()
        provider_user_id = str(provider_user_id or "").strip()
        if not provider or not provider_user_id:
            return None

        model = self.social_db.orm
        try:
            row = model.select().where(
                (model.provider == provider) & (model.provider_user_id == provider_user_id)
            ).first()
            account = self._row_data(row)
        except Exception:
            account = None

        if not account:
            return None
        return self.get(id=account.get("user_id"))

    def _social_username_base(self, provider, profile):
        email = self.normalize_email(profile.get("email") or "")
        name = str(profile.get("name") or "").strip().lower()
        subject = str(profile.get("provider_user_id") or "").strip().lower()
        seed = email.split("@", 1)[0] if email else name or f"{provider}_{subject[-8:]}"
        seed = re.sub(r"[^a-z0-9_]+", "_", seed).strip("_")
        if not seed or seed in RESERVED_USERNAMES:
            seed = f"{provider}_{subject[-8:] or secrets.token_hex(4)}"
        if len(seed) < 3:
            seed = f"{seed}_{provider}"
        return seed[:24].strip("_") or f"{provider}_{secrets.token_hex(4)}"

    def _unique_social_username(self, provider, profile):
        base = self._social_username_base(provider, profile)
        for index in range(50):
            suffix = "" if index == 0 else f"_{index}"
            candidate = f"{base[:30 - len(suffix)]}{suffix}"
            if candidate in RESERVED_USERNAMES:
                continue
            valid, username, _message = self.validate_username(candidate)
            if valid and not self.username_exists(username):
                return username
        return f"{provider}_{secrets.token_hex(6)}"[:30]

    def link_social_account(self, user_id, profile):
        provider = str(profile.get("provider") or "").strip().lower()
        provider_user_id = str(profile.get("provider_user_id") or "").strip()
        if not user_id or not provider or not provider_user_id:
            return False

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "user_id": user_id,
            "provider": provider,
            "provider_user_id": provider_user_id,
            "email": self.normalize_email(profile.get("email") or "") or None,
            "name": str(profile.get("name") or "").strip()[:50] or None,
            "profile_image": str(profile.get("profile_image") or "").strip() or None,
            "updated": now,
        }

        model = self.social_db.orm
        database = model._meta.database
        database.connect(reuse_if_open=True)
        with database.atomic():
            existing = model.select().where(
                (model.provider == provider) & (model.provider_user_id == provider_user_id)
            ).first()
            if existing is not None:
                model.update(payload).where(model.id == existing.id).execute()
                return True

            payload["id"] = str(uuid.uuid4())
            payload["created_at"] = now
            self.social_db.insert(payload)
        return True

    def find_or_create_social_user(self, profile):
        provider = str(profile.get("provider") or "").strip().lower()
        provider_user_id = str(profile.get("provider_user_id") or "").strip()
        if provider not in ("naver", "google", "apple") or not provider_user_id:
            raise ValueError("지원하지 않는 소셜 계정입니다.")

        user = self.get_by_social_account(provider, provider_user_id)
        if user:
            return user

        email = self.normalize_email(profile.get("email") or "")
        user = self.get_by_email(email) if email else None
        if not user:
            username = self._unique_social_username(provider, profile)
            display_name = str(profile.get("name") or "").strip()[:50] or f"{provider} 사용자"
            payload = {
                "username": username,
                "password": secrets.token_urlsafe(32),
                "name": display_name,
                "display_name": display_name,
                "role": "user",
                "profile_image": str(profile.get("profile_image") or "").strip() or None,
            }
            if email:
                payload["email"] = email
            user_id = self.create(payload)
            user = self.get(id=user_id)

        self.link_social_account(user.get("id"), profile)
        if profile.get("profile_image") and not user.get("profile_image"):
            try:
                self.update_profile(user.get("id"), profile_image=str(profile.get("profile_image") or ""))
                user = self.get(id=user.get("id"))
            except Exception:
                pass
        return user

    def _row_data(self, row):
        if row is None:
            return None
        if isinstance(row, dict):
            data = dict(row)
        elif hasattr(row, "__data__"):
            data = dict(row.__data__)
        else:
            data = {}

        for key in ("running_start_date", "created", "created_at", "updated"):
            value = data.get(key)
            if hasattr(value, "strftime"):
                data[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        return data

    def _without_password(self, user):
        data = self._row_data(user)
        if data:
            data.pop("password", None)
            data.pop("password_hash", None)
        return data

    def _password_hash(self, user):
        data = self._row_data(user)
        if not data:
            return ""
        return data.get("password_hash") or data.get("password") or ""

    def public_profile(self, user, viewer_id=None):
        data = self._without_password(user)
        if not data:
            return None

        user_id = data.get("id") or ""
        counts = self.core.follow.counts(user_id)
        relation = self.core.follow.relation(viewer_id, user_id) if viewer_id else {
            "is_following": False,
            "is_follower": False,
            "is_mutual": False,
        }
        return {
            "id": user_id,
            "email": data.get("email") or "",
            "username": data.get("username") or (user_id if not UUID_PATTERN.match(user_id) else ""),
            "display_id": data.get("username") or data.get("email") or user_id,
            "display_name": data.get("display_name") or data.get("name") or "",
            "name": data.get("display_name") or data.get("name") or "",
            "gender": self.normalize_gender(data.get("gender")),
            "mobile": data.get("mobile") or "",
            "role": data.get("role") or "user",
            "running_start_date": str(data.get("running_start_date") or "")[:10],
            "profile_image": data.get("profile_image") or "",
            "onboarded": bool(data.get("onboarded")),
            "is_public": bool(data.get("is_public", True)),
            "is_me": bool(viewer_id and user_id == viewer_id),
            **counts,
            **relation,
        }

    def authenticate_with_reason(self, email, password):
        """아이디 또는 이메일/비밀번호 인증

        Args:
            email: 아이디 또는 이메일
            password: 평문 비밀번호

        Returns:
            (dict (사용자 정보), reason) 또는 (None, 실패 사유)
        """
        user = self.get_by_identifier(email, include_password=True)
        if user is None:
            return None, "user_not_found"

        password_hash = self._password_hash(user)
        if not self._check_password(password, password_hash):
            normalized_password = password.strip() if isinstance(password, str) else password
            if normalized_password == password or not self._check_password(normalized_password, password_hash):
                return None, "password_mismatch"
            reason = "trimmed_password"
        else:
            reason = ""

        # 비밀번호 필드 제거 후 반환
        user.pop('password', None)
        user.pop('password_hash', None)
        return user, reason

    def authenticate(self, email, password):
        user, _reason = self.authenticate_with_reason(email, password)
        return user

    def get(self, id=None):
        """사용자 단건 조회 (비밀번호 제외)

        Args:
            id: 사용자 ID

        Returns:
            dict 또는 None
        """
        user = self.db.get(id=id)
        return self._without_password(user)

    def list(self, text="", role=""):
        """사용자 목록 조회

        Args:
            text: 이름/이메일 검색어
            role: 역할 필터

        Returns:
            list[dict]
        """
        kwargs = dict()
        like = None

        if role:
            kwargs['role'] = role
        if text:
            kwargs['name'] = text
            like = "name"

        rows = self.db.rows(
            orderby="created", order="ASC",
            like=like,
            **kwargs
        )
        # 비밀번호 필드 제거
        for r in rows:
            r.pop('password', None)
            r.pop('password_hash', None)
        return rows

    def list_by_ids(self, ids):
        """ID 목록으로 사용자 조회"""
        ordered_ids = []
        seen = set()
        for value in ids or []:
            user_id = str(value or "").strip()
            if user_id and user_id not in seen:
                ordered_ids.append(user_id)
                seen.add(user_id)

        if not ordered_ids:
            return []

        model = self.db.orm
        rows = model.select().where(model.id.in_(ordered_ids))
        users = {}
        for row in rows:
            data = self._without_password(row)
            if data:
                users[data.get("id")] = data
        return [users[user_id] for user_id in ordered_ids if user_id in users]

    def search(self, q="", viewer_id="", limit=20):
        """아이디/이메일/이름 검색"""
        text = str(q or "").strip()
        if not text:
            return []

        try:
            limit = max(1, min(50, int(limit)))
        except Exception:
            limit = 20

        model = self.db.orm
        query = (
            model
            .select()
            .where(
                (model.name.contains(text))
                | (model.email.contains(text))
                | (model.username.contains(text))
                | (model.id.contains(text))
            )
            .order_by(model.name.asc(), model.username.asc(), model.email.asc())
            .limit(limit)
        )
        users = []
        for row in query:
            data = self._without_password(row)
            if not data:
                continue
            if viewer_id and data.get("id") == viewer_id:
                continue
            users.append(data)
        return users

    def create(self, data):
        """사용자 생성

        Args:
            data: {"email", "password", "name", "role"} dict

        Returns:
            생성된 사용자 ID
        """
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = dict(data or {})
        explicit_id = str(payload.get("id") or "").strip()
        username = self.normalize_username(payload.get("username") or "")
        if not username and explicit_id and not UUID_PATTERN.match(explicit_id):
            username = self.normalize_username(explicit_id)

        if username:
            valid, username, message = self.validate_username(username)
            if not valid:
                raise ValueError(message or "아이디가 올바르지 않습니다.")
            payload["username"] = username

        if not explicit_id or not UUID_PATTERN.match(explicit_id):
            payload["id"] = str(uuid.uuid4())
        else:
            payload["id"] = explicit_id

        email = self.normalize_email(payload.get("email") or "")
        if not email and username:
            email = f"{username}@runningmate.local"
        if email:
            payload["email"] = email

        display_name = str(payload.get("display_name") or payload.get("name") or "").strip()[:50]
        payload["display_name"] = display_name
        payload["name"] = display_name
        if not payload.get("friend_code"):
            payload["friend_code"] = self._unique_friend_code()
        if "gender" in payload:
            payload["gender"] = self.normalize_gender(payload.get("gender")) or None

        hashed = self._hash_password(payload['password'])
        payload['password_hash'] = hashed
        payload['password'] = hashed
        payload['created_at'] = now
        payload['created'] = now
        payload['updated'] = now
        if not payload.get('role'):
            payload['role'] = 'user'
        return self.db.insert(payload)

    def update_profile(self, id, **fields):
        """프로필 업데이트 (name, mobile, onboarded 등)

        Args:
            id: 사용자 ID
            **fields: 업데이트할 필드
        """
        if "name" in fields and "display_name" not in fields:
            fields["display_name"] = fields.get("name")
        if "display_name" in fields and "name" not in fields:
            fields["name"] = fields.get("display_name")
        fields['updated'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.update(fields, id=id)

    def change_password(self, id, current_password, new_password):
        """비밀번호 변경"""
        ok, _message, _meta = self.change_password_with_policy(id, current_password, new_password)
        return ok

    def change_password_with_policy(self, id, current_password, new_password, invalidate_sessions=True):
        """비밀번호 변경 정책을 적용하고 결과 메시지를 반환한다."""
        now = datetime.datetime.now()
        now_text = now.strftime("%Y-%m-%d %H:%M:%S")
        user = self.db.get(id=id)
        if user is None:
            return False, "사용자를 찾을 수 없습니다.", {}
        if not current_password:
            return False, "현재 비밀번호를 입력해주세요.", {}
        if not new_password:
            return False, "새 비밀번호를 입력해주세요.", {}
        if len(new_password) < 8:
            return False, "새 비밀번호는 8자 이상이어야 합니다.", {}

        locked_until = self._parse_datetime(user.get("password_locked_until"))
        if locked_until and locked_until > now:
            return False, "현재 비밀번호 확인 시도가 많아 잠시 후 다시 시도해주세요.", {
                "locked_until": self._format_datetime(locked_until)
            }

        current_hash = self._password_hash(user)
        if not self._check_password(current_password, current_hash):
            failed_count = int(user.get("password_failed_count") or 0) + 1
            updates = {
                "password_failed_count": failed_count,
                "updated": now_text,
            }
            if failed_count >= PASSWORD_CHANGE_LOCK_THRESHOLD:
                locked_until = now + datetime.timedelta(minutes=PASSWORD_CHANGE_LOCK_MINUTES)
                updates["password_locked_until"] = locked_until.strftime("%Y-%m-%d %H:%M:%S")
            self.db.update(updates, id=id)

            if failed_count >= PASSWORD_CHANGE_LOCK_THRESHOLD:
                return False, "현재 비밀번호 확인 시도가 많아 잠시 제한됐습니다.", {
                    "locked_until": updates.get("password_locked_until")
                }
            return False, "현재 비밀번호가 올바르지 않습니다.", {
                "remaining_attempts": max(0, PASSWORD_CHANGE_LOCK_THRESHOLD - failed_count)
            }

        if self._check_password(new_password, current_hash):
            return False, "새 비밀번호는 현재 비밀번호와 달라야 합니다.", {}

        hashed = self._hash_password(new_password)
        updates = {
            "password_hash": hashed,
            "password": hashed,
            "password_failed_count": 0,
            "password_locked_until": None,
            "updated": now_text,
        }
        if invalidate_sessions:
            updates["password_changed_at"] = now_text
        self.db.update(updates, id=id)

        return True, "", {
            "password_changed_at": updates.get("password_changed_at") or self.password_session_version(id)
        }

    def set_password(self, id, new_password):
        """현재 비밀번호 확인 없이 비밀번호를 갱신한다."""
        if not id or not new_password:
            return False
        user = self.db.get(id=id)
        if user is None:
            return False
        hashed = self._hash_password(new_password)
        self.db.update(dict(
            password_hash=hashed,
            password=hashed,
            password_changed_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            password_failed_count=0,
            password_locked_until=None,
            updated=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ), id=id)
        return True

    def issue_password_reset(self, email):
        """비밀번호 재설정 토큰을 발급하고 원문 토큰을 반환한다."""
        user = self.get_by_email(email)
        if not user:
            return None

        now = datetime.datetime.now()
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_reset_token(token)
        expires_at = now + datetime.timedelta(minutes=PASSWORD_RESET_MINUTES)
        reset_model = self.password_reset_db.orm

        try:
            reset_model.update(used=True).where(
                (reset_model.user_id == user.get("id")) & (reset_model.used == False)
            ).execute()
        except Exception:
            pass

        self.password_reset_db.insert({
            "id": str(uuid.uuid4()),
            "user_id": user.get("id"),
            "token": token_hash,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "used": False,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return {
            "token": token,
            "user": user,
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def reset_password_with_token(self, token, new_password):
        """1회용 비밀번호 재설정 토큰을 검증하고 비밀번호를 갱신한다."""
        token = str(token or "").strip()
        if not token:
            return False, "재설정 토큰이 필요합니다."
        if not new_password:
            return False, "새 비밀번호를 입력해주세요."
        if len(new_password) < 8:
            return False, "비밀번호는 8자 이상이어야 합니다."

        token_hash = self._hash_reset_token(token)
        reset_model = self.password_reset_db.orm
        database = reset_model._meta.database
        now = datetime.datetime.now()

        database.connect(reuse_if_open=True)
        with database.atomic():
            reset = reset_model.select().where(reset_model.token == token_hash).first()
            if reset is None:
                return False, "재설정 링크가 만료되었거나 사용할 수 없습니다."

            reset_data = self._row_data(reset)
            expires_at = self._parse_datetime(reset_data.get("expires_at"))
            if reset_data.get("used") or expires_at is None or expires_at <= now:
                return False, "재설정 링크가 만료되었거나 사용할 수 없습니다."

            if not self.set_password(reset_data.get("user_id"), new_password):
                return False, "사용자를 찾을 수 없습니다."

            reset_model.update(used=True).where(reset_model.id == reset_data.get("id")).execute()

        return True, ""

    def verify_password(self, id, password):
        """현재 비밀번호 검증"""
        user = self.db.get(id=id)
        if user is None or not password:
            return False
        return self._check_password(password, self._password_hash(user))

    def delete_account(self, id):
        """사용자 계정과 계정 약관 기록 삭제"""
        user = self.db.get(id=id)
        if user is None:
            return False

        database = self.db.orm._meta.database
        database.connect(reuse_if_open=True)
        with database.atomic():
            self.core.agreement.delete_user(id)
            self.core.follow.delete_user(id)
            self.social_db.delete(user_id=id)
            self.password_reset_db.delete(user_id=id)
            self.db.delete(id=id)
        return True

    def count(self, **kwargs):
        """사용자 수 조회"""
        return self.db.count(**kwargs) or 0

Model = User
