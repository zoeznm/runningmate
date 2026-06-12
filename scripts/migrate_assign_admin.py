#!/usr/bin/env python3
"""
Assign legacy RunningMate records to the owner admin account.

Production backup guide before running:
  1. Back up the application data directory, for example:
     tar -C /opt/app -czf /opt/app/data-backup-before-admin-assign.tgz data
  2. Back up the user database, for example:
     mysqldump -h "$DB_HOST" -u "$DB_USER" -p "$DB_NAME" > user-db-backup.sql
  3. Then run:
     ADMIN_INIT_PASSWORD='...' npm run migrate:assign-admin

The script also creates a local rollback snapshot under
RUNNINGMATE_DATA_DIR/migration_backups before it writes JSON data.
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

import bcrypt
import pymysql


ADMIN_USERNAME = "dudghk933"
ADMIN_LOGIN_USERNAME = "matomabo"
DEFAULT_ADMIN_DISPLAY_NAME = "\uae40\ubcf4\ubbf8"
DEFAULT_ADMIN_EMAIL_DOMAIN = "runningmate.local"

JSON_RECORD_FILES = [
    ("running_logs", "running_logs.json", "list"),
    ("rest_days", "rest_days.json", "rest_days"),
    ("monthly_goals", "goals.json", "list"),
    ("run_media", "run_media.json", "list"),
    ("weight_logs", "weight_logs.json", "weights"),
    ("day_notes", "day_notes.json", "list"),
    ("cycle_logs", "cycle_logs.json", "list"),
    ("chat_sessions", "chat_history.json", "list"),
    ("user_badges", "user_badges.json", "list"),
]

SQL_RECORD_TABLES = [
    "running_logs",
    "rest_days",
    "monthly_goals",
    "run_media",
    "weight_logs",
    "day_notes",
    "cycle_logs",
    "chat_sessions",
    "user_badges",
]


def _utc_timestamp() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).strftime("%Y%m%d%H%M%S")


def _now() -> str:
    return _datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _text(value) -> str:
    return str(value or "").strip()


def _config_value(config, key, default=None):
    if isinstance(config, dict):
        return config.get(key, default)
    try:
        if key in config:
            return config[key]
    except Exception:
        pass
    return getattr(config, key, default)


def _load_database_config(project_root: Path, namespace: str = "base"):
    config_path = Path(
        os.environ.get("RUNNINGMATE_DATABASE_CONFIG")
        or project_root / "config" / "database.py"
    )
    if not config_path.exists():
        raise RuntimeError(f"Database config not found: {config_path}")

    spec = importlib.util.spec_from_file_location("runningmate_database_config", config_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    if not hasattr(module, namespace):
        raise RuntimeError(f"Database namespace '{namespace}' is missing in {config_path}")
    return getattr(module, namespace)


class SQLAdapter:
    def __init__(self, config, project_root: Path):
        self.kind = _text(_config_value(config, "type", "sqlite")).lower()
        self.conn = self._connect(config, project_root)

    def _connect(self, config, project_root: Path):
        if self.kind == "mysql":
            return pymysql.connect(
                host=_config_value(config, "host", "127.0.0.1"),
                user=_config_value(config, "user", "root"),
                password=_config_value(config, "password", ""),
                database=_config_value(config, "database"),
                port=int(_config_value(config, "port", 3306)),
                charset=_config_value(config, "charset", "utf8"),
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor,
            )

        raw_path = Path(_config_value(config, "path", "data/base.db"))
        if raw_path.is_absolute():
            db_path = raw_path
        else:
            wiz_root = Path(os.environ.get("WIZ_ROOT", "/opt/app"))
            db_path = wiz_root / raw_path
            if not db_path.exists():
                candidate = project_root / raw_path
                if candidate.exists():
                    db_path = candidate
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def placeholder(self) -> str:
        return "%s" if self.kind == "mysql" else "?"

    def quote(self, identifier: str) -> str:
        return "`" + identifier.replace("`", "``") + "`"

    def execute(self, sql: str, params=()):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, params)
            return cursor.rowcount
        finally:
            cursor.close()

    def fetchone(self, sql: str, params=()):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return dict(row) if row is not None else None
        finally:
            cursor.close()

    def fetchall(self, sql: str, params=()):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    def table_exists(self, table: str) -> bool:
        if self.kind == "mysql":
            row = self.fetchone("SHOW TABLES LIKE " + self.placeholder, (table,))
            return row is not None

        row = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        )
        return row is not None

    def columns(self, table: str):
        if self.kind == "mysql":
            rows = self.fetchall(f"SHOW COLUMNS FROM {self.quote(table)}")
            return {
                row.get("Field"): {
                    "type": row.get("Type") or "varchar(32)",
                    "nullable": str(row.get("Null") or "").upper() == "YES",
                }
                for row in rows
            }

        rows = self.fetchall(f"PRAGMA table_info({self.quote(table)})")
        return {
            row.get("name"): {
                "type": row.get("type") or "TEXT",
                "nullable": not bool(row.get("notnull")),
                "pk": bool(row.get("pk")),
            }
            for row in rows
        }

    def primary_key(self, table: str) -> str | None:
        if self.kind == "mysql":
            rows = self.fetchall(f"SHOW KEYS FROM {self.quote(table)} WHERE Key_name = 'PRIMARY'")
            if rows:
                return rows[0].get("Column_name")
            return None

        columns = self.columns(table)
        for name, meta in columns.items():
            if meta.get("pk"):
                return name
        return None

    def ensure_user_table(self):
        if not self.table_exists("user"):
            if self.kind == "mysql":
                self.execute(
                    """
                    CREATE TABLE `user` (
                      `id` varchar(32) NOT NULL,
                      `email` varchar(128) NOT NULL,
                      `password` varchar(200) NOT NULL,
                      `name` varchar(50) NOT NULL,
                      `mobile` varchar(20) NOT NULL DEFAULT '',
                      `running_start_date` date NULL,
                      `profile_image` longtext NULL,
                      `onboarded` tinyint(1) NOT NULL DEFAULT 0,
                      `is_public` tinyint(1) NOT NULL DEFAULT 1,
                      `role` varchar(16) NOT NULL DEFAULT 'user',
                      `created` datetime NOT NULL,
                      `updated` datetime NOT NULL,
                      PRIMARY KEY (`id`),
                      UNIQUE KEY `user_email_unique` (`email`)
                    )
                    """
                )
            else:
                self.execute(
                    """
                    CREATE TABLE `user` (
                      `id` TEXT NOT NULL PRIMARY KEY,
                      `email` TEXT NOT NULL UNIQUE,
                      `password` TEXT NOT NULL,
                      `name` TEXT NOT NULL,
                      `mobile` TEXT NOT NULL DEFAULT '',
                      `running_start_date` TEXT NULL,
                      `profile_image` TEXT NULL,
                      `onboarded` INTEGER NOT NULL DEFAULT 0,
                      `is_public` INTEGER NOT NULL DEFAULT 1,
                      `role` TEXT NOT NULL DEFAULT 'user',
                      `created` TEXT NOT NULL,
                      `updated` TEXT NOT NULL
                    )
                    """
                )
            return

        columns = self.columns("user")
        additions = {
            "mobile": "varchar(20) NOT NULL DEFAULT ''" if self.kind == "mysql" else "TEXT NOT NULL DEFAULT ''",
            "running_start_date": "date NULL" if self.kind == "mysql" else "TEXT NULL",
            "profile_image": "longtext NULL" if self.kind == "mysql" else "TEXT NULL",
            "onboarded": "tinyint(1) NOT NULL DEFAULT 0" if self.kind == "mysql" else "INTEGER NOT NULL DEFAULT 0",
            "is_public": "tinyint(1) NOT NULL DEFAULT 1" if self.kind == "mysql" else "INTEGER NOT NULL DEFAULT 1",
            "role": "varchar(16) NOT NULL DEFAULT 'user'" if self.kind == "mysql" else "TEXT NOT NULL DEFAULT 'user'",
            "username": "varchar(30) NULL" if self.kind == "mysql" else "TEXT NULL",
            "password_hash": "longtext NULL" if self.kind == "mysql" else "TEXT NULL",
            "display_name": "varchar(50) NULL" if self.kind == "mysql" else "TEXT NULL",
            "created_at": "datetime NULL" if self.kind == "mysql" else "TEXT NULL",
            "password_changed_at": "datetime NULL" if self.kind == "mysql" else "TEXT NULL",
            "password_failed_count": "int NOT NULL DEFAULT 0" if self.kind == "mysql" else "INTEGER NOT NULL DEFAULT 0",
            "password_locked_until": "datetime NULL" if self.kind == "mysql" else "TEXT NULL",
            "created": "datetime NULL" if self.kind == "mysql" else "TEXT NULL",
            "updated": "datetime NULL" if self.kind == "mysql" else "TEXT NULL",
        }
        for name, ddl in additions.items():
            if name not in columns:
                self.execute(f"ALTER TABLE `user` ADD COLUMN {self.quote(name)} {ddl}")

    def ensure_user_id_column(self, table: str) -> bool:
        columns = self.columns(table)
        if "user_id" in columns:
            return False
        ddl = "varchar(32) NULL" if self.kind == "mysql" else "TEXT NULL"
        self.execute(f"ALTER TABLE {self.quote(table)} ADD COLUMN `user_id` {ddl}")
        return True

    def make_user_id_nullable(self, table: str):
        if self.kind != "mysql":
            return
        columns = self.columns(table)
        meta = columns.get("user_id")
        if not meta:
            return
        self.execute(
            f"ALTER TABLE {self.quote(table)} MODIFY `user_id` {meta.get('type') or 'varchar(32)'} NULL"
        )

    def make_user_id_not_null(self, table: str):
        if self.kind != "mysql":
            return "SQLite cannot ALTER an existing column to NOT NULL in place."
        columns = self.columns(table)
        meta = columns.get("user_id")
        if not meta:
            return "user_id column is missing."
        self.execute(
            f"ALTER TABLE {self.quote(table)} MODIFY `user_id` {meta.get('type') or 'varchar(32)'} NOT NULL"
        )
        return ""


def _bcrypt_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _seed_admin(db: SQLAdapter, manifest: dict, dry_run: bool) -> dict:
    admin_email_env = _text(os.environ.get("ADMIN_INIT_EMAIL"))
    admin_email = admin_email_env or f"{ADMIN_USERNAME}@{DEFAULT_ADMIN_EMAIL_DOMAIN}"
    admin_login_username = _text(os.environ.get("ADMIN_INIT_USERNAME")) or ADMIN_LOGIN_USERNAME
    admin_name = _text(os.environ.get("ADMIN_DISPLAY_NAME")) or DEFAULT_ADMIN_DISPLAY_NAME
    now = _now()

    user_table_existed = db.table_exists("user")
    if not dry_run:
        db.ensure_user_table()

    existing = db.fetchone(
        f"SELECT * FROM `user` WHERE `id` = {db.placeholder}",
        (ADMIN_USERNAME,),
    ) if db.table_exists("user") else None
    conflict = None
    if db.table_exists("user"):
        columns = db.columns("user")
        conflict_conditions = []
        conflict_params = []
        if admin_email and "email" in columns:
            conflict_conditions.append(f"`email` = {db.placeholder}")
            conflict_params.append(admin_email)
        if admin_login_username and "username" in columns:
            conflict_conditions.append(f"`username` = {db.placeholder}")
            conflict_params.append(admin_login_username)
        if conflict_conditions:
            conflict = db.fetchone(
                f"SELECT * FROM `user` WHERE ({' OR '.join(conflict_conditions)}) AND `id` <> {db.placeholder}",
                tuple(conflict_params + [ADMIN_USERNAME]),
            )
    if conflict:
        raise RuntimeError(
            f"Requested admin email/username already belongs to another user id: {conflict.get('id')}"
        )

    manifest["admin"] = {
        "user_table_existed": user_table_existed,
        "admin_existed": existing is not None,
        "admin_row": existing,
        "admin_login_username": admin_login_username,
    }

    password = os.environ.get("ADMIN_INIT_PASSWORD")
    if existing is None:
        if not password:
            raise RuntimeError("ADMIN_INIT_PASSWORD is required when the admin account does not exist.")
        if len(password) < 8:
            raise RuntimeError("ADMIN_INIT_PASSWORD must be at least 8 characters.")

        if not dry_run:
            columns = db.columns("user")
            password_hash = _bcrypt_hash(password)
            values = {
                "id": ADMIN_USERNAME,
                "username": admin_login_username,
                "email": admin_email,
                "password_hash": password_hash,
                "password": password_hash,
                "display_name": admin_name,
                "name": admin_name,
                "mobile": "",
                "onboarded": 1,
                "is_public": 1,
                "role": "admin",
                "created_at": now,
                "password_changed_at": now,
                "password_failed_count": 0,
                "password_locked_until": None,
                "created": now,
                "updated": now,
            }
            insert_values = {key: value for key, value in values.items() if key in columns}
            column_sql = ", ".join(db.quote(key) for key in insert_values)
            placeholder_sql = ", ".join([db.placeholder] * len(insert_values))
            db.execute(
                f"INSERT INTO `user` ({column_sql}) VALUES ({placeholder_sql})",
                tuple(insert_values.values()),
            )
        return {"created": 1, "updated": 0, "email": admin_email, "username": admin_login_username}

    updates = {}
    admin_email = admin_email_env or existing.get("email") or admin_email
    columns = db.columns("user")
    if existing.get("role") != "admin":
        updates["role"] = "admin"
    if "username" in columns and admin_login_username and existing.get("username") != admin_login_username:
        updates["username"] = admin_login_username
    if admin_name and existing.get("name") != admin_name:
        updates["name"] = admin_name
    if "display_name" in columns and admin_name and existing.get("display_name") != admin_name:
        updates["display_name"] = admin_name
    if admin_email_env and existing.get("email") != admin_email:
        updates["email"] = admin_email
    if password:
        if len(password) < 8:
            raise RuntimeError("ADMIN_INIT_PASSWORD must be at least 8 characters.")
        password_hash = _bcrypt_hash(password)
        updates["password"] = password_hash
        if "password_hash" in columns:
            updates["password_hash"] = password_hash
        if "password_changed_at" in columns:
            updates["password_changed_at"] = now
        if "password_failed_count" in columns:
            updates["password_failed_count"] = 0
        if "password_locked_until" in columns:
            updates["password_locked_until"] = None

    if not updates:
        return {
            "created": 0,
            "updated": 0,
            "email": existing.get("email") or admin_email,
            "username": existing.get("username") or admin_login_username,
        }

    updates["updated"] = now
    if not dry_run:
        assignments = ", ".join(f"{db.quote(key)} = {db.placeholder}" for key in updates)
        params = list(updates.values()) + [ADMIN_USERNAME]
        db.execute(
            f"UPDATE `user` SET {assignments} WHERE `id` = {db.placeholder}",
            params,
        )
    return {"created": 0, "updated": 1, "email": admin_email, "username": admin_login_username}


def _row_has_user_id(row: dict) -> bool:
    owner_id = _text(row.get("user_id") or row.get("userId"))
    return bool(owner_id and owner_id != "local-user")


def _assign_row(row, admin_id: str):
    if isinstance(row, dict):
        if not _row_has_user_id(row):
            row = dict(row)
            row["user_id"] = admin_id
            return row, 1
        return row, 0
    return row, 0


def _assign_list(payload, admin_id: str):
    if not isinstance(payload, list):
        return payload, 0
    changed = 0
    rows = []
    for row in payload:
        next_row, did_change = _assign_row(row, admin_id)
        rows.append(next_row)
        changed += did_change
    return rows, changed


def _assign_rest_days(payload, admin_id: str):
    if not isinstance(payload, list):
        return payload, 0
    changed = 0
    rows = []
    for row in payload:
        if isinstance(row, dict):
            next_row, did_change = _assign_row(row, admin_id)
        else:
            next_row = {"date": row, "user_id": admin_id}
            did_change = 1
        rows.append(next_row)
        changed += did_change
    return rows, changed


def _assign_weights(payload, admin_id: str):
    if isinstance(payload, dict):
        rows = [
            {"date": date, "weight_kg": weight, "user_id": admin_id}
            for date, weight in payload.items()
        ]
        return rows, len(rows)
    return _assign_list(payload, admin_id)


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, ensure_ascii=False, indent=2)


def _backup_json_file(path: Path, backup_dir: Path, manifest: dict):
    rel = path.name
    backup_path = backup_dir / rel
    entry = {
        "path": str(path),
        "backup_path": str(backup_path),
        "existed": path.exists(),
    }
    if path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
    manifest.setdefault("json_files", {})[rel] = entry


def _migrate_json_files(data_dir: Path, backup_dir: Path, manifest: dict, admin_id: str, dry_run: bool):
    summary = {}
    handlers = {
        "list": _assign_list,
        "rest_days": _assign_rest_days,
        "weights": _assign_weights,
    }

    for label, filename, kind in JSON_RECORD_FILES:
        path = data_dir / filename
        if not path.exists():
            summary[label] = 0
            continue
        payload = _read_json(path)
        next_payload, changed = handlers[kind](payload, admin_id)
        summary[label] = changed
        if changed and not dry_run:
            _backup_json_file(path, backup_dir, manifest)
            _write_json(path, next_payload)
    return summary


def _migrate_sql_tables(db: SQLAdapter, manifest: dict, admin_id: str, dry_run: bool):
    results = {}
    for table in SQL_RECORD_TABLES:
        if not db.table_exists(table):
            continue

        added_column = False
        if not dry_run:
            added_column = db.ensure_user_id_column(table)

        columns = db.columns(table)
        if "user_id" not in columns and dry_run:
            results[table] = {"updated": 0, "warning": "user_id column would be added."}
            continue

        pk = db.primary_key(table)
        changed_ids = []
        if pk:
            rows = db.fetchall(
                f"SELECT {db.quote(pk)} FROM {db.quote(table)} WHERE `user_id` IS NULL OR `user_id` = ''"
            )
            changed_ids = [row.get(pk) for row in rows]

        if dry_run:
            updated = len(changed_ids)
            warning = "" if pk else "Primary key missing; dry-run count skipped."
        else:
            updated = db.execute(
                f"UPDATE {db.quote(table)} SET `user_id` = {db.placeholder} WHERE `user_id` IS NULL OR `user_id` = ''",
                (admin_id,),
            )
            warning = db.make_user_id_not_null(table) or ""

        entry = {
            "table": table,
            "primary_key": pk,
            "changed_ids": changed_ids,
            "added_user_id_column": added_column,
            "updated": updated,
            "warning": warning,
        }
        manifest.setdefault("sql_tables", []).append(entry)
        results[table] = {"updated": updated, "warning": warning}
    return results


def _latest_backup_dir(data_dir: Path) -> Path | None:
    root = data_dir / "migration_backups"
    if not root.exists():
        return None
    candidates = sorted(root.glob("assign_admin_*"), reverse=True)
    return candidates[0] if candidates else None


def _restore_json_files(manifest: dict, dry_run: bool):
    restored = 0
    for entry in (manifest.get("json_files") or {}).values():
        path = Path(entry.get("path") or "")
        backup_path = Path(entry.get("backup_path") or "")
        if dry_run:
            restored += 1
            continue
        if entry.get("existed") and backup_path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, path)
            restored += 1
        elif not entry.get("existed") and path.exists():
            path.unlink()
            restored += 1
    return restored


def _restore_admin(db: SQLAdapter, manifest: dict, dry_run: bool):
    admin = manifest.get("admin") or {}
    existing = admin.get("admin_row")
    if admin.get("admin_existed") and isinstance(existing, dict):
        if dry_run:
            return "would_restore"
        columns = db.columns("user")
        values = {key: value for key, value in existing.items() if key in columns and key != "id"}
        assignments = ", ".join(f"{db.quote(key)} = {db.placeholder}" for key in values)
        if assignments:
            db.execute(
                f"UPDATE `user` SET {assignments} WHERE `id` = {db.placeholder}",
                list(values.values()) + [ADMIN_USERNAME],
            )
        return "restored"

    if dry_run:
        return "would_delete"
    if db.table_exists("user"):
        db.execute(f"DELETE FROM `user` WHERE `id` = {db.placeholder}", (ADMIN_USERNAME,))
    return "deleted"


def _rollback_sql_tables(db: SQLAdapter, manifest: dict, dry_run: bool):
    results = {}
    for entry in manifest.get("sql_tables") or []:
        table = entry.get("table")
        pk = entry.get("primary_key")
        changed_ids = entry.get("changed_ids") or []
        if not table or not db.table_exists(table):
            continue
        if not pk or not changed_ids:
            results[table] = 0
            continue
        if dry_run:
            results[table] = len(changed_ids)
            continue
        db.make_user_id_nullable(table)
        for start in range(0, len(changed_ids), 500):
            chunk = changed_ids[start:start + 500]
            placeholders = ", ".join([db.placeholder] * len(chunk))
            db.execute(
                f"UPDATE {db.quote(table)} SET `user_id` = NULL WHERE {db.quote(pk)} IN ({placeholders})",
                chunk,
            )
        results[table] = len(changed_ids)
    return results


def migrate(args):
    project_root = Path(args.project_root).resolve()
    data_dir = Path(args.data_dir or os.environ.get("RUNNINGMATE_DATA_DIR", "/opt/app/data")).resolve()
    backup_dir = data_dir / "migration_backups" / f"assign_admin_{_utc_timestamp()}"
    manifest = {
        "migration": "assign_admin",
        "created_at": _now(),
        "admin_id": ADMIN_USERNAME,
        "admin_username": ADMIN_USERNAME,
        "admin_login_username": _text(os.environ.get("ADMIN_INIT_USERNAME")) or ADMIN_LOGIN_USERNAME,
        "data_dir": str(data_dir),
        "backup_dir": str(backup_dir),
        "dry_run": bool(args.dry_run),
        "json_files": {},
        "sql_tables": [],
    }

    db = SQLAdapter(_load_database_config(project_root), project_root)
    try:
        admin_summary = _seed_admin(db, manifest, args.dry_run)
        json_summary = _migrate_json_files(data_dir, backup_dir, manifest, ADMIN_USERNAME, args.dry_run)
        sql_summary = _migrate_sql_tables(db, manifest, ADMIN_USERNAME, args.dry_run)
        if not args.dry_run:
            backup_dir.mkdir(parents=True, exist_ok=True)
            (backup_dir / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            db.commit()
        else:
            db.rollback()
        return {
            "admin": admin_summary,
            "json": json_summary,
            "sql": sql_summary,
            "backup_dir": str(backup_dir),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def rollback(args):
    project_root = Path(args.project_root).resolve()
    data_dir = Path(args.data_dir or os.environ.get("RUNNINGMATE_DATA_DIR", "/opt/app/data")).resolve()
    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else _latest_backup_dir(data_dir)
    if backup_dir is None:
        raise RuntimeError("No assign_admin backup directory was found.")

    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    db = SQLAdapter(_load_database_config(project_root), project_root)
    try:
        admin_result = _restore_admin(db, manifest, args.dry_run)
        sql_result = _rollback_sql_tables(db, manifest, args.dry_run)
        json_restored = _restore_json_files(manifest, args.dry_run)
        if not args.dry_run:
            db.commit()
        else:
            db.rollback()
        return {
            "backup_dir": str(backup_dir),
            "admin": admin_result,
            "sql": sql_result,
            "json_restored": json_restored,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Assign legacy records to the admin user.")
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--data-dir", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--backup-dir", default="")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    result = rollback(args) if args.rollback else migrate(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
