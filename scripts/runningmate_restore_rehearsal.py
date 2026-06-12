#!/usr/bin/env python3
"""Restore a RunningMate backup into a temporary MySQL database and verify it."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import pymysql


DEFAULT_BACKUP_DIR = "/opt/app/data/backups"
DEFAULT_SOURCE_ENV = "/opt/app/config/backup.env"
DEFAULT_ADMIN_ENV = "/opt/app/config/database.env.before-root"


def load_env(path: str | os.PathLike[str]) -> dict[str, str]:
    data: dict[str, str] = {}
    env_path = Path(path)
    if not env_path.exists():
        return data
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def merged_env(*paths: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for path in paths:
        data.update(load_env(path))
    return data


def db_connect(env: dict[str, str], database: str | None = None):
    return pymysql.connect(
        host=env["RUNNINGMATE_DB_HOST"],
        port=int(env.get("RUNNINGMATE_DB_PORT", "3306")),
        user=env["RUNNINGMATE_DB_USER"],
        password=env["RUNNINGMATE_DB_PASSWORD"],
        database=database or env.get("RUNNINGMATE_DB_NAME"),
        charset=env.get("RUNNINGMATE_DB_CHARSET") or "utf8",
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
        autocommit=True,
    )


def latest_backup(root: Path) -> Path:
    candidates = [path for path in root.iterdir() if path.is_dir()]
    if not candidates:
        raise RuntimeError(f"No backup directories under {root}")
    return sorted(candidates)[-1]


def table_counts(env: dict[str, str], database: str) -> dict[str, int]:
    conn = db_connect(env, database=database)
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
            tables = [row[0] for row in cur.fetchall()]
            counts: dict[str, int] = {}
            for table in tables:
                escaped = table.replace("`", "``")
                cur.execute(f"SELECT COUNT(*) FROM `{escaped}`")
                counts[table] = int(cur.fetchone()[0])
            return counts
    finally:
        conn.close()


def write_mysql_defaults(env: dict[str, str], database: str | None = None) -> Path:
    fd, raw_path = tempfile.mkstemp(prefix="runningmate-mysql-", suffix=".cnf")
    path = Path(raw_path)
    with os.fdopen(fd, "w", encoding="utf-8") as fp:
        fp.write("[client]\n")
        fp.write(f"host={env['RUNNINGMATE_DB_HOST']}\n")
        fp.write(f"port={env.get('RUNNINGMATE_DB_PORT', '3306')}\n")
        fp.write(f"user={env['RUNNINGMATE_DB_USER']}\n")
        fp.write(f"password={env['RUNNINGMATE_DB_PASSWORD']}\n")
        fp.write(f"default-character-set={env.get('RUNNINGMATE_DB_CHARSET') or 'utf8'}\n")
        if database:
            fp.write(f"database={database}\n")
    path.chmod(0o600)
    return path


def mysql_exec(admin_env: dict[str, str], sql: str, database: str | None = None) -> None:
    defaults = write_mysql_defaults(admin_env, database=database)
    try:
        result = subprocess.run(
            ["mysql", f"--defaults-extra-file={defaults}"],
            input=sql,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "mysql command failed").strip())
    finally:
        defaults.unlink(missing_ok=True)


def restore_dump(admin_env: dict[str, str], backup_dir: Path, restore_db: str) -> None:
    dump = backup_dir / "database.sql.gz"
    if not dump.exists():
        raise RuntimeError(f"Missing database dump: {dump}")

    defaults = write_mysql_defaults(admin_env, database=restore_db)
    try:
        sql_bytes = gzip.open(dump, "rb").read()
        result = subprocess.run(
            ["mysql", f"--defaults-extra-file={defaults}", restore_db],
            input=sql_bytes,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or b"mysql restore failed").decode("utf-8", "replace")
            raise RuntimeError(message.strip())
    finally:
        defaults.unlink(missing_ok=True)


def tar_summary(path: Path) -> dict[str, int | str | bool]:
    if not path.exists():
        return {"exists": False, "members": 0, "size": 0}
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
    return {"exists": True, "members": len(members), "size": path.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup-root", default=os.environ.get("RUNNINGMATE_BACKUP_DIR", DEFAULT_BACKUP_DIR))
    parser.add_argument("--backup-dir", default="")
    parser.add_argument("--source-env", default=os.environ.get("RUNNINGMATE_BACKUP_ENV_FILE", DEFAULT_SOURCE_ENV))
    parser.add_argument("--admin-env", default=os.environ.get("RUNNINGMATE_RESTORE_ADMIN_ENV_FILE", DEFAULT_ADMIN_ENV))
    parser.add_argument("--keep-db", action="store_true")
    args = parser.parse_args()

    backup_dir = Path(args.backup_dir).resolve() if args.backup_dir else latest_backup(Path(args.backup_root).resolve())
    source_env = merged_env(args.source_env)
    admin_env = merged_env(args.admin_env)
    source_db = source_env["RUNNINGMATE_DB_NAME"]
    restore_db = f"{source_db}_restore_rehearsal_{time.strftime('%Y%m%d%H%M%S', time.gmtime())}"

    report: dict[str, object] = {
        "backup_dir": str(backup_dir),
        "source_db": source_db,
        "restore_db": restore_db,
        "kept_restore_db": args.keep_db,
        "ok": False,
    }

    try:
        source_counts = table_counts(source_env, source_db)
        mysql_exec(
            admin_env,
            f"DROP DATABASE IF EXISTS `{restore_db}`; "
            f"CREATE DATABASE `{restore_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
        )
        restore_dump(admin_env, backup_dir, restore_db)
        restore_counts = table_counts(admin_env, restore_db)
        mismatches = {
            table: {"source": count, "restored": restore_counts.get(table)}
            for table, count in source_counts.items()
            if restore_counts.get(table) != count
        }

        archives = {
            "data": tar_summary(backup_dir / "data.tar.gz"),
            "run_images": tar_summary(backup_dir / "run_images.tar.gz"),
            "run_media": tar_summary(backup_dir / "run_media.tar.gz"),
        }

        report.update(
            {
                "source_table_count": len(source_counts),
                "restored_table_count": len(restore_counts),
                "row_count_mismatches": mismatches,
                "archives": archives,
                "ok": not mismatches,
            }
        )
        if mismatches:
            return_code = 2
        else:
            return_code = 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return_code = 1
    finally:
        if not args.keep_db:
            try:
                mysql_exec(admin_env, f"DROP DATABASE IF EXISTS `{restore_db}`;")
                report["restore_db_dropped"] = True
            except Exception as exc:
                report["restore_db_drop_error"] = f"{type(exc).__name__}: {exc}"

        report_path = backup_dir / "restore-rehearsal-report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        report_path.chmod(0o600)

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return return_code


if __name__ == "__main__":
    sys.exit(main())
