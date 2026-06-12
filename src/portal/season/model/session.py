class Session:
    def __init__(self):
        self.flask = wiz.server.package.flask
        self._validating = False

    def _bearer_token(self):
        try:
            header = self.flask.request.headers.get("Authorization", "")
        except Exception:
            return ""
        prefix = "Bearer "
        if not header.startswith(prefix):
            return ""
        return header[len(prefix):].strip()

    def _sync_bearer(self):
        if self.flask.session.get("id") or self._validating:
            return

        token = self._bearer_token()
        if not token:
            return

        self._validating = True
        try:
            auth = wiz.model("auth")
            verified, _error = auth.verify_token(token, token_type="access")
            if not verified:
                return
            self.set(**auth.session_payload(verified.get("user")))
        except Exception:
            return
        finally:
            self._validating = False

    def _is_current(self):
        self._sync_bearer()
        if self._validating:
            return True

        user_id = self.flask.session.get("id")
        if not user_id:
            return True

        self._validating = True
        try:
            struct = wiz.model("struct")
            checker = getattr(struct.user, "session_is_current", None)
            if checker is None:
                return True
            if checker(dict(self.flask.session)):
                return True
            self.clear()
            return False
        except Exception:
            return True
        finally:
            self._validating = False
    
    def has(self, key):
        if key == "id":
            self._sync_bearer()
        if key == "id" and not self._is_current():
            return False
        if key in self.flask.session:
            return True
        return False
    
    def delete(self, key):
        self.flask.session.pop(key)
    
    def set(self, **kwargs):
        for key in kwargs:
            self.flask.session[key] = kwargs[key]
    
    def get(self, key=None, default=None):
        if key is None or key == "id":
            self._sync_bearer()
        if key == "id" and not self._is_current():
            return default
        if key is None:
            return self.to_dict()
        if key in self.flask.session:
            return self.flask.session[key]
        return default

    def clear(self):
        self.flask.session.clear()

    def to_dict(self):
        return season.util.stdClass(dict(self.flask.session))

    def user_id(self):
        config = wiz.model("portal/season/config")
        session_user_id = config.session_user_id
        return session_user_id()
    
    def create(self, key):
        config = wiz.model("portal/season/config")
        config.session_create(wiz, key)

    @classmethod
    def use(cls):
        return cls()

Model = Session()
