# 라즈베리파이 배포 준비 체크리스트

작성일: 2026-06-11
대상: 러닝메이트 WIZ 프로젝트 `main`
조사 기준: `/opt/app/project/main` 프로젝트 파일과 `/opt/app` WIZ 런타임 설정

## 1. 프론트엔드/백엔드 프레임워크

- [x] 프론트엔드: Angular 18 기반 WIZ Source App 구조
  - 근거: `src/angular/package.json`, `src/app/page.*`, `src/app/layout.*`, `src/app/component.*`
  - 템플릿/스타일: Pug, SCSS, Tailwind CSS
- [x] 백엔드: WIZ/Season Framework + Flask 기반 Python 라우트/API
  - 근거: `/opt/app/public/app.py`의 `season.app()`, `src/route/*/controller.py`, `src/app/*/api.py`
  - ORM: Peewee, DB 접속은 `config/database.py`와 `src/portal/season/model/orm.py` 경유
- [x] 실시간/소켓 기반: Flask-SocketIO 설정이 WIZ 런타임에 포함됨
  - 근거: `/opt/app/config/boot.py`의 `socketio` 설정, `src/angular/wiz.ts`의 `socket.io-client`
- [x] 모바일 래퍼: Capacitor 8 기반 iOS 래퍼가 있지만 라즈베리파이 웹 배포에는 필수 아님
  - 근거: `capacitor.config.json`, `ios/`

## 2. 사용 언어와 런타임 버전

- [x] Python: 현재 환경 기준 `3.14.4`
- [x] WIZ/Season: 현재 설치 기준 `season 2.5.2`
- [x] Flask: 현재 설치 기준 `3.0.2`
- [x] Flask-SocketIO: 현재 설치 기준 `5.3.6`
- [x] Node.js: 현재 환경 기준 `v24.15.0`
- [x] npm: 현재 환경 기준 `11.12.1`
- [x] Angular: `18.2.x`
- [x] TypeScript: `~5.5.4`
- [x] 주요 언어/파일: Python, TypeScript, Pug, SCSS, JSON, Bash
- [ ] 라즈베리파이에서는 위 버전을 그대로 맞추거나, WIZ/Season과 native wheel 호환성이 검증된 Python/Node 버전으로 고정해야 함

## 3. 실행 관련 파일 유무

- [x] `package.json`: 있음. 루트는 Capacitor/iOS 및 일부 migration script 중심
- [x] `package-lock.json`: 있음
- [x] `src/angular/package.json`: 있음. Angular 앱 의존성과 `build/start/test` script 포함
- [x] `.env.example`: 있음. 운영 환경변수 이름을 한곳에 모아둠
- [x] `config/database.py`: 있음. DB 접속을 `RUNNINGMATE_DB_*` 또는 `/opt/app/config/database.env`에서 읽음
- [x] `config-sample/database.py`: 있음. 샘플 DB 설정
- [x] `ops/nginx-runningmate.conf.example`: 있음. 80/443 프록시 예시
- [x] `scripts/*.sh`, `scripts/*.py`: 있음. 백업, 헬스체크, 로그 감시, secret 검증, migration 스크립트 포함
- [x] `/opt/app/run.sh`: 있음. 현재 WIZ 컨테이너형 런타임 초기화 및 `wiz service` 실행 스크립트
- [ ] `requirements.txt`: 없음
- [ ] `Dockerfile`: 없음
- [ ] `docker-compose.yml` 또는 `docker-compose.yaml`: 없음
- [ ] `pyproject.toml`, `Pipfile`, `poetry.lock`: 없음

## 4. 앱 실행 명령어

- [x] 현재 WIZ 런타임 기본 실행 흐름

```bash
cd /opt/app
pip install -U season
wiz service regist app 3000
wiz service start app
```

- [x] 실제 앱 프로세스 형태

```bash
/opt/conda/envs/app/bin/wiz run --log /var/log/wiz/app
```

- [x] 현재 재시작 helper

```bash
cd /opt/app/project/main
scripts/runningmate_restart_wiz_app.sh
```

- [x] 단발 실행 확인용

```bash
cd /opt/app
python public/app.py
```

- [ ] 라즈베리파이 systemd 배포 시에는 `ExecStart`를 WIZ 실행 명령 또는 `/usr/local/bin/wiz.app` 래퍼로 고정하고, `/opt/app/config`, `/opt/app/data`, `/var/log/wiz` 권한을 먼저 맞춰야 함

## 5. 빌드 명령어

- [x] WIZ 프로젝트 빌드/번들

```bash
cd /opt/app
wiz bundle --project=main
```

- [x] WIZ MCP 기준 빌드 도구: `wiz_project_build` (`clean=false` 기본)
- [x] Angular 단독 점검이 필요할 때

```bash
cd /opt/app/project/main/src/angular
npm install
npm run build
```

- [ ] 루트 `package.json`에는 일반 웹앱 `build` script가 없음
- [ ] 문서 변경만 수행한 이번 작업에서는 WIZ/Angular 빌드를 실행하지 않음

## 6. 사용하는 포트

- [x] 앱 내부 포트: `3000`
  - 근거: `/opt/app/config/boot.py`의 `run['port'] = 3000`, `/opt/app/run.sh`의 `wiz service regist app 3000`
- [x] 앱 바인딩 호스트: `0.0.0.0`
  - 근거: `/opt/app/config/boot.py`의 `run['host'] = "0.0.0.0"`
- [x] Nginx 공개 포트: `80`, `443`
  - 근거: `ops/nginx-runningmate.conf.example`
- [x] DB 포트: 기본 `3306`
  - 근거: `config/database.py`, `.env.example`
- [x] 헬스체크 URL: `http://127.0.0.1:3000/healthz`
  - 근거: `docs/private-server-ops-alert-rollback-2026-06-09.md`, `scripts/runningmate_healthcheck.py`
- [x] SMTP를 쓰면 보통 outbound `587`
- [ ] Redis 포트 사용 근거 없음

## 7. 필요한 외부 서비스

- [x] MySQL 또는 MariaDB: 운영 기준 필요
  - `RUNNINGMATE_DB_TYPE=mysql` 기본값, Peewee DB 모델 사용
- [x] 로컬 영속 스토리지: 필요
  - `/opt/app/data`, `/opt/app/data/run_images`, `/opt/app/data/run_media`, `/opt/app/data/backups`
- [x] OpenAI API: AI 채팅/이미지 파싱 기능에 필요
- [x] 이메일 발송: 비밀번호 재설정/운영 알림에 SendGrid 또는 SMTP 필요
- [x] OAuth: Google/Naver 소셜 로그인을 쓰면 각 provider 설정 필요
- [x] 날씨 API: 월간 날씨 기능에 기상청 API key 필요, 일부 근거리 보강은 외부 날씨 API 호출 가능
- [x] Apple Music API: 음악 기능을 쓰면 MusicKit/Apple Music 설정 필요
- [x] 백업 원격지: Google Drive/rclone은 운영 백업 복제에 권장
- [x] ClamAV: 업로드 악성 파일 스캔을 `required` 모드로 쓰면 로컬 패키지 필요
- [ ] Redis 사용 근거 없음

## 8. 환경변수 키 목록

실제 값은 문서나 저장소에 넣지 않는다. 아래는 이름만 정리한 목록이다.

### 기본/세션/도메인

- [ ] `WIZ_SECRET_KEY`
- [ ] `FLASK_SECRET_KEY`
- [ ] `SECRET_KEY`
- [ ] `SESSION_COOKIE_SECURE`
- [ ] `SESSION_COOKIE_SAMESITE`
- [ ] `RUNNINGMATE_PUBLIC_BASE_URL`
- [ ] `RUNNINGMATE_ALLOWED_ORIGINS`
- [ ] `RUNNINGMATE_ADMIN_TOKEN`

### DB

- [ ] `RUNNINGMATE_DB_ENV_FILE`
- [ ] `RUNNINGMATE_DB_TYPE`
- [ ] `RUNNINGMATE_DB_NAME`
- [ ] `RUNNINGMATE_DB_USER`
- [ ] `RUNNINGMATE_DB_PASSWORD`
- [ ] `RUNNINGMATE_DB_HOST`
- [ ] `RUNNINGMATE_DB_PORT`
- [ ] `RUNNINGMATE_DB_CHARSET`
- [ ] `RUNNINGMATE_DATABASE_CONFIG`

### 데이터/업로드/보안

- [ ] `RUNNINGMATE_DATA_DIR`
- [ ] `RUNNINGMATE_UPLOAD_DIR`
- [ ] `RUNNINGMATE_MEDIA_UPLOAD_DIR`
- [ ] `RUNNINGMATE_MAX_UPLOAD_BYTES`
- [ ] `RUNNINGMATE_MAX_MEDIA_UPLOAD_BYTES`
- [ ] `RUNNINGMATE_RUNS_STORAGE`
- [ ] `RUNNINGMATE_RUNS_JSON_MIRROR`
- [ ] `RUNNINGMATE_FILE_URL_SECRET`
- [ ] `RUNNINGMATE_JWT_SECRET`
- [ ] `RUNNINGMATE_UPLOAD_URL_TTL_SECONDS`
- [ ] `RUNNINGMATE_AUDIT_LOG_FILE`
- [ ] `RUNNINGMATE_AV_SCAN_DISABLED`
- [ ] `RUNNINGMATE_AV_SCAN_MODE`
- [ ] `RUNNINGMATE_AV_SCAN_TIMEOUT_SECONDS`
- [ ] `RUNNINGMATE_AV_SCANNER`

### OpenAI/AI

- [ ] `RUNNINGMATE_OPENAI_ENV_FILE`
- [ ] `OPENAI_API_KEY`
- [ ] `OPENAI_ADMIN_KEY`
- [ ] `OPENAI_BASE_URL`
- [ ] `RUNNINGMATE_AI_PROVIDER`
- [ ] `RUNNINGMATE_CHAT_MODEL`
- [ ] `RUNNINGMATE_VISION_MODEL`
- [ ] `RUNNINGMATE_IMAGE_DETAIL`
- [ ] `RUNNINGMATE_CODEX_TIMEOUT`
- [ ] `RUNNINGMATE_CODEX_MODEL`
- [ ] `CODEX_ACCESS_TOKEN`
- [ ] `RUNNINGMATE_MAX_CHAT_MESSAGE_CHARS`
- [ ] `RUNNINGMATE_AI_CHAT_DAILY_LIMIT`
- [ ] `RUNNINGMATE_AI_CHAT_MONTHLY_LIMIT`
- [ ] `RUNNINGMATE_AI_CHAT_ADMIN_DAILY_LIMIT`
- [ ] `RUNNINGMATE_AI_CHAT_ADMIN_MONTHLY_LIMIT`
- [ ] `RUNNINGMATE_AI_CHAT_COOLDOWN_SECONDS`
- [ ] `RUNNINGMATE_AI_CHAT_RATE_WINDOW_SECONDS`
- [ ] `RUNNINGMATE_AI_CHAT_RATE_MAX_REQUESTS`
- [ ] `RUNNINGMATE_AI_IMAGE_PARSE_COOLDOWN_SECONDS`
- [ ] `RUNNINGMATE_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS`
- [ ] `RUNNINGMATE_AI_IMAGE_PARSE_RATE_MAX_REQUESTS`
- [ ] `RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT`
- [ ] `RUNNINGMATE_OPENAI_RETRY_MAX`
- [ ] `RUNNINGMATE_OPENAI_BACKOFF_BASE_SECONDS`
- [ ] `RUNNINGMATE_OPENAI_BACKOFF_MAX_SECONDS`
- [ ] `RUNNINGMATE_OPENAI_PROJECT_ID`
- [ ] `RUNNINGMATE_OPENAI_DAILY_BUDGET_USD`
- [ ] `RUNNINGMATE_OPENAI_MONTHLY_BUDGET_USD`
- [ ] `RUNNINGMATE_OPENAI_ALERT_THRESHOLDS`

### OAuth

- [ ] `RUNNINGMATE_OAUTH_ENV_FILE`
- [ ] `RUNNINGMATE_OAUTH_REQUIRE_PUBLIC_BASE_URL`
- [ ] `RUNNINGMATE_OAUTH_STATE_TTL_SECONDS`
- [ ] `RUNNINGMATE_OAUTH_REDIRECT_URI`
- [ ] `OAUTH_REDIRECT_URI`
- [ ] `NAVER_CLIENT_ID`
- [ ] `NAVER_CLIENT_SECRET`
- [ ] `NAVER_REDIRECT_URI`
- [ ] `GOOGLE_CLIENT_ID`
- [ ] `GOOGLE_CLIENT_SECRET`
- [ ] `GOOGLE_REDIRECT_URI`

### 메일/알림

- [ ] `RUNNINGMATE_MAIL_ENV_FILE`
- [ ] `RUNNINGMATE_PASSWORD_RESET_BASE_URL`
- [ ] `RUNNINGMATE_MAIL_DOMAIN`
- [ ] `RUNNINGMATE_MAIL_FROM`
- [ ] `RUNNINGMATE_MAIL_FROM_NAME`
- [ ] `RUNNINGMATE_MAIL_LOG`
- [ ] `RUNNINGMATE_DIRECT_MX_ENABLED`
- [ ] `RUNNINGMATE_DIRECT_MX_TIMEOUT`
- [ ] `SENDGRID_API_KEY`
- [ ] `SENDGRID_FROM_EMAIL`
- [ ] `SMTP_HOST`
- [ ] `SMTP_PORT`
- [ ] `SMTP_USERNAME`
- [ ] `SMTP_PASSWORD`
- [ ] `SMTP_USER`
- [ ] `SMTP_PASS`
- [ ] `SMTP_SENDER`
- [ ] `SMTP_FROM`
- [ ] `SMTP_FROM_NAME`
- [ ] `SMTP_USE_TLS`
- [ ] `SMTP_USE_SSL`
- [ ] `RUNNINGMATE_ALERT_EMAIL_TO`
- [ ] `RUNNINGMATE_ALERT_EMAIL_FROM`
- [ ] `RUNNINGMATE_ALERT_REPEAT_SECONDS`

### 날씨/Apple Music/백업/운영

- [ ] `RUNNINGMATE_WEATHER_ENV_FILE`
- [ ] `RUNNINGMATE_WEATHER_SERVICE_KEY`
- [ ] `RUNNINGMATE_WEATHER_LOCATION`
- [ ] `RUNNINGMATE_WEATHER_LAND_REG_ID`
- [ ] `RUNNINGMATE_WEATHER_TEMP_REG_ID`
- [ ] `RUNNINGMATE_WEATHER_CACHE_DIR`
- [ ] `RUNNINGMATE_APPLE_MUSIC_ENV_FILE`
- [ ] `RUNNINGMATE_APPLE_MUSIC_TEAM_ID`
- [ ] `RUNNINGMATE_APPLE_MUSIC_KEY_ID`
- [ ] `RUNNINGMATE_APPLE_MUSIC_PRIVATE_KEY_PATH`
- [ ] `RUNNINGMATE_APPLE_MUSIC_PRIVATE_KEY`
- [ ] `RUNNINGMATE_APPLE_MUSIC_DEVELOPER_TOKEN`
- [ ] `RUNNINGMATE_APPLE_MUSIC_TOKEN_TTL_SECONDS`
- [ ] `RUNNINGMATE_BACKUP_DIR`
- [ ] `RUNNINGMATE_BACKUP_ENV_FILE`
- [ ] `RUNNINGMATE_DB_MYSQL_DEFAULTS_FILE`
- [ ] `RUNNINGMATE_BACKUP_PASSPHRASE_FILE`
- [ ] `RUNNINGMATE_BACKUP_RCLONE_CONFIG`
- [ ] `RUNNINGMATE_BACKUP_RCLONE_REMOTE`
- [ ] `RUNNINGMATE_BACKUP_REMOTE_DIR`
- [ ] `RUNNINGMATE_SERVER_CONFIG_DIR`
- [ ] `RUNNINGMATE_OPS_ENV_FILE`
- [ ] `RUNNINGMATE_OPS_STATE_DIR`
- [ ] `RUNNINGMATE_HEALTHCHECK_URL`
- [ ] `RUNNINGMATE_HEALTHCHECK_RESTART`
- [ ] `RUNNINGMATE_RESTART_COMMAND`
- [ ] `RUNNINGMATE_LOG_ALERT_PATTERN`
- [ ] `RUNNINGMATE_LOG_ALERT_MAX_LINES`
- [ ] `RUNNINGMATE_WIZ_APP`
- [ ] `RUNNINGMATE_WIZ_RESTART_LOG`
- [ ] `RUNNINGMATE_PROJECT_ROOT`
- [ ] `RUNNINGMATE_PYTHON_BIN`
- [ ] `RUNNINGMATE_WATCHDOG_HEALTH_INTERVAL_SECONDS`
- [ ] `RUNNINGMATE_WATCHDOG_LOG_INTERVAL_SECONDS`
- [ ] `RUNNINGMATE_WATCHDOG_HEALTH_LOG`
- [ ] `RUNNINGMATE_WATCHDOG_LOG_WATCH_LOG`
- [ ] `RUNNINGMATE_FIREWALL_APPLY`
- [ ] `RUNNINGMATE_SSH_ALLOW_CIDR`

### 초기 관리자 migration

- [ ] `ADMIN_INIT_EMAIL`
- [ ] `ADMIN_INIT_USERNAME`
- [ ] `ADMIN_DISPLAY_NAME`
- [ ] `ADMIN_INIT_PASSWORD`

## 9. Docker 사용 가능성

- [x] Docker 배포는 가능함
  - 앱은 WIZ/Season Python 런타임, Node/Angular build, MySQL 접속, `/opt/app/config`, `/opt/app/data` 마운트 구조로 컨테이너화할 수 있음
- [ ] 현재 프로젝트에는 `Dockerfile`과 `docker-compose.yml`이 없음
- [ ] 바로 배포 가능한 Docker 구조는 아직 아님
- [ ] Docker로 가려면 최소 구성 필요
  - ARM64 지원 base image
  - Python/WIZ/Season 설치
  - Node/npm 설치 및 Angular build
  - MySQL/MariaDB는 별도 컨테이너 또는 호스트 서비스로 분리
  - `/opt/app/config`는 secret volume
  - `/opt/app/data`는 persistent volume
  - Nginx는 별도 컨테이너 또는 호스트 Nginx
  - ClamAV, rclone, mysql client, logrotate/cron 대체 프로세스 포함 여부 결정

## 10. 라즈베리파이 ARM64 의존성 리스크

- [ ] Python 3.14.4는 ARM64에서 일부 native wheel 확보가 Python 3.12/3.13보다 불안정할 수 있음
- [ ] `season` 의존성에 native/대형 패키지가 포함됨
  - `numpy`, `pandas`, `Pillow`, `psutil`, `gevent`, `eventlet` 등
- [ ] 앱/스크립트 직접 의존성에도 native wheel 가능성이 있는 패키지가 있음
  - `bcrypt`, `pymysql`, `peewee`, `openai` 하위의 `pydantic-core`, `jiter` 등
- [ ] Angular/Node build는 ARM64에서 가능하지만 라즈베리파이 메모리 부족 위험이 있음
  - 서버에서 직접 build한다면 swap 또는 더 큰 메모리 모델 권장
  - 가능하면 x86_64/CI에서 build 후 `bundle/`을 배포하는 방식도 검토
- [ ] ClamAV는 라즈베리파이에서 동작하지만 메모리와 signature update 시간이 부담될 수 있음
- [ ] iOS/Capacitor `ios/` 폴더는 라즈베리파이 웹 배포 대상이 아니며 Xcode가 필요하므로 제외 가능
- [x] Redis 의존성은 확인되지 않음
- [x] MySQL/MariaDB, Nginx, rclone은 ARM64 패키지로 운영 가능

## 11. 서버로 옮겨야 하는 파일/폴더

### WIZ 런타임을 서버에 이미 설치하는 경우

- [x] 필수 프로젝트 파일
  - `project/main/src/`
  - `project/main/config/`
  - `project/main/config-sample/`
  - `project/main/package.json`
  - `project/main/package-lock.json`
  - `project/main/.env.example`
  - `project/main/scripts/`
  - `project/main/ops/`
  - `project/main/docs/`
  - `project/main/README.md`
- [x] 빌드 산출물을 함께 배포할 경우
  - `project/main/bundle/`
  - `project/main/build/`
- [x] 운영 런타임 secret과 데이터는 별도 준비
  - `/opt/app/config/*.env`
  - `/opt/app/config/.secret_key` 또는 `WIZ_SECRET_KEY`
  - `/opt/app/config/mysql-backup.cnf`
  - `/opt/app/config/backup-passphrase`
  - `/opt/app/config/rclone/rclone.conf`
  - `/opt/app/data/`
  - `/var/log/wiz/`
- [ ] `node_modules/`는 서버에서 `npm install`로 재생성하는 편이 안전함
- [ ] `ios/`는 웹 배포에는 필요 없음

### WIZ 런타임까지 같이 옮기는 경우

- [x] `/opt/app/public/`
- [x] `/opt/app/config/boot.py`, `/opt/app/config/service.py`, `/opt/app/config/plugin.json` 등 WIZ 런타임 설정
- [x] `/opt/app/run.sh` 또는 systemd unit
- [x] WIZ/Season이 설치된 Python 환경 또는 동일 버전을 재현할 설치 스크립트
- [x] `project/main/` 전체
- [x] persistent volume으로 `/opt/app/config`, `/opt/app/data`, `/var/log/wiz` 분리

## 배포 전 최소 검증

- [ ] 라즈베리파이에서 Python/Node/npm 버전 확인
- [ ] `pip install -U season` 또는 고정 버전 설치 성공 확인
- [ ] `npm install` 및 `wiz bundle --project=main` 성공 확인
- [ ] MySQL/MariaDB `rundb` 접속 확인
- [ ] `python scripts/verify_runtime_secrets.py` 통과 확인
- [ ] `curl -f http://127.0.0.1:3000/healthz` 통과 확인
- [ ] 로그인, 이미지 업로드, AI 채팅/이미지 파싱, 비밀번호 재설정 메일, 백업 생성 확인
