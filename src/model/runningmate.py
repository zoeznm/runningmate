import calendar
import datetime
import json
import math
import os
import re
import uuid


class RunningMateData:
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
    VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v"}
    MEDIA_MIME_EXTENSIONS = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/heic": ".heic",
        "image/heif": ".heif",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
        "video/x-m4v": ".m4v",
    }
    DEFAULT_MAX_MEDIA_UPLOAD_BYTES = 50 * 1024 * 1024
    RUN_TYPE_ORDER = ("jogging", "long", "interval", "tempo", "race", "recovery", "strength", "home_training")
    GOAL_TYPE_ORDER = ("distance", "count", "duration", "pace")
    GOAL_TYPE_LABELS = {
        "distance": "월 총 거리",
        "count": "월 러닝 횟수",
        "duration": "월 총 시간",
        "pace": "평균 페이스",
    }
    CHALLENGE_TYPE_ORDER = ("total_distance", "individual_distance", "count")
    CHALLENGE_TYPE_LABELS = {
        "total_distance": "다같이 거리 합산",
        "individual_distance": "각자 거리 달성",
        "count": "러닝 횟수",
    }
    REST_STREAK_DAYS = 5
    REST_WEEKLY_INCREASE_PCT = 30
    CAUTION_WEEKLY_INCREASE_PCT = 10
    HEART_RATE_SIGNIFICANT_DELTA = 10
    HEART_RATE_SIGNIFICANT_RATIO = 1.08
    NEGATIVE_CONDITION_MARKERS = ("😣", "🤕")
    NEGATIVE_CONDITION_WORDS = (
        "아프",
        "통증",
        "피곤",
        "힘들",
        "무겁",
        "지침",
        "불편",
        "부상",
        "무릎",
        "발목",
        "쑤심",
    )
    RUN_TYPE_LABELS = {
        "jogging": "조깅",
        "long": "장거리",
        "interval": "인터벌",
        "tempo": "템포",
        "race": "대회",
        "recovery": "회복주",
        "strength": "근력운동",
        "home_training": "홈트",
    }
    RUN_TYPE_ALIASES = {
        "jog": "jogging",
        "jogging": "jogging",
        "조깅": "jogging",
        "편안한 러닝": "jogging",
        "long": "long",
        "longrun": "long",
        "long_run": "long",
        "장거리": "long",
        "장거리 러닝": "long",
        "interval": "interval",
        "intervals": "interval",
        "인터벌": "interval",
        "스피드 런": "interval",
        "speedrun": "interval",
        "speed_run": "interval",
        "tempo": "tempo",
        "템포": "tempo",
        "템포런": "tempo",
        "race": "race",
        "대회": "race",
        "레이스": "race",
        "recovery": "recovery",
        "recoveryrun": "recovery",
        "recovery_run": "recovery",
        "회복주": "recovery",
        "회복 러닝": "recovery",
        "strength": "strength",
        "strength_training": "strength",
        "weight_training": "strength",
        "근력운동": "strength",
        "근력 운동": "strength",
        "웨이트": "strength",
        "home_training": "home_training",
        "hometraining": "home_training",
        "homeworkout": "home_training",
        "home_workout": "home_training",
        "홈트": "home_training",
        "홈트레이닝": "home_training",
    }
    REACTION_TYPES = ("like", "fire", "clap", "strong")
    REACTION_META = {
        "like": {"emoji": "👍", "label": "좋아요"},
        "fire": {"emoji": "🔥", "label": "불꽃"},
        "clap": {"emoji": "👏", "label": "박수"},
        "strong": {"emoji": "💪", "label": "힘내"},
    }
    CYCLE_PHASE_ORDER = ("menstrual", "follicular", "ovulation", "luteal")
    DEFAULT_PERIOD_DAYS = 7
    CYCLE_PHASE_LABELS = {
        "menstrual": "생리기",
        "follicular": "난포기",
        "ovulation": "배란기",
        "luteal": "황체기",
    }
    CYCLE_CONDITION_EMOJIS = ("😊", "😐", "😣")
    DEFAULT_BADGES = [
        {
            "id": 1,
            "code": "first_5k",
            "title": "첫 5km",
            "description": "한 번의 러닝에서 5km 이상 달성",
            "icon": "fa-route",
            "condition_type": "single_distance",
            "threshold": 5,
        },
        {
            "id": 2,
            "code": "first_10k",
            "title": "첫 10km",
            "description": "한 번의 러닝에서 10km 이상 달성",
            "icon": "fa-road",
            "condition_type": "single_distance",
            "threshold": 10,
        },
        {
            "id": 3,
            "code": "first_15k",
            "title": "첫 15km",
            "description": "한 번의 러닝에서 15km 이상 달성",
            "icon": "fa-location-arrow",
            "condition_type": "single_distance",
            "threshold": 15,
        },
        {
            "id": 4,
            "code": "first_half",
            "title": "하프 거리",
            "description": "한 번의 러닝에서 21.1km 이상 달성",
            "icon": "fa-medal",
            "condition_type": "single_distance",
            "threshold": 21.1,
        },
        {
            "id": 5,
            "code": "first_30k",
            "title": "첫 30km",
            "description": "한 번의 러닝에서 30km 이상 달성",
            "icon": "fa-mountain-sun",
            "condition_type": "single_distance",
            "threshold": 30,
        },
        {
            "id": 6,
            "code": "first_marathon",
            "title": "마라톤 거리",
            "description": "한 번의 러닝에서 42.195km 이상 달성",
            "icon": "fa-trophy",
            "condition_type": "single_distance",
            "threshold": 42.195,
        },
        {
            "id": 7,
            "code": "total_100k",
            "title": "누적 100km",
            "description": "전체 러닝 거리 100km 달성",
            "icon": "fa-layer-group",
            "condition_type": "total_distance",
            "threshold": 100,
        },
        {
            "id": 8,
            "code": "total_250k",
            "title": "누적 250km",
            "description": "전체 러닝 거리 250km 달성",
            "icon": "fa-layer-group",
            "condition_type": "total_distance",
            "threshold": 250,
        },
        {
            "id": 9,
            "code": "total_500k",
            "title": "누적 500km",
            "description": "전체 러닝 거리 500km 달성",
            "icon": "fa-layer-group",
            "condition_type": "total_distance",
            "threshold": 500,
        },
        {
            "id": 10,
            "code": "total_1000k",
            "title": "누적 1000km",
            "description": "전체 러닝 거리 1000km 달성",
            "icon": "fa-infinity",
            "condition_type": "total_distance",
            "threshold": 1000,
        },
        {
            "id": 11,
            "code": "total_2000k",
            "title": "누적 2000km",
            "description": "전체 러닝 거리 2000km 달성",
            "icon": "fa-infinity",
            "condition_type": "total_distance",
            "threshold": 2000,
        },
        {
            "id": 12,
            "code": "streak_3",
            "title": "3일 연속",
            "description": "3일 연속 러닝 달성",
            "icon": "fa-fire",
            "condition_type": "streak",
            "threshold": 3,
        },
        {
            "id": 13,
            "code": "streak_7",
            "title": "7일 연속",
            "description": "7일 연속 러닝 달성",
            "icon": "fa-fire-flame-curved",
            "condition_type": "streak",
            "threshold": 7,
        },
        {
            "id": 14,
            "code": "streak_14",
            "title": "14일 연속",
            "description": "14일 연속 러닝 달성",
            "icon": "fa-calendar-check",
            "condition_type": "streak",
            "threshold": 14,
        },
        {
            "id": 15,
            "code": "streak_30",
            "title": "30일 연속",
            "description": "30일 연속 러닝 달성",
            "icon": "fa-calendar-days",
            "condition_type": "streak",
            "threshold": 30,
        },
        {
            "id": 16,
            "code": "streak_60",
            "title": "60일 연속",
            "description": "60일 연속 러닝 달성",
            "icon": "fa-calendar-plus",
            "condition_type": "streak",
            "threshold": 60,
        },
        {
            "id": 17,
            "code": "run_count_1",
            "title": "첫 러닝",
            "description": "러닝 기록 1회 저장",
            "icon": "fa-shoe-prints",
            "condition_type": "run_count",
            "threshold": 1,
        },
        {
            "id": 18,
            "code": "run_count_10",
            "title": "누적 10회",
            "description": "러닝 기록 10회 저장",
            "icon": "fa-person-running",
            "condition_type": "run_count",
            "threshold": 10,
        },
        {
            "id": 19,
            "code": "run_count_50",
            "title": "누적 50회",
            "description": "러닝 기록 50회 저장",
            "icon": "fa-person-running",
            "condition_type": "run_count",
            "threshold": 50,
        },
        {
            "id": 20,
            "code": "run_count_100",
            "title": "누적 100회",
            "description": "러닝 기록 100회 저장",
            "icon": "fa-ranking-star",
            "condition_type": "run_count",
            "threshold": 100,
        },
        {
            "id": 21,
            "code": "run_count_200",
            "title": "누적 200회",
            "description": "러닝 기록 200회 저장",
            "icon": "fa-award",
            "condition_type": "run_count",
            "threshold": 200,
        },
        {
            "id": 22,
            "code": "monthly_goal",
            "title": "한 달 목표 달성",
            "description": "한 달 누적 거리 100km 달성",
            "icon": "fa-bullseye",
            "condition_type": "monthly_goal",
            "threshold": 100,
        },
        {
            "id": 23,
            "code": "monthly_100k",
            "title": "한 달 100km",
            "description": "한 달 누적 거리 100km 달성",
            "icon": "fa-chart-line",
            "condition_type": "monthly_distance",
            "threshold": 100,
        },
        {
            "id": 24,
            "code": "monthly_150k",
            "title": "한 달 150km",
            "description": "한 달 누적 거리 150km 달성",
            "icon": "fa-chart-line",
            "condition_type": "monthly_distance",
            "threshold": 150,
        },
        {
            "id": 25,
            "code": "dawn_5",
            "title": "새벽 러닝 5회",
            "description": "새벽 시간대 러닝 5회 달성",
            "icon": "fa-sun",
            "condition_type": "dawn_count",
            "threshold": 5,
        },
        {
            "id": 26,
            "code": "dawn_10",
            "title": "새벽 러닝 10회",
            "description": "새벽 시간대 러닝 10회 달성",
            "icon": "fa-sun",
            "condition_type": "dawn_count",
            "threshold": 10,
        },
        {
            "id": 27,
            "code": "night_5",
            "title": "야간 러닝 5회",
            "description": "야간 시간대 러닝 5회 달성",
            "icon": "fa-moon",
            "condition_type": "night_count",
            "threshold": 5,
        },
        {
            "id": 28,
            "code": "night_10",
            "title": "야간 러닝 10회",
            "description": "야간 시간대 러닝 10회 달성",
            "icon": "fa-moon",
            "condition_type": "night_count",
            "threshold": 10,
        },
        {
            "id": 29,
            "code": "first_interval",
            "title": "첫 인터벌",
            "description": "인터벌 러닝 1회 저장",
            "icon": "fa-bolt",
            "condition_type": "first_interval",
            "threshold": 1,
        },
        {
            "id": 30,
            "code": "first_race",
            "title": "첫 대회",
            "description": "대회 러닝 1회 저장",
            "icon": "fa-flag-checkered",
            "condition_type": "first_race",
            "threshold": 1,
        },
    ]

    DATE_KEYS = (
        "date",
        "run_date",
        "runDate",
        "workout_date",
        "workoutDate",
        "activity_date",
        "activityDate",
        "날짜",
        "일자",
    )

    DISTANCE_KEYS = (
        "distance_km",
        "distanceKm",
        "distance_kilometers",
        "distanceKilometers",
        "distance",
        "km",
        "total_km",
        "totalKm",
        "total_distance_km",
        "totalDistanceKm",
        "total_distance",
        "totalDistance",
        "run_distance_km",
        "runDistanceKm",
        "running_distance_km",
        "runningDistanceKm",
        "running_distance",
        "runningDistance",
        "거리_km",
        "거리",
        "총거리",
        "총 거리",
        "러닝거리",
        "러닝 거리",
        "운동거리",
        "운동 거리",
    )

    def data_dir(self):
        return os.environ.get("RUNNINGMATE_DATA_DIR", "/opt/app/data")

    def data_path(self):
        return os.path.join(self.data_dir(), "running_logs.json")

    def runs_migration_marker_path(self):
        return os.path.join(self.data_dir(), "running_logs.json.db_migrated")

    def _runs_storage_mode(self):
        return (os.environ.get("RUNNINGMATE_RUNS_STORAGE") or "db").strip().lower()

    def _runs_json_mirror_enabled(self):
        value = (os.environ.get("RUNNINGMATE_RUNS_JSON_MIRROR") or "true").strip().lower()
        return value in ("1", "true", "yes", "y", "on")

    def _running_log_db(self):
        if self._runs_storage_mode() == "json":
            return None

        try:
            db = wiz.model("portal/season/orm").use("running_log")
            db.orm.create_table(safe=True)
            return db
        except Exception:
            return None

    def _db_date(self, value):
        text = self._date(value)
        if not text:
            return None
        try:
            return datetime.date.fromisoformat(text)
        except Exception:
            return None

    def _db_datetime(self, value):
        if isinstance(value, datetime.datetime):
            dt = value
        elif isinstance(value, datetime.date):
            dt = datetime.datetime.combine(value, datetime.time.min)
        else:
            text = self._text(value)
            if not text:
                return None
            try:
                dt = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
            except Exception:
                return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return dt.replace(microsecond=0)

    def _json_text(self, value):
        if value in (None, "", [], {}):
            return None
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            return None

    def _json_value(self, value, fallback):
        if value in (None, ""):
            return fallback
        if isinstance(value, (list, dict)):
            return value
        try:
            parsed = json.loads(value)
            if fallback is None:
                return parsed if isinstance(parsed, dict) else None
            return parsed if isinstance(parsed, type(fallback)) else fallback
        except Exception:
            return fallback

    def _run_db_payload(self, row):
        run = self.normalize_run(row)
        run_id = self._text(run.get("id"))
        run_date = self._db_date(run.get("date"))
        user_id = self._text(run.get("user_id"))
        if not run_id or not run_date or run.get("distance_km") is None or not user_id:
            return None

        now = datetime.datetime.utcnow().replace(microsecond=0)
        return {
            "id": run_id,
            "user_id": user_id,
            "date": run_date,
            "distance_km": run.get("distance_km"),
            "avg_pace": self._text(run.get("avg_pace")),
            "duration": self._text(run.get("duration")),
            "run_type": self._text(run.get("run_type")),
            "start_time": self._text(run.get("start_time")),
            "calories": run.get("calories"),
            "avg_heart_rate": run.get("avg_heart_rate"),
            "cadence": run.get("cadence"),
            "elevation_gain": run.get("elevation_gain"),
            "water_before_ml": run.get("water_before_ml"),
            "water_after_ml": run.get("water_after_ml"),
            "image_url": self._text(run.get("image_url")),
            "journal": self._journal(run.get("journal")),
            "playlist_name": self._playlist_name(run.get("playlist_name")),
            "music_url": self._music_url(run.get("music_url")),
            "top_tracks": self._json_text(run.get("top_tracks")),
            "is_public": bool(run.get("is_public")),
            "raw_parsed_json": self._json_text(run.get("raw_parsed_json")),
            "created_at": self._db_datetime(run.get("created_at")) or now,
            "updated_at": now,
        }

    def _run_from_db_row(self, row):
        source = dict(row or {})
        if source.get("date"):
            source["date"] = self._date(source.get("date"))
        if source.get("created_at"):
            created = self._db_datetime(source.get("created_at"))
            source["created_at"] = created.isoformat() + "Z" if created else self._text(source.get("created_at"))
        source["top_tracks"] = self._json_value(source.get("top_tracks"), [])
        source["raw_parsed_json"] = self._json_value(source.get("raw_parsed_json"), None)
        return self.normalize_run(source)

    def _load_runs_from_json(self):
        path = self.data_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        normalized = []
        for row in rows:
            run = self.normalize_run(row)
            if run.get("date") and run.get("distance_km") is not None:
                normalized.append(run)
        return normalized

    def _migrate_runs_json_to_db(self, db):
        if db is None or os.path.exists(self.runs_migration_marker_path()):
            return

        rows = self._load_runs_from_json()
        migrated = 0
        for row in rows:
            if not row.get("id"):
                row["id"] = uuid.uuid4().hex
            payload = self._run_db_payload(row)
            if not payload:
                continue
            try:
                db.upsert(payload)
                migrated += 1
            except Exception:
                pass

        try:
            os.makedirs(os.path.dirname(self.runs_migration_marker_path()), exist_ok=True)
            with open(self.runs_migration_marker_path(), "w", encoding="utf-8") as fp:
                json.dump({"migrated": migrated, "created_at": self._utcnow()}, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_runs_from_db(self):
        db = self._running_log_db()
        if db is None:
            return None

        self._migrate_runs_json_to_db(db)
        try:
            rows = db.rows(order="DESC", orderby="date,created_at")
        except Exception:
            return None

        normalized = []
        for row in rows:
            run = self._run_from_db_row(row)
            if run.get("date") and run.get("distance_km") is not None:
                normalized.append(run)
        return normalized

    def _write_runs_to_json(self, rows):
        path = self.data_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        clean_rows = []
        for row in rows:
            clean = dict(row) if isinstance(row, dict) else {}
            clean.pop("media", None)
            clean_rows.append(clean)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(clean_rows, fp, ensure_ascii=False, indent=2)

    def _write_runs_to_db(self, rows):
        db = self._running_log_db()
        if db is None:
            return False

        self._migrate_runs_json_to_db(db)
        payloads = []
        for row in rows:
            clean = dict(row) if isinstance(row, dict) else {}
            clean.pop("media", None)
            payload = self._run_db_payload(clean)
            if payload:
                payloads.append(payload)

        incoming_ids = {payload["id"] for payload in payloads}
        try:
            database = db.orm._meta.database
            database.connect(reuse_if_open=True)
            with database.atomic():
                for payload in payloads:
                    db.upsert(payload)
                for existing in db.rows(fields="id"):
                    if existing.get("id") not in incoming_ids:
                        db.delete(id=existing.get("id"))
            return True
        except Exception:
            return False

    def rest_days_path(self):
        return os.path.join(self.data_dir(), "rest_days.json")

    def day_notes_path(self):
        return os.path.join(self.data_dir(), "day_notes.json")

    def weight_logs_path(self):
        return os.path.join(self.data_dir(), "weight_logs.json")

    def weight_settings_path(self):
        return os.path.join(self.data_dir(), "weight_settings.json")

    def cycle_logs_path(self):
        return os.path.join(self.data_dir(), "cycle_logs.json")

    def cycle_settings_path(self):
        return os.path.join(self.data_dir(), "cycle_settings.json")

    def chat_history_path(self):
        return os.path.join(self.data_dir(), "chat_history.json")

    def ai_usage_path(self):
        return os.path.join(self.data_dir(), "ai_usage.json")

    def ai_rate_limits_path(self):
        return os.path.join(self.data_dir(), "ai_rate_limits.json")

    def goals_path(self):
        return os.path.join(self.data_dir(), "goals.json")

    def challenges_path(self):
        return os.path.join(self.data_dir(), "challenges.json")

    def ranking_social_path(self):
        return os.path.join(self.data_dir(), "ranking_social.json")

    def badges_path(self):
        return os.path.join(self.data_dir(), "badges.json")

    def user_badges_path(self):
        return os.path.join(self.data_dir(), "user_badges.json")

    def run_media_path(self):
        return os.path.join(self.data_dir(), "run_media.json")

    def run_reactions_path(self):
        return os.path.join(self.data_dir(), "run_reactions.json")

    def run_comments_path(self):
        return os.path.join(self.data_dir(), "run_comments.json")

    def notifications_path(self):
        return os.path.join(self.data_dir(), "notifications.json")

    def media_upload_dir(self):
        return os.environ.get("RUNNINGMATE_MEDIA_UPLOAD_DIR", "/opt/app/data/run_media")

    def _upload_url_path(self, url):
        try:
            return wiz.model("security").local_upload_url_path(url)
        except Exception:
            return ""

    def _upload_url_storage_value(self, url):
        path = self._upload_url_path(url)
        return path or self._text(url)

    def signed_upload_payload(self, value):
        if isinstance(value, list):
            return [self.signed_upload_payload(item) for item in value]
        if isinstance(value, dict):
            return {key: self.signed_upload_payload(item) for key, item in value.items()}
        if isinstance(value, str):
            try:
                return wiz.model("security").sign_upload_url(value)
            except Exception:
                return value
        return value

    def _same_upload_url(self, value, target):
        return self._upload_url_path(value) == target

    def _run_file_visible_to_viewer(self, run, viewer_id):
        viewer_id = self._text(viewer_id)
        owner_id = self._account_row_user_id(run)
        if not viewer_id or not owner_id:
            return False
        if owner_id == viewer_id:
            return True
        if (run or {}).get("is_public") is False:
            return False
        try:
            struct = wiz.model("struct")
            owner = struct.user.get(id=owner_id)
            profile = struct.user.public_profile(owner, viewer_id)
            return bool(profile and (profile.get("is_public") or profile.get("is_mutual") or profile.get("is_me")))
        except Exception:
            return False

    def can_access_upload_file(self, upload_type, filename, viewer_id=None):
        filename = os.path.basename(str(filename or ""))
        viewer_id = self._text(viewer_id)
        if not filename or not viewer_id:
            return False

        if upload_type in ("run-image", "run-images", "image"):
            target = f"/api/run-images/{filename}"
            for run in self.load_runs(include_media=False):
                if self._same_upload_url(run.get("image_url"), target):
                    return self._run_file_visible_to_viewer(run, viewer_id)
            return False

        if upload_type in ("run-media", "media"):
            target = f"/api/run-media/{filename}"
            media = next(
                (row for row in self.load_run_media() if self._same_upload_url(row.get("media_url"), target)),
                None,
            )
            if not media:
                return False
            if self._text(media.get("user_id")) == viewer_id:
                return True
            run_id = self._text(media.get("run_id"))
            run = next((row for row in self.load_runs(include_media=False) if row.get("id") == run_id), None)
            return self._run_file_visible_to_viewer(run, viewer_id)

        return False

    def account_data_paths(self):
        return [
            self.data_path(),
            self.rest_days_path(),
            self.day_notes_path(),
            self.weight_logs_path(),
            self.weight_settings_path(),
            self.cycle_logs_path(),
            self.cycle_settings_path(),
            self.chat_history_path(),
            self.ai_usage_path(),
            self.ai_rate_limits_path(),
            self.goals_path(),
            self.challenges_path(),
            self.ranking_social_path(),
            self.user_badges_path(),
            self.run_media_path(),
            self.run_reactions_path(),
            self.run_comments_path(),
            self.notifications_path(),
        ]

    def snapshot_account_data(self):
        snapshot = {}
        for path in self.account_data_paths():
            try:
                snapshot[path] = open(path, "rb").read() if os.path.exists(path) else None
            except Exception:
                snapshot[path] = None
        return snapshot

    def restore_account_data(self, snapshot):
        if not isinstance(snapshot, dict):
            return

        for path, content in snapshot.items():
            try:
                if content is None:
                    if os.path.exists(path):
                        os.unlink(path)
                    continue
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as fp:
                    fp.write(content)
            except Exception:
                pass

    def assign_legacy_records(self, user_id):
        owner_id = self._text(user_id)
        if not owner_id:
            return {}

        summary = {}
        for path in self.account_data_paths():
            payload = self._load_account_json(path, [])
            changed, next_payload = self._assign_legacy_payload(payload, owner_id)
            if changed:
                self._write_account_json(path, next_payload)
            summary[os.path.basename(path)] = changed
        return summary

    def _assign_legacy_payload(self, payload, user_id):
        if isinstance(payload, dict):
            changed = 0
            next_payload = {}
            for key, value in payload.items():
                if isinstance(value, dict):
                    row, did_change = self._assign_legacy_row(value, user_id)
                    next_payload[key] = row
                    changed += did_change
                else:
                    next_payload[key] = value
            return changed, next_payload

        if not isinstance(payload, list):
            return 0, payload

        changed = 0
        rows = []
        for row in payload:
            if isinstance(row, dict):
                next_row, did_change = self._assign_legacy_row(row, user_id)
            else:
                next_row = {"date": row, "user_id": user_id}
                did_change = 1
            rows.append(next_row)
            changed += did_change
        return changed, rows

    def _assign_legacy_row(self, row, user_id):
        next_row = dict(row)
        owner_id = self._account_row_user_id(next_row)
        if owner_id and owner_id != "local-user":
            return next_row, 0
        next_row["user_id"] = user_id
        return next_row, 1

    def delete_account_data(self, user_id, include_legacy=True, delete_files=True):
        user_id = self._text(user_id)
        if not user_id:
            return {"success": False, "message": "삭제할 사용자 정보가 없습니다."}

        snapshot = self.snapshot_account_data()
        try:
            summary = {
                "running_logs": 0,
                "rest_days": 0,
                "day_notes": 0,
                "weight_logs": 0,
                "weight_settings": 0,
                "cycle_logs": 0,
                "cycle_settings": 0,
                "monthly_goals": 0,
                "run_media": 0,
                "reactions": 0,
                "comments": 0,
                "notifications": 0,
                "user_badges": 0,
                "chat_sessions": 0,
                "ai_usage": 0,
                "ai_rate_limits": 0,
                "challenges_deleted": 0,
                "challenges_anonymized": 0,
                "social_relations": 0,
                "files": [],
            }

            deleted_run_ids = self._delete_account_runs(user_id, include_legacy, summary)
            self._delete_account_run_media(user_id, include_legacy, deleted_run_ids, summary)
            self._delete_account_run_social(user_id, include_legacy, deleted_run_ids, summary)
            self._delete_account_collection(self.rest_days_path(), user_id, include_legacy, "rest_days", summary)
            self._delete_account_collection(self.day_notes_path(), user_id, include_legacy, "day_notes", summary)
            self._delete_account_collection(self.weight_logs_path(), user_id, include_legacy, "weight_logs", summary)
            self._delete_account_collection(self.weight_settings_path(), user_id, include_legacy, "weight_settings", summary)
            self._delete_account_collection(self.cycle_logs_path(), user_id, include_legacy, "cycle_logs", summary)
            self._delete_account_collection(self.cycle_settings_path(), user_id, include_legacy, "cycle_settings", summary)
            self._delete_account_collection(self.goals_path(), user_id, include_legacy, "monthly_goals", summary)
            self._delete_account_collection(self.user_badges_path(), user_id, include_legacy, "user_badges", summary)
            self._delete_account_collection(self.chat_history_path(), user_id, include_legacy, "chat_sessions", summary)
            self._delete_account_collection(self.ai_usage_path(), user_id, include_legacy, "ai_usage", summary)
            self._delete_account_collection(self.ai_rate_limits_path(), user_id, include_legacy, "ai_rate_limits", summary)
            self._delete_account_challenges(user_id, summary)
            self._delete_account_social(user_id, summary)

            summary["files"] = sorted(set(summary["files"]))
            if delete_files:
                summary["file_cleanup"] = self.delete_account_files(summary["files"])
            return {"success": True, "data": summary}
        except Exception:
            self.restore_account_data(snapshot)
            raise

    def delete_account_files(self, file_urls):
        result = {"deleted": 0, "missing": 0, "failed": []}
        for url in file_urls or []:
            filepath = self._account_upload_path(url)
            if not filepath:
                continue
            if not os.path.exists(filepath):
                result["missing"] += 1
                continue
            try:
                os.unlink(filepath)
                result["deleted"] += 1
            except Exception:
                result["failed"].append(url)
        return result

    def load_runs(self, include_media=True, user_id=None, include_legacy=False):
        if user_id:
            self.migrate_day_notes_to_journals(user_id)

        normalized = self._load_runs_from_db()
        if normalized is None:
            normalized = self._load_runs_from_json()

        normalized = self._user_scoped_rows(normalized, user_id, include_legacy)
        normalized = sorted(normalized, key=lambda row: row.get("date") or "", reverse=True)
        if include_media:
            media_map = self.run_media_by_run(user_id=user_id, include_legacy=include_legacy)
            for run in normalized:
                run["media"] = media_map.get(run.get("id"), [])

        return normalized

    def load_run_media(self, user_id=None, include_legacy=False):
        path = self.run_media_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        media = []
        for row in rows:
            item = self.normalize_run_media(row)
            if item:
                media.append(item)

        media = self._user_scoped_rows(media, user_id, include_legacy)
        return sorted(media, key=lambda row: row.get("created_at") or "", reverse=True)

    def run_media_by_run(self, user_id=None, include_legacy=False):
        grouped = {}
        for item in self.load_run_media(user_id=user_id, include_legacy=include_legacy):
            grouped.setdefault(item.get("run_id"), []).append(item)
        return grouped

    def load_badges(self):
        rows = []
        path = self.badges_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    loaded = json.load(fp)
                if isinstance(loaded, list):
                    rows = loaded
            except Exception:
                rows = []

        if not rows:
            rows = self.DEFAULT_BADGES

        badges = []
        seen = set()
        for index, row in enumerate(rows, start=1):
            badge = self.normalize_badge(row, index)
            if badge and badge.get("code") not in seen:
                badges.append(badge)
                seen.add(badge.get("code"))

        return badges

    def load_user_badges(self):
        path = self.user_badges_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        user_badges = []
        seen = set()
        for row in rows:
            item = self.normalize_user_badge(row)
            key = (item.get("user_id") if item else "", item.get("badge_code") if item else "")
            if item and key not in seen:
                user_badges.append(item)
                seen.add(key)

        return sorted(user_badges, key=lambda row: row.get("achieved_at") or "", reverse=True)

    def badges_summary(self, user_id=None):
        owner_id = self._text(user_id)
        self.award_badges(owner_id)
        rows = self.load_runs(include_media=False)
        if owner_id:
            rows = self._user_scoped_rows(rows, owner_id)
        earned = {
            row.get("badge_code"): row
            for row in self.load_user_badges()
            if row.get("badge_code")
            and (not owner_id or self._account_row_user_id(row) == owner_id)
        }
        badges = []
        for badge in self.load_badges():
            user_badge = earned.get(badge.get("code"))
            item = dict(badge)
            item["achieved"] = bool(user_badge)
            item["achieved_at"] = user_badge.get("achieved_at") if user_badge else None
            item["progress"] = self.badge_progress(badge, rows)
            badges.append(item)

        earned_count = sum(1 for badge in badges if badge.get("achieved"))
        total_count = len(badges)
        return {
            "data": badges,
            "earned_count": earned_count,
            "total_count": total_count,
            "achievement_rate": round((earned_count / total_count) * 100) if total_count else 0,
            "user_badges": list(earned.values()),
        }

    def public_badges(self, user_id=None, limit=6):
        summary = self.badges_summary(user_id)
        try:
            limit = max(0, int(limit))
        except Exception:
            limit = 6

        earned = [
            badge for badge in summary.get("data", [])
            if badge.get("achieved")
        ]
        return {
            "badges": earned[:limit] if limit else earned,
            "earned_badge_count": summary.get("earned_count", len(earned)),
            "total_badge_count": summary.get("total_count", len(summary.get("data", []))),
            "achievement_rate": summary.get("achievement_rate", 0),
        }

    def award_badges(self, user_id=None):
        owner_id = self._text(user_id)
        rows = self.load_runs(include_media=False)
        if owner_id:
            rows = self._user_scoped_rows(rows, owner_id)
        badges = self.load_badges()
        all_current = self.load_user_badges()
        current = [
            row for row in all_current
            if not owner_id or self._account_row_user_id(row) == owner_id
        ]
        earned_codes = {row.get("badge_code") for row in current}
        newly_earned = []
        now = self._utcnow()

        for badge in badges:
            code = badge.get("code")
            if not code or code in earned_codes:
                continue
            if not self._badge_condition_met(badge, rows):
                continue

            user_badge = {
                "id": uuid.uuid4().hex,
                "badge_code": code,
                "achieved_at": now,
                "user_id": owner_id,
            }
            current.append(user_badge)
            all_current.append(user_badge)
            earned_codes.add(code)

            item = dict(badge)
            item["achieved"] = True
            item["achieved_at"] = now
            item["progress"] = self.badge_progress(badge, rows)
            newly_earned.append(item)

        if newly_earned:
            self._write_user_badges(all_current)

        return newly_earned

    def normalize_badge(self, row, fallback_id=None):
        source = row if isinstance(row, dict) else {}
        code = self._text(source.get("code"))
        title = self._text(source.get("title"))
        condition_type = self._text(source.get("condition_type"))
        threshold = self._number(source.get("threshold"))
        if not code or not title or not condition_type or threshold is None:
            return None

        badge_id = source.get("id")
        if badge_id is None or badge_id == "":
            badge_id = fallback_id or code

        return {
            "id": badge_id,
            "code": code,
            "title": title,
            "description": self._text(source.get("description")) or "",
            "icon": self._text(source.get("icon")) or "fa-medal",
            "condition_type": condition_type,
            "threshold": int(threshold) if float(threshold).is_integer() else threshold,
        }

    def normalize_user_badge(self, row):
        source = row if isinstance(row, dict) else {}
        badge_code = self._text(source.get("badge_code") or source.get("badgeCode"))
        achieved_at = self._text(source.get("achieved_at") or source.get("achievedAt"))
        if not badge_code or not achieved_at:
            return None

        return {
            "id": self._text(source.get("id")) or uuid.uuid4().hex,
            "badge_code": badge_code,
            "achieved_at": achieved_at,
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def badge_progress(self, badge, rows=None):
        rows = rows if rows is not None else self.load_runs(include_media=False)
        condition_type = badge.get("condition_type")
        threshold = self._number(badge.get("threshold")) or 1
        current = self._badge_current_value(condition_type, rows, threshold)
        capped = min(current, threshold)
        percent = round((capped / threshold) * 100) if threshold else 0
        return {
            "current": round(current, 2),
            "threshold": int(threshold) if float(threshold).is_integer() else threshold,
            "percent": max(0, min(100, percent)),
            "label": self._badge_progress_label(condition_type, current, threshold),
        }

    def run_detail(self, run_id, user_id=None):
        run_id = self._text(run_id)
        if not run_id:
            return None
        return next((row for row in self.load_runs(include_media=True, user_id=user_id) if row.get("id") == run_id), None)

    def load_run_reactions(self):
        rows = self._load_account_json(self.run_reactions_path(), [])
        if not isinstance(rows, list):
            return []

        reactions = {}
        for row in rows:
            reaction = self.normalize_run_reaction(row)
            if not reaction:
                continue
            key = (reaction.get("run_id"), reaction.get("user_id"), reaction.get("type"))
            current = reactions.get(key)
            if not current or (reaction.get("created_at") or "") >= (current.get("created_at") or ""):
                reactions[key] = reaction

        return sorted(reactions.values(), key=lambda row: row.get("created_at") or "", reverse=True)

    def load_run_comments(self):
        rows = self._load_account_json(self.run_comments_path(), [])
        if not isinstance(rows, list):
            return []

        comments = []
        seen = set()
        for row in rows:
            comment = self.normalize_run_comment(row)
            if not comment:
                continue
            if comment.get("id") in seen:
                continue
            comments.append(comment)
            seen.add(comment.get("id"))

        return sorted(comments, key=lambda row: row.get("created_at") or "")

    def load_notifications(self, user_id=None, limit=50):
        owner_id = self._text(user_id)
        rows = self._load_account_json(self.notifications_path(), [])
        if not isinstance(rows, list):
            return []

        notifications = []
        for row in rows:
            item = self.normalize_notification(row)
            if item and (not owner_id or item.get("user_id") == owner_id):
                notifications.append(item)

        try:
            limit = max(1, int(limit))
        except Exception:
            limit = 50
        return sorted(notifications, key=lambda row: row.get("created_at") or "", reverse=True)[:limit]

    def mark_notifications_read(self, user_id, notification_id=None):
        owner_id = self._text(user_id)
        target_id = self._text(notification_id)
        if not owner_id:
            return []

        rows = self.load_notifications(limit=500)
        changed = False
        now = self._utcnow()
        next_rows = []
        for row in rows:
            item = dict(row)
            if item.get("user_id") == owner_id and (not target_id or item.get("id") == target_id):
                if not item.get("read_at"):
                    item["read_at"] = now
                    changed = True
            next_rows.append(item)

        if changed:
            self._write_notifications(next_rows)
        return self.load_notifications(owner_id)

    def normalize_run_reaction(self, row):
        source = row if isinstance(row, dict) else {}
        run_id = self._text(source.get("run_id") or source.get("runId"))
        user_id = self._text(source.get("user_id") or source.get("userId"))
        reaction_type = self._reaction_type(source.get("type") or source.get("reaction"))
        if not run_id or not user_id or not reaction_type:
            return None

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "run_id": run_id,
            "user_id": user_id,
            "type": reaction_type,
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "user_name": self._text(source.get("user_name") or source.get("userName") or source.get("name")) or "",
            "profile_image": self._text(source.get("profile_image") or source.get("profileImage")) or "",
        }

    def normalize_run_comment(self, row):
        source = row if isinstance(row, dict) else {}
        run_id = self._text(source.get("run_id") or source.get("runId"))
        user_id = self._text(source.get("user_id") or source.get("userId"))
        content = self._comment_content(source.get("content") or source.get("text") or source.get("comment"))
        if not run_id or not user_id or not content:
            return None

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "run_id": run_id,
            "user_id": user_id,
            "content": content,
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "user_name": self._text(source.get("user_name") or source.get("userName") or source.get("name")) or "",
            "profile_image": self._text(source.get("profile_image") or source.get("profileImage")) or "",
        }

    def normalize_notification(self, row):
        source = row if isinstance(row, dict) else {}
        user_id = self._text(source.get("user_id") or source.get("userId"))
        actor_id = self._text(source.get("actor_id") or source.get("actorId"))
        run_id = self._text(source.get("run_id") or source.get("runId"))
        notice_type = self._text(source.get("type"))
        if not user_id or not actor_id or notice_type not in ("follow", "reaction", "comment"):
            return None
        if notice_type != "follow" and not run_id:
            return None
        actor_name = self._text(source.get("actor_name") or source.get("actorName")) or "러너"
        message = self._text(source.get("message"))
        if not message:
            if notice_type == "follow":
                message = f"{actor_name}님이 팔로우하기 시작했어."
            elif notice_type == "comment":
                message = f"{actor_name}님이 내 러닝에 댓글을 남겼어."
            else:
                message = f"{actor_name}님이 내 러닝을 응원했어."

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "user_id": user_id,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "run_id": run_id,
            "type": notice_type,
            "reaction_type": self._reaction_type(source.get("reaction_type") or source.get("reactionType")),
            "comment_id": self._text(source.get("comment_id") or source.get("commentId")),
            "message": message,
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "read_at": self._text(source.get("read_at") or source.get("readAt")),
        }

    def run_social_state(self, run_id, viewer_id="", users_by_id=None):
        run_id = self._text(run_id)
        if not run_id:
            return None

        return {
            "run_id": run_id,
            "reaction_summary": self.reaction_summary_for_run(run_id, viewer_id, users_by_id),
            "reaction_count": sum(1 for row in self.load_run_reactions() if row.get("run_id") == run_id),
            "comment_count": sum(1 for row in self.load_run_comments() if row.get("run_id") == run_id),
            "comments": self.comments_for_run(run_id, viewer_id, users_by_id),
        }

    def reaction_summary_for_run(self, run_id, viewer_id="", users_by_id=None):
        run_id = self._text(run_id)
        viewer_id = self._text(viewer_id) or ""
        users_by_id = users_by_id if isinstance(users_by_id, dict) else {}
        grouped = {
            reaction_type: {
                "type": reaction_type,
                "emoji": self.REACTION_META[reaction_type]["emoji"],
                "label": self.REACTION_META[reaction_type]["label"],
                "count": 0,
                "reacted": False,
                "users": [],
            }
            for reaction_type in self.REACTION_TYPES
        }

        for reaction in self.load_run_reactions():
            if reaction.get("run_id") != run_id:
                continue
            reaction_type = reaction.get("type")
            item = grouped.get(reaction_type)
            if not item:
                continue
            item["count"] += 1
            if reaction.get("user_id") == viewer_id:
                item["reacted"] = True
            item["users"].append(self._reaction_user_payload(reaction, users_by_id, viewer_id))

        return [grouped[reaction_type] for reaction_type in self.REACTION_TYPES]

    def comments_for_run(self, run_id, viewer_id="", users_by_id=None):
        run_id = self._text(run_id)
        viewer_id = self._text(viewer_id) or ""
        users_by_id = users_by_id if isinstance(users_by_id, dict) else {}
        comments = []
        for comment in self.load_run_comments():
            if comment.get("run_id") != run_id:
                continue
            comments.append(self._comment_payload(comment, users_by_id, viewer_id))
        return comments

    def save_run_reaction(self, run_id, user_id, reaction_type, user_name="", profile_image=""):
        run = self.run_detail(run_id)
        actor_id = self._text(user_id)
        reaction_type = self._reaction_type(reaction_type)
        if not run:
            return None, "러닝 기록을 찾지 못했습니다."
        if not actor_id:
            return None, "로그인이 필요합니다."
        if not reaction_type:
            return None, "지원하지 않는 반응입니다."

        rows = self.load_run_reactions()
        existing = next(
            (
                row for row in rows
                if row.get("run_id") == run.get("id")
                and row.get("user_id") == actor_id
                and row.get("type") == reaction_type
            ),
            None,
        )
        if existing:
            return existing, None

        item = {
            "id": str(uuid.uuid4()),
            "run_id": run.get("id"),
            "user_id": actor_id,
            "type": reaction_type,
            "created_at": self._utcnow(),
            "user_name": self._text(user_name) or "",
            "profile_image": self._text(profile_image) or "",
        }
        rows.insert(0, item)
        self._write_run_reactions(rows)
        self._create_run_notification("reaction", run, actor_id, item.get("user_name"), reaction_type=reaction_type)
        return item, None

    def delete_run_reaction(self, run_id, user_id, reaction_type):
        run_id = self._text(run_id)
        actor_id = self._text(user_id)
        reaction_type = self._reaction_type(reaction_type)
        if not run_id or not actor_id or not reaction_type:
            return False

        rows = self.load_run_reactions()
        next_rows = [
            row for row in rows
            if not (
                row.get("run_id") == run_id
                and row.get("user_id") == actor_id
                and row.get("type") == reaction_type
            )
        ]
        if len(next_rows) == len(rows):
            return False

        self._write_run_reactions(next_rows)
        return True

    def save_run_comment(self, run_id, user_id, content, user_name="", profile_image=""):
        run = self.run_detail(run_id)
        actor_id = self._text(user_id)
        text = self._comment_content(content)
        if not run:
            return None, "러닝 기록을 찾지 못했습니다."
        if not actor_id:
            return None, "로그인이 필요합니다."
        if not text:
            return None, "댓글을 입력해주세요."

        item = {
            "id": str(uuid.uuid4()),
            "run_id": run.get("id"),
            "user_id": actor_id,
            "content": text,
            "created_at": self._utcnow(),
            "user_name": self._text(user_name) or "",
            "profile_image": self._text(profile_image) or "",
        }
        rows = self.load_run_comments()
        rows.append(item)
        self._write_run_comments(rows)
        self._create_run_notification("comment", run, actor_id, item.get("user_name"), comment_id=item.get("id"))
        return item, None

    def delete_run_comment(self, run_id, comment_id, user_id):
        run_id = self._text(run_id)
        comment_id = self._text(comment_id)
        actor_id = self._text(user_id)
        if not run_id or not comment_id or not actor_id:
            return False, "삭제할 댓글을 찾지 못했습니다."

        rows = self.load_run_comments()
        target = next((row for row in rows if row.get("id") == comment_id and row.get("run_id") == run_id), None)
        if not target:
            return False, "삭제할 댓글을 찾지 못했습니다."
        if target.get("user_id") != actor_id:
            return False, "내가 작성한 댓글만 삭제할 수 있습니다."

        self._write_run_comments([row for row in rows if row.get("id") != comment_id])
        return True, ""

    def feed(self, viewer_id, following_ids, users_by_id=None, limit=20):
        viewer_id = self._text(viewer_id) or ""
        users_by_id = users_by_id if isinstance(users_by_id, dict) else {}
        follow_set = {
            self._text(user_id)
            for user_id in (following_ids or [])
            if self._text(user_id)
        }

        try:
            limit = min(100, max(1, int(limit)))
        except Exception:
            limit = 20

        items = []
        for run in self.load_runs(include_media=True):
            owner_id = self._text(run.get("user_id") or run.get("userId"))
            if not owner_id or owner_id not in follow_set:
                continue
            if run.get("is_public") is False:
                continue
            user = users_by_id.get(owner_id) or {}
            if user and user.get("is_public") is False and not user.get("is_mutual") and not user.get("is_me"):
                continue
            item = self._feed_run_payload(run, viewer_id, users_by_id)
            if item:
                items.append(item)
            if len(items) >= limit:
                break

        return items

    def social_cheer_context(self, user_id=None, limit=5):
        owner_id = self._text(user_id)
        if not owner_id:
            return {
                "reaction_count": 0,
                "comment_count": 0,
                "summary": "아직 친구 응원 데이터가 없어.",
                "recent": [],
            }

        runs = [
            row for row in self.load_runs(include_media=False)
            if self._account_row_user_id(row) == owner_id
        ]
        run_ids = {row.get("id") for row in runs if row.get("id")}
        reactions = [
            row for row in self.load_run_reactions()
            if row.get("run_id") in run_ids and row.get("user_id") != owner_id
        ]
        comments = [
            row for row in self.load_run_comments()
            if row.get("run_id") in run_ids and row.get("user_id") != owner_id
        ]
        recent = []
        for row in reactions[:limit]:
            meta = self.REACTION_META.get(row.get("type"), {})
            recent.append({
                "type": "reaction",
                "run_id": row.get("run_id"),
                "actor_name": row.get("user_name") or "친구",
                "reaction_type": row.get("type"),
                "emoji": meta.get("emoji") or "",
                "created_at": row.get("created_at"),
            })
        for row in sorted(comments, key=lambda item: item.get("created_at") or "", reverse=True)[:limit]:
            recent.append({
                "type": "comment",
                "run_id": row.get("run_id"),
                "actor_name": row.get("user_name") or "친구",
                "content": row.get("content"),
                "created_at": row.get("created_at"),
            })
        recent = sorted(recent, key=lambda item: item.get("created_at") or "", reverse=True)[:limit]

        reaction_count = len(reactions)
        comment_count = len(comments)
        if reaction_count or comment_count:
            summary = f"친구들이 최근 내 기록에 반응 {reaction_count}개, 댓글 {comment_count}개를 남겼어."
        else:
            summary = "아직 친구 응원 데이터가 없어."
        return {
            "reaction_count": reaction_count,
            "comment_count": comment_count,
            "summary": summary,
            "recent": recent,
        }

    def _reaction_user_payload(self, reaction, users_by_id, viewer_id=""):
        user_id = self._text(reaction.get("user_id"))
        user = users_by_id.get(user_id) if isinstance(users_by_id, dict) else None
        user = user if isinstance(user, dict) else {}
        return {
            "user_id": user_id,
            "name": self._text(user.get("name") or reaction.get("user_name")) or ("나" if user_id == viewer_id else "러너"),
            "profile_image": self._text(user.get("profile_image") or reaction.get("profile_image")) or "",
            "type": reaction.get("type"),
            "created_at": reaction.get("created_at"),
            "is_me": bool(viewer_id and user_id == viewer_id),
        }

    def _comment_payload(self, comment, users_by_id, viewer_id=""):
        user_id = self._text(comment.get("user_id"))
        user = users_by_id.get(user_id) if isinstance(users_by_id, dict) else None
        user = user if isinstance(user, dict) else {}
        return {
            "id": comment.get("id"),
            "run_id": comment.get("run_id"),
            "user_id": user_id,
            "user_name": self._text(user.get("name") or comment.get("user_name")) or ("나" if user_id == viewer_id else "러너"),
            "profile_image": self._text(user.get("profile_image") or comment.get("profile_image")) or "",
            "content": comment.get("content") or "",
            "created_at": comment.get("created_at"),
            "is_mine": bool(viewer_id and user_id == viewer_id),
        }

    def _feed_run_payload(self, run, viewer_id="", users_by_id=None):
        if not isinstance(run, dict):
            return None
        users_by_id = users_by_id if isinstance(users_by_id, dict) else {}
        owner_id = self._text(run.get("user_id") or run.get("userId"))
        if not owner_id:
            return None

        user = users_by_id.get(owner_id) or {}
        state = self.run_social_state(run.get("id"), viewer_id, users_by_id) or {}
        payload = dict(run)
        payload["user"] = {
            "id": owner_id,
            "name": self._text(user.get("name")) or ("나" if owner_id == viewer_id else "러너"),
            "display_id": self._text(user.get("display_id") or user.get("email")) or owner_id,
            "profile_image": self._text(user.get("profile_image")) or "",
            "is_me": bool(viewer_id and owner_id == viewer_id),
        }
        payload["reaction_summary"] = state.get("reaction_summary") or self.reaction_summary_for_run(run.get("id"), viewer_id, users_by_id)
        payload["reaction_count"] = state.get("reaction_count") or 0
        payload["comment_count"] = state.get("comment_count") or 0
        payload["comments"] = state.get("comments") or []
        return payload

    def _create_run_notification(self, notice_type, run, actor_id, actor_name="", reaction_type=None, comment_id=None):
        if not isinstance(run, dict):
            return None
        recipient_id = self._account_row_user_id(run)
        actor_id = self._text(actor_id)
        if not recipient_id or not actor_id or recipient_id == actor_id:
            return None

        actor_name = self._text(actor_name) or "친구"
        meta = self.REACTION_META.get(reaction_type or "", {})
        if notice_type == "reaction":
            message = f"{actor_name}님이 내 러닝에 {meta.get('emoji') or '응원'} 반응을 남겼어."
        elif notice_type == "comment":
            message = f"{actor_name}님이 내 러닝에 댓글을 남겼어."
        else:
            return None

        item = {
            "id": str(uuid.uuid4()),
            "user_id": recipient_id,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "run_id": run.get("id"),
            "type": notice_type,
            "reaction_type": reaction_type,
            "comment_id": comment_id,
            "message": message,
            "created_at": self._utcnow(),
            "read_at": None,
        }
        rows = self.load_notifications(limit=500)
        rows.insert(0, item)
        self._write_notifications(rows[:500])
        return item

    def create_follow_notification(self, recipient_id, actor_id, actor_name=""):
        recipient_id = self._text(recipient_id)
        actor_id = self._text(actor_id)
        if not recipient_id or not actor_id or recipient_id == actor_id:
            return None

        actor_name = self._text(actor_name) or "러너"
        item = {
            "id": str(uuid.uuid4()),
            "user_id": recipient_id,
            "actor_id": actor_id,
            "actor_name": actor_name,
            "run_id": "",
            "type": "follow",
            "reaction_type": "",
            "comment_id": "",
            "message": f"{actor_name}님이 팔로우하기 시작했어.",
            "created_at": self._utcnow(),
            "read_at": None,
        }
        rows = self.load_notifications(limit=500)
        rows.insert(0, item)
        self._write_notifications(rows[:500])
        return item

    def load_rest_days(self, user_id=None, include_legacy=False):
        path = self.rest_days_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        dates = []
        for row in rows:
            if user_id and not self._row_belongs_to_user(row if isinstance(row, dict) else {}, self._text(user_id), include_legacy):
                continue
            value = row.get("date") if isinstance(row, dict) else row
            date = self._date(value)
            if date:
                dates.append(date)

        return sorted(set(dates))

    def load_day_notes(self, user_id=None, include_legacy=False):
        path = self.day_notes_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if isinstance(rows, dict):
            rows = [{"date": key, "memo": value} for key, value in rows.items()]
        if not isinstance(rows, list):
            return []

        notes = {}
        for row in rows:
            note = self.normalize_day_note(row)
            if user_id and note and not self._row_belongs_to_user(note, self._text(user_id), include_legacy):
                continue
            if note:
                notes[(note.get("user_id"), note["date"])] = note

        return [notes[key] for key in sorted(notes.keys(), key=lambda key: key[1])]

    def normalize_day_note(self, row):
        source = row if isinstance(row, dict) else {}
        date = self._date(source.get("date"))
        memo = self._text(source.get("memo") or source.get("note") or source.get("text"))
        if not date or not memo:
            return None

        return {
            "date": date,
            "memo": memo[:2000],
            "updated_at": self._text(source.get("updated_at")) or self._utcnow(),
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def day_note(self, value, user_id=None):
        date = self._date(value)
        if not date:
            return None

        return next((row for row in self.load_day_notes(user_id=user_id) if row.get("date") == date), None)

    def save_day_note(self, value, memo, user_id=None):
        date = self._date(value)
        if not date:
            return False, "메모 날짜가 올바르지 않습니다.", None, self.load_day_notes(user_id)

        owner_id = self._text(user_id)
        if not owner_id:
            return False, "사용자 정보가 없습니다.", None, self.load_day_notes(user_id)

        text = self._text(memo)
        if not text:
            self.delete_day_note(date, owner_id)
            return True, "", None, self.load_day_notes(owner_id)

        note = {
            "date": date,
            "memo": text[:2000],
            "updated_at": self._utcnow(),
            "user_id": owner_id,
        }
        notes = [
            row for row in self.load_day_notes()
            if row.get("date") != date or (
                self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id
            )
        ]
        notes.append(note)
        self._write_day_notes(notes)
        return True, "", note, self.load_day_notes(owner_id)

    def delete_day_note(self, value, user_id=None):
        date = self._date(value)
        if not date:
            return False

        owner_id = self._text(user_id)
        notes = [
            row for row in self.load_day_notes()
            if row.get("date") != date or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        self._write_day_notes(notes)
        return True

    def migrate_day_notes_to_journals(self, user_id=None):
        owner_id = self._text(user_id)
        if not owner_id:
            return 0

        notes_rows = self._load_account_json(self.day_notes_path(), [])
        if isinstance(notes_rows, dict):
            notes_rows = [{"date": key, "memo": value} for key, value in notes_rows.items()]
        if not isinstance(notes_rows, list) or not notes_rows:
            return 0

        notes_by_date = {}
        remaining_notes = []
        for row in notes_rows:
            note = self.normalize_day_note(row)
            if note and self._row_belongs_to_user(note, owner_id, include_legacy=True):
                notes_by_date[note["date"]] = note
            else:
                remaining_notes.append(row)

        if not notes_by_date:
            return 0

        run_rows = self._load_runs_from_db()
        if run_rows is None:
            run_rows = self._load_runs_from_json()
        if not isinstance(run_rows, list):
            self._write_day_notes(remaining_notes)
            return 0

        migrated = 0
        for date, note in notes_by_date.items():
            target_index = None
            for index, row in enumerate(run_rows):
                run = self.normalize_run(row)
                if (
                    run.get("date") == date
                    and self._row_belongs_to_user(run, owner_id, include_legacy=False)
                ):
                    target_index = index
                    break

            if target_index is None:
                remaining_notes.append(note)
                continue

            current = dict(run_rows[target_index]) if isinstance(run_rows[target_index], dict) else {}
            memo = note.get("memo") or ""
            existing = self._journal(current.get("journal"))
            if existing and memo and memo not in existing:
                current["journal"] = f"{existing}\n\n{memo}"
            elif memo:
                current["journal"] = existing or memo
            run_rows[target_index] = current
            migrated += 1

        if migrated:
            self._write_runs(run_rows)
        self._write_day_notes(remaining_notes)
        return migrated

    def load_weights(self, period=None, user_id=None, include_legacy=False):
        path = self.weight_logs_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if isinstance(rows, dict):
            rows = [{"date": key, "weight_kg": value} for key, value in rows.items()]
        if not isinstance(rows, list):
            return []

        logs = {}
        for row in rows:
            log = self.normalize_weight_log(row)
            if user_id and log and not self._row_belongs_to_user(log, self._text(user_id), include_legacy):
                continue
            if log:
                logs[(log.get("user_id"), log["date"])] = log

        weights = sorted(logs.values(), key=lambda row: row.get("date") or "", reverse=True)
        start = self._period_start(period)
        if start:
            weights = [row for row in weights if row.get("date") >= start]
        return weights

    def normalize_weight_log(self, row):
        source = row if isinstance(row, dict) else {}
        date = self._date(source.get("date"))
        weight = self._weight(source.get("weight_kg", source.get("weightKg", source.get("weight"))))
        if not date or weight is None:
            return None

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "date": date,
            "weight_kg": weight,
            "created_at": self._text(source.get("created_at")) or self._utcnow(),
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def load_weight_settings(self, user_id=None, include_legacy=False):
        rows = self._load_weight_settings_rows()
        owner_id = self._text(user_id)
        if owner_id:
            rows = [
                row for row in rows
                if self._row_belongs_to_user(row, owner_id, include_legacy)
            ]
        if not rows:
            return {
                "target_weight_kg": None,
                "updated_at": "",
                "user_id": owner_id,
            }

        rows = sorted(rows, key=lambda row: row.get("updated_at") or "", reverse=True)
        settings = rows[0]
        return {
            "target_weight_kg": settings.get("target_weight_kg"),
            "updated_at": settings.get("updated_at") or "",
            "user_id": settings.get("user_id") or owner_id,
        }

    def save_weight_settings(self, payload, user_id=None):
        source = payload if isinstance(payload, dict) else {}
        owner_id = self._text(user_id or source.get("user_id") or source.get("userId"))
        target = self._weight(
            source.get("target_weight_kg")
            if "target_weight_kg" in source
            else source.get("targetWeightKg") if "targetWeightKg" in source else source.get("target_weight")
        )

        if not owner_id:
            return None, "사용자 정보가 없습니다."
        if target is None:
            return None, "목표 체중은 0.1kg 단위의 숫자로 입력해주세요."

        settings = {
            "target_weight_kg": target,
            "updated_at": self._utcnow(),
            "user_id": owner_id,
        }
        rows = self._load_weight_settings_rows()
        next_rows = [
            row for row in rows
            if self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id
        ]
        next_rows.append(settings)
        self._write_weight_settings(next_rows)
        return settings, None

    def save_weight(self, payload):
        source = payload if isinstance(payload, dict) else {}
        date = self._date(source.get("date")) or datetime.date.today().isoformat()
        weight = self._weight(source.get("weight_kg", source.get("weightKg", source.get("weight"))))
        owner_id = self._text(source.get("user_id") or source.get("userId"))

        if not date:
            return None, "체중 기록 날짜가 올바르지 않습니다."
        if weight is None:
            return None, "체중은 0.1kg 단위의 숫자로 입력해주세요."
        if not owner_id:
            return None, "사용자 정보가 없습니다."

        rows = self.load_weights()
        previous = next(
            (
                row for row in rows
                if row.get("date") == date
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            ),
            None,
        )
        log = {
            "id": (previous or {}).get("id") or str(uuid.uuid4()),
            "date": date,
            "weight_kg": weight,
            "created_at": (previous or {}).get("created_at") or self._utcnow(),
            "user_id": owner_id,
        }

        next_rows = [
            row for row in rows
            if row.get("date") != date or (
                self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id
            )
        ]
        next_rows.append(log)
        self._write_weights(next_rows)
        return log, None

    def delete_weight(self, value, user_id=None):
        date = self._date(value)
        if not date:
            return False

        owner_id = self._text(user_id)
        rows = self.load_weights()
        next_rows = [
            row for row in rows
            if row.get("date") != date or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        if len(next_rows) == len(rows):
            return False

        self._write_weights(next_rows)
        return True

    def weight_summary(self, period="3m", user_id=None):
        all_logs = sorted(self.load_weights(user_id=user_id), key=lambda row: row.get("date") or "")
        period_logs = sorted(self.load_weights(period, user_id=user_id), key=lambda row: row.get("date") or "")
        if not all_logs:
            return {
                "latest": None,
                "start": None,
                "change_kg": None,
                "period": period,
                "period_count": 0,
                "recent": [],
            }

        latest = all_logs[-1]
        start = all_logs[0]
        change = round(latest.get("weight_kg") - start.get("weight_kg"), 1)
        return {
            "latest": latest,
            "start": start,
            "change_kg": change,
            "period": period,
            "period_count": len(period_logs),
            "recent": list(reversed(period_logs[-8:])),
        }

    def load_cycles(self, user_id=None, include_legacy=False):
        path = self.cycle_logs_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        logs = {}
        for row in rows:
            log = self.normalize_cycle_log(row)
            if user_id and log and not self._row_belongs_to_user(log, self._text(user_id), include_legacy):
                continue
            if log:
                logs[log["id"]] = log

        return sorted(logs.values(), key=lambda row: row.get("start_date") or "", reverse=True)

    def load_cycle_settings(self, user_id=None, include_legacy=False):
        rows = self._load_cycle_settings_rows()
        owner_id = self._text(user_id)
        if owner_id:
            rows = [
                row for row in rows
                if self._row_belongs_to_user(row, owner_id, include_legacy)
            ]
        return sorted(rows, key=lambda row: row.get("updated_at") or "", reverse=True)

    def cycle_setting(self, user_id=None):
        owner_id = self._text(user_id)
        rows = self.load_cycle_settings(owner_id) if owner_id else []
        if not rows:
            return {
                "enabled": False,
                "configured": False,
                "updated_at": "",
                "user_id": owner_id,
            }

        setting = rows[0]
        return {
            "enabled": bool(setting.get("enabled")),
            "configured": True,
            "updated_at": setting.get("updated_at") or "",
            "user_id": setting.get("user_id") or owner_id,
        }

    def save_cycle_setting(self, payload=None, user_id=None):
        source = payload if isinstance(payload, dict) else {}
        owner_id = self._text(user_id or source.get("user_id") or source.get("userId"))
        if not owner_id:
            return None, "사용자 정보가 없습니다."

        enabled_value = source.get("enabled")
        if enabled_value is None:
            enabled_value = source.get("cycle_enabled", source.get("cycleEnabled"))

        setting = {
            "enabled": self._bool(enabled_value),
            "updated_at": self._utcnow(),
            "user_id": owner_id,
        }
        rows = self._load_cycle_settings_rows()
        next_rows = [
            row for row in rows
            if self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id
        ]
        next_rows.append(setting)
        self._write_cycle_settings(next_rows)
        return self.cycle_setting(owner_id), None

    def normalize_cycle_log(self, row):
        source = row if isinstance(row, dict) else {}
        start_date = self._date(source.get("start_date", source.get("startDate")))
        end_date = self._date(source.get("end_date", source.get("endDate"))) or start_date
        phase = self._cycle_phase(source.get("cycle_phase", source.get("cyclePhase")))
        flow_level = self._cycle_flow_level(source.get("flow_level", source.get("flowLevel", source.get("flow"))))
        condition_emoji = self._cycle_condition_emoji(
            source.get("condition_emoji", source.get("conditionEmoji", source.get("condition")))
        )
        note = self._text(source.get("note"))

        if not start_date or not end_date:
            return None
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "start_date": start_date,
            "end_date": end_date,
            "cycle_phase": phase,
            "flow_level": flow_level,
            "condition_emoji": condition_emoji,
            "note": note[:2000] if note else "",
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def save_cycle(self, payload):
        source = payload if isinstance(payload, dict) else {}
        owner_id = self._text(source.get("user_id") or source.get("userId"))
        if not owner_id:
            return None, "사용자 정보가 없습니다."

        log = self.normalize_cycle_log(payload)
        if not log:
            return None, "주기 기록 날짜가 올바르지 않습니다."
        log["user_id"] = owner_id
        log["cycle_phase"] = "menstrual"

        requested_id = self._text(source.get("id"))
        rows = self.load_cycles()
        previous = next(
            (
                row for row in rows
                if requested_id
                and row.get("id") == requested_id
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            ),
            None,
        ) or next(
            (
                row for row in rows
                if row.get("cycle_phase") == "menstrual"
                and row.get("start_date") == log.get("start_date")
                and row.get("end_date") == log.get("end_date")
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            ),
            None,
        )
        if previous:
            log["id"] = previous.get("id")

        next_rows = [
            row for row in rows
            if row.get("id") != log.get("id") or (
                self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id
            )
        ]
        next_rows.append(log)
        self._write_cycles(next_rows)
        return log, None

    def delete_cycle(self, cycle_id=None, delete_all=False, user_id=None):
        owner_id = self._text(user_id)
        if delete_all:
            if not owner_id:
                self._write_cycles([])
            else:
                self._write_cycles([
                    row for row in self.load_cycles()
                    if self._account_row_user_id(row) != owner_id
                ])
            return True

        cycle_id = self._text(cycle_id)
        if not cycle_id:
            return False

        rows = self.load_cycles()
        next_rows = [
            row for row in rows
            if row.get("id") != cycle_id or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        if len(next_rows) == len(rows):
            return False

        self._write_cycles(next_rows)
        return True

    def cycle_summary(self, user_id=None):
        logs = self.load_cycles(user_id=user_id)
        menstrual_logs = [
            row for row in logs
            if row.get("cycle_phase") == "menstrual" and self._cycle_flow_level(row.get("flow_level")) != "none"
        ]
        menstrual_windows = self._cycle_menstrual_windows(logs)
        cycle_lengths = []
        period_lengths = []

        for index, row in enumerate(menstrual_windows):
            start = self._date_obj(row.get("start_date"))
            end = self._date_obj(row.get("end_date"))
            if start and end:
                period_length = max(1, (end - start).days + 1)
                if period_length >= 1 and end < datetime.date.today():
                    period_lengths.append(period_length)
            if index > 0:
                prev = self._date_obj(menstrual_windows[index - 1].get("start_date"))
                if start and prev:
                    length = (start - prev).days
                    if 15 <= length <= 60:
                        cycle_lengths.append(length)

        average_cycle_days = round(sum(cycle_lengths) / len(cycle_lengths)) if cycle_lengths else 28
        average_period_days = max(1, min(12, round(sum(period_lengths) / len(period_lengths)))) if period_lengths else self.DEFAULT_PERIOD_DAYS
        latest = menstrual_windows[-1] if menstrual_windows else None
        next_start_date = None
        current_phase = None
        current_phase_label = None

        if latest:
            latest_start = self._date_obj(latest.get("start_date"))
            if latest_start:
                next_start_date = (latest_start + datetime.timedelta(days=average_cycle_days)).isoformat()
            today = datetime.date.today().isoformat()
            current_phase = self.cycle_phase_for_date(today, logs, average_cycle_days, average_period_days)
            current_phase_label = self.CYCLE_PHASE_LABELS.get(current_phase)

        return {
            "average_cycle_days": average_cycle_days,
            "average_period_days": average_period_days,
            "next_start_date": next_start_date,
            "current_phase": current_phase,
            "current_phase_label": current_phase_label,
            "log_count": len(logs),
            "menstrual_log_count": len(menstrual_logs),
        }

    def cycle_phase_for_date(self, value, logs=None, average_cycle_days=None, average_period_days=None):
        date = self._date_obj(value)
        if not date:
            return None

        logs = logs if logs is not None else self.load_cycles()
        menstrual_windows = self._cycle_menstrual_windows(logs)
        if not menstrual_windows:
            return None

        if average_cycle_days is None or average_period_days is None:
            summary = self.cycle_summary()
            average_cycle_days = summary.get("average_cycle_days") or 28
            average_period_days = summary.get("average_period_days") or self.DEFAULT_PERIOD_DAYS

        previous = None
        for row in menstrual_windows:
            start = self._date_obj(row.get("start_date"))
            end = self._date_obj(row.get("end_date"))
            if start and end and start <= date <= end:
                return "menstrual"
            if start and start <= date:
                previous = row
            elif start and start > date:
                break

        if not previous:
            return None

        start = self._date_obj(previous.get("start_date"))
        if not start:
            return None

        day_index = (date - start).days
        average_cycle_days = int(average_cycle_days)
        average_period_days = int(average_period_days)
        max_projection_days = average_cycle_days * 6
        if day_index < 0 or day_index >= max_projection_days:
            return None

        phase_index = day_index % average_cycle_days
        if phase_index < average_period_days:
            return "menstrual"

        ovulation_day = max(average_period_days, average_cycle_days - 14)
        if phase_index == ovulation_day:
            return "ovulation"
        if phase_index < ovulation_day:
            return "follicular"
        return "luteal"

    def cycle_context(self, user_id=None):
        logs = self.load_cycles(user_id=user_id)
        summary = self.cycle_summary(user_id=user_id)
        if not logs:
            return {
                "enabled": False,
                "summary": summary,
                "patterns": [],
            }

        runs = self.load_runs(include_media=False, user_id=user_id)
        average_cycle_days = summary.get("average_cycle_days") or 28
        average_period_days = summary.get("average_period_days") or self.DEFAULT_PERIOD_DAYS
        patterns = []
        for phase in self.CYCLE_PHASE_ORDER:
            group = [
                row for row in runs
                if self.cycle_phase_for_date(row.get("date"), logs, average_cycle_days, average_period_days) == phase
            ]
            distance = round(sum(row.get("distance_km") or 0 for row in group), 2)
            duration = sum(self._run_duration_seconds(row) or 0 for row in group)
            pace = round(duration / distance) if distance and duration else None
            patterns.append({
                "phase": phase,
                "label": self.CYCLE_PHASE_LABELS.get(phase, phase),
                "run_count": len(group),
                "average_distance_km": round(distance / len(group), 2) if group else 0,
                "average_pace": self.seconds_to_pace(pace),
                "condition_distribution": self._cycle_condition_distribution(phase, logs),
            })

        return {
            "enabled": True,
            "summary": summary,
            "patterns": patterns,
        }

    def running_weight_context(self, user_id=None):
        today = datetime.date.today()
        month_key = today.strftime("%Y-%m")
        month_runs = [row for row in self.load_runs(include_media=False, user_id=user_id) if str(row.get("date") or "").startswith(month_key)]
        month_weights = sorted(
            [row for row in self.load_weights(user_id=user_id) if str(row.get("date") or "").startswith(month_key)],
            key=lambda row: row.get("date") or "",
        )
        total_km = round(sum(row.get("distance_km") or 0 for row in month_runs), 2)
        weight_change = None
        if len(month_weights) >= 2:
            weight_change = round(month_weights[-1].get("weight_kg") - month_weights[0].get("weight_kg"), 1)

        return {
            "weight_summary": self.weight_summary("3m", user_id=user_id),
            "this_month": {
                "run_distance_km": total_km,
                "run_count": len(month_runs),
                "weight_change_kg": weight_change,
                "weight_logs": month_weights,
            },
        }

    def load_goals(self, user_id=None, include_legacy=False):
        path = self.goals_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        goals = []
        seen = set()
        for row in rows:
            goal = self.normalize_goal(row)
            if not goal:
                continue
            if user_id and not self._row_belongs_to_user(goal, self._text(user_id), include_legacy):
                continue
            key = (goal.get("user_id"), goal.get("year_month"), goal.get("goal_type"))
            if key in seen:
                continue
            goals.append(goal)
            seen.add(key)

        return sorted(goals, key=lambda row: (row.get("year_month") or "", -self._goal_sort(row.get("goal_type"))), reverse=True)

    def goals_for_month(self, year_month=None, user_id=None):
        target_month = self._year_month(year_month) or self.latest_year_month(self.load_runs(include_media=False, user_id=user_id))
        if not target_month:
            return []
        rows = self.load_goals(user_id=user_id)
        month_goals = [
            row for row in rows
            if row.get("year_month") == target_month
        ]
        if not month_goals and not os.path.exists(self.goals_path()) and not user_id:
            month_goals = self._default_goal_rows(target_month)
            if month_goals:
                self._write_goals(month_goals)
        return sorted(
            month_goals,
            key=lambda row: self._goal_sort(row.get("goal_type")),
        )

    def save_goal(self, year_month, payload, user_id=None):
        target_month = self._year_month(year_month)
        source = payload if isinstance(payload, dict) else {}
        owner_id = self._text(user_id or source.get("user_id") or source.get("userId"))
        if not target_month:
            return None, "목표 월 형식이 올바르지 않습니다."
        if not owner_id:
            return None, "사용자 정보가 없습니다."

        goal_type = self._goal_type(source.get("goal_type") or source.get("goalType") or source.get("type"))
        if not goal_type:
            return None, "목표 종류가 올바르지 않습니다."

        target_value = self._goal_target_value(
            goal_type,
            source.get("target_value")
            if "target_value" in source
            else source.get("targetValue") if "targetValue" in source else source.get("value")
        )
        if target_value is None:
            return None, "목표값이 올바르지 않습니다."

        rows = self.load_goals()
        existing = next(
            (
                row for row in rows
                if row.get("year_month") == target_month
                and row.get("goal_type") == goal_type
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            ),
            None,
        )
        goal = self.normalize_goal({
            "id": existing.get("id") if existing else source.get("id"),
            "year_month": target_month,
            "goal_type": goal_type,
            "target_value": target_value,
            "created_at": existing.get("created_at") if existing else source.get("created_at"),
            "user_id": owner_id,
        })
        if not goal:
            return None, "목표를 저장하지 못했습니다."

        next_rows = [
            row for row in rows
            if not (
                row.get("year_month") == target_month
                and row.get("goal_type") == goal_type
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            )
        ]
        next_rows.append(goal)
        self._write_goals(next_rows)
        return goal, None

    def replace_goals(self, year_month, goals, user_id=None):
        target_month = self._year_month(year_month)
        if not target_month:
            return [], "목표 월 형식이 올바르지 않습니다."

        if not isinstance(goals, list):
            return [], "목표 목록이 필요합니다."

        owner_id = self._text(user_id)
        if not owner_id:
            return [], "사용자 정보가 없습니다."

        next_month_goals = []
        seen = set()
        for row in goals:
            source = row if isinstance(row, dict) else {}
            source = dict(source)
            source["year_month"] = target_month
            source["user_id"] = owner_id
            goal = self.normalize_goal(source)
            if not goal:
                return [], "목표 목록에 올바르지 않은 값이 있습니다."
            if goal.get("goal_type") in seen:
                continue
            next_month_goals.append(goal)
            seen.add(goal.get("goal_type"))

        rows = [
            row for row in self.load_goals()
            if row.get("year_month") != target_month
            or (self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id)
        ]
        rows.extend(next_month_goals)
        self._write_goals(rows)
        return self.goals_for_month(target_month, owner_id), None

    def delete_goal(self, year_month, goal_type=None, user_id=None):
        target_month = self._year_month(year_month)
        if not target_month:
            return False

        normalized_type = self._goal_type(goal_type)
        owner_id = self._text(user_id)
        rows = self.load_goals()
        if normalized_type:
            next_rows = [
                row for row in rows
                if not (
                    row.get("year_month") == target_month
                    and row.get("goal_type") == normalized_type
                    and (not owner_id or self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
                )
            ]
        else:
            next_rows = [
                row for row in rows
                if row.get("year_month") != target_month
                or (owner_id and self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id)
            ]

        if len(next_rows) == len(rows):
            return False

        self._write_goals(next_rows)
        return True

    def normalize_goal(self, row):
        source = row if isinstance(row, dict) else {}
        year_month = self._year_month(source.get("year_month") or source.get("yearMonth"))
        goal_type = self._goal_type(source.get("goal_type") or source.get("goalType") or source.get("type"))
        target_value = self._goal_target_value(
            goal_type,
            source.get("target_value")
            if "target_value" in source
            else source.get("targetValue") if "targetValue" in source else source.get("value")
        )
        if not year_month or not goal_type or target_value is None:
            return None

        if goal_type in ("count", "pace"):
            target_value = int(round(target_value))
        else:
            target_value = round(float(target_value), 2)

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "year_month": year_month,
            "goal_type": goal_type,
            "target_value": target_value,
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def goal_progress(self, year_month=None, user_id=None):
        target_month = self._year_month(year_month) or self.latest_year_month(self.load_runs(include_media=False, user_id=user_id))
        goals = self.goals_for_month(target_month, user_id=user_id)
        stats = self._month_goal_stats(target_month, user_id=user_id)
        return [self._goal_progress_item(goal, stats) for goal in goals]

    def goal_history(self, limit=6, user_id=None):
        try:
            limit = max(1, min(24, int(limit)))
        except Exception:
            limit = 6

        goals = self.load_goals(user_id=user_id)
        run_months = {
            str(row.get("date") or "")[:7]
            for row in self.load_runs(include_media=False, user_id=user_id)
            if re.match(r"^\d{4}-\d{2}", str(row.get("date") or ""))
        }
        months = sorted({
            row.get("year_month")
            for row in goals
            if row.get("year_month")
        } | run_months, reverse=True)[:limit]

        history = []
        for month in months:
            progress = self.goal_progress(month, user_id=user_id)
            achieved_count = sum(1 for item in progress if item.get("achieved"))
            history.append({
                "year_month": month,
                "label": self._year_month_label(month),
                "goal_count": len(progress),
                "achieved_count": achieved_count,
                "achieved": bool(progress) and achieved_count == len(progress),
                "items": progress,
            })
        return history

    def goals_context(self, year_month=None, user_id=None):
        target_month = self._year_month(year_month) or self.latest_year_month(self.load_runs(include_media=False, user_id=user_id))
        progress = self.goal_progress(target_month, user_id=user_id)
        return {
            "year_month": target_month,
            "goals": progress,
            "summary": self._goals_summary(progress),
            "history": self.goal_history(6, user_id=user_id),
        }

    def weekly_ranking(self, year_week=None, period="this_week", viewer=None, users=None, target_user_ids=None, scope="global"):
        actor = viewer if isinstance(viewer, dict) else {}
        viewer_id = self._text(actor.get("id")) or "local-user"
        viewer_name = self._text(actor.get("name")) or "나"
        viewer_profile_image = self._text(actor.get("profile_image"))
        viewer_following_ids = {
            self._text(user_id)
            for user_id in actor.get("following_ids", [])
            if self._text(user_id)
        }
        viewer_follower_ids = {
            self._text(user_id)
            for user_id in actor.get("follower_ids", [])
            if self._text(user_id)
        }
        period_info = self._ranking_period(period, year_week)
        ranking_scope = "following" if self._text(scope) == "following" else "global"
        social = self.load_ranking_social()
        profiles = self._ranking_profiles(social, users, viewer_id, viewer_name, viewer_profile_image)
        if target_user_ids is None:
            target_ids = self._ranking_target_user_ids(social, profiles, viewer_id)
        else:
            explicit_ids = {viewer_id}
            for user_id in target_user_ids or []:
                normalized_id = self._text(user_id)
                if normalized_id:
                    explicit_ids.add(normalized_id)
            target_ids = [
                user_id
                for user_id in explicit_ids
                if self._ranking_profile_visible(profiles.get(user_id) or {}, user_id == viewer_id)
            ]
        rows = self.load_runs(include_media=False)
        totals = {
            user_id: {"distance_km": 0, "run_count": 0, "duration_seconds": 0}
            for user_id in target_ids
        }

        for row in rows:
            date = self._date_obj(row.get("date"))
            if not date or date < period_info.get("start") or date > period_info.get("end"):
                continue

            run_user_id = self._text(row.get("user_id") or row.get("userId")) or viewer_id
            if run_user_id not in target_ids:
                continue

            try:
                distance = float(row.get("distance_km") or 0)
            except Exception:
                distance = 0
            distance = distance if math.isfinite(distance) and distance > 0 else 0
            duration_seconds = self._run_duration_seconds(row)

            totals.setdefault(run_user_id, {"distance_km": 0, "run_count": 0, "duration_seconds": 0})
            totals[run_user_id]["distance_km"] += distance
            totals[run_user_id]["run_count"] += 1
            if duration_seconds is not None and math.isfinite(duration_seconds) and duration_seconds > 0:
                totals[run_user_id]["duration_seconds"] += duration_seconds

        entries = []
        for user_id in target_ids:
            profile = profiles.get(user_id) or self._ranking_profile({}, user_id)
            user_total = totals.get(user_id, {})
            raw_distance = user_total.get("distance_km", 0) or 0
            distance = round(raw_distance, 2)
            duration_seconds = user_total.get("duration_seconds", 0) or 0
            avg_pace_seconds = round(duration_seconds / raw_distance) if raw_distance and duration_seconds else None
            is_following = user_id in viewer_following_ids
            is_follower = user_id in viewer_follower_ids
            entry = {
                "user_id": user_id,
                "name": profile.get("name") or ("나" if user_id == viewer_id else "러너"),
                "profile_image": profile.get("profile_image") or "",
                "distance_km": distance,
                "distance_text": self.km_text(distance),
                "run_count": int(totals.get(user_id, {}).get("run_count", 0)),
                "is_viewer": user_id == viewer_id,
                "is_following": is_following,
                "is_follower": is_follower,
                "is_mutual": is_following and is_follower,
                "privacy": "private" if profile.get("is_private") else "public",
                "_avg_pace_seconds": avg_pace_seconds,
            }
            entries.append(entry)

        entries = sorted(entries, key=lambda row: (
            -row.get("distance_km", 0),
            row.get("_avg_pace_seconds") if row.get("_avg_pace_seconds") is not None else math.inf,
            row.get("name") or "",
            row.get("user_id") or "",
        ))
        max_distance = max([row.get("distance_km") or 0 for row in entries] or [0])
        rank_key = None
        current_rank = 0
        ranked_position = 0
        for entry in entries:
            if (entry.get("distance_km") or 0) <= 0:
                entry["rank"] = 0
                entry["rank_out"] = True
                entry["rank_label"] = "순위 밖"
                entry["rank_status"] = "달리지 않아서 순위 밖"
                entry["bar_percent"] = 0
                entry["highlight"] = bool(entry.get("is_viewer"))
                entry["medal"] = ""
                continue

            ranked_position += 1
            next_rank_key = (entry.get("distance_km") or 0, entry.get("_avg_pace_seconds"))
            if next_rank_key != rank_key:
                current_rank = ranked_position
                rank_key = next_rank_key
            entry["rank"] = current_rank
            entry["rank_out"] = False
            entry["rank_label"] = f"{current_rank}위"
            entry["rank_status"] = ""
            entry["bar_percent"] = round(((entry.get("distance_km") or 0) / max_distance) * 100) if max_distance else 0
            entry["highlight"] = bool(entry.get("is_viewer"))
            entry["medal"] = "gold" if current_rank == 1 else "silver" if current_rank == 2 else "bronze" if current_rank == 3 else ""

        distance_groups = {}
        rank_groups = {}
        for entry in entries:
            distance_groups.setdefault(entry.get("distance_km") or 0, []).append(entry)
            rank_groups.setdefault(entry.get("rank") or 0, []).append(entry)

        for entry in entries:
            same_distance = distance_groups.get(entry.get("distance_km") or 0, [])
            same_rank = rank_groups.get(entry.get("rank") or 0, [])
            pace_tiebreak_applied = (
                not entry.get("rank_out") and
                len(same_distance) > 1
                and len({row.get("rank") for row in same_distance}) > 1
                and any(row.get("_avg_pace_seconds") is not None for row in same_distance)
            )
            entry["rank_tied"] = not entry.get("rank_out") and len(same_rank) > 1
            entry["rank_tiebreaker"] = "pace" if pace_tiebreak_applied else ""
            entry.pop("_avg_pace_seconds", None)

        for entry in entries:
            entry["name"] = self._ranking_display_name(
                entry.get("name"),
                entry.get("is_viewer"),
                entry.get("is_following") or entry.get("is_mutual"),
            )

        me = next((row for row in entries if row.get("is_viewer")), None)
        current_week = self._ranking_period("this_week", None)
        is_current = period_info.get("period_key") == current_week.get("period_key") and period_info.get("period") != "this_month"
        winner = entries[0] if entries and entries[0].get("distance_km") else None
        archived = False
        if ranking_scope == "global" and not is_current and period_info.get("period") != "this_month" and winner:
            archived = self._remember_weekly_winner(social, period_info, winner)

        return {
            "success": True,
            "data": {
                "period": period_info.get("period"),
                "period_key": period_info.get("period_key"),
                "period_label": self._ranking_period_label(period_info.get("start"), period_info.get("end")),
                "start_date": period_info.get("start").isoformat(),
                "end_date": period_info.get("end").isoformat(),
                "entries": entries,
                "me": me,
                "motivation_text": self._ranking_motivation(entries, me, period_info.get("period")),
                "finalized": not is_current,
                "archived": archived,
                "winner": winner,
                "scope": ranking_scope,
                "scope_label": "내 친구 랭킹" if ranking_scope == "following" else "전체 랭킹",
                "target_count": len([user_id for user_id in target_ids if user_id != viewer_id]),
                "viewer": {
                    "user_id": viewer_id,
                    "ranking_enabled": self._ranking_profile_enabled(profiles.get(viewer_id) or {}, True),
                },
            },
        }

    def load_ranking_social(self):
        path = self.ranking_social_path()
        if not os.path.exists(path):
            return {"profiles": [], "follows": [], "weekly_winners": []}

        try:
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception:
            data = {}

        return data if isinstance(data, dict) else {"profiles": [], "follows": [], "weekly_winners": []}

    def set_ranking_participation(self, user_id, enabled=True, profile=None):
        lookup = self._text(user_id) or "local-user"
        social = self.load_ranking_social()
        profiles = social.get("profiles")
        if not isinstance(profiles, list):
            profiles = []

        actor = profile if isinstance(profile, dict) else {}
        current = None
        next_profiles = []
        for row in profiles:
            item = self._ranking_profile(row, self._text((row or {}).get("user_id") or (row or {}).get("userId")))
            if not item:
                continue
            if item.get("user_id") == lookup:
                current = item
            else:
                next_profiles.append(item)

        current = current or self._ranking_profile({}, lookup)
        current["name"] = self._text(actor.get("name")) or current.get("name") or "나"
        current["profile_image"] = self._text(actor.get("profile_image")) or current.get("profile_image") or ""
        current["ranking_enabled"] = bool(enabled)
        current["ranking_consent"] = bool(enabled)
        next_profiles.append(current)
        social["profiles"] = next_profiles
        self._write_ranking_social(social)
        return current

    def ranking_context(self, viewer=None):
        data = self.weekly_ranking(period="this_week", viewer=viewer).get("data") or {}
        me = data.get("me") or {}
        leader = (data.get("entries") or [{}])[0] if data.get("entries") else {}
        return {
            "period_label": data.get("period_label"),
            "my_rank": None if me.get("rank_out") else me.get("rank"),
            "my_rank_status": me.get("rank_status") or "",
            "my_distance_km": me.get("distance_km"),
            "leader_name": leader.get("name"),
            "leader_distance_km": leader.get("distance_km"),
            "motivation_text": data.get("motivation_text"),
        }

    def load_challenges(self, user_id=None):
        rows = self._challenge_rows()
        if rows:
            rows = self._refresh_challenge_contributions(rows)
            self._write_challenges(rows)

        return [self._decorate_challenge(row, user_id) for row in rows]

    def recalculate_challenge_contributions(self):
        rows = self._challenge_rows()
        if not rows:
            return []

        rows = self._refresh_challenge_contributions(rows)
        self._write_challenges(rows)
        return rows

    def challenge_detail(self, challenge_id, user_id=None):
        lookup = self._text(challenge_id)
        if not lookup:
            return None

        normalized_lookup = lookup.upper()
        for challenge in self.load_challenges(user_id):
            if challenge.get("id") == lookup or challenge.get("invite_code") == normalized_lookup:
                return challenge
        return None

    def create_challenge(self, payload, user=None):
        source = payload if isinstance(payload, dict) else {}
        actor = user if isinstance(user, dict) else {}
        creator_id = self._text(actor.get("id")) or "local-user"
        creator_name = self._text(actor.get("name")) or "나"

        title = self._text(source.get("title")) or ""
        if not title:
            return None, "챌린지 제목을 입력해주세요."
        if len(title) > 100:
            title = title[:100]

        challenge_type = self._challenge_type(source.get("type") or source.get("challenge_type") or source.get("challengeType"))
        if not challenge_type:
            return None, "챌린지 종류가 올바르지 않습니다."

        goal_value = self._challenge_goal_value(challenge_type, source.get("goal_value") if "goal_value" in source else source.get("goalValue"))
        if goal_value is None:
            return None, "목표값은 0보다 큰 숫자로 입력해주세요."

        start_date = self._date(source.get("start_date") or source.get("startDate"))
        end_date = self._date(source.get("end_date") or source.get("endDate"))
        if not start_date or not end_date:
            return None, "챌린지 기간을 확인해주세요."
        if end_date < start_date:
            return None, "종료일은 시작일 이후여야 합니다."

        rows = self._challenge_rows()
        invite_code = self._generate_invite_code({row.get("invite_code") for row in rows})
        challenge = self.normalize_challenge({
            "id": str(uuid.uuid4()),
            "title": title,
            "type": challenge_type,
            "goal_value": goal_value,
            "start_date": start_date,
            "end_date": end_date,
            "creator_id": creator_id,
            "creator_name": creator_name,
            "invite_code": invite_code,
            "created_at": self._utcnow(),
            "members": [{
                "challenge_id": "",
                "user_id": creator_id,
                "user_name": creator_name,
                "joined_at": self._utcnow(),
                "contributed_value": 0,
            }],
        })
        if not challenge:
            return None, "챌린지를 만들지 못했습니다."

        challenge["members"] = [
            dict(member, challenge_id=challenge.get("id"))
            for member in challenge.get("members", [])
        ]
        rows.insert(0, challenge)
        rows = self._refresh_challenge_contributions(rows)
        self._write_challenges(rows)
        return self.challenge_detail(challenge.get("id"), actor), None

    def join_challenge(self, payload, user=None):
        source = payload if isinstance(payload, dict) else {}
        actor = user if isinstance(user, dict) else {}
        user_id = self._text(actor.get("id")) or "local-user"
        user_name = self._text(actor.get("name")) or "나"
        lookup = self._text(
            source.get("invite_code")
            or source.get("inviteCode")
            or source.get("code")
            or source.get("challenge_id")
            or source.get("challengeId")
            or source.get("id")
        )
        if not lookup:
            return None, "초대코드를 입력해주세요."

        normalized_lookup = lookup.upper()
        rows = self._challenge_rows()
        target_index = -1
        for index, row in enumerate(rows):
            if row.get("id") == lookup or row.get("invite_code") == normalized_lookup:
                target_index = index
                break

        if target_index < 0:
            return None, "참여할 챌린지를 찾지 못했습니다."

        challenge = rows[target_index]
        if self._challenge_status(challenge) == "ended":
            return None, "종료된 챌린지는 참여할 수 없습니다."

        members = challenge.get("members") or []
        if not any(member.get("user_id") == user_id for member in members):
            members.append(self.normalize_challenge_member({
                "challenge_id": challenge.get("id"),
                "user_id": user_id,
                "user_name": user_name,
                "joined_at": self._utcnow(),
                "contributed_value": 0,
            }, challenge.get("id")))
            challenge["members"] = [member for member in members if member]
            rows[target_index] = challenge

        rows = self._refresh_challenge_contributions(rows)
        self._write_challenges(rows)
        return self.challenge_detail(challenge.get("id"), actor), None

    def delete_challenge(self, challenge_id, user=None):
        actor = user if isinstance(user, dict) else {}
        user_id = self._text(actor.get("id")) or ""
        lookup = self._text(challenge_id)
        if not user_id:
            return None, "로그인이 필요합니다."
        if not lookup:
            return None, "챌린지를 찾지 못했습니다."

        normalized_lookup = lookup.upper()
        rows = self._challenge_rows()
        next_rows = []
        deleted = None

        for row in rows:
            challenge = self.normalize_challenge(row)
            if not challenge:
                continue
            matched = challenge.get("id") == lookup or challenge.get("invite_code") == normalized_lookup
            if not matched:
                next_rows.append(challenge)
                continue
            if not self._challenge_owned_by(challenge, user):
                return None, "주최한 챌린지만 삭제할 수 있습니다."
            deleted = challenge

        if not deleted:
            return None, "챌린지를 찾지 못했습니다."

        self._write_challenges(next_rows)
        return deleted, None

    def normalize_challenge(self, row):
        source = row if isinstance(row, dict) else {}
        challenge_id = self._text(source.get("id")) or str(uuid.uuid4())
        title = self._text(source.get("title")) or ""
        challenge_type = self._challenge_type(source.get("type") or source.get("challenge_type") or source.get("challengeType"))
        goal_value = self._challenge_goal_value(challenge_type, source.get("goal_value") if "goal_value" in source else source.get("goalValue"))
        start_date = self._date(source.get("start_date") or source.get("startDate"))
        end_date = self._date(source.get("end_date") or source.get("endDate"))
        creator_id = self._text(source.get("creator_id") or source.get("creatorId")) or "local-user"
        creator_name = self._text(source.get("creator_name") or source.get("creatorName")) or "나"
        invite_code = self._invite_code(source.get("invite_code") or source.get("inviteCode")) or challenge_id.replace("-", "").upper()[:8]

        if not title or not challenge_type or goal_value is None or not start_date or not end_date:
            return None
        if end_date < start_date:
            start_date, end_date = end_date, start_date

        members = []
        seen = set()
        for item in source.get("members") or source.get("challenge_members") or []:
            member = self.normalize_challenge_member(item, challenge_id)
            if not member or member.get("user_id") in seen:
                continue
            members.append(member)
            seen.add(member.get("user_id"))

        if creator_id not in seen:
            members.insert(0, self.normalize_challenge_member({
                "challenge_id": challenge_id,
                "user_id": creator_id,
                "user_name": creator_name,
                "joined_at": source.get("created_at") or source.get("createdAt") or self._utcnow(),
                "contributed_value": 0,
            }, challenge_id))

        return {
            "id": challenge_id,
            "title": title[:100],
            "type": challenge_type,
            "goal_value": goal_value,
            "start_date": start_date,
            "end_date": end_date,
            "creator_id": creator_id,
            "creator_name": creator_name,
            "invite_code": invite_code,
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "members": [member for member in members if member],
        }

    def normalize_challenge_member(self, row, challenge_id=None):
        source = row if isinstance(row, dict) else {}
        user_id = self._text(source.get("user_id") or source.get("userId"))
        if not user_id:
            return None

        contributed_value = self._number(source.get("contributed_value") if "contributed_value" in source else source.get("contributedValue"))
        return {
            "challenge_id": self._text(source.get("challenge_id") or source.get("challengeId") or challenge_id) or "",
            "user_id": user_id,
            "user_name": self._text(source.get("user_name") or source.get("userName") or source.get("name")) or "러너",
            "joined_at": self._text(source.get("joined_at") or source.get("joinedAt")) or self._utcnow(),
            "contributed_value": round(contributed_value or 0, 2),
        }

    def normalize_ai_usage(self, row):
        source = row if isinstance(row, dict) else {}
        user_id = self._account_row_user_id(source)
        if not user_id:
            return None

        action = self._text(source.get("action")) or "chat"
        day_key = self._date(source.get("day_key") or source.get("dayKey"))
        month_key = self._text(source.get("month_key") or source.get("monthKey"))
        if not month_key and day_key:
            month_key = day_key[:7]
        if month_key and not re.match(r"^\d{4}-\d{2}$", month_key):
            month_key = None

        daily_count = self._int(source.get("daily_count") or source.get("dailyCount"))
        monthly_count = self._int(source.get("monthly_count") or source.get("monthlyCount"))
        return {
            "user_id": user_id,
            "action": action,
            "day_key": day_key,
            "month_key": month_key,
            "daily_count": max(0, daily_count or 0),
            "monthly_count": max(0, monthly_count or 0),
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "updated_at": self._text(source.get("updated_at") or source.get("updatedAt")) or self._utcnow(),
        }

    def load_ai_usage(self, user_id=None, action=None):
        payload = self._load_account_json(self.ai_usage_path(), [])
        if not isinstance(payload, list):
            return []

        owner_id = self._text(user_id)
        action_key = self._text(action)
        rows = []
        for row in payload:
            usage = self.normalize_ai_usage(row)
            if not usage:
                continue
            if owner_id and usage.get("user_id") != owner_id:
                continue
            if action_key and usage.get("action") != action_key:
                continue
            rows.append(usage)
        return rows

    def ai_usage_status(self, user_id, action="chat", daily_limit=0, monthly_limit=0):
        return self._ai_usage_payload(
            user_id=user_id,
            action=action,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            reserve=False,
        )

    def reserve_ai_usage(self, user_id, action="chat", daily_limit=0, monthly_limit=0):
        return self._ai_usage_payload(
            user_id=user_id,
            action=action,
            daily_limit=daily_limit,
            monthly_limit=monthly_limit,
            reserve=True,
        )

    def _ai_usage_payload(self, user_id, action="chat", daily_limit=0, monthly_limit=0, reserve=False):
        owner_id = self._text(user_id)
        if not owner_id:
            return {
                "allowed": False,
                "reason": "missing_user",
                "message": "사용자 정보가 없어 AI 사용량을 확인하지 못했습니다.",
            }

        action_key = self._text(action) or "chat"
        daily_limit = max(0, self._int(daily_limit) or 0)
        monthly_limit = max(0, self._int(monthly_limit) or 0)
        now = self._utcnow()
        day_key = self._date(now)
        month_key = day_key[:7]

        payload = self._load_account_json(self.ai_usage_path(), [])
        if not isinstance(payload, list):
            payload = []

        rows = []
        target = None
        for raw in payload:
            usage = self.normalize_ai_usage(raw)
            if not usage:
                continue
            if usage.get("user_id") == owner_id and usage.get("action") == action_key:
                if target is None:
                    target = usage
                else:
                    if usage.get("day_key") == target.get("day_key"):
                        target["daily_count"] += usage.get("daily_count") or 0
                    if usage.get("month_key") == target.get("month_key"):
                        target["monthly_count"] += usage.get("monthly_count") or 0
                continue
            rows.append(usage)

        if target is None:
            target = {
                "user_id": owner_id,
                "action": action_key,
                "day_key": day_key,
                "month_key": month_key,
                "daily_count": 0,
                "monthly_count": 0,
                "created_at": now,
                "updated_at": now,
            }
        else:
            if target.get("month_key") != month_key:
                target["month_key"] = month_key
                target["monthly_count"] = 0
            if target.get("day_key") != day_key:
                target["day_key"] = day_key
                target["daily_count"] = 0

        reason = ""
        if daily_limit and target.get("daily_count", 0) >= daily_limit:
            reason = "daily_limit"
        elif monthly_limit and target.get("monthly_count", 0) >= monthly_limit:
            reason = "monthly_limit"

        allowed = not reason
        if reserve:
            if allowed:
                target["daily_count"] = target.get("daily_count", 0) + 1
                target["monthly_count"] = target.get("monthly_count", 0) + 1
            target["updated_at"] = now

        result = self._shape_ai_usage_result(target, daily_limit, monthly_limit, allowed, reason)
        if reserve or target.get("day_key") == day_key or target.get("month_key") == month_key:
            self._write_ai_usage([target, *rows])
        return result

    def _shape_ai_usage_result(self, usage, daily_limit, monthly_limit, allowed=True, reason=""):
        daily_count = usage.get("daily_count") or 0
        monthly_count = usage.get("monthly_count") or 0
        message = ""
        if reason == "daily_limit":
            message = "오늘 페이서 AI 사용량을 모두 사용했어. 내일 다시 이용해줘."
        elif reason == "monthly_limit":
            message = "이번 달 페이서 AI 사용량을 모두 사용했어. 다음 달에 다시 이용해줘."

        return {
            "allowed": allowed,
            "reason": reason,
            "message": message,
            "user_id": usage.get("user_id"),
            "action": usage.get("action") or "chat",
            "day_key": usage.get("day_key"),
            "month_key": usage.get("month_key"),
            "daily_count": daily_count,
            "daily_limit": daily_limit,
            "daily_remaining": None if not daily_limit else max(0, daily_limit - daily_count),
            "monthly_count": monthly_count,
            "monthly_limit": monthly_limit,
            "monthly_remaining": None if not monthly_limit else max(0, monthly_limit - monthly_count),
            "updated_at": usage.get("updated_at"),
        }

    def normalize_ai_rate_limit(self, row):
        source = row if isinstance(row, dict) else {}
        user_id = self._account_row_user_id(source)
        if not user_id:
            return None

        action = self._text(source.get("action")) or "chat"
        request_timestamps = (
            source.get("request_timestamps")
            or source.get("requestTimestamps")
            or source.get("requests")
            or []
        )
        if not isinstance(request_timestamps, list):
            request_timestamps = []

        clean_timestamps = []
        for value in request_timestamps:
            timestamp = self._timestamp(value)
            if timestamp and timestamp > 0:
                clean_timestamps.append(round(timestamp, 3))

        blocked_until_ts = self._timestamp(
            source.get("blocked_until_ts")
            or source.get("blockedUntilTs")
            or source.get("blocked_until")
            or source.get("blockedUntil")
        ) or 0

        return {
            "user_id": user_id,
            "action": action,
            "request_timestamps": sorted(clean_timestamps)[-200:],
            "blocked_until_ts": max(0, round(blocked_until_ts, 3)),
            "blocked_until": self._iso_from_timestamp(blocked_until_ts) if blocked_until_ts > 0 else "",
            "blocked_reason": self._text(source.get("blocked_reason") or source.get("blockedReason")) or "",
            "created_at": self._text(source.get("created_at") or source.get("createdAt")) or self._utcnow(),
            "updated_at": self._text(source.get("updated_at") or source.get("updatedAt")) or self._utcnow(),
        }

    def reserve_ai_rate_limit(self, user_id, action="chat", cooldown_seconds=0, window_seconds=60, max_requests=0):
        owner_id = self._text(user_id)
        if not owner_id:
            return {
                "allowed": False,
                "reason": "missing_user",
                "message": "사용자 정보가 없어 AI 요청 제한을 확인하지 못했습니다.",
            }

        action_key = self._text(action) or "chat"
        cooldown_seconds = max(0, self._int(cooldown_seconds) or 0)
        window_seconds = max(1, self._int(window_seconds) or 60)
        max_requests = max(0, self._int(max_requests) or 0)
        now_ts = self._now_timestamp()
        now = self._iso_from_timestamp(now_ts)

        payload = self._load_account_json(self.ai_rate_limits_path(), [])
        if not isinstance(payload, list):
            payload = []

        rows = []
        target = None
        for raw in payload:
            rate_limit = self.normalize_ai_rate_limit(raw)
            if not rate_limit:
                continue
            if rate_limit.get("user_id") == owner_id and rate_limit.get("action") == action_key:
                if target is None:
                    target = rate_limit
                else:
                    target["request_timestamps"].extend(rate_limit.get("request_timestamps") or [])
                    if rate_limit.get("blocked_until_ts", 0) > target.get("blocked_until_ts", 0):
                        target["blocked_until_ts"] = rate_limit.get("blocked_until_ts", 0)
                        target["blocked_reason"] = rate_limit.get("blocked_reason") or target.get("blocked_reason") or ""
                continue
            rows.append(rate_limit)

        if target is None:
            target = {
                "user_id": owner_id,
                "action": action_key,
                "request_timestamps": [],
                "blocked_until_ts": 0,
                "blocked_until": "",
                "blocked_reason": "",
                "created_at": now,
                "updated_at": now,
            }

        recent = sorted([
            timestamp
            for timestamp in (target.get("request_timestamps") or [])
            if timestamp and timestamp > now_ts - window_seconds
        ])
        target["request_timestamps"] = recent

        reason = ""
        retry_after = 0
        blocked_until_ts = target.get("blocked_until_ts") or 0
        if blocked_until_ts > now_ts:
            reason = target.get("blocked_reason") or "burst_limit"
            retry_after = math.ceil(blocked_until_ts - now_ts)
        elif cooldown_seconds and recent and now_ts - recent[-1] < cooldown_seconds:
            reason = "cooldown"
            retry_after = math.ceil(cooldown_seconds - (now_ts - recent[-1]))
        elif max_requests and len(recent) >= max_requests:
            reason = "burst_limit"
            retry_after = max(1, window_seconds)
            blocked_until_ts = now_ts + retry_after
            target["blocked_until_ts"] = round(blocked_until_ts, 3)
            target["blocked_reason"] = reason
        else:
            target["blocked_until_ts"] = 0
            target["blocked_until"] = ""
            target["blocked_reason"] = ""

        allowed = not reason
        if allowed:
            recent.append(round(now_ts, 3))
            target["request_timestamps"] = recent[-200:]

        if target.get("blocked_until_ts", 0) > 0:
            target["blocked_until"] = self._iso_from_timestamp(target.get("blocked_until_ts"))
        target["updated_at"] = now

        result = self._shape_ai_rate_limit_result(
            target,
            allowed=allowed,
            reason=reason,
            retry_after_seconds=retry_after,
            cooldown_seconds=cooldown_seconds,
            window_seconds=window_seconds,
            max_requests=max_requests,
            now_ts=now_ts,
        )
        self._write_ai_rate_limits([target, *rows])
        return result

    def _shape_ai_rate_limit_result(
        self,
        rate_limit,
        allowed=True,
        reason="",
        retry_after_seconds=0,
        cooldown_seconds=0,
        window_seconds=60,
        max_requests=0,
        now_ts=None,
    ):
        now_ts = now_ts if now_ts is not None else self._now_timestamp()
        request_timestamps = [
            timestamp for timestamp in (rate_limit.get("request_timestamps") or [])
            if timestamp and timestamp > now_ts - max(1, window_seconds)
        ]
        retry_after_seconds = max(0, self._int(retry_after_seconds) or 0)
        reset_at_ts = 0
        if retry_after_seconds:
            reset_at_ts = now_ts + retry_after_seconds
        elif request_timestamps:
            reset_at_ts = request_timestamps[0] + max(1, window_seconds)

        message = ""
        if reason == "cooldown":
            message = f"요청이 너무 빠릅니다. {retry_after_seconds}초 후 다시 시도해주세요."
        elif reason in ("burst_limit", "blocked"):
            message = f"짧은 시간에 AI 요청이 많아 잠시 차단했습니다. {retry_after_seconds}초 후 다시 시도해주세요."

        remaining = None
        if max_requests:
            remaining = max(0, max_requests - len(request_timestamps))

        return {
            "allowed": allowed,
            "reason": reason,
            "message": message,
            "user_id": rate_limit.get("user_id"),
            "action": rate_limit.get("action") or "chat",
            "cooldown_seconds": cooldown_seconds,
            "window_seconds": window_seconds,
            "max_requests": max_requests,
            "request_count": len(request_timestamps),
            "remaining_in_window": remaining,
            "retry_after_seconds": retry_after_seconds,
            "reset_at": self._iso_from_timestamp(reset_at_ts) if reset_at_ts else "",
            "blocked_until": rate_limit.get("blocked_until") or "",
            "updated_at": rate_limit.get("updated_at"),
        }

    def load_chat_sessions(self, user_id=None, include_legacy=False):
        path = self.chat_history_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        sessions = []
        for row in rows:
            session = self.normalize_chat_session(row)
            if user_id and session and not self._row_belongs_to_user(session, self._text(user_id), include_legacy):
                continue
            if session:
                sessions.append(session)

        return sorted(sessions, key=lambda row: row.get("updated_at") or "", reverse=True)

    def save_chat_exchange(self, session_id, user_text, ai_text, user_id=None, chat_day=None):
        user_text = self._text(user_text)
        ai_text = self._text(ai_text)
        if not user_text and not ai_text:
            return None
        owner_id = self._text(user_id)
        if not owner_id:
            return None

        now = self._utcnow()
        chat_day = self._date(chat_day) or self._date(now)
        session_id = self._text(session_id) or uuid.uuid4().hex
        sessions = self.load_chat_sessions()
        existing_same_id = next((row for row in sessions if row.get("id") == session_id), None)
        if existing_same_id and self._account_row_user_id(existing_same_id) and self._account_row_user_id(existing_same_id) != owner_id:
            return None
        session = next(
            (
                row for row in sessions
                if row.get("id") == session_id
                and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            ),
            None,
        )
        if session and self._chat_session_day_key(session) != chat_day:
            session_id = uuid.uuid4().hex
            session = None

        if not session:
            session = {
                "id": session_id,
                "title": self._chat_title(user_text),
                "created_at": now,
                "updated_at": now,
                "day_key": chat_day,
                "user_id": owner_id,
                "messages": [],
            }
        else:
            session["user_id"] = owner_id
            session["day_key"] = self._chat_session_day_key(session) or chat_day

        if user_text:
            session["messages"].append({
                "sender": "user",
                "text": user_text,
                "created_at": now,
            })
        if ai_text:
            session["messages"].append({
                "sender": "ai",
                "text": ai_text,
                "created_at": now,
            })

        if not session.get("title") or session.get("title") == "새 대화":
            session["title"] = self._chat_title(user_text or ai_text)
        session["updated_at"] = now

        next_sessions = [
            session,
            *[
                row for row in sessions
                if row.get("id") != session_id
                or (self._account_row_user_id(row) and self._account_row_user_id(row) != owner_id)
            ],
        ]
        self._write_chat_sessions(next_sessions)
        return self.normalize_chat_session(session)

    def delete_chat_session(self, session_id, user_id=None):
        session_id = self._text(session_id)
        if not session_id:
            return False

        owner_id = self._text(user_id)
        sessions = self.load_chat_sessions()
        next_sessions = [
            row for row in sessions
            if row.get("id") != session_id or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        if len(next_sessions) == len(sessions):
            return False

        self._write_chat_sessions(next_sessions)
        return True

    def normalize_chat_session(self, row):
        source = row if isinstance(row, dict) else {}
        messages = []

        for item in source.get("messages") or []:
            if not isinstance(item, dict):
                continue

            sender = self._text(item.get("sender"))
            text = self._text(item.get("text"))
            if sender not in ("ai", "user") or not text:
                continue

            messages.append({
                "sender": sender,
                "text": text,
                "created_at": self._text(item.get("created_at")) or self._utcnow(),
            })

        if not messages:
            return None

        first_user = next((msg.get("text") for msg in messages if msg.get("sender") == "user"), "")
        created_at = self._text(source.get("created_at")) or messages[0].get("created_at") or self._utcnow()
        updated_at = self._text(source.get("updated_at")) or messages[-1].get("created_at") or created_at

        return {
            "id": self._text(source.get("id")) or uuid.uuid4().hex,
            "title": self._chat_title(source.get("title") or first_user or messages[0].get("text")),
            "created_at": created_at,
            "updated_at": updated_at,
            "day_key": self._chat_session_day_key(source) or self._date(updated_at) or self._date(created_at) or self._date(messages[0].get("created_at")),
            "user_id": self._text(source.get("user_id") or source.get("userId")),
            "preview": self._chat_preview(messages),
            "message_count": len(messages),
            "messages": messages[-120:],
        }

    def set_rest_day(self, value, enabled=True, user_id=None):
        date = self._date(value)
        if not date:
            return False, "휴식일 날짜가 올바르지 않습니다.", self.load_rest_days(user_id)

        owner_id = self._text(user_id)
        if not owner_id:
            return False, "사용자 정보가 없습니다.", self.load_rest_days(user_id)

        if not enabled:
            self.delete_rest_day(date, owner_id)
            return True, "", self.load_rest_days(owner_id)

        if any(
            row.get("date") == date
            and (self._account_row_user_id(row) == owner_id or not self._account_row_user_id(row))
            for row in self.load_runs(user_id=owner_id)
        ):
            return False, "러닝 기록이 있는 날짜는 휴식일로 지정할 수 없습니다.", self.load_rest_days(owner_id)

        current = self._load_account_json(self.rest_days_path(), [])
        if not isinstance(current, list):
            current = []
        next_rows = []
        exists = False
        for row in current:
            row_date = self._date(row.get("date")) if isinstance(row, dict) else self._date(row)
            row_user_id = self._account_row_user_id(row)
            if row_date == date and (row_user_id == owner_id or not row_user_id):
                exists = True
                next_rows.append({"date": date, "user_id": owner_id})
            else:
                next_rows.append(row)
        if not exists:
            next_rows.append({"date": date, "user_id": owner_id})
        self._write_rest_days(sorted(next_rows, key=lambda row: row.get("date") if isinstance(row, dict) else str(row)))
        return True, "", self.load_rest_days(owner_id)

    def delete_rest_day(self, value, user_id=None):
        date = self._date(value)
        if not date:
            return False

        owner_id = self._text(user_id)
        current = self._load_account_json(self.rest_days_path(), [])
        if not isinstance(current, list):
            return False

        next_rows = []
        deleted = False
        for row in current:
            row_date = self._date(row.get("date")) if isinstance(row, dict) else self._date(row)
            row_user_id = self._account_row_user_id(row)
            if row_date == date and (not owner_id or row_user_id == owner_id or not row_user_id):
                deleted = True
                continue
            next_rows.append(row)

        if not deleted:
            return False

        self._write_rest_days(next_rows)
        return True

    def save_run(self, payload):
        run = self.normalize_run(payload)
        errors = []
        if not run.get("date"):
            errors.append("date")
        if run.get("distance_km") is None:
            errors.append("distance_km")
        if not run.get("user_id"):
            errors.append("user_id")

        if errors:
            return None, errors

        run["id"] = run.get("id") or uuid.uuid4().hex
        run["created_at"] = run.get("created_at") or datetime.datetime.utcnow().isoformat() + "Z"

        rows = self.load_runs(include_media=False)
        existing = next((row for row in rows if row.get("id") == run["id"]), None)
        if existing and self._account_row_user_id(existing) != run.get("user_id"):
            return None, ["id"]
        rows = [row for row in rows if row.get("id") != run["id"]]
        rows.insert(0, run)
        self._write_runs(rows)
        self.delete_rest_day(run.get("date"), run.get("user_id"))
        self.recalculate_challenge_contributions()
        return run, []

    def update_run_journal(self, run_id, journal, user_id=None):
        return self.update_run(run_id, {"journal": journal}, user_id=user_id)

    def update_run(self, run_id, payload, user_id=None):
        run_id = self._text(run_id)
        if not run_id:
            return None, "수정할 러닝 기록을 찾지 못했습니다."

        source = payload if isinstance(payload, dict) else {}
        journal_keys = ("journal",)
        water_before_keys = ("water_before_ml", "waterBeforeMl", "water_before", "waterBefore", "before_water_ml", "beforeWaterMl")
        water_after_keys = ("water_after_ml", "waterAfterMl", "water_after", "waterAfter", "after_water_ml", "afterWaterMl")
        public_keys = ("is_public", "isPublic", "public", "privacy")
        playlist_keys = ("playlist_name", "playlistName", "music_playlist_name", "musicPlaylistName")
        music_url_keys = ("music_url", "musicUrl", "apple_music_url", "appleMusicUrl")
        top_tracks_keys = ("top_tracks", "topTracks", "music_tracks", "musicTracks")
        record_keys = self.DATE_KEYS + self.DISTANCE_KEYS + (
            "avg_pace",
            "avgPace",
            "pace",
            "average_pace",
            "averagePace",
            "duration",
            "time",
            "elapsed_time",
            "elapsedTime",
            "moving_time",
            "movingTime",
            "run_type",
            "runType",
            "running_type",
            "runningType",
            "start_time",
            "startTime",
            "started_at",
            "startedAt",
            "calories",
            "avg_heart_rate",
            "avgHeartRate",
            "heart_rate",
            "heartRate",
            "cadence",
            "elevation_gain",
            "elevationGain",
            "image_url",
            "imageUrl",
            "raw_parsed_json",
            "rawParsedJson",
        )
        has_journal = self._has_any_key(source, journal_keys)
        has_before = self._has_any_key(source, water_before_keys)
        has_after = self._has_any_key(source, water_after_keys)
        has_public = self._has_any_key(source, public_keys)
        has_playlist = self._has_any_key(source, playlist_keys)
        has_music_url = self._has_any_key(source, music_url_keys)
        has_top_tracks = self._has_any_key(source, top_tracks_keys)
        has_record = self._has_any_key(source, record_keys)
        if not has_record and not has_journal and not has_before and not has_after and not has_public and not has_playlist and not has_music_url and not has_top_tracks:
            return None, "수정할 필드가 없습니다."

        owner_id = self._text(user_id)
        rows = self.load_runs(include_media=False)
        updated = None
        next_rows = []
        for row in rows:
            if row.get("id") != run_id:
                next_rows.append(row)
                continue
            if owner_id and self._account_row_user_id(row) != owner_id:
                next_rows.append(row)
                continue

            next_row = dict(row)
            if has_record:
                merged = dict(next_row)
                for key, value in source.items():
                    if key in ("id", "user_id", "userId", "created_at", "createdAt"):
                        continue
                    merged[key] = value
                for alias, canonical in (
                    ("avgHeartRate", "avg_heart_rate"),
                    ("heart_rate", "avg_heart_rate"),
                    ("heartRate", "avg_heart_rate"),
                    ("elevationGain", "elevation_gain"),
                    ("imageUrl", "image_url"),
                    ("rawParsedJson", "raw_parsed_json"),
                ):
                    if alias in source and canonical not in source:
                        merged[canonical] = source.get(alias)
                merged["id"] = next_row.get("id")
                merged["user_id"] = next_row.get("user_id")
                merged["created_at"] = next_row.get("created_at")
                normalized = self.normalize_run(merged)
                if not normalized.get("date") or normalized.get("distance_km") is None:
                    return None, "날짜와 거리 값을 확인하지 못했습니다."
                next_row.update(normalized)
            if has_journal:
                text = self._journal(source.get("journal"))
                if text:
                    next_row["journal"] = text
                else:
                    next_row.pop("journal", None)
            if has_before:
                before = self._water_ml(self._first_value(source, water_before_keys))
                if before is None:
                    next_row.pop("water_before_ml", None)
                else:
                    next_row["water_before_ml"] = before
            if has_after:
                after = self._water_ml(self._first_value(source, water_after_keys))
                if after is None:
                    next_row.pop("water_after_ml", None)
                else:
                    next_row["water_after_ml"] = after
            if has_public:
                next_row["is_public"] = self._run_public(source)
            if has_playlist:
                playlist_name = self._playlist_name(self._first_value(source, playlist_keys))
                if playlist_name:
                    next_row["playlist_name"] = playlist_name
                else:
                    next_row.pop("playlist_name", None)
            if has_music_url:
                music_url = self._music_url(self._first_value(source, music_url_keys))
                if music_url:
                    next_row["music_url"] = music_url
                else:
                    next_row.pop("music_url", None)
            if has_top_tracks:
                top_tracks = self._top_tracks(self._first_value(source, top_tracks_keys))
                if top_tracks:
                    next_row["top_tracks"] = top_tracks
                else:
                    next_row.pop("top_tracks", None)
            updated = self.normalize_run(next_row)
            next_rows.append(updated)

        if not updated:
            return None, "수정할 러닝 기록을 찾지 못했습니다."

        self._write_runs(next_rows)
        self.delete_rest_day(updated.get("date"), updated.get("user_id"))
        self.recalculate_challenge_contributions()
        return self.run_detail(run_id, owner_id), ""

    def journal_runs(self, page=1, limit=20, user_id=None):
        try:
            page = max(1, int(page))
        except Exception:
            page = 1
        try:
            limit = min(100, max(1, int(limit)))
        except Exception:
            limit = 20

        rows = [row for row in self.load_runs(include_media=True, user_id=user_id) if self._journal(row.get("journal"))]
        total = len(rows)
        start = (page - 1) * limit
        end = start + limit
        return {
            "items": rows[start:end],
            "page": page,
            "limit": limit,
            "total": total,
            "has_more": end < total,
        }

    def recent_journals(self, limit=3, user_id=None):
        try:
            limit = max(1, int(limit))
        except Exception:
            limit = 3

        return [
            {
                "date": row.get("date"),
                "distance_km": row.get("distance_km"),
                "avg_pace": row.get("avg_pace"),
                "run_type": row.get("run_type"),
                "journal": row.get("journal"),
            }
            for row in self.load_runs(include_media=False, user_id=user_id)
            if self._journal(row.get("journal"))
        ][:limit]

    def delete_run(self, run_id, user_id=None):
        run_id = self._text(run_id)
        if not run_id:
            return False

        owner_id = self._text(user_id)
        rows = self.load_runs(include_media=False)
        deleted_rows = [
            row for row in rows
            if row.get("id") == run_id and (not owner_id or self._account_row_user_id(row) == owner_id)
        ]
        next_rows = [
            row for row in rows
            if row.get("id") != run_id or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        if len(next_rows) == len(rows):
            return False

        self._write_runs(next_rows)
        for row in deleted_rows:
            self._delete_run_image(row.get("image_url"))
            for item in self.media_for_run(row.get("id")):
                self.delete_run_media(item.get("id"))
        self.recalculate_challenge_contributions()
        return True

    def media_for_run(self, run_id, user_id=None):
        run_id = self._text(run_id)
        if not run_id:
            return []
        return [row for row in self.load_run_media(user_id=user_id) if row.get("run_id") == run_id]

    def save_run_media(self, run_id, file_storage, user_id=None):
        run_id = self._text(run_id)
        run = next((row for row in self.load_runs(include_media=False) if row.get("id") == run_id), None)
        if not run_id or not run:
            return None, "첨부할 러닝 기록을 찾지 못했습니다."
        owner_id = self._account_row_user_id(run)
        if user_id and owner_id != self._text(user_id):
            return None, "첨부할 러닝 기록을 찾지 못했습니다."
        if not owner_id:
            return None, "사용자 정보가 없습니다."
        if not file_storage:
            return None, "업로드할 사진/영상 파일이 필요합니다."

        media_type = self._media_type(file_storage)
        filepath, media_url, error = self._persist_uploaded_media(file_storage, media_type)
        if error:
            return None, error

        item = {
            "id": str(uuid.uuid4()),
            "run_id": run_id,
            "media_url": media_url,
            "media_type": media_type,
            "created_at": self._utcnow(),
            "user_id": owner_id,
        }

        rows = self.load_run_media()
        rows.insert(0, item)
        self._write_run_media(rows)
        return item, None

    def delete_run_media(self, media_id, user_id=None):
        media_id = self._text(media_id)
        if not media_id:
            return False

        owner_id = self._text(user_id)
        rows = self.load_run_media()
        deleted_rows = [
            row for row in rows
            if row.get("id") == media_id and (not owner_id or self._account_row_user_id(row) == owner_id)
        ]
        next_rows = [
            row for row in rows
            if row.get("id") != media_id or (owner_id and self._account_row_user_id(row) != owner_id)
        ]
        if len(next_rows) == len(rows):
            return False

        self._write_run_media(next_rows)
        for row in deleted_rows:
            self._delete_run_media_file(row.get("media_url"))
        return True

    def normalize_run_media(self, row):
        source = row if isinstance(row, dict) else {}
        media_type = self._text(source.get("media_type"))
        media_url = self._upload_url_storage_value(source.get("media_url"))
        run_id = self._text(source.get("run_id"))
        if media_type not in ("photo", "video") or not media_url or not run_id:
            return None

        return {
            "id": self._text(source.get("id")) or str(uuid.uuid4()),
            "run_id": run_id,
            "media_url": media_url,
            "media_type": media_type,
            "created_at": self._text(source.get("created_at")) or self._utcnow(),
            "user_id": self._text(source.get("user_id") or source.get("userId")),
        }

    def normalize_run(self, payload):
        row = payload if isinstance(payload, dict) else {}
        avg_pace = self._pace(self._first_value(row, ("avg_pace", "avgPace", "pace", "average_pace", "averagePace", "평균 페이스")))
        duration = self._duration(self._first_value(row, ("duration", "time", "elapsed_time", "elapsedTime", "moving_time", "movingTime", "시간")))
        distance = self._distance(row)
        distance = self._distance_from_pace_duration(distance, avg_pace, duration)

        return {
            "id": self._text(row.get("id")),
            "date": self._date(self._first_value(row, self.DATE_KEYS)),
            "distance_km": distance,
            "avg_pace": avg_pace,
            "duration": duration,
            "run_type": self._run_type(self._first_value(row, ("run_type", "runType", "running_type", "runningType", "type", "종류", "러닝종류", "러닝 종류"))),
            "start_time": self._start_time(self._first_value(row, ("start_time", "startTime", "started_at", "startedAt", "start_at", "startAt", "workout_start_time", "workoutStartTime", "시작시간", "시작 시간", "출발시간", "출발 시간"))),
            "calories": self._int(row.get("calories")),
            "avg_heart_rate": self._int(row.get("avg_heart_rate")),
            "cadence": self._int(row.get("cadence")),
            "elevation_gain": self._float(row.get("elevation_gain")),
            "water_before_ml": self._water_ml(self._first_value(row, ("water_before_ml", "waterBeforeMl", "water_before", "waterBefore", "before_water_ml", "beforeWaterMl", "러닝 전 수분", "러닝전수분", "러닝 전 물", "운동 전 수분"))),
            "water_after_ml": self._water_ml(self._first_value(row, ("water_after_ml", "waterAfterMl", "water_after", "waterAfter", "after_water_ml", "afterWaterMl", "러닝 후 수분", "러닝후수분", "러닝 후 물", "운동 후 수분"))),
            "image_url": self._upload_url_storage_value(row.get("image_url")),
            "journal": self._journal(row.get("journal")),
            "playlist_name": self._playlist_name(self._first_value(row, ("playlist_name", "playlistName", "music_playlist_name", "musicPlaylistName"))),
            "music_url": self._music_url(self._first_value(row, ("music_url", "musicUrl", "apple_music_url", "appleMusicUrl"))),
            "top_tracks": self._top_tracks(self._first_value(row, ("top_tracks", "topTracks", "music_tracks", "musicTracks"))),
            "is_public": self._run_public(row),
            "user_id": self._text(row.get("user_id") or row.get("userId")),
            "raw_parsed_json": row.get("raw_parsed_json") if isinstance(row.get("raw_parsed_json"), dict) else None,
            "created_at": self._text(row.get("created_at")),
        }

    def runs_for_month(self, year_month=None, user_id=None):
        rows = self.load_runs(user_id=user_id)
        if not year_month:
            year_month = self.latest_year_month(rows)

        if not year_month:
            return []

        return [row for row in rows if str(row.get("date") or "").startswith(year_month)]

    def latest_year_month(self, rows=None):
        rows = rows if rows is not None else self.load_runs()
        if rows:
            return str(rows[0].get("date") or "")[:7]
        return datetime.date.today().strftime("%Y-%m")

    def weekly_stats(self, year_week=None, user_id=None):
        rows = self.load_runs(user_id=user_id)
        if not rows:
            return {"points": [], "distanceFooter": "러닝 기록 없음", "paceFooter": "러닝 기록 없음"}

        anchor = self._anchor_week_date(rows, year_week)
        starts = [anchor - datetime.timedelta(days=anchor.weekday() + (6 - i) * 7) for i in range(7)]
        points = []
        for start in starts:
            end = start + datetime.timedelta(days=7)
            group = [row for row in rows if start <= self._date_obj(row.get("date")) < end]
            points.append(self._period_point(group, start, f"{start.month}/{start.day}"))

        return {
            "points": points,
            "distanceFooter": self._distance_footer(points, "이번주", "지난주"),
            "paceFooter": self._pace_footer(points, "이번주", "지난주"),
        }

    def monthly_stats(self, year_month=None, user_id=None):
        rows = self.load_runs(user_id=user_id)
        if not rows:
            return {"points": [], "distanceFooter": "러닝 기록 없음", "paceFooter": "러닝 기록 없음"}

        anchor_month = year_month or str(rows[0].get("date") or "")[:7]
        anchor_year, anchor_mon = [int(part) for part in anchor_month.split("-")]
        months = []
        for offset in range(5, -1, -1):
            total_month = anchor_year * 12 + anchor_mon - 1 - offset
            year = total_month // 12
            month = total_month % 12 + 1
            months.append((year, month))

        points = []
        for year, month in months:
            key = f"{year:04d}-{month:02d}"
            group = [row for row in rows if str(row.get("date") or "").startswith(key)]
            start = datetime.date(year, month, 1)
            points.append(self._period_point(group, start, f"{month}월"))

        return {
            "points": points,
            "distanceFooter": self._distance_footer(points, "이번달", "지난달"),
            "paceFooter": self._pace_footer(points, "이번달", "지난달"),
        }

    def summary(self, user_id=None):
        rows = self.load_runs(user_id=user_id)
        if not rows:
            return {
                "metrics": [
                    {"label": "평균 심박수", "value": "-", "unit": "bpm"},
                    {"label": "평균 케이던스", "value": "-", "unit": "spm"},
                    {"label": "최저 심박", "value": "-", "unit": "bpm"},
                    {"label": "최고 케이던스", "value": "-", "unit": "spm"},
                ],
                "prs": {
                    "longestDistance": {"label": "최장거리", "value": "-", "date": "-"},
                    "bestPace": {"label": "최고페이스", "value": "-", "date": "-"},
                },
            }

        heart_rates = [row["avg_heart_rate"] for row in rows if row.get("avg_heart_rate") is not None]
        cadences = [row["cadence"] for row in rows if row.get("cadence") is not None]
        longest = max(rows, key=lambda row: row.get("distance_km") or 0)
        pace_rows = [row for row in rows if self.pace_to_seconds(row.get("avg_pace")) is not None]
        best_pace = min(pace_rows, key=lambda row: self.pace_to_seconds(row.get("avg_pace"))) if pace_rows else None

        return {
            "metrics": [
                {"label": "평균 심박수", "value": self._avg_text(heart_rates), "unit": "bpm"},
                {"label": "평균 케이던스", "value": self._avg_text(cadences), "unit": "spm"},
                {"label": "최저 심박", "value": str(min(heart_rates)) if heart_rates else "-", "unit": "bpm"},
                {"label": "최고 케이던스", "value": str(max(cadences)) if cadences else "-", "unit": "spm"},
            ],
            "prs": {
                "longestDistance": {
                    "label": "최장거리",
                    "value": self.km_text(longest.get("distance_km")),
                    "date": self.display_date(longest.get("date")),
                },
                "bestPace": {
                    "label": "최고페이스",
                    "value": best_pace.get("avg_pace") if best_pace else "-",
                    "date": self.display_date(best_pace.get("date")) if best_pace else "-",
                },
            },
        }

    def public_user_stats(self, user_id, include_legacy=False):
        target_id = self._text(user_id)
        if not target_id:
            return self._empty_public_user_stats()

        rows = []
        for row in self.load_runs(include_media=False):
            owner_id = self._text(row.get("user_id") or row.get("userId"))
            if owner_id == target_id or (include_legacy and not owner_id):
                rows.append(row)

        if not rows:
            return self._empty_public_user_stats()

        this_month = datetime.date.today().strftime("%Y-%m")
        month_rows = [row for row in rows if str(row.get("date") or "").startswith(this_month)]
        total_distance = round(sum(row.get("distance_km") or 0 for row in rows), 2)
        month_distance = round(sum(row.get("distance_km") or 0 for row in month_rows), 2)
        longest = max(rows, key=lambda row: row.get("distance_km") or 0)
        pace_rows = [row for row in rows if self.pace_to_seconds(row.get("avg_pace")) is not None]
        best_pace = min(pace_rows, key=lambda row: self.pace_to_seconds(row.get("avg_pace"))) if pace_rows else None

        return {
            "total_distance_km": total_distance,
            "total_distance_text": self.km_text(total_distance),
            "run_count": len(rows),
            "this_month_distance_km": month_distance,
            "this_month_distance_text": self.km_text(month_distance),
            "this_month_run_count": len(month_rows),
            "longest_distance_km": round(longest.get("distance_km") or 0, 2),
            "longest_distance_text": self.km_text(longest.get("distance_km") or 0),
            "best_pace": best_pace.get("avg_pace") if best_pace else "-",
            "latest_run_date": rows[0].get("date") or "",
            "latest_run_date_text": self.display_date(rows[0].get("date")) if rows[0].get("date") else "-",
        }

    def _empty_public_user_stats(self):
        return {
            "total_distance_km": 0,
            "total_distance_text": "0.00km",
            "run_count": 0,
            "this_month_distance_km": 0,
            "this_month_distance_text": "0.00km",
            "this_month_run_count": 0,
            "longest_distance_km": 0,
            "longest_distance_text": "0.00km",
            "best_pace": "-",
            "latest_run_date": "",
            "latest_run_date_text": "-",
        }

    def stats(self, year_month=None, user_id=None):
        rows = self.load_runs(user_id=user_id)
        target_month = year_month or self.latest_year_month(rows)
        return {
            "year_month": target_month,
            "summary": self.summary(user_id=user_id),
            "runTypeLabels": self.RUN_TYPE_LABELS,
            "runTypeStats": self.run_type_stats(target_month, rows),
            "hydrationStats": self.hydration_stats(target_month, rows),
            "trainingLoad": self.training_load(rows=rows),
        }

    def training_load(self, anchor_date=None, rows=None):
        rows = rows if rows is not None else self.load_runs(include_media=False)
        rows = sorted(rows, key=lambda row: row.get("date") or "", reverse=True)
        anchor = self._date_obj(anchor_date) or datetime.date.today()
        week_start = anchor - datetime.timedelta(days=anchor.weekday())
        previous_week_start = week_start - datetime.timedelta(days=7)
        next_week_start = week_start + datetime.timedelta(days=7)

        streak = self._recent_run_streak(rows, anchor)
        current_week_distance = self._distance_between(rows, week_start, next_week_start)
        previous_week_distance = self._distance_between(rows, previous_week_start, week_start)
        weekly_increase_pct = None
        if previous_week_distance > 0:
            weekly_increase_pct = round(((current_week_distance - previous_week_distance) / previous_week_distance) * 100, 1)

        heart_summary = self._heart_rate_load(rows)
        negative_condition_streak = self._negative_condition_streak(rows)

        reasons = []
        if streak >= self.REST_STREAK_DAYS:
            reasons.append(f"{streak}일 연속 달렸어")
        if weekly_increase_pct is not None and weekly_increase_pct >= self.REST_WEEKLY_INCREASE_PCT:
            reasons.append(
                f"이번주 벌써 {self.km_text(current_week_distance)} 뛰었고 지난주보다 {round(weekly_increase_pct)}% 늘었어"
            )
        if heart_summary.get("elevated"):
            reasons.append(
                f"최근 3회 평균 심박이 {heart_summary.get('recent_avg_heart_rate')}bpm으로 평소보다 {heart_summary.get('heart_rate_delta_bpm')}bpm 높아"
            )
        if negative_condition_streak >= 2:
            reasons.append(f"최근 컨디션이 {negative_condition_streak}회 연속 좋지 않았어")

        recommend_rest = bool(reasons)
        status = "danger" if recommend_rest else "safe"
        if not recommend_rest:
            if weekly_increase_pct is not None and weekly_increase_pct >= self.CAUTION_WEEKLY_INCREASE_PCT:
                status = "caution"
            elif streak >= self.REST_STREAK_DAYS - 1:
                status = "caution"
            elif heart_summary.get("heart_rate_delta_bpm") is not None and heart_summary.get("heart_rate_delta_bpm") >= 7:
                status = "caution"
            elif negative_condition_streak == 1:
                status = "caution"

        reason = self._training_load_reason(reasons, status, weekly_increase_pct, rows)
        return {
            "streak": streak,
            "weekly_increase_pct": weekly_increase_pct,
            "recommend_rest": recommend_rest,
            "reason": reason,
            "reasons": reasons,
            "current_week_distance_km": current_week_distance,
            "previous_week_distance_km": previous_week_distance,
            "recent_avg_heart_rate": heart_summary.get("recent_avg_heart_rate"),
            "baseline_avg_heart_rate": heart_summary.get("baseline_avg_heart_rate"),
            "heart_rate_delta_bpm": heart_summary.get("heart_rate_delta_bpm"),
            "negative_condition_streak": negative_condition_streak,
            "status": status,
            "status_label": {"safe": "안전", "caution": "주의", "danger": "위험"}.get(status, "안전"),
        }

    def hydration_stats(self, year_month=None, rows=None):
        rows = rows if rows is not None else self.load_runs()
        target_month = year_month or self.latest_year_month(rows)
        period_rows = [row for row in rows if target_month and str(row.get("date") or "").startswith(target_month)]
        hydrated_rows = [row for row in period_rows if self._run_water_total(row) > 0]
        total_ml = sum(self._run_water_total(row) for row in hydrated_rows)
        total_distance = sum(row.get("distance_km") or 0 for row in hydrated_rows)
        long_rows = [row for row in period_rows if (row.get("distance_km") or 0) >= 8]
        low_long_rows = [
            row for row in long_rows
            if self._run_water_total(row) < self._hydration_target_ml(row.get("distance_km") or 0)
        ]

        return {
            "runCount": len(period_rows),
            "loggedRunCount": len(hydrated_rows),
            "averageMlPerRun": round(total_ml / len(hydrated_rows)) if hydrated_rows else 0,
            "mlPerKm": round(total_ml / total_distance) if total_distance else 0,
            "longRunCount": len(long_rows),
            "lowLongRunCount": len(low_long_rows),
            "recent": [
                {
                    "date": row.get("date"),
                    "distance_km": row.get("distance_km"),
                    "water_before_ml": row.get("water_before_ml"),
                    "water_after_ml": row.get("water_after_ml"),
                    "water_total_ml": self._run_water_total(row),
                    "target_ml": self._hydration_target_ml(row.get("distance_km") or 0),
                }
                for row in period_rows[:8]
            ],
        }

    def hydration_context(self, user_id=None):
        rows = self.load_runs(include_media=False, user_id=user_id)
        target_month = self.latest_year_month(rows)
        stats = self.hydration_stats(target_month, rows)
        latest_low = None
        for row in rows[:8]:
            distance = row.get("distance_km") or 0
            total = self._run_water_total(row)
            if distance >= 8 and total < self._hydration_target_ml(distance):
                latest_low = {
                    "date": row.get("date"),
                    "distance_km": distance,
                    "water_total_ml": total,
                    "target_ml": self._hydration_target_ml(distance),
                }
                break

        return {
            "year_month": target_month,
            "stats": stats,
            "latest_long_run_low_hydration": latest_low,
        }

    def run_type_stats(self, year_month=None, rows=None):
        rows = rows if rows is not None else self.load_runs()
        target_month = year_month or self.latest_year_month(rows)
        month_rows = [row for row in rows if target_month and str(row.get("date") or "").startswith(target_month)]
        total_count = len(month_rows)
        total_distance = sum(row.get("distance_km") or 0 for row in month_rows)
        stats = []

        for run_type in self.RUN_TYPE_ORDER:
            group = [row for row in month_rows if self._run_type(row.get("run_type")) == run_type]
            distance = round(sum(row.get("distance_km") or 0 for row in group), 2)
            duration_seconds = sum(self._run_duration_seconds(row) or 0 for row in group)
            pace_seconds = round(duration_seconds / distance) if distance and duration_seconds else None
            ratio = round((len(group) / total_count) * 100, 1) if total_count else 0
            distance_ratio = round((distance / total_distance) * 100, 1) if total_distance else 0
            stats.append({
                "runType": run_type,
                "label": self.RUN_TYPE_LABELS.get(run_type, run_type),
                "count": len(group),
                "distanceKm": distance,
                "distanceText": self.km_text(distance) if distance else "0.00km",
                "paceSeconds": pace_seconds,
                "avgPace": self.seconds_to_pace(pace_seconds),
                "ratio": ratio,
                "distanceRatio": distance_ratio,
            })

        return stats

    def pace_to_seconds(self, pace):
        if not pace:
            return None

        text = str(pace).strip()
        match = re.search(r"(\d{1,2})\s*[':]\s*(\d{1,2})", text)
        if not match:
            return None

        return int(match.group(1)) * 60 + int(match.group(2))

    def seconds_to_pace(self, seconds):
        if seconds is None:
            return "-"

        seconds = int(round(seconds))
        minutes = seconds // 60
        remain = seconds % 60
        return f"{minutes}'{remain:02d}\""

    def km_text(self, value):
        if value is None:
            return "-"
        return f"{round(float(value), 2):.2f}km"

    def display_date(self, value):
        date = self._date_obj(value)
        if not date:
            return "-"
        return date.strftime("%Y.%m.%d")

    def _write_runs(self, rows):
        clean_rows = []
        for row in rows:
            clean = dict(row) if isinstance(row, dict) else {}
            clean.pop("media", None)
            clean_rows.append(clean)

        if self._write_runs_to_db(clean_rows):
            if self._runs_json_mirror_enabled():
                self._write_runs_to_json(clean_rows)
            return

        self._write_runs_to_json(clean_rows)

    def _write_run_media(self, rows):
        path = self.run_media_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        media = []
        for row in rows:
            item = self.normalize_run_media(row)
            if item:
                media.append(item)

        media = sorted(media, key=lambda row: row.get("created_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(media, fp, ensure_ascii=False, indent=2)

    def _write_run_reactions(self, rows):
        path = self.run_reactions_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        reactions = []
        seen = set()
        for row in rows:
            reaction = self.normalize_run_reaction(row)
            if not reaction:
                continue
            key = (reaction.get("run_id"), reaction.get("user_id"), reaction.get("type"))
            if key in seen:
                continue
            reactions.append(reaction)
            seen.add(key)

        reactions = sorted(reactions, key=lambda row: row.get("created_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(reactions, fp, ensure_ascii=False, indent=2)

    def _write_run_comments(self, rows):
        path = self.run_comments_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        comments = []
        seen = set()
        for row in rows:
            comment = self.normalize_run_comment(row)
            if not comment or comment.get("id") in seen:
                continue
            comments.append(comment)
            seen.add(comment.get("id"))

        comments = sorted(comments, key=lambda row: row.get("created_at") or "")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(comments, fp, ensure_ascii=False, indent=2)

    def _write_notifications(self, rows):
        path = self.notifications_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        notifications = []
        seen = set()
        for row in rows:
            item = self.normalize_notification(row)
            if not item or item.get("id") in seen:
                continue
            notifications.append(item)
            seen.add(item.get("id"))

        notifications = sorted(notifications, key=lambda row: row.get("created_at") or "", reverse=True)[:500]
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(notifications, fp, ensure_ascii=False, indent=2)

    def _write_rest_days(self, rows):
        path = self.rest_days_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(rows, fp, ensure_ascii=False, indent=2)

    def _write_day_notes(self, rows):
        path = self.day_notes_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        notes = []
        for row in rows:
            note = self.normalize_day_note(row)
            if note:
                notes.append(note)

        notes = sorted(notes, key=lambda row: row.get("date") or "")
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(notes, fp, ensure_ascii=False, indent=2)

    def _write_weights(self, rows):
        path = self.weight_logs_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        weights = []
        for row in rows:
            log = self.normalize_weight_log(row)
            if log:
                weights.append(log)

        weights = sorted(weights, key=lambda row: row.get("date") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(weights, fp, ensure_ascii=False, indent=2)

    def _load_weight_settings_rows(self):
        path = self.weight_settings_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception:
            return []

        if isinstance(payload, dict):
            if "target_weight_kg" in payload or "targetWeightKg" in payload or "target_weight" in payload:
                payload = [payload]
            else:
                rows = []
                for user_id, value in payload.items():
                    if isinstance(value, dict):
                        row = dict(value)
                        row.setdefault("user_id", user_id)
                    else:
                        row = {"user_id": user_id, "target_weight_kg": value}
                    rows.append(row)
                payload = rows
        if not isinstance(payload, list):
            return []

        settings = []
        for row in payload:
            source = row if isinstance(row, dict) else {}
            target = self._weight(source.get("target_weight_kg", source.get("targetWeightKg", source.get("target_weight"))))
            if target is None:
                continue
            settings.append({
                "target_weight_kg": target,
                "updated_at": self._text(source.get("updated_at")) or self._utcnow(),
                "user_id": self._text(source.get("user_id") or source.get("userId")),
            })
        return settings

    def _write_weight_settings(self, rows):
        path = self.weight_settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        settings = []
        for row in rows:
            source = row if isinstance(row, dict) else {}
            target = self._weight(source.get("target_weight_kg", source.get("targetWeightKg", source.get("target_weight"))))
            if target is None:
                continue
            settings.append({
                "target_weight_kg": target,
                "updated_at": self._text(source.get("updated_at")) or self._utcnow(),
                "user_id": self._text(source.get("user_id") or source.get("userId")),
            })
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(settings, fp, ensure_ascii=False, indent=2)

    def _load_cycle_settings_rows(self):
        payload = self._load_account_json(self.cycle_settings_path(), [])
        if isinstance(payload, dict):
            if "enabled" in payload or "cycle_enabled" in payload or "cycleEnabled" in payload:
                payload = [payload]
            else:
                rows = []
                for user_id, value in payload.items():
                    if isinstance(value, dict):
                        row = dict(value)
                        row.setdefault("user_id", user_id)
                    else:
                        row = {"user_id": user_id, "enabled": value}
                    rows.append(row)
                payload = rows
        if not isinstance(payload, list):
            return []

        settings = []
        for row in payload:
            setting = self.normalize_cycle_setting(row)
            if setting:
                settings.append(setting)
        return settings

    def normalize_cycle_setting(self, row):
        source = row if isinstance(row, dict) else {}
        owner_id = self._text(source.get("user_id") or source.get("userId"))
        if not owner_id:
            return None

        enabled_value = source.get("enabled")
        if enabled_value is None:
            enabled_value = source.get("cycle_enabled", source.get("cycleEnabled"))

        return {
            "enabled": self._bool(enabled_value),
            "updated_at": self._text(source.get("updated_at") or source.get("updatedAt")) or self._utcnow(),
            "user_id": owner_id,
        }

    def _write_cycle_settings(self, rows):
        path = self.cycle_settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        settings_by_user = {}
        for row in rows:
            setting = self.normalize_cycle_setting(row)
            if not setting:
                continue
            owner_id = setting.get("user_id")
            current = settings_by_user.get(owner_id)
            if not current or (setting.get("updated_at") or "") >= (current.get("updated_at") or ""):
                settings_by_user[owner_id] = setting

        settings = sorted(settings_by_user.values(), key=lambda row: row.get("updated_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(settings, fp, ensure_ascii=False, indent=2)

    def _write_cycles(self, rows):
        path = self.cycle_logs_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        cycles = []
        for row in rows:
            log = self.normalize_cycle_log(row)
            if log:
                cycles.append(log)

        cycles = sorted(cycles, key=lambda row: row.get("start_date") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(cycles, fp, ensure_ascii=False, indent=2)

    def _write_chat_sessions(self, rows):
        path = self.chat_history_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        sessions = []
        for row in rows:
            session = self.normalize_chat_session(row)
            if session:
                sessions.append(session)

        sessions = sorted(sessions, key=lambda row: row.get("updated_at") or "", reverse=True)[:80]
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(sessions, fp, ensure_ascii=False, indent=2)

    def _write_ai_usage(self, rows):
        path = self.ai_usage_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        usage_rows = []
        seen = set()
        for row in rows:
            usage = self.normalize_ai_usage(row)
            if not usage:
                continue
            key = (usage.get("user_id"), usage.get("action"))
            if key in seen:
                continue
            seen.add(key)
            usage_rows.append(usage)

        usage_rows = sorted(usage_rows, key=lambda row: row.get("updated_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(usage_rows, fp, ensure_ascii=False, indent=2)

    def _write_ai_rate_limits(self, rows):
        path = self.ai_rate_limits_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        rate_limit_rows = []
        seen = set()
        for row in rows:
            rate_limit = self.normalize_ai_rate_limit(row)
            if not rate_limit:
                continue
            key = (rate_limit.get("user_id"), rate_limit.get("action"))
            if key in seen:
                continue
            seen.add(key)
            rate_limit_rows.append(rate_limit)

        rate_limit_rows = sorted(rate_limit_rows, key=lambda row: row.get("updated_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(rate_limit_rows, fp, ensure_ascii=False, indent=2)

    def _write_goals(self, rows):
        path = self.goals_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        goals = []
        seen = set()
        for row in rows:
            goal = self.normalize_goal(row)
            if not goal:
                continue
            key = (goal.get("user_id"), goal.get("year_month"), goal.get("goal_type"))
            if key in seen:
                continue
            goals.append(goal)
            seen.add(key)

        goals = sorted(goals, key=lambda row: (row.get("year_month") or "", -self._goal_sort(row.get("goal_type"))), reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(goals, fp, ensure_ascii=False, indent=2)

    def _write_ranking_social(self, data):
        path = self.ranking_social_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        source = data if isinstance(data, dict) else {}
        payload = {
            "profiles": source.get("profiles") if isinstance(source.get("profiles"), list) else [],
            "follows": source.get("follows") if isinstance(source.get("follows"), list) else [],
            "weekly_winners": source.get("weekly_winners") if isinstance(source.get("weekly_winners"), list) else [],
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def _load_account_json(self, path, fallback):
        if not os.path.exists(path):
            return fallback
        try:
            with open(path, "r", encoding="utf-8") as fp:
                return json.load(fp)
        except Exception:
            return fallback

    def _write_account_json(self, path, payload):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def _account_row_user_id(self, row):
        if not isinstance(row, dict):
            return ""
        return self._text(
            row.get("user_id")
            or row.get("userId")
            or row.get("owner_id")
            or row.get("ownerId")
            or row.get("creator_id")
            or row.get("creatorId")
        )

    def _row_belongs_to_user(self, row, user_id, include_legacy=False):
        owner_id = self._account_row_user_id(row)
        if owner_id:
            return owner_id == user_id or (include_legacy and owner_id == "local-user")
        return bool(include_legacy)

    def _user_scoped_rows(self, rows, user_id=None, include_legacy=False):
        owner_id = self._text(user_id)
        if not owner_id:
            return list(rows or [])
        return [
            row for row in (rows or [])
            if self._row_belongs_to_user(row, owner_id, include_legacy)
        ]

    def _is_account_row(self, row, user_id, include_legacy=True):
        owner_id = self._account_row_user_id(row)
        if owner_id:
            return owner_id == user_id
        return bool(include_legacy)

    def _delete_account_collection(self, path, user_id, include_legacy, summary_key, summary):
        payload = self._load_account_json(path, [])
        if isinstance(payload, dict):
            if include_legacy:
                summary[summary_key] += len(payload)
                self._write_account_json(path, {})
            return
        if not isinstance(payload, list):
            return

        next_rows = []
        deleted = 0
        for row in payload:
            if self._is_account_row(row, user_id, include_legacy):
                deleted += 1
            else:
                next_rows.append(row)

        if deleted:
            summary[summary_key] += deleted
            self._write_account_json(path, next_rows)

    def _delete_account_runs(self, user_id, include_legacy, summary):
        db = self._running_log_db()
        if db is not None:
            deleted_rows = [
                row for row in self.load_runs(include_media=False)
                if self._is_account_row(row, user_id, include_legacy)
            ]
            deleted_run_ids = {
                self._text(row.get("id"))
                for row in deleted_rows
                if self._text(row.get("id"))
            }
            if deleted_rows:
                file_urls = [
                    self._text(row.get("image_url") or row.get("imageUrl"))
                    for row in deleted_rows
                    if self._text(row.get("image_url") or row.get("imageUrl"))
                ]
                try:
                    database = db.orm._meta.database
                    database.connect(reuse_if_open=True)
                    with database.atomic():
                        for run_id in deleted_run_ids:
                            db.delete(id=run_id)
                except Exception:
                    return set()

                summary["running_logs"] += len(deleted_rows)
                summary["files"].extend(file_urls)

            json_rows = self._load_account_json(self.data_path(), [])
            if isinstance(json_rows, list):
                next_rows = [
                    row for row in json_rows
                    if not self._is_account_row(row, user_id, include_legacy)
                ]
                if len(next_rows) != len(json_rows):
                    self._write_account_json(self.data_path(), next_rows)
            return deleted_run_ids

        rows = self._load_account_json(self.data_path(), [])
        if not isinstance(rows, list):
            return set()

        next_rows = []
        deleted_run_ids = set()
        for row in rows:
            if self._is_account_row(row, user_id, include_legacy):
                summary["running_logs"] += 1
                if isinstance(row, dict):
                    run_id = self._text(row.get("id"))
                    if run_id:
                        deleted_run_ids.add(run_id)
                    image_url = self._text(row.get("image_url") or row.get("imageUrl"))
                    if image_url:
                        summary["files"].append(image_url)
            else:
                next_rows.append(row)

        if summary["running_logs"]:
            self._write_account_json(self.data_path(), next_rows)
        return deleted_run_ids

    def _delete_account_run_media(self, user_id, include_legacy, deleted_run_ids, summary):
        rows = self._load_account_json(self.run_media_path(), [])
        if not isinstance(rows, list):
            return

        next_rows = []
        for row in rows:
            run_id = self._text((row or {}).get("run_id") or (row or {}).get("runId")) if isinstance(row, dict) else ""
            owned = self._is_account_row(row, user_id, False)
            legacy_or_orphan = include_legacy and not run_id and not self._account_row_user_id(row)
            if run_id in deleted_run_ids or owned or legacy_or_orphan:
                summary["run_media"] += 1
                if isinstance(row, dict):
                    media_url = self._text(row.get("media_url") or row.get("mediaUrl"))
                    if media_url:
                        summary["files"].append(media_url)
            else:
                next_rows.append(row)

        if summary["run_media"]:
            self._write_account_json(self.run_media_path(), next_rows)

    def _delete_account_run_social(self, user_id, include_legacy, deleted_run_ids, summary):
        for path, summary_key in (
            (self.run_reactions_path(), "reactions"),
            (self.run_comments_path(), "comments"),
        ):
            rows = self._load_account_json(path, [])
            if not isinstance(rows, list):
                continue

            next_rows = []
            for row in rows:
                run_id = self._text((row or {}).get("run_id") or (row or {}).get("runId")) if isinstance(row, dict) else ""
                owned = self._is_account_row(row, user_id, False)
                legacy_or_orphan = include_legacy and not run_id and not self._account_row_user_id(row)
                if run_id in deleted_run_ids or owned or legacy_or_orphan:
                    summary[summary_key] += 1
                else:
                    next_rows.append(row)

            if summary[summary_key]:
                self._write_account_json(path, next_rows)

        rows = self._load_account_json(self.notifications_path(), [])
        if not isinstance(rows, list):
            return

        next_rows = []
        for row in rows:
            if not isinstance(row, dict):
                next_rows.append(row)
                continue
            run_id = self._text(row.get("run_id") or row.get("runId"))
            recipient_id = self._text(row.get("user_id") or row.get("userId"))
            actor_id = self._text(row.get("actor_id") or row.get("actorId"))
            if run_id in deleted_run_ids or recipient_id == user_id or actor_id == user_id:
                summary["notifications"] += 1
            else:
                next_rows.append(row)

        if summary["notifications"]:
            self._write_account_json(self.notifications_path(), next_rows)

    def _delete_account_challenges(self, user_id, summary):
        rows = self._load_account_json(self.challenges_path(), [])
        if not isinstance(rows, list):
            return

        next_rows = []
        for row in rows:
            if not isinstance(row, dict):
                next_rows.append(row)
                continue

            creator_id = self._text(row.get("creator_id") or row.get("creatorId"))
            creator_deleted = creator_id == user_id
            members = row.get("members") if isinstance(row.get("members"), list) else []
            next_members = []
            removed_member = False
            for member in members:
                member_user_id = self._text((member or {}).get("user_id") or (member or {}).get("userId")) if isinstance(member, dict) else ""
                if member_user_id == user_id:
                    removed_member = True
                    continue
                next_members.append(member)

            if creator_deleted and not next_members:
                summary["challenges_deleted"] += 1
                continue

            next_row = dict(row)
            if creator_deleted:
                next_row["creator_id"] = "deleted-user"
                next_row["creator_name"] = "탈퇴한 사용자"
                summary["challenges_anonymized"] += 1
            if removed_member:
                next_row["members"] = next_members
                summary["social_relations"] += 1
            next_rows.append(next_row)

        self._write_account_json(self.challenges_path(), next_rows)

    def _delete_account_social(self, user_id, summary):
        social = self._load_account_json(self.ranking_social_path(), {"profiles": [], "follows": [], "weekly_winners": []})
        if not isinstance(social, dict):
            return

        profiles = social.get("profiles") if isinstance(social.get("profiles"), list) else []
        follows = social.get("follows") if isinstance(social.get("follows"), list) else []
        winners = social.get("weekly_winners") if isinstance(social.get("weekly_winners"), list) else []

        next_profiles = [
            row for row in profiles
            if self._text((row or {}).get("user_id") or (row or {}).get("userId")) != user_id
        ]
        next_follows = []
        removed_follows = 0
        for row in follows:
            if not isinstance(row, dict):
                next_follows.append(row)
                continue
            follower_id = self._text(row.get("follower_id") or row.get("followerId"))
            following_id = self._text(row.get("following_id") or row.get("followingId"))
            if follower_id == user_id or following_id == user_id:
                removed_follows += 1
            else:
                next_follows.append(row)

        next_winners = [
            row for row in winners
            if self._text((row or {}).get("user_id") or (row or {}).get("userId")) != user_id
        ]

        removed = (len(profiles) - len(next_profiles)) + removed_follows + (len(winners) - len(next_winners))
        if removed:
            summary["social_relations"] += removed
            self._write_account_json(self.ranking_social_path(), {
                "profiles": next_profiles,
                "follows": next_follows,
                "weekly_winners": next_winners,
            })

    def _ranking_period(self, period, year_week=None):
        normalized = self._text(period) or "this_week"
        today = datetime.date.today()
        if normalized == "last_week":
            start = self._week_start(today) - datetime.timedelta(days=7)
            end = start + datetime.timedelta(days=6)
            return {
                "period": "last_week",
                "period_key": self._year_week(start),
                "start": start,
                "end": end,
            }

        if normalized == "this_month":
            start = today.replace(day=1)
            end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            return {
                "period": "this_month",
                "period_key": today.strftime("%Y-%m"),
                "start": start,
                "end": end,
            }

        try:
            start = self._anchor_week_date([{"date": today.isoformat()}], year_week)
        except Exception:
            start = today
        start = self._week_start(start)
        return {
            "period": "this_week",
            "period_key": self._year_week(start),
            "start": start,
            "end": start + datetime.timedelta(days=6),
        }

    def _ranking_period_label(self, start, end):
        if not start or not end:
            return ""
        return f"{start.month}월 {start.day}일 - {end.month}월 {end.day}일"

    def _ranking_profiles(self, social, users, viewer_id, viewer_name, viewer_profile_image=""):
        profiles = {}
        for row in (social.get("profiles") if isinstance(social, dict) else []) or []:
            user_id = self._text((row or {}).get("user_id") or (row or {}).get("userId"))
            profile = self._ranking_profile(row, user_id)
            if profile:
                profiles[profile["user_id"]] = profile

        for row in users or []:
            if not isinstance(row, dict):
                continue
            user_id = self._text(row.get("id") or row.get("user_id") or row.get("userId"))
            if not user_id:
                continue
            current = profiles.get(user_id) or self._ranking_profile({}, user_id)
            current["name"] = self._text(row.get("name")) or current.get("name") or "러너"
            current["profile_image"] = self._text(row.get("profile_image") or row.get("profileImage")) or current.get("profile_image") or ""
            profiles[user_id] = current

        for row in self.load_runs(include_media=False):
            user_id = self._text(row.get("user_id") or row.get("userId")) or viewer_id
            if user_id and user_id not in profiles:
                profiles[user_id] = self._ranking_profile({}, user_id)

        current = profiles.get(viewer_id) or self._ranking_profile({}, viewer_id)
        current["name"] = viewer_name or current.get("name") or "나"
        current["profile_image"] = viewer_profile_image or current.get("profile_image") or ""
        if "ranking_enabled" not in current:
            current["ranking_enabled"] = True
        if "ranking_consent" not in current:
            current["ranking_consent"] = True
        profiles[viewer_id] = current
        return profiles

    def _ranking_profile(self, row, fallback_user_id):
        source = row if isinstance(row, dict) else {}
        user_id = self._text(source.get("user_id") or source.get("userId") or fallback_user_id)
        if not user_id:
            return None

        is_private = self._bool(source.get("is_private") if "is_private" in source else source.get("private"))
        return {
            "user_id": user_id,
            "name": self._text(source.get("name")) or ("나" if user_id == "local-user" else "러너"),
            "profile_image": self._text(source.get("profile_image") or source.get("profileImage")),
            "is_private": is_private,
            "ranking_enabled": self._bool(source.get("ranking_enabled") if "ranking_enabled" in source else source.get("rankingEnabled"), default=True),
            "ranking_consent": self._bool(source.get("ranking_consent") if "ranking_consent" in source else source.get("rankingConsent"), default=True),
        }

    def _ranking_target_user_ids(self, social, profiles, viewer_id):
        follows = social.get("follows") if isinstance(social, dict) else []
        target_ids = {viewer_id}
        has_follow_rules = False

        for row in follows or []:
            if not isinstance(row, dict):
                continue
            follower_id = self._text(row.get("follower_id") or row.get("followerId"))
            following_id = self._text(row.get("following_id") or row.get("followingId"))
            status = self._text(row.get("status")) or "accepted"
            if status not in ("accepted", "active", "following", "mutual"):
                continue
            if follower_id == viewer_id and following_id:
                target_ids.add(following_id)
                has_follow_rules = True
            if following_id == viewer_id and follower_id and self._bool(row.get("mutual")):
                target_ids.add(follower_id)
                has_follow_rules = True

        if not has_follow_rules:
            target_ids.update(profiles.keys())

        return [
            user_id
            for user_id in target_ids
            if self._ranking_profile_visible(profiles.get(user_id) or {}, user_id == viewer_id)
        ]

    def _ranking_profile_visible(self, profile, is_viewer=False):
        if is_viewer:
            return True
        if not self._ranking_profile_enabled(profile):
            return False
        if profile.get("is_private") and not profile.get("ranking_consent"):
            return False
        return True

    def _ranking_profile_enabled(self, profile, is_viewer=False):
        if is_viewer and "ranking_enabled" not in profile:
            return True
        return self._bool(profile.get("ranking_enabled"), default=True)

    def _ranking_display_name(self, name, is_viewer=False, is_friend=False):
        text = self._text(name) or "러너"
        if is_viewer or is_friend:
            return text or "나"

        parts = [part for part in text.split() if part]
        if len(parts) > 1:
            return f"{parts[0][0]}**" if len(parts[0]) == 1 else f"{parts[0]} **"
        if len(text) <= 1:
            return f"{text}**"
        return f"{text[0]}**"

    def _ranking_motivation(self, entries, me, period):
        if not me:
            return "랭킹 참여를 켜면 친구들과 거리 흐름을 비교할 수 있어."
        if me.get("rank_out") or not entries or not (me.get("distance_km") or 0):
            return "아직 달리지 않아서 순위 밖이야. 첫 기록을 올리면 랭킹이 바로 시작돼."

        tied_count = len([
            row for row in entries
            if row.get("rank") == me.get("rank") and (row.get("distance_km") or 0) == (me.get("distance_km") or 0)
        ])
        period_text = "이번달" if period == "this_month" else "이번주"
        if tied_count > 1:
            return f"현재 공동 {me.get('rank')}위야. {period_text} 페이스를 유지해보자."

        if me.get("rank") == 1:
            runner_up = next((row for row in entries if row.get("rank") != 1 and row.get("distance_km")), None)
            if runner_up and runner_up.get("distance_km"):
                gap = round((me.get("distance_km") or 0) - (runner_up.get("distance_km") or 0), 2)
                return f"{runner_up.get('name')}를 {gap:.2f}km 차로 앞서고 있어."
            return "현재 1위야. 이번 기간 페이스를 유지해보자."

        try:
            me_index = entries.index(me)
        except ValueError:
            me_index = -1

        ahead = None
        if me_index > 0:
            for row in reversed(entries[:me_index]):
                if (row.get("rank") or 0) < (me.get("rank") or 0):
                    ahead = row
                    break

        if ahead:
            gap = round((ahead.get("distance_km") or 0) - (me.get("distance_km") or 0), 2)
            if gap <= 0 and me.get("rank_tiebreaker") == "pace":
                return f"{period_text} 거리는 동률이라 평균 페이스로 순위가 갈리고 있어."
            return f"{period_text} {ahead.get('name')}를 {gap:.2f}km 차로 추격 중!"
        return "조금만 더 뛰면 순위를 올릴 수 있어."

    def _remember_weekly_winner(self, social, period_info, winner):
        if not isinstance(social, dict) or not winner:
            return False

        rows = social.get("weekly_winners")
        if not isinstance(rows, list):
            rows = []

        period_key = period_info.get("period_key")
        if not period_key:
            return False

        item = {
            "period_key": period_key,
            "start_date": period_info.get("start").isoformat(),
            "end_date": period_info.get("end").isoformat(),
            "user_id": winner.get("user_id"),
            "name": winner.get("name"),
            "distance_km": winner.get("distance_km"),
            "archived_at": self._utcnow(),
        }
        next_rows = [row for row in rows if not isinstance(row, dict) or row.get("period_key") != period_key]
        next_rows.append(item)
        social["weekly_winners"] = sorted(next_rows, key=lambda row: row.get("period_key") or "", reverse=True)[:52]
        self._write_ranking_social(social)
        return True

    def _week_start(self, date):
        return date - datetime.timedelta(days=date.weekday())

    def _year_week(self, date):
        iso = date.isocalendar()
        return f"{iso[0]}-W{iso[1]:02d}"

    def _write_challenges(self, rows):
        path = self.challenges_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        challenges = []
        seen_ids = set()
        seen_codes = set()
        for row in rows:
            challenge = self.normalize_challenge(row)
            if not challenge:
                continue
            if challenge.get("id") in seen_ids:
                continue
            if challenge.get("invite_code") in seen_codes:
                challenge["invite_code"] = self._generate_invite_code(seen_codes)
            challenges.append(challenge)
            seen_ids.add(challenge.get("id"))
            seen_codes.add(challenge.get("invite_code"))

        challenges = sorted(challenges, key=lambda row: row.get("created_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(challenges, fp, ensure_ascii=False, indent=2)

    def _write_user_badges(self, rows):
        path = self.user_badges_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)

        user_badges = []
        seen = set()
        for row in rows:
            item = self.normalize_user_badge(row)
            key = (item.get("user_id") if item else "", item.get("badge_code") if item else "")
            if item and key not in seen:
                user_badges.append(item)
                seen.add(key)

        user_badges = sorted(user_badges, key=lambda row: row.get("achieved_at") or "", reverse=True)
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(user_badges, fp, ensure_ascii=False, indent=2)

    def _challenge_rows(self):
        path = self.challenges_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as fp:
                rows = json.load(fp)
        except Exception:
            return []

        if not isinstance(rows, list):
            return []

        challenges = []
        for row in rows:
            challenge = self.normalize_challenge(row)
            if challenge:
                challenges.append(challenge)

        return sorted(challenges, key=lambda row: row.get("created_at") or "", reverse=True)

    def _refresh_challenge_contributions(self, rows):
        runs = self.load_runs(include_media=False)
        refreshed = []
        for row in rows:
            challenge = self.normalize_challenge(row)
            if not challenge:
                continue

            members = []
            for member in challenge.get("members") or []:
                next_member = dict(member)
                next_member["contributed_value"] = self._challenge_member_contribution(challenge, member, runs)
                members.append(next_member)

            challenge["members"] = members
            refreshed.append(challenge)

        return refreshed

    def _viewer_identity(self, viewer=None):
        ids = set()
        names = set()

        if isinstance(viewer, dict):
            for key in ("id", "user_id", "userId", "username", "display_id", "displayId", "email"):
                value = self._text(viewer.get(key))
                if value:
                    ids.add(value)
            for key in ("name", "display_name", "displayName", "user_name", "userName"):
                value = self._text(viewer.get(key))
                if value:
                    names.add(value)
        else:
            value = self._text(viewer)
            if value:
                ids.add(value)

        return ids, names

    def _challenge_owned_by(self, challenge, viewer=None):
        viewer_ids, viewer_names = self._viewer_identity(viewer)
        creator_id = self._text(challenge.get("creator_id"))
        creator_name = self._text(challenge.get("creator_name"))

        if creator_id and creator_id in viewer_ids:
            return True
        if creator_name and creator_name in viewer_names:
            return True

        for member in challenge.get("members") or []:
            member_id = self._text(member.get("user_id"))
            member_name = self._text(member.get("user_name"))
            if creator_id and member_id == creator_id and member_id in viewer_ids:
                return True
            if creator_name and member_name == creator_name and member_name in viewer_names:
                return True

        return False

    def _decorate_challenge(self, row, viewer_id=None):
        challenge = self.normalize_challenge(row)
        if not challenge:
            return None

        members = sorted(
            challenge.get("members") or [],
            key=lambda member: member.get("contributed_value") or 0,
            reverse=True,
        )
        ranked_members = []
        for index, member in enumerate(members, start=1):
            item = dict(member)
            item["rank"] = index
            item["contributed_text"] = self._challenge_value_text(challenge.get("type"), item.get("contributed_value") or 0)
            item["progress_percent"] = self._challenge_member_percent(challenge, item)
            ranked_members.append(item)

        challenge["members"] = ranked_members
        progress = self._challenge_progress(challenge)
        status = self._challenge_status(challenge)
        viewer_ids, viewer_names = self._viewer_identity(viewer_id)
        viewer_member = next((
            member for member in ranked_members
            if member.get("user_id") in viewer_ids or member.get("user_name") in viewer_names
        ), None)
        viewer_owned = self._challenge_owned_by(challenge, viewer_id)

        challenge.update({
            "type_label": self.CHALLENGE_TYPE_LABELS.get(challenge.get("type"), challenge.get("type")),
            "status": status,
            "status_label": self._challenge_status_label(status, bool(viewer_member)),
            "member_count": len(ranked_members),
            "viewer_joined": bool(viewer_member),
            "viewer_owned": viewer_owned,
            "viewer_member": viewer_member,
            "current_value": progress.get("current_value"),
            "target_value": progress.get("target_value"),
            "remaining_value": progress.get("remaining_value"),
            "progress_percent": progress.get("percent"),
            "achieved": progress.get("achieved"),
            "goal_text": self._challenge_goal_text(challenge),
            "current_text": self._challenge_value_text(challenge.get("type"), progress.get("current_value") or 0),
            "target_text": self._challenge_value_text(challenge.get("type"), progress.get("target_value") or challenge.get("goal_value") or 0),
            "remaining_text": self._challenge_value_text(challenge.get("type"), progress.get("remaining_value") or 0),
            "d_day": self._challenge_d_day(challenge),
            "period_text": self._challenge_period_text(challenge),
            "result_status": self._challenge_result_status(challenge, progress),
            "result_text": self._challenge_result_text(challenge, progress),
        })
        return challenge

    def _challenge_member_contribution(self, challenge, member, runs):
        start_date = challenge.get("start_date")
        end_date = challenge.get("end_date")
        member_id = member.get("user_id")
        creator_id = challenge.get("creator_id")
        member_count = len(challenge.get("members") or [])
        total = 0

        for run in runs:
            date = run.get("date")
            if not date or date < start_date or date > end_date:
                continue

            run_user_id = self._text(run.get("user_id") or run.get("userId"))
            if run_user_id and run_user_id != member_id:
                continue
            if not run_user_id and member_id != creator_id and member_count > 1:
                continue

            if challenge.get("type") == "count":
                total += 1
            else:
                total += run.get("distance_km") or 0

        return round(total, 2)

    def _challenge_progress(self, challenge):
        members = challenge.get("members") or []
        goal_value = challenge.get("goal_value") or 0
        challenge_type = challenge.get("type")

        if challenge_type == "individual_distance":
            target_value = round(goal_value * max(1, len(members)), 2)
            capped_current = round(sum(min(member.get("contributed_value") or 0, goal_value) for member in members), 2)
            raw_current = round(sum(member.get("contributed_value") or 0 for member in members), 2)
            achieved = bool(members) and all((member.get("contributed_value") or 0) >= goal_value for member in members)
            percent = round((capped_current / target_value) * 100) if target_value else 0
            remaining = max(0, round(target_value - capped_current, 2))
            return {
                "current_value": raw_current,
                "target_value": target_value,
                "remaining_value": remaining,
                "percent": max(0, min(100, percent)),
                "achieved": achieved,
            }

        current = round(sum(member.get("contributed_value") or 0 for member in members), 2)
        target_value = goal_value
        achieved = current >= target_value if target_value else False
        percent = round((min(current, target_value) / target_value) * 100) if target_value else 0
        return {
            "current_value": current,
            "target_value": target_value,
            "remaining_value": max(0, round(target_value - current, 2)),
            "percent": max(0, min(100, percent)),
            "achieved": achieved,
        }

    def _challenge_member_percent(self, challenge, member):
        goal_value = challenge.get("goal_value") or 0
        if not goal_value:
            return 0

        if challenge.get("type") == "individual_distance":
            current = min(member.get("contributed_value") or 0, goal_value)
            return max(0, min(100, round((current / goal_value) * 100)))

        total = sum(item.get("contributed_value") or 0 for item in challenge.get("members") or [])
        if not total:
            return 0
        return max(0, min(100, round(((member.get("contributed_value") or 0) / total) * 100)))

    def _challenge_type(self, value):
        text = self._text(value)
        if not text:
            return None

        key = re.sub(r"[\s\-]+", "_", text.strip().lower())
        aliases = {
            "total_distance": "total_distance",
            "group_distance": "total_distance",
            "team_distance": "total_distance",
            "distance": "total_distance",
            "individual_distance": "individual_distance",
            "personal_distance": "individual_distance",
            "each_distance": "individual_distance",
            "count": "count",
            "run_count": "count",
            "runs": "count",
        }
        return aliases.get(key) if aliases.get(key) in self.CHALLENGE_TYPE_ORDER else None

    def _challenge_goal_value(self, challenge_type, value):
        number = self._number(value)
        if number is None or number <= 0:
            return None
        if challenge_type == "count":
            return int(round(number))
        return round(float(number), 2)

    def _invite_code(self, value):
        text = self._text(value)
        if not text:
            return None
        code = re.sub(r"[^A-Z0-9]", "", text.upper())[:10]
        return code or None

    def _generate_invite_code(self, used_codes=None):
        used = {self._invite_code(code) for code in (used_codes or set()) if self._invite_code(code)}
        for _ in range(20):
            code = uuid.uuid4().hex[:8].upper()
            if code not in used:
                return code
        return uuid.uuid4().hex[:10].upper()

    def _challenge_status(self, challenge):
        today = datetime.date.today().isoformat()
        if challenge.get("end_date") and challenge.get("end_date") < today:
            return "ended"
        if challenge.get("start_date") and challenge.get("start_date") > today:
            return "recruiting"
        return "active"

    def _challenge_status_label(self, status, joined=False):
        if status == "ended":
            return "종료"
        if joined:
            return "참여중"
        return "모집중"

    def _challenge_d_day(self, challenge):
        today = datetime.date.today()
        start = self._date_obj(challenge.get("start_date"))
        end = self._date_obj(challenge.get("end_date"))
        if not start or not end:
            return "-"
        if today < start:
            return f"D-{(start - today).days} 시작"
        if today <= end:
            days = (end - today).days
            return "D-day" if days == 0 else f"D-{days}"
        return "종료"

    def _challenge_period_text(self, challenge):
        start = self.display_date(challenge.get("start_date"))
        end = self.display_date(challenge.get("end_date"))
        return f"{start} - {end}"

    def _challenge_goal_text(self, challenge):
        challenge_type = challenge.get("type")
        value = self._challenge_value_text(challenge_type, challenge.get("goal_value") or 0)
        if challenge_type == "individual_distance":
            return f"각자 {value}"
        return value

    def _challenge_value_text(self, challenge_type, value):
        number = self._number(value) or 0
        if challenge_type == "count":
            return f"{int(round(number))}회"
        return f"{round(float(number), 2):.2f}km"

    def _challenge_result_status(self, challenge, progress):
        if progress.get("achieved"):
            return "achieved"
        if self._challenge_status(challenge) == "ended":
            return "missed"
        return "in_progress"

    def _challenge_result_text(self, challenge, progress):
        result_status = self._challenge_result_status(challenge, progress)
        if result_status == "achieved":
            return "목표 달성"
        if result_status == "missed":
            return f"목표까지 {self._challenge_value_text(challenge.get('type'), progress.get('remaining_value') or 0)} 부족"
        return f"{self._challenge_d_day(challenge)} · {progress.get('percent') or 0}%"

    def _delete_run_image(self, image_url):
        filepath = self._account_upload_path(image_url)
        if not filepath:
            return

        try:
            os.unlink(filepath)
        except Exception:
            pass

    def _delete_run_media_file(self, media_url):
        filepath = self._account_upload_path(media_url)
        if not filepath:
            return

        try:
            os.unlink(filepath)
        except Exception:
            pass

    def _account_upload_path(self, url):
        text = self._upload_url_path(url) or self._text(url).split("?", 1)[0]
        rules = (
            (
                "/api/run-images/",
                os.environ.get("RUNNINGMATE_UPLOAD_DIR", "/opt/app/data/run_images"),
                r"^[a-f0-9]{32}\.(?:jpg|jpeg|png|webp|gif|heic|heif)$",
            ),
            (
                "/api/run-media/",
                self.media_upload_dir(),
                r"^[a-f0-9]{32}\.(?:jpg|jpeg|png|webp|gif|heic|heif|mp4|mov|webm|m4v)$",
            ),
        )

        for prefix, root, pattern in rules:
            if not text.startswith(prefix):
                continue
            filename = os.path.basename(text[len(prefix):])
            if not re.match(pattern, filename):
                return None
            real_root = os.path.realpath(root)
            filepath = os.path.realpath(os.path.join(real_root, filename))
            if not filepath.startswith(real_root + os.sep):
                return None
            return filepath
        return None

    def _media_type(self, file_storage):
        ext = os.path.splitext(file_storage.filename or "")[1].lower()
        mimetype = str(file_storage.mimetype or "").lower()
        if ext in self.VIDEO_EXTENSIONS or mimetype.startswith("video/"):
            return "video"
        return "photo"

    def _media_extension(self, file_storage):
        ext = os.path.splitext(file_storage.filename or "")[1].lower()
        if ext in self.IMAGE_EXTENSIONS or ext in self.VIDEO_EXTENSIONS:
            return ext

        return self.MEDIA_MIME_EXTENSIONS.get(str(file_storage.mimetype or "").lower(), ".jpg")

    def _max_media_upload_bytes(self):
        try:
            return max(1024, int(os.environ.get("RUNNINGMATE_MAX_MEDIA_UPLOAD_BYTES", self.DEFAULT_MAX_MEDIA_UPLOAD_BYTES)))
        except Exception:
            return self.DEFAULT_MAX_MEDIA_UPLOAD_BYTES

    def _uploaded_size(self, file_storage):
        content_length = getattr(file_storage, "content_length", None)
        if content_length:
            try:
                return int(content_length)
            except Exception:
                pass

        stream = getattr(file_storage, "stream", None)
        if not stream:
            return 0

        try:
            position = stream.tell()
            stream.seek(0, os.SEEK_END)
            size = stream.tell()
            stream.seek(position)
            return size
        except Exception:
            self._rewind_file(file_storage)
            return 0

    def _read_header(self, file_storage, size=64):
        stream = getattr(file_storage, "stream", None)
        if not stream:
            return b""

        try:
            position = stream.tell()
            stream.seek(0)
            header = stream.read(size)
            stream.seek(position)
            return header or b""
        except Exception:
            self._rewind_file(file_storage)
            return b""

    def _rewind_file(self, file_storage):
        try:
            file_storage.stream.seek(0)
        except Exception:
            pass

    def _validate_media_upload(self, file_storage, media_type):
        ext = os.path.splitext(file_storage.filename or "")[1].lower()
        mimetype = str(file_storage.mimetype or "").lower()
        allowed_exts = self.IMAGE_EXTENSIONS | self.VIDEO_EXTENSIONS
        if ext not in allowed_exts and mimetype not in self.MEDIA_MIME_EXTENSIONS:
            return "지원하지 않는 사진/영상 형식입니다."

        size = self._uploaded_size(file_storage)
        if size <= 0:
            return "비어 있는 파일은 첨부할 수 없습니다."
        if size > self._max_media_upload_bytes():
            return "사진/영상 파일이 너무 큽니다."

        if not self._looks_like_supported_media(file_storage, media_type):
            return "사진/영상 파일 형식을 확인하지 못했습니다."

        return None

    def _looks_like_supported_media(self, file_storage, media_type):
        ext = self._media_extension(file_storage)
        mimetype = str(file_storage.mimetype or "").lower()
        header = self._read_header(file_storage)

        if media_type == "photo":
            if ext in {".jpg", ".jpeg"} or mimetype == "image/jpeg":
                return header.startswith(b"\xff\xd8\xff")
            if ext == ".png" or mimetype == "image/png":
                return header.startswith(b"\x89PNG\r\n\x1a\n")
            if ext == ".gif" or mimetype == "image/gif":
                return header.startswith((b"GIF87a", b"GIF89a"))
            if ext == ".webp" or mimetype == "image/webp":
                return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
            if ext in {".heic", ".heif"} or mimetype in {"image/heic", "image/heif"}:
                return b"ftyp" in header[:16] and any(brand in header[:32] for brand in (b"heic", b"heif", b"mif1", b"msf1"))
            return False

        if ext == ".webm" or mimetype == "video/webm":
            return header.startswith(b"\x1a\x45\xdf\xa3")
        return b"ftyp" in header[:16]

    def _persist_uploaded_media(self, file_storage, media_type):
        validation_error = self._validate_media_upload(file_storage, media_type)
        if validation_error:
            self._rewind_file(file_storage)
            return None, None, validation_error

        temp_path = None
        try:
            security = wiz.model("security")
            upload_dir = self.media_upload_dir()
            os.makedirs(upload_dir, exist_ok=True)
            incoming_dir = security.upload_incoming_dir(upload_dir)
            filename = f"{uuid.uuid4().hex}{self._media_extension(file_storage)}"
            filepath = os.path.join(upload_dir, filename)
            temp_path = os.path.join(incoming_dir, f"{filename}.upload")
            file_storage.save(temp_path)
            scan_ok, scan_error = security.scan_upload_file(temp_path)
            if not scan_ok:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
                self._rewind_file(file_storage)
                return None, None, scan_error
            os.replace(temp_path, filepath)
            self._rewind_file(file_storage)
            return filepath, f"/api/run-media/{filename}", None
        except Exception:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass
            self._rewind_file(file_storage)
            return None, None, "업로드 파일을 저장하지 못했습니다."

    def _period_point(self, rows, start, label):
        distance = round(sum(row.get("distance_km") or 0 for row in rows), 2)
        duration_seconds = sum(self._run_duration_seconds(row) or 0 for row in rows)
        pace_seconds = round(duration_seconds / distance) if distance and duration_seconds else None

        return {
            "label": label,
            "date": start.isoformat(),
            "distanceKm": distance,
            "paceSeconds": pace_seconds,
            "distanceText": self.km_text(distance) if distance else "0.00km",
            "paceText": self.seconds_to_pace(pace_seconds),
        }

    def _distance_footer(self, points, current_label, previous_label):
        if not points:
            return "러닝 기록 없음"

        current = points[-1].get("distanceKm") or 0
        previous = points[-2].get("distanceKm") or 0 if len(points) > 1 else 0
        if not current:
            return f"{current_label} 기록 없음"

        left = f"{current_label} {self.km_text(current)}"
        if not previous:
            return f"{left} / 비교 기록 없음"

        diff = round(current - previous, 2)
        if diff >= 0:
            return f"{left} / ▲ {previous_label}보다 {diff:.2f}km↑"
        return f"{left} / ▼ {previous_label}보다 {abs(diff):.2f}km↓"

    def _pace_footer(self, points, current_label, previous_label):
        if not points:
            return "러닝 기록 없음"

        current = points[-1].get("paceSeconds")
        previous = points[-2].get("paceSeconds") if len(points) > 1 else None
        if current is None:
            return f"{current_label} 페이스 기록 없음"

        left = f"{current_label} 평균 {self.seconds_to_pace(current)}"
        if previous is None:
            return f"{left} / 비교 기록 없음"

        diff = int(round(previous - current))
        if diff >= 0:
            return f"{left} / ▲ {diff}초 빠름"
        return f"{left} / ▼ {abs(diff)}초 느림"

    def _run_duration_seconds(self, row):
        duration = self._duration_seconds(row.get("duration"))
        if duration is not None:
            return duration

        pace = self.pace_to_seconds(row.get("avg_pace"))
        distance = row.get("distance_km")
        if pace is None or distance is None:
            return None

        return pace * float(distance)

    def _duration_seconds(self, value):
        if not value:
            return None

        try:
            parts = [part for part in re.split(r"[:]", str(value).strip()) if part != ""]
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return None
        except Exception:
            return None

    def _anchor_week_date(self, rows, year_week):
        if year_week:
            match = re.match(r"^(\d{4})-?W(\d{1,2})$", year_week)
            if match:
                return datetime.date.fromisocalendar(int(match.group(1)), int(match.group(2)), 1)

        return self._date_obj(rows[0].get("date")) or datetime.date.today()

    def _recent_run_streak(self, rows, anchor):
        run_dates = {
            self._date_obj(row.get("date"))
            for row in rows
            if self._date_obj(row.get("date"))
        }
        if not run_dates:
            return 0

        cursor = anchor if anchor in run_dates else anchor - datetime.timedelta(days=1)
        count = 0
        while cursor in run_dates:
            count += 1
            cursor -= datetime.timedelta(days=1)
        return count

    def _distance_between(self, rows, start, end):
        total = 0
        for row in rows:
            run_date = self._date_obj(row.get("date"))
            if run_date and start <= run_date < end:
                total += row.get("distance_km") or 0
        return round(total, 2)

    def _heart_rate_load(self, rows):
        values = [
            row.get("avg_heart_rate")
            for row in rows
            if row.get("avg_heart_rate") is not None
        ]
        if len(values) < 6:
            return {
                "recent_avg_heart_rate": round(sum(values[:3]) / 3) if len(values) >= 3 else None,
                "baseline_avg_heart_rate": None,
                "heart_rate_delta_bpm": None,
                "elevated": False,
            }

        recent_values = values[:3]
        baseline_values = values[3:]
        recent_avg = round(sum(recent_values) / len(recent_values))
        baseline_avg = round(sum(baseline_values) / len(baseline_values))
        delta = recent_avg - baseline_avg
        elevated = (
            delta >= self.HEART_RATE_SIGNIFICANT_DELTA
            and recent_avg >= round(baseline_avg * self.HEART_RATE_SIGNIFICANT_RATIO)
        )
        return {
            "recent_avg_heart_rate": recent_avg,
            "baseline_avg_heart_rate": baseline_avg,
            "heart_rate_delta_bpm": delta,
            "elevated": elevated,
        }

    def _negative_condition_streak(self, rows):
        count = 0
        for row in rows:
            if self._run_condition_negative(row):
                count += 1
                continue
            break
        return count

    def _run_condition_negative(self, row):
        journal = self._text(row.get("journal")).lower()
        if not journal:
            return False
        if any(marker in journal for marker in self.NEGATIVE_CONDITION_MARKERS):
            return True
        return any(word in journal for word in self.NEGATIVE_CONDITION_WORDS)

    def _training_load_reason(self, reasons, status, weekly_increase_pct, rows):
        if reasons:
            return reasons[0]
        if not rows:
            return "러닝 기록이 쌓이면 훈련 부하를 계산할게."
        if status == "caution":
            if weekly_increase_pct is not None:
                return f"이번주 거리가 지난주보다 {round(weekly_increase_pct)}% 늘어 주의 구간이야."
            return "휴식 권고 단계는 아니지만 회복 신호를 지켜보자."
        return "훈련 부하는 안전 구간이야."

    def _date_obj(self, value):
        normalized = self._date(value)
        if not normalized:
            return None
        return datetime.date.fromisoformat(normalized)

    def _date(self, value):
        if not value:
            return None

        if isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime("%Y-%m-%d")

        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"):
            try:
                return datetime.datetime.strptime(text[:10], fmt).strftime("%Y-%m-%d")
            except Exception:
                pass

        korean = re.search(r"(?:(\d{4})년\s*)?(\d{1,2})월\s*(\d{1,2})일", text)
        if korean:
            year = int(korean.group(1) or datetime.date.today().year)
            month = int(korean.group(2))
            day = int(korean.group(3))
            if 1 <= month <= 12 and 1 <= day <= calendar.monthrange(year, month)[1]:
                return f"{year:04d}-{month:02d}-{day:02d}"

        return None

    def _duration(self, value):
        if not value:
            return None

        text = str(value).strip()
        if self._duration_seconds(text) is not None:
            parts = [int(part) for part in text.split(":")]
            if len(parts) == 2:
                return f"00:{parts[0]:02d}:{parts[1]:02d}"
            return f"{parts[0]:02d}:{parts[1]:02d}:{parts[2]:02d}"

        match = re.search(r"(?:(\d+)\s*h)?\s*(\d+)\s*m(?:\s*(\d+)\s*s)?", text, re.I)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        return text

    def _start_time(self, value):
        if not value:
            return None

        text = str(value).strip()
        ampm = re.search(r"(오전|오후|am|pm)\s*(\d{1,2})(?:\s*[:시]\s*(\d{1,2}))?", text, re.I)
        if ampm:
            hour = int(ampm.group(2))
            minute = int(ampm.group(3) or 0)
            marker = ampm.group(1).lower()
            if marker in ("오후", "pm") and hour < 12:
                hour += 12
            if marker in ("오전", "am") and hour == 12:
                hour = 0
        else:
            match = re.search(r"(\d{1,2})\s*[:시]\s*(\d{1,2})?", text)
            if not match:
                return None
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        return f"{hour:02d}:{minute:02d}"

    def _pace(self, value):
        seconds = self.pace_to_seconds(value)
        if seconds is None:
            return None
        return self.seconds_to_pace(seconds)

    def _first_value(self, row, keys):
        for key in keys:
            if key in row and row.get(key) not in (None, ""):
                return row.get(key)

        raw = row.get("raw_parsed_json")
        if isinstance(raw, dict):
            for key in keys:
                if key in raw and raw.get(key) not in (None, ""):
                    return raw.get(key)

        return None

    def _has_any_key(self, row, keys):
        return isinstance(row, dict) and any(key in row for key in keys)

    def _distance(self, row):
        value = self._first_value(row, self.DISTANCE_KEYS)
        distance = self._float(value)
        if distance is not None:
            return distance

        for key in ("raw_text", "ocr_text", "text", "description"):
            value = row.get(key)
            distance = self._distance_from_text(value)
            if distance is not None:
                return distance

        for value in self._text_values(row):
            distance = self._distance_from_text(value)
            if distance is not None:
                return distance

        return None

    def _distance_from_text(self, value):
        if not value:
            return None

        text = str(value).replace("㎞", "km")
        patterns = (
            r"(?:distance|total|running|거리|킬로미터|킬로)\D{0,12}(-?\d+(?:[,.]\d+)*)\s*(?:km|kilometer|kilometers|킬로미터|킬로)?",
            r"(-?\d+(?:[,.]\d+)*)\s*(?:km|kilometer|kilometers|킬로미터|킬로)",
        )
        for pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return self._float(match.group(1))

        return None

    def _distance_from_pace_duration(self, distance, avg_pace, duration):
        pace_seconds = self.pace_to_seconds(avg_pace)
        duration_seconds = self._duration_seconds(duration)
        inferred = None
        if pace_seconds and duration_seconds:
            inferred = round(duration_seconds / pace_seconds, 2)

        if distance is None:
            return inferred

        if inferred is not None and distance > 100 and inferred < 100 and distance / inferred > 10:
            return inferred

        return distance

    def _text_values(self, value):
        if isinstance(value, dict):
            for item in value.values():
                yield from self._text_values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self._text_values(item)
        elif isinstance(value, str):
            yield value

    def _text(self, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _bool(self, value, default=False):
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "y", "on")
        return default

    def _run_public(self, row):
        source = row if isinstance(row, dict) else {}
        privacy = (self._text(source.get("privacy")) or "").lower()
        default = privacy != "private"
        value = self._first_value(source, ("is_public", "isPublic", "public"))
        return self._bool(value, default=default)

    def _reaction_type(self, value):
        text = (self._text(value) or "").lower()
        aliases = {
            "like": "like",
            "thumb": "like",
            "thumbs_up": "like",
            "👍": "like",
            "좋아요": "like",
            "fire": "fire",
            "flame": "fire",
            "🔥": "fire",
            "불꽃": "fire",
            "clap": "clap",
            "👏": "clap",
            "박수": "clap",
            "strong": "strong",
            "muscle": "strong",
            "💪": "strong",
            "힘내": "strong",
        }
        key = re.sub(r"[\s\-]+", "_", text)
        normalized = aliases.get(key) or aliases.get(key.replace("_", ""))
        return normalized if normalized in self.REACTION_TYPES else None

    def _comment_content(self, value):
        text = self._text(value)
        if not text:
            return None
        text = re.sub(r"\s+", " ", text).strip()
        return text[:300] if text else None

    def _journal(self, value):
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _playlist_name(self, value):
        text = self._text(value)
        if not text:
            return None
        return text[:200]

    def _music_url(self, value):
        text = self._text(value)
        if not text:
            return None
        if not re.match(r"^https?://", text, re.I) and not text.startswith("music://"):
            return None
        return text[:2000]

    def _top_tracks(self, value):
        if value is None or value == "":
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except Exception:
                return []
        else:
            parsed = value

        if not isinstance(parsed, list):
            return []

        tracks = []
        for item in parsed[:30]:
            track = self._top_track(item)
            if track:
                tracks.append(track)
        return tracks

    def _top_track(self, value):
        if not isinstance(value, dict):
            return None

        title = self._text(value.get("title") or value.get("name"))
        artist = self._text(value.get("artist") or value.get("artist_name") or value.get("artistName"))
        if not title or not artist:
            return None

        album_art_url = self._music_url(value.get("album_art_url") or value.get("albumArtUrl") or value.get("artworkUrl")) or ""
        album = self._text(value.get("album") or value.get("album_name") or value.get("albumName")) or ""
        url = self._music_url(value.get("url") or value.get("music_url") or value.get("musicUrl")) or ""
        track = {
            "title": title[:160],
            "artist": artist[:160],
            "album_art_url": album_art_url[:2000],
        }
        if album:
            track["album"] = album[:200]
        if url:
            track["url"] = url[:2000]
        return track

    def _run_type(self, value):
        text = self._text(value)
        if not text:
            return "jogging"

        key = re.sub(r"[\s\-]+", "_", text.strip().lower())
        normalized = self.RUN_TYPE_ALIASES.get(key)
        if normalized in self.RUN_TYPE_ORDER:
            return normalized

        compact = key.replace("_", "")
        normalized = self.RUN_TYPE_ALIASES.get(compact)
        if normalized in self.RUN_TYPE_ORDER:
            return normalized

        for source, target in self.RUN_TYPE_ALIASES.items():
            if source in text:
                return target

        return "jogging"

    def _cycle_phase(self, value):
        text = self._text(value)
        if not text:
            return "menstrual"

        key = re.sub(r"[\s\-]+", "_", text.strip().lower())
        aliases = {
            "menstrual": "menstrual",
            "period": "menstrual",
            "menses": "menstrual",
            "생리": "menstrual",
            "생리기": "menstrual",
            "follicular": "follicular",
            "난포": "follicular",
            "난포기": "follicular",
            "ovulation": "ovulation",
            "ovulatory": "ovulation",
            "배란": "ovulation",
            "배란기": "ovulation",
            "luteal": "luteal",
            "황체": "luteal",
            "황체기": "luteal",
        }
        normalized = aliases.get(key) or aliases.get(key.replace("_", ""))
        if normalized in self.CYCLE_PHASE_ORDER:
            return normalized

        for source, target in aliases.items():
            if source in text:
                return target

        return "menstrual"

    def _cycle_flow_level(self, value):
        text = self._text(value)
        if not text:
            return ""

        key = re.sub(r"[\s\-_]+", "", text.strip().lower())
        aliases = {
            "none": "none",
            "no": "none",
            "없음": "none",
            "안함": "none",
            "안해": "none",
            "안해요": "none",
            "무": "none",
            "light": "light",
            "low": "light",
            "small": "light",
            "적음": "light",
            "적어": "light",
            "소량": "light",
            "normal": "normal",
            "medium": "normal",
            "보통": "normal",
            "heavy": "heavy",
            "high": "heavy",
            "많음": "heavy",
            "많아": "heavy",
            "다량": "heavy",
        }
        return aliases.get(key, "")

    def _cycle_menstrual_windows(self, logs):
        ranges = []
        for row in logs or []:
            if self._cycle_phase(row.get("cycle_phase")) != "menstrual":
                continue
            start_date = self._date(row.get("start_date"))
            end_date = self._date(row.get("end_date")) or start_date
            if not start_date or not end_date:
                continue
            if end_date < start_date:
                start_date, end_date = end_date, start_date
            ranges.append({
                "start_date": start_date,
                "end_date": end_date,
                "is_none": self._cycle_flow_level(row.get("flow_level")) == "none",
            })

        ranges = sorted(ranges, key=lambda row: (row.get("start_date") or "", 1 if row.get("is_none") else 0))
        windows = []
        for row in ranges:
            if row.get("is_none"):
                if not windows:
                    continue
                current = windows[-1]
                none_start = self._date_obj(row.get("start_date"))
                if not none_start:
                    continue
                cutoff = (none_start - datetime.timedelta(days=1)).isoformat()
                if cutoff < current.get("start_date"):
                    windows.pop()
                elif cutoff < current.get("end_date"):
                    current["end_date"] = cutoff
                continue

            if not windows:
                windows.append({"start_date": row.get("start_date"), "end_date": row.get("end_date")})
                continue

            current = windows[-1]
            current_end = self._date_obj(current.get("end_date"))
            row_start = self._date_obj(row.get("start_date"))
            if not current_end or not row_start or row_start > current_end + datetime.timedelta(days=1):
                windows.append({"start_date": row.get("start_date"), "end_date": row.get("end_date")})
                continue

            if row.get("end_date") > current.get("end_date"):
                current["end_date"] = row.get("end_date")

        return windows

    def _cycle_condition_emoji(self, value):
        text = self._text(value)
        if not text:
            return ""
        if text in self.CYCLE_CONDITION_EMOJIS:
            return text

        key = re.sub(r"[\s\-_]+", "", text.strip().lower())
        aliases = {
            "good": "😊",
            "happy": "😊",
            "great": "😊",
            "best": "😊",
            "좋음": "😊",
            "좋아": "😊",
            "괜찮음": "😐",
            "normal": "😐",
            "neutral": "😐",
            "ok": "😐",
            "보통": "😐",
            "hard": "😣",
            "bad": "😣",
            "tired": "😣",
            "힘듦": "😣",
            "힘듬": "😣",
            "피곤": "😣",
        }
        return aliases.get(key, "")

    def _cycle_condition_distribution(self, phase, logs):
        counts = {emoji: 0 for emoji in self.CYCLE_CONDITION_EMOJIS}
        total = 0
        for row in logs or []:
            if self._cycle_phase(row.get("cycle_phase")) != phase:
                continue
            if self._cycle_flow_level(row.get("flow_level")) == "none":
                continue
            emoji = self._cycle_condition_emoji(row.get("condition_emoji"))
            if not emoji:
                continue
            counts[emoji] += 1
            total += 1

        if not total:
            return []

        return [
            {
                "emoji": emoji,
                "count": count,
                "percent": round((count / total) * 100),
            }
            for emoji, count in counts.items()
            if count
        ]

    def _direct_cycle_phase(self, date, logs):
        for row in logs:
            if self._cycle_flow_level(row.get("flow_level")) == "none":
                continue
            start = self._date_obj(row.get("start_date"))
            end = self._date_obj(row.get("end_date"))
            phase = self._cycle_phase(row.get("cycle_phase"))
            if start and end and start <= date <= end:
                return phase
        return None

    def _badge_condition_met(self, badge, rows):
        threshold = self._number(badge.get("threshold")) or 1
        current = self._badge_current_value(badge.get("condition_type"), rows, threshold)
        return current >= threshold

    def _badge_current_value(self, condition_type, rows, threshold=1):
        condition_type = self._text(condition_type)
        rows = rows or []

        if condition_type == "single_distance":
            return max([row.get("distance_km") or 0 for row in rows] or [0])
        if condition_type == "total_distance":
            return round(sum(row.get("distance_km") or 0 for row in rows), 2)
        if condition_type == "streak":
            return self._longest_run_streak(rows)
        if condition_type == "run_count":
            return len(rows)
        if condition_type in ("monthly_goal", "monthly_distance"):
            return self._max_monthly_distance(rows)
        if condition_type == "dawn_count":
            return self._time_of_day_run_count(rows, "dawn")
        if condition_type == "night_count":
            return self._time_of_day_run_count(rows, "night")
        if condition_type == "first_interval":
            return sum(1 for row in rows if self._run_type(row.get("run_type")) == "interval")
        if condition_type == "first_race":
            return sum(1 for row in rows if self._run_type(row.get("run_type")) == "race")

        return 0

    def _badge_progress_label(self, condition_type, current, threshold):
        condition_type = self._text(condition_type)
        if condition_type in ("single_distance", "total_distance", "monthly_goal", "monthly_distance"):
            return f"{self.km_text(current)} / {self.km_text(threshold)}"
        if condition_type == "streak":
            return f"{int(current)}일 / {int(threshold)}일"
        return f"{int(current)}회 / {int(threshold)}회"

    def _longest_run_streak(self, rows):
        dates = sorted({
            self._date_obj(row.get("date"))
            for row in rows
            if self._date_obj(row.get("date"))
        })
        if not dates:
            return 0

        longest = 1
        current = 1
        for index in range(1, len(dates)):
            if (dates[index] - dates[index - 1]).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)

        return longest

    def _max_monthly_distance(self, rows):
        totals = {}
        for row in rows:
            date = self._date(row.get("date"))
            if not date:
                continue
            key = date[:7]
            totals[key] = totals.get(key, 0) + (row.get("distance_km") or 0)
        return round(max(totals.values()) if totals else 0, 2)

    def _time_of_day_run_count(self, rows, bucket):
        count = 0
        for row in rows:
            minutes = self._start_minutes(row.get("start_time"))
            if minutes is None:
                continue
            if bucket == "dawn" and 4 * 60 <= minutes < 7 * 60:
                count += 1
            elif bucket == "night" and minutes >= 20 * 60:
                count += 1
        return count

    def _start_minutes(self, value):
        time_text = self._start_time(value)
        if not time_text:
            return None
        match = re.match(r"^(\d{2}):(\d{2})$", time_text)
        if not match:
            return None
        return int(match.group(1)) * 60 + int(match.group(2))

    def _run_water_total(self, row):
        if not isinstance(row, dict):
            return 0
        return (self._water_ml(row.get("water_before_ml")) or 0) + (self._water_ml(row.get("water_after_ml")) or 0)

    def _hydration_target_ml(self, distance_km):
        try:
            distance = max(0, float(distance_km or 0))
        except Exception:
            distance = 0
        if distance < 8:
            return 0
        return max(500, int(round(distance * 80)))

    def _default_goal_rows(self, year_month=None):
        month = self._year_month(year_month) or self.latest_year_month(self.load_runs(include_media=False))
        if not month:
            return []
        goal = self.normalize_goal({
            "id": str(uuid.uuid4()),
            "year_month": month,
            "goal_type": "distance",
            "target_value": 100,
            "created_at": self._utcnow(),
        })
        return [goal] if goal else []

    def _year_month(self, value):
        text = self._text(value)
        if not text:
            return None
        match = re.match(r"^(\d{4})-(\d{1,2})", text)
        if not match:
            return None
        year = int(match.group(1))
        month = int(match.group(2))
        if not (1 <= month <= 12):
            return None
        return f"{year:04d}-{month:02d}"

    def _year_month_label(self, value):
        month = self._year_month(value)
        if not month:
            return "-"
        year, mon = month.split("-")
        return f"{year}.{mon}"

    def _goal_type(self, value):
        text = (self._text(value) or "").lower()
        aliases = {
            "distance": "distance",
            "km": "distance",
            "거리": "distance",
            "count": "count",
            "runs": "count",
            "run_count": "count",
            "횟수": "count",
            "duration": "duration",
            "time": "duration",
            "minutes": "duration",
            "시간": "duration",
            "pace": "pace",
            "avg_pace": "pace",
            "페이스": "pace",
        }
        key = re.sub(r"[\s\-]+", "_", text)
        normalized = aliases.get(key) or aliases.get(key.replace("_", ""))
        return normalized if normalized in self.GOAL_TYPE_ORDER else None

    def _goal_sort(self, goal_type):
        try:
            return self.GOAL_TYPE_ORDER.index(goal_type)
        except Exception:
            return len(self.GOAL_TYPE_ORDER)

    def _goal_target_value(self, goal_type, value):
        goal_type = self._goal_type(goal_type)
        if not goal_type:
            return None

        if goal_type == "pace":
            seconds = self.pace_to_seconds(value)
            if seconds is None:
                number = self._number(value)
                if number is None:
                    return None
                seconds = number * 60 if number < 30 else number
            seconds = int(round(seconds))
            return seconds if 120 <= seconds <= 1800 else None

        number = self._number(value)
        if number is None or number <= 0:
            return None
        if goal_type == "count":
            count = int(round(number))
            return count if 1 <= count <= 1000 else None
        if goal_type == "distance":
            return round(number, 2) if number <= 100000 else None
        if goal_type == "duration":
            return round(number, 2) if number <= 100000 else None
        return None

    def _month_goal_stats(self, year_month=None, user_id=None):
        target_month = self._year_month(year_month) or self.latest_year_month(self.load_runs(include_media=False, user_id=user_id))
        rows = [
            row for row in self.load_runs(include_media=False, user_id=user_id)
            if target_month and str(row.get("date") or "").startswith(target_month)
        ]
        distance = round(sum(row.get("distance_km") or 0 for row in rows), 2)
        duration_seconds = sum(self._run_duration_seconds(row) or 0 for row in rows)
        pace_seconds = round(duration_seconds / distance) if distance and duration_seconds else None
        return {
            "year_month": target_month,
            "distance": distance,
            "count": len(rows),
            "duration": round(duration_seconds / 60, 1) if duration_seconds else 0,
            "pace": pace_seconds,
        }

    def _goal_progress_item(self, goal, stats):
        goal_type = goal.get("goal_type")
        target = self._number(goal.get("target_value")) or 0
        current = stats.get(goal_type)
        if goal_type == "pace":
            achieved = current is not None and current > 0 and current <= target
            percent = 0 if not current else min(100, round((target / current) * 100))
            remaining = 0 if achieved else max(0, round((current or 0) - target))
        else:
            current = self._number(current) or 0
            achieved = target > 0 and current >= target
            percent = 0 if not target else min(100, round((current / target) * 100))
            remaining = max(0, round(target - current, 2))

        item = {
            "id": goal.get("id"),
            "year_month": goal.get("year_month"),
            "goal_type": goal_type,
            "label": self.GOAL_TYPE_LABELS.get(goal_type, goal_type),
            "target_value": target,
            "current_value": current,
            "remaining_value": remaining,
            "percent": percent,
            "achieved": achieved,
            "unit": self._goal_unit(goal_type),
            "target_text": self._goal_value_text(goal_type, target),
            "current_text": self._goal_value_text(goal_type, current),
        }
        item["message"] = self._goal_message(item)
        return item

    def _goal_unit(self, goal_type):
        if goal_type == "distance":
            return "km"
        if goal_type == "count":
            return "회"
        if goal_type == "duration":
            return "분"
        if goal_type == "pace":
            return "/km"
        return ""

    def _goal_value_text(self, goal_type, value):
        if value is None:
            return "-"
        if goal_type == "pace":
            return f"{self.seconds_to_pace(value)}/km" if value else "-"
        if goal_type == "distance":
            return self.km_text(value)
        if goal_type == "duration":
            number = self._number(value) or 0
            return f"{int(round(number))}분"
        if goal_type == "count":
            return f"{int(round(self._number(value) or 0))}회"
        return str(value)

    def _goal_message(self, item):
        label = item.get("label") or "목표"
        goal_type = item.get("goal_type")
        if item.get("achieved"):
            return f"{label} 목표를 달성했어."

        remaining = item.get("remaining_value") or 0
        if goal_type == "distance":
            return f"이번달 거리 목표까지 {self.km_text(remaining)} 남았어."
        if goal_type == "count":
            return f"이번달 횟수 목표까지 {int(round(remaining))}번 남았어."
        if goal_type == "duration":
            return f"이번달 시간 목표까지 {int(round(remaining))}분 남았어."
        if goal_type == "pace":
            current = item.get("current_value")
            if not current:
                return f"평균 페이스 목표는 {item.get('target_text')}야."
            return f"평균 페이스 목표까지 {int(round(remaining))}초 줄이면 돼."
        return f"{label} 목표 진행 중이야."

    def _goals_summary(self, progress):
        if not progress:
            return "이번달 목표가 아직 없어."
        pending = [item for item in progress if not item.get("achieved")]
        if not pending:
            return "이번달 설정한 목표를 모두 달성했어."
        pending = sorted(pending, key=lambda item: self._goal_sort(item.get("goal_type")))
        return pending[0].get("message") or "이번달 목표를 이어가자."

    def _chat_title(self, value):
        text = re.sub(r"\s+", " ", self._text(value) or "새 대화").strip()
        return f"{text[:32]}..." if len(text) > 32 else text

    def _chat_preview(self, messages):
        text = ""
        for message in reversed(messages):
            text = self._text(message.get("text") if isinstance(message, dict) else "")
            if text:
                break
        text = re.sub(r"\s+", " ", text or "").strip()
        return f"{text[:54]}..." if len(text) > 54 else text

    def _chat_session_day_key(self, row):
        source = row if isinstance(row, dict) else {}
        day_key = self._date(
            source.get("day_key")
            or source.get("dayKey")
            or source.get("date_key")
            or source.get("dateKey")
        )
        if day_key:
            return day_key

        messages = source.get("messages") if isinstance(source.get("messages"), list) else []
        first_message = messages[0] if messages and isinstance(messages[0], dict) else {}
        return (
            self._date(source.get("updated_at") or source.get("updatedAt"))
            or self._date(source.get("created_at") or source.get("createdAt"))
            or self._date(first_message.get("created_at") or first_message.get("createdAt"))
            or self._date(self._utcnow())
        )

    def _utcnow(self):
        return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _now_timestamp(self):
        return datetime.datetime.now(datetime.timezone.utc).timestamp()

    def _timestamp(self, value):
        if value is None or value == "" or isinstance(value, bool):
            return None
        if isinstance(value, datetime.datetime):
            stamp = value
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=datetime.timezone.utc)
            return stamp.timestamp()
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()
        if not text:
            return None
        if "T" in text or "-" in text:
            try:
                stamp = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=datetime.timezone.utc)
                return stamp.timestamp()
            except Exception:
                return None
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            try:
                return float(text)
            except Exception:
                return None
        return None

    def _iso_from_timestamp(self, timestamp):
        try:
            return (
                datetime.datetime.fromtimestamp(float(timestamp), datetime.timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
        except Exception:
            return ""

    def _period_start(self, period):
        text = (self._text(period) or "").lower()
        if text in ("all", "전체"):
            return None

        months = 3
        if text in ("1m", "1month", "month", "1개월"):
            months = 1
        elif text in ("3m", "3month", "3months", "3개월"):
            months = 3

        start = datetime.date.today() - datetime.timedelta(days=31 * months)
        return start.isoformat()

    def _weight(self, value):
        number = self._number(value)
        if number is None:
            return None
        if number <= 0 or number >= 1000:
            return None
        return round(number, 1)

    def _water_ml(self, value):
        number = self._number(value)
        if number is None:
            return None
        amount = int(round(number))
        if amount <= 0 or amount > 20000:
            return None
        return amount

    def _float(self, value):
        number = self._number(value)
        if number is None:
            return None
        return round(number, 2)

    def _number(self, value):
        if value is None or value == "" or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip().replace("㎞", "km").replace(" ", "")
        match = re.search(r"-?\d+(?:[,.]\d+)*", text)
        if not match:
            return None

        number = match.group(0)
        if "," in number and "." in number:
            number = number.replace(",", "")
        elif "," in number:
            parts = number.split(",")
            if len(parts[-1]) <= 2:
                number = "".join(parts[:-1]) + "." + parts[-1]
            else:
                number = number.replace(",", "")

        try:
            return float(number)
        except Exception:
            return None

    def _int(self, value):
        number = self._number(value)
        if number is None:
            return None
        return int(round(number))

    def _avg_text(self, values):
        if not values:
            return "-"
        return str(int(round(sum(values) / len(values))))


Model = RunningMateData()
