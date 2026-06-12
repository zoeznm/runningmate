# Secret Audit - 2026-06-09

## Scope

- Review ID: lnpjpixpqoacfdgqaesqqvpbiripxnjg
- Scope checked: current WIZ project files, ignored project config, referenced server env files under `/opt/app/config`, and local log candidates.
- Secret values were not recorded in this document.

## Findings

| Location | Finding | Action |
| --- | --- | --- |
| `config/database.py:7` | Plaintext DB password was present in the project config file. | Removed from the file. DB connection now reads `RUNNINGMATE_DB_*` variables or `/opt/app/config/database.env`. Rotate the previous DB credential before production. |
| `/opt/app/config/openai.env:1` | Active-looking `OPENAI_API_KEY` is present in a plaintext server env file. File mode is `600`, but the key must be considered exposed to server filesystem readers. | Revoke the current OpenAI key, create a new production project key, and inject it from Secrets Manager or a deployment environment variable. |
| `/opt/app/config/oauth.env:4` | `NAVER_CLIENT_SECRET` is present in a plaintext server env file. File mode is `600`. | Rotate the Naver OAuth secret and inject it from Secrets Manager or a deployment environment variable. |
| `/opt/app/config/oauth.env:6` | `GOOGLE_CLIENT_SECRET` is present in a plaintext server env file. File mode is `600`. | Rotate the Google OAuth secret and inject it from Secrets Manager or a deployment environment variable. |
| `/opt/app/config/mail.env:6` | Active-looking SendGrid API key is present in a plaintext server env file. File mode is `600`. | Revoke the SendGrid key, create a least-privilege mail-send key, and inject it from Secrets Manager or a deployment environment variable. |
| `README.md:142`, `.env.example:1` | OpenAI key examples used `sk-...` shaped placeholders. | Replaced with blank or bracketed placeholders to reduce copy/paste and scanner false-positive risk. |
| `src/app/page.members/api.py:39` | A fixed default invite password was hardcoded. | Replaced with a per-user random temporary password and no longer returns the generated value. Invitees must use the password reset flow. |
| ReviewOps message on 2026-06-09 | A new OpenAI key was pasted into the work request. | Treat it as exposed. Do not commit it or document it. Revoke it and inject a newly generated key through managed runtime secrets. |
| `/opt/app/config/openai.env` | Runtime provider was configured as `codex`. | Updated `RUNNINGMATE_AI_PROVIDER` to `openai` without printing or changing the key value. |
| `/opt/app/config/database.env` | DB runtime env file has been created with existing DB connection settings. File mode is `600`. | Keep it out of the project repository and move the same values to Secrets Manager or process environment for managed production deployment. Rotate the DB password because it was previously present in project config. |

## Items To Move To Managed Secrets

- `OPENAI_API_KEY`
- `CODEX_ACCESS_TOKEN` if Codex fallback remains enabled for development
- `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `NAVER_REDIRECT_URI`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
- `SENDGRID_API_KEY`
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`
- `RUNNINGMATE_DB_TYPE`, `RUNNINGMATE_DB_NAME`, `RUNNINGMATE_DB_USER`, `RUNNINGMATE_DB_PASSWORD`, `RUNNINGMATE_DB_HOST`, `RUNNINGMATE_DB_PORT`, `RUNNINGMATE_DB_CHARSET`
- `WIZ_SECRET_KEY` or the framework session secret file if it is shared across environments
- `RUNNINGMATE_ADMIN_TOKEN`
- `RUNNINGMATE_WEATHER_SERVICE_KEY`
- Apple Music private key path and developer token values

## Pre-Deploy Verification

1. Revoke the previously exposed OpenAI, OAuth, mail, and DB credentials in their provider consoles.
2. Create production-only replacements with least privilege and billing/usage limits.
3. Inject replacements through Secrets Manager or server process environment variables. Avoid committing `.env` or provider env files.
4. Set DB variables before restarting WIZ; `RUNNINGMATE_DB_PASSWORD` must be non-empty in production.
5. Run a masked secret scan:

```bash
rg -n --hidden -g '!node_modules/**' -g '!.git/**' -g '!build/**' -g '!bundle/**' \
  'sk-(proj-)?[A-Za-z0-9_-]{20,}|GOCSPX-[A-Za-z0-9_-]{20,}|SG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}|password="[^"]+"' .
```

6. Confirm server env file permissions are `600` if temporary files are still used during the transition.
7. Restart WIZ and verify `/api/ai-config`, OAuth login, password reset mail, and DB-backed login without printing secrets in logs.
8. Run the runtime verifier:

```bash
python scripts/verify_runtime_secrets.py
```
