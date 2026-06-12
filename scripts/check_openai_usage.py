#!/usr/bin/env python3
"""Check OpenAI project usage and costs without printing secrets."""

import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


SERVER_CONFIG_DIR = Path(os.environ.get("RUNNINGMATE_SERVER_CONFIG_DIR", "/opt/app/config"))
ENV_FILE = Path(os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", SERVER_CONFIG_DIR / "openai.env"))
API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")


def load_env_file(path):
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


def env_float(name, default=0.0):
    try:
        return max(0.0, float(os.environ.get(name, default) or 0))
    except Exception:
        return default


def env_list(name, default):
    value = os.environ.get(name, default)
    items = []
    for item in str(value or "").split(","):
        try:
            items.append(float(item.strip()))
        except Exception:
            continue
    return sorted(set(item for item in items if item >= 0))


def month_start(now):
    return dt.datetime(now.year, now.month, 1, tzinfo=dt.timezone.utc)


def day_start(now):
    return dt.datetime(now.year, now.month, now.day, tzinfo=dt.timezone.utc)


def unix_seconds(value):
    return int(value.timestamp())


def api_get(path, params, admin_key):
    query = urllib.parse.urlencode(params, doseq=True)
    request = urllib.request.Request(
        f"{API_BASE}{path}?{query}",
        headers={
            "Authorization": f"Bearer {admin_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def cost_total(payload):
    total = 0.0
    for bucket in payload.get("data") or []:
        for result in bucket.get("results") or []:
            amount = result.get("amount") if isinstance(result, dict) else None
            if isinstance(amount, dict):
                try:
                    total += float(amount.get("value") or 0)
                except Exception:
                    pass
    return round(total, 4)


def completion_usage_totals(payload):
    totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "input_cached_tokens": 0,
        "num_model_requests": 0,
    }
    for bucket in payload.get("data") or []:
        for result in bucket.get("results") or []:
            if not isinstance(result, dict):
                continue
            for key in totals:
                try:
                    totals[key] += int(result.get(key) or 0)
                except Exception:
                    pass
    return totals


def percentage(value, budget):
    if not budget:
        return 0.0
    return round((value / budget) * 100, 2)


def status_for(daily_pct, monthly_pct, thresholds):
    if daily_pct >= 100 or monthly_pct >= 100:
        return "critical", 2
    warn_at = max([item for item in thresholds if item < 100] or [80])
    if daily_pct >= warn_at or monthly_pct >= warn_at:
        return "warning", 1
    return "ok", 0


def main():
    load_env_file(ENV_FILE)
    admin_key = os.environ.get("OPENAI_ADMIN_KEY", "").strip()
    if not admin_key:
        print(json.dumps({
            "success": False,
            "message": "OPENAI_ADMIN_KEY is required for OpenAI usage monitoring.",
        }, ensure_ascii=False))
        return 1

    project_id = os.environ.get("RUNNINGMATE_OPENAI_PROJECT_ID", "").strip()
    daily_budget = env_float("RUNNINGMATE_OPENAI_DAILY_BUDGET_USD", 0.0)
    monthly_budget = env_float("RUNNINGMATE_OPENAI_MONTHLY_BUDGET_USD", 0.0)
    thresholds = env_list("RUNNINGMATE_OPENAI_ALERT_THRESHOLDS", "50,80,95,100")
    now = dt.datetime.now(dt.timezone.utc)

    base_params = {"bucket_width": "1d", "limit": 31}
    if project_id:
        base_params["project_ids"] = [project_id]

    monthly_costs = api_get("/organization/costs", {
        **base_params,
        "start_time": unix_seconds(month_start(now)),
        "end_time": unix_seconds(now),
        "group_by": ["project_id", "line_item"],
    }, admin_key)
    daily_costs = api_get("/organization/costs", {
        **base_params,
        "start_time": unix_seconds(day_start(now)),
        "end_time": unix_seconds(now),
        "group_by": ["project_id", "line_item"],
    }, admin_key)
    completions = api_get("/organization/usage/completions", {
        **base_params,
        "start_time": unix_seconds(month_start(now)),
        "end_time": unix_seconds(now),
        "group_by": ["project_id", "model"],
    }, admin_key)

    daily_spend = cost_total(daily_costs)
    monthly_spend = cost_total(monthly_costs)
    daily_pct = percentage(daily_spend, daily_budget)
    monthly_pct = percentage(monthly_spend, monthly_budget)
    status, exit_code = status_for(daily_pct, monthly_pct, thresholds)

    print(json.dumps({
        "success": True,
        "status": status,
        "project_id": project_id or None,
        "checked_at": now.replace(microsecond=0).isoformat(),
        "budgets_usd": {
            "daily": daily_budget,
            "monthly": monthly_budget,
        },
        "spend_usd": {
            "daily": daily_spend,
            "monthly": monthly_spend,
        },
        "budget_percent": {
            "daily": daily_pct,
            "monthly": monthly_pct,
        },
        "alert_thresholds": thresholds,
        "completion_usage_month": completion_usage_totals(completions),
    }, ensure_ascii=False, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
