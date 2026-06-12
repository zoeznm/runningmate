# =============================================================================
# 프로젝트 루트 Struct (Composite Struct / Singleton)
# =============================================================================
# 호출 예시:
#   struct = wiz.model("struct")
#   struct.user.list()                    # 프로젝트 고유 User Sub-Struct
#   struct.user.authenticate(email, pw)   # 사용자 인증
#   struct.post.post.search()             # portal/post 패키지 Struct → Post Sub-Struct
# =============================================================================

class Struct:
    def __init__(self):
        self.orm = wiz.model("portal/season/orm")
        self.session = wiz.model("portal/season/session").use()

        # 프로젝트 고유 Sub-Struct 클래스 로드
        self._User = wiz.model("struct/user")
        self._Agreement = wiz.model("struct/agreement")
        self._Follow = wiz.model("struct/follow")

        # 패키지 Struct 캐시
        self._packages = {}

        # 테이블 자동 생성
        self._init_tables()

    def _init_tables(self):
        """DB 테이블이 없으면 자동 생성"""
        tables = ["user", "user_agreements", "follow", "password_resets", "social_account", "running_log"]
        for name in tables:
            try:
                db = self.orm.use(name)
                db.orm.create_table(safe=True)
                if name == "user":
                    self._ensure_user_columns(db.orm)
            except Exception:
                pass

    def _ensure_user_columns(self, model):
        """기존 user 테이블에 온보딩 컬럼을 보강한다."""
        try:
            database = model._meta.database
            database.connect(reuse_if_open=True)
            table = model._meta.table_name
            columns = {column.name for column in database.get_columns(table)}
        except Exception:
            return

        statements = []
        db_class = type(database).__name__.lower()
        if "mysql" in db_class:
            try:
                statements.append(f"ALTER TABLE `{table}` MODIFY `id` VARCHAR(36) NOT NULL")
            except Exception:
                pass
        if "username" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `username` VARCHAR(30) NULL")
        if "password_hash" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `password_hash` LONGTEXT NULL")
        if "display_name" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `display_name` VARCHAR(50) NULL")
        if "friend_code" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `friend_code` VARCHAR(16) NULL")
        if "gender" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `gender` VARCHAR(16) NULL")
        if "created_at" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `created_at` DATETIME NULL")
        if "running_start_date" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `running_start_date` DATE NULL")
        if "profile_image" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `profile_image` LONGTEXT NULL")
        if "onboarded" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `onboarded` BOOLEAN NOT NULL DEFAULT 0")
        if "is_public" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `is_public` BOOLEAN NOT NULL DEFAULT 1")
        if "password_changed_at" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `password_changed_at` DATETIME NULL")
        if "password_failed_count" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `password_failed_count` INTEGER NOT NULL DEFAULT 0")
        if "password_locked_until" not in columns:
            statements.append(f"ALTER TABLE `{table}` ADD COLUMN `password_locked_until` DATETIME NULL")

        for statement in statements:
            try:
                database.execute_sql(statement)
            except Exception:
                pass

        try:
            database.execute_sql(f"CREATE UNIQUE INDEX `user_username_unique` ON `{table}` (`username`)")
        except Exception:
            pass
        try:
            database.execute_sql(f"CREATE UNIQUE INDEX `user_friend_code_unique` ON `{table}` (`friend_code`)")
        except Exception:
            pass

    def db(self, name):
        """ORM Wrapper 반환 (src/model/db/{name}.py)"""
        return self.orm.use(name)

    @property
    def user(self):
        """User Sub-Struct 접근 (호출마다 새 인스턴스)"""
        return self._User(self)

    @property
    def agreement(self):
        """Agreement Sub-Struct 접근 (호출마다 새 인스턴스)"""
        return self._Agreement(self)

    @property
    def follow(self):
        """Follow Sub-Struct 접근 (호출마다 새 인스턴스)"""
        return self._Follow(self)

    def __getattr__(self, name):
        """알 수 없는 속성 → 패키지 Struct 동적 로드"""
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._packages:
            try:
                self._packages[name] = wiz.model(f"portal/{name}/struct")
            except Exception:
                raise AttributeError(f"Package '{name}' not found")
        return self._packages[name]

Model = Struct()
