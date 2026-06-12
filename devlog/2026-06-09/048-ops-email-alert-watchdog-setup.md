# 048. 운영 이메일 알림 실제 설정 및 watchdog 실행

- 날짜: 2026-06-09
- 요청: "그러면 이메일 알림 실제 설정 해줘"

## 변경 파일

- `/opt/app/config/ops.env`
- `scripts/runningmate_log_watch.py`
- `scripts/runningmate_ops_watchdog.sh`
- `docs/private-server-ops-alert-rollback-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/048-ops-email-alert-watchdog-setup.md`

## 변경 내용

- 기존 `/opt/app/config/mail.env`의 SendGrid 설정을 활용하도록 운영 알림 설정 파일 `/opt/app/config/ops.env`를 추가했다.
- 알림 수신/발신 주소를 운영 이메일로 설정했다.
- 헬스체크 URL, 실패 시 재시작 명령, 로그 감시 패턴을 설정했다.
- cron이 없는 현재 컨테이너에서도 주기 감시가 돌도록 `runningmate_ops_watchdog.sh`를 추가했다.
- 기존 로그에서 과거 오류가 한꺼번에 발송되지 않도록 `runningmate_log_watch.py --initialize` 옵션을 추가했다.
- watchdog 실행 절차를 운영 문서에 반영했다.

## 확인 결과

- `/opt/app/config/ops.env` 권한 `600` 확인.
- SendGrid 기반 테스트 이메일 발송 성공.
- `runningmate_log_watch.py` Python 문법 검증 통과.
- `runningmate_ops_watchdog.sh` shell 문법 검증 통과.
- 기존 `/var/log/wiz/app` 끝 위치로 로그 감시 상태 초기화 완료.
- watchdog 프로세스 실행 확인.
- watchdog에서 `/healthz` HTTP 200 헬스체크와 로그 감시 실행 확인.
