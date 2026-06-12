# 개인 서버 비밀값 정리

작성일: 2026-06-10

## 원칙

- 이 문서에는 실제 비밀번호, API key, OAuth secret, rclone token을 기록하지 않는다.
- 실제 값은 비밀번호 관리자와 개인 서버의 `/opt/app/config` 아래 권한 제한 파일에만 둔다.
- Google Drive는 운영 DB가 아니라 백업 보관소다. 운영 DB는 MySQL에 있고, Google Drive에는 암호화된 백업 산출물만 올라간다.
- 회사 서버에서 만든 임시 토큰은 개인 서버 이전 후 폐기하거나 재발급한다.

## 내가 정리할 수 있는 것과 사용자가 해야 할 것

| 구분 | Codex가 할 수 있는 일 | 사용자가 해야 할 일 |
| --- | --- | --- |
| 비밀값 목록 | 필요한 항목과 위치를 문서화한다. | 실제 값을 비밀번호 관리자에 저장한다. |
| 서버 파일 | 예시 파일 구조와 검증 명령을 제공한다. | 개인 서버에서 실제 값을 입력하고 `chmod 600`을 적용한다. |
| Google Drive | rclone/백업 비밀값 위치를 정리한다. | 개인 서버에서 Google 계정 인증을 완료한다. |
| 검증 | `scripts/verify_runtime_secrets.py`와 백업 리허설 절차를 제공한다. | 실제 서버에서 명령을 실행하고 결과를 확인한다. |

## 비밀번호 관리자에 만들 항목

권장 항목명: `RunningMate Production Secrets`

저장할 필드:

| 필드 | 설명 | 저장 위치 |
| --- | --- | --- |
| `mysql_admin_password` | DB root/admin 계정 비밀번호 | 비밀번호 관리자만 |
| `runningmate_app_password` | 앱이 `rundb`를 읽고 쓰는 DB 계정 비밀번호 | `database.env` |
| `runningmate_backup_password` | 백업 스크립트가 `rundb`를 읽는 DB 계정 비밀번호 | `mysql-backup.cnf` |
| `openai_api_key` | 앱에서 쓰는 OpenAI API key | `openai.env` |
| `openai_project_id` | 운영 OpenAI project id | `openai.env` 또는 운영 문서 |
| `naver_client_secret` | Naver OAuth client secret | `oauth.env` |
| `google_client_secret` | Google OAuth client secret | `oauth.env` |
| `sendgrid_api_key` | 이메일/알림 발송 API key | `mail.env` 또는 `ops.env` |
| `wiz_secret_key` | WIZ 세션/서명용 secret | `service.env` 또는 프로세스 환경변수 |
| `runningmate_admin_token` | 운영 점검/관리 API token | `service.env` 또는 프로세스 환경변수 |
| `backup_passphrase` | 백업 파일 암호화 passphrase | `/opt/app/config/backup-passphrase` |
| `rclone_google_drive_token` | Google Drive OAuth token | `rclone.conf` 내부 |
| `rclone_crypt_password` | rclone crypt remote를 쓸 때의 암호 | `rclone.conf` 내부 |

## 개인 서버 파일 배치

개인 서버에서는 아래 파일을 만들고 모두 `600` 권한으로 제한한다.

```text
/opt/app/config/
  database.env
  openai.env
  oauth.env
  mail.env
  ops.env
  backup.env
  mysql-backup.cnf
  backup-passphrase
  rclone/
    rclone.conf
```

권한:

```bash
chmod 700 /opt/app/config /opt/app/config/rclone
chmod 600 /opt/app/config/*.env /opt/app/config/mysql-backup.cnf /opt/app/config/backup-passphrase
chmod 600 /opt/app/config/rclone/rclone.conf
```

## 파일별 템플릿

### `/opt/app/config/database.env`

```env
RUNNINGMATE_DB_TYPE=mysql
RUNNINGMATE_DB_NAME=rundb
RUNNINGMATE_DB_USER=runningmate_app
RUNNINGMATE_DB_PASSWORD=<runningmate_app_password>
RUNNINGMATE_DB_HOST=127.0.0.1
RUNNINGMATE_DB_PORT=3306
RUNNINGMATE_DB_CHARSET=utf8mb4
```

### `/opt/app/config/mysql-backup.cnf`

```ini
[client]
user=runningmate_backup
password=<runningmate_backup_password>
host=127.0.0.1
port=3306
```

### `/opt/app/config/backup.env`

```env
RUNNINGMATE_BACKUP_DIR=/opt/app/data/backups
RUNNINGMATE_DB_MYSQL_DEFAULTS_FILE=/opt/app/config/mysql-backup.cnf
RUNNINGMATE_BACKUP_PASSPHRASE_FILE=/opt/app/config/backup-passphrase
RUNNINGMATE_BACKUP_RCLONE_CONFIG=/opt/app/config/rclone/rclone.conf
RUNNINGMATE_BACKUP_RCLONE_REMOTE=runningmate-drive:
RUNNINGMATE_BACKUP_REMOTE_DIR=runningmate-backups
```

### `/opt/app/config/backup-passphrase`

한 줄짜리 긴 임의 문자열만 넣는다. 생성 예:

```bash
openssl rand -base64 48
```

### `/opt/app/config/openai.env`

```env
RUNNINGMATE_AI_PROVIDER=openai
OPENAI_API_KEY=<openai_api_key>
RUNNINGMATE_OPENAI_PROJECT_ID=<openai_project_id>
RUNNINGMATE_CHAT_MODEL=gpt-5.4-mini-2026-03-17
RUNNINGMATE_VISION_MODEL=gpt-5.4-mini-2026-03-17
RUNNINGMATE_AI_CHAT_DAILY_LIMIT=5
RUNNINGMATE_AI_CHAT_MONTHLY_LIMIT=120
RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT=35
```

### `/opt/app/config/oauth.env`

```env
NAVER_CLIENT_ID=<naver_client_id>
NAVER_CLIENT_SECRET=<naver_client_secret>
NAVER_REDIRECT_URI=https://<personal-domain>/api/auth/naver/callback
GOOGLE_CLIENT_ID=<google_client_id>
GOOGLE_CLIENT_SECRET=<google_client_secret>
GOOGLE_REDIRECT_URI=https://<personal-domain>/api/auth/google/callback
```

### `/opt/app/config/mail.env`

```env
RUNNINGMATE_MAIL_FROM=<verified_sender_email>
RUNNINGMATE_MAIL_FROM_NAME=RunningMate
SENDGRID_API_KEY=<sendgrid_api_key>
```

### `/opt/app/config/ops.env`

```env
RUNNINGMATE_ALERT_EMAIL_TO=<owner_email>
RUNNINGMATE_ALERT_REPEAT_SECONDS=3600
RUNNINGMATE_HEALTHCHECK_URL=http://127.0.0.1:3000/healthz
RUNNINGMATE_HEALTHCHECK_RESTART=1
RUNNINGMATE_RESTART_COMMAND=systemctl restart runningmate
```

## Google Drive에 올라갈 것

Google Drive에는 원본 DB 접속 정보나 원본 env 파일을 올리지 않는다.

올릴 대상:

- `database.sql.gz`가 포함된 백업 묶음
- `data.tar.gz`
- `run_images.tar.gz`
- `run_media.tar.gz`
- `manifest.txt`
- `restore-rehearsal-report.json`
- 위 산출물을 묶고 암호화한 `*.tar.gz.enc`
- 무결성 확인용 `*.sha256`

권장 방식:

1. `scripts/backup-runningmate-private-server.sh`로 로컬 백업을 만든다.
2. `scripts/encrypt-runningmate-backup.sh`로 백업 디렉터리를 암호화한다.
3. 암호화된 `*.tar.gz.enc`와 `*.sha256`만 Google Drive에 복사한다.
4. 복구 리허설 때는 Google Drive에서 내려받은 파일을 복호화한 뒤 임시 DB에 복원한다.

## 개인 서버 이전 전 해야 할 일

1. 비밀번호 관리자에 `RunningMate Production Secrets` 항목을 만든다.
2. `runningmate_app`, `runningmate_backup`, OpenAI, OAuth, SendGrid, backup passphrase 값을 항목별로 넣는다.
3. 개인 서버 도메인이 확정되기 전까지 OAuth redirect URI와 메일 도메인 인증은 임시 상태로 표시한다.
4. 회사 서버에는 Google Drive rclone token을 새로 만들지 않는다. 부득이하게 만들었다면 개인 서버 이전 후 폐기한다.
5. 현재 회사 서버의 `/opt/app/config/*.env` 값은 개인 서버 이전 후 재발급 또는 비밀번호 변경 대상으로 표시한다.

## 개인 서버 이전 후 해야 할 일

1. `/opt/app/config` 파일들을 실제 값으로 생성하고 권한을 `600`으로 제한한다.
2. Google Drive용 `rclone config`를 개인 서버에서 실행해 `/opt/app/config/rclone/rclone.conf`를 만든다.
3. 백업 생성, 암호화, Google Drive 업로드를 한 번 수동 실행한다.
4. Google Drive에서 백업을 내려받아 복구 리허설을 실행한다.
5. `/healthz`, 로그인, 이미지 업로드, AI 채팅, 이미지 파싱, 이메일 알림을 확인한다.
6. 회사 서버에 남아 있던 임시 key, OAuth secret, SendGrid key, DB 비밀번호를 폐기 또는 회전한다.

## 검증 명령

런타임 secret 파일 검증:

```bash
cd /opt/app/project/main
python scripts/verify_runtime_secrets.py
```

백업 생성:

```bash
cd /opt/app/project/main
scripts/backup-runningmate-private-server.sh
```

백업 암호화:

```bash
cd /opt/app/project/main
RUNNINGMATE_BACKUP_PASSPHRASE_FILE=/opt/app/config/backup-passphrase \
  scripts/encrypt-runningmate-backup.sh /opt/app/data/backups/<timestamp>
```

Google Drive 업로드 예:

```bash
rclone --config /opt/app/config/rclone/rclone.conf copy \
  /opt/app/data/backups/<timestamp>.tar.gz.enc \
  runningmate-drive:runningmate-backups/
```

복구 리허설:

```bash
cd /opt/app/project/main
python scripts/runningmate_restore_rehearsal.py --backup-dir /opt/app/data/backups/<timestamp>
```
