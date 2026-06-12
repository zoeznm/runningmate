# 개인 서버 로그/알림/장애 대응/롤백 절차

작성일: 2026-06-09

## 배포 방식이란

배포 방식은 새 버전의 앱을 서버에 반영하는 방법이다. 방식에 따라 롤백도 달라진다.

| 방식 | 의미 | 롤백 기준 |
| --- | --- | --- |
| Git 배포 | 서버에서 `git pull` 후 build/restart | 이전 commit/tag로 되돌림 |
| 압축 파일 배포 | 빌드 산출물이나 프로젝트 폴더를 tar/zip으로 교체 | 이전 압축본 재압축 해제 |
| Docker 배포 | 새 image tag로 container 교체 | 이전 image tag로 재기동 |
| 수동 WIZ 배포 | 현재 서버에서 파일 수정 후 WIZ build/restart | 수정 전 snapshot 또는 git 상태로 복구 |

현재 작업 환경은 수동 WIZ 배포에 가깝다. 개인 서버로 옮길 때는 Git 배포 또는 Docker 배포 중 하나로 고정하는 것이 좋다.

## 1. 이메일 알림 설정

알림 설정은 코드에 넣지 말고 `/opt/app/config/ops.env` 또는 기존 `/opt/app/config/mail.env`에 둔다.

SMTP 예시:

```env
RUNNINGMATE_ALERT_EMAIL_TO=owner@example.com
RUNNINGMATE_ALERT_EMAIL_FROM=alert@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=alert@example.com
SMTP_PASSWORD=<smtp-password>
SMTP_USE_TLS=true
RUNNINGMATE_ALERT_REPEAT_SECONDS=3600
```

SendGrid 예시:

```env
RUNNINGMATE_ALERT_EMAIL_TO=owner@example.com
RUNNINGMATE_MAIL_FROM=alert@example.com
SENDGRID_API_KEY=<sendgrid-api-key>
RUNNINGMATE_ALERT_REPEAT_SECONDS=3600
```

권한:

```bash
chmod 600 /opt/app/config/ops.env
```

## 2. 헬스체크와 자동 재시작

스크립트:

- `scripts/runningmate_healthcheck.py`

기본 확인 URL은 `http://127.0.0.1:3000/healthz`다.

현재 컨테이너형 WIZ 실행 방식의 재시작 명령 예:

```env
RUNNINGMATE_HEALTHCHECK_URL=http://127.0.0.1:3000/healthz
RUNNINGMATE_HEALTHCHECK_RESTART=1
RUNNINGMATE_RESTART_COMMAND=/opt/app/project/main/scripts/runningmate_restart_wiz_app.sh
```

크론 예:

```cron
* * * * * cd /opt/app/project/main && /opt/conda/envs/app/bin/python scripts/runningmate_healthcheck.py >> /var/log/wiz/healthcheck.log 2>&1
```

cron이 없는 컨테이너 환경에서는 watchdog 루프를 사용할 수 있다.

```bash
cd /opt/app/project/main
/opt/conda/envs/app/bin/python scripts/runningmate_log_watch.py --initialize
setsid scripts/runningmate_ops_watchdog.sh >/var/log/wiz/ops-watchdog.log 2>&1 < /dev/null &
```

개인 서버에서 systemd 서비스를 쓰면 `RUNNINGMATE_RESTART_COMMAND`는 다음처럼 바뀐다.

```env
RUNNINGMATE_RESTART_COMMAND=systemctl restart runningmate
```

## 3. 에러 로그 감시

스크립트:

- `scripts/runningmate_log_watch.py`
- `scripts/runningmate_ops_watchdog.sh`

기본 로그 파일은 `/var/log/wiz/app`이고, `ERROR`, `Traceback`, `OperationalError`, `Internal Server Error`, `Access denied`, `RuntimeError`를 감시한다.

크론 예:

```cron
*/5 * * * * cd /opt/app/project/main && /opt/conda/envs/app/bin/python scripts/runningmate_log_watch.py >> /var/log/wiz/log-watch.log 2>&1
```

패턴을 바꾸려면:

```env
RUNNINGMATE_LOG_ALERT_PATTERN=(ERROR|Traceback|OperationalError|Internal Server Error|Access denied|RuntimeError)
RUNNINGMATE_LOG_ALERT_MAX_LINES=80
```

## 4. 로그 보존

개인 서버에서는 로그가 디스크를 채우지 않게 회전시켜야 한다.

logrotate 예:

```text
/var/log/wiz/app /var/log/wiz/healthcheck.log /var/log/wiz/log-watch.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
    create 0640 root root
}
```

## 5. 배포 전후 절차

배포 전:

1. 현재 버전 commit/tag 또는 snapshot을 남긴다.
2. `/healthz`가 200인지 확인한다.
3. DB 백업과 미디어 백업이 가능한 상태인지 확인한다.

배포:

1. 새 코드를 반영한다.
2. WIZ build 또는 Docker image build를 실행한다.
3. 앱을 재시작한다.

배포 후:

1. `/healthz` 200 확인.
2. `/dashboard` 200 확인.
3. DB 조회 API 1개 확인.
4. 이미지/미디어 API 1개 확인.
5. 에러 로그 증가 여부 확인.

실패 시:

1. 새 버전을 즉시 중지한다.
2. 이전 commit/tag, 이전 압축본, 이전 Docker image 중 하나로 되돌린다.
3. 앱 재시작 후 `/healthz`와 핵심 API를 다시 확인한다.
4. 실패 원인 로그를 보존한다.

## 6. 운영자가 정해야 할 것

- 최종 배포 방식: Git, Docker, 압축 파일, 수동 WIZ 중 하나.
- 알림 수신 이메일 주소.
- SMTP 또는 SendGrid 중 사용할 메일 발송 방식.
- 앱을 systemd 서비스로 띄울지, Docker 컨테이너로 띄울지.

추천은 개인 서버에서는 Docker 배포다. 이미지 tag로 버전을 고정할 수 있어서 롤백이 가장 단순하다.
