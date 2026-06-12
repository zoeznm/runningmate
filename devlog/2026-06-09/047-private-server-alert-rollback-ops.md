# 047. 개인 서버 로그/이메일 알림/장애 대응/롤백 절차 추가

- 날짜: 2026-06-09
- 요청: "그러면 개인 서버용 로그/알림/장애 대응/롤백 절차를 순서대로 진행해주고 알림 받을 채널은 이메일로 해주면 좋겠어. 개인 서버 배포 방식이라는게 정확히 뭐를 말하는거야?"

## 변경 파일

- `scripts/runningmate_ops_common.py`
- `scripts/runningmate_healthcheck.py`
- `scripts/runningmate_log_watch.py`
- `scripts/runningmate_restart_wiz_app.sh`
- `docs/private-server-ops-alert-rollback-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/047-private-server-alert-rollback-ops.md`

## 변경 내용

- SMTP 또는 SendGrid 기반 이메일 알림 공통 모듈을 추가했다.
- `/healthz` 헬스체크 스크립트를 추가했다.
- 헬스체크 실패 시 선택적으로 앱 재시작 명령을 실행하고, 실패/복구 상태를 이메일로 알릴 수 있게 했다.
- `/var/log/wiz/app` 신규 로그 라인에서 `ERROR`, `Traceback`, `OperationalError`, `Internal Server Error` 등 운영 장애 패턴을 감시하는 스크립트를 추가했다.
- 현재 WIZ 컨테이너 실행 방식에 맞는 앱 재시작 스크립트를 추가했다.
- 개인 서버 기준 이메일 설정, cron 예시, logrotate 예시, 배포 전후 점검, 롤백 기준을 문서화했다.
- 배포 방식이 Git, 압축 파일, Docker, 수동 WIZ 중 무엇을 의미하는지 정리했다.

## 확인 결과

- `runningmate_ops_common.py`, `runningmate_healthcheck.py`, `runningmate_log_watch.py` Python 문법 검증 통과.
- `runningmate_restart_wiz_app.sh` shell 문법 검증 통과.
- 헬스체크 정상 경로에서 `/healthz` HTTP 200 확인.
- 정상 로그 파일 감시에서 매칭 오류 없음 확인.
- 샘플 `ERROR` 로그에서 이메일 알림 dry-run 동작 확인.
- 실패 헬스체크 URL에서 이메일 알림 dry-run 동작 확인.
