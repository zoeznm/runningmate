# 개인 서버 비밀값 인벤토리 및 구글 드라이브 백업 secret 정리

## 사용자 요청

구글 드라이브 만들었고 비밀값 정리는 너가 해주면 안돼?

## 변경 파일

- `docs/private-server-secret-inventory-2026-06-10.md`
  - 실제 비밀값을 기록하지 않는 원칙을 명시했다.
  - DB, OpenAI, OAuth, 메일, WIZ/app, Google Drive/rclone, 백업 암호화 passphrase 항목을 비밀번호 관리자 기준으로 정리했다.
  - 개인 서버의 `/opt/app/config` 파일 배치, 권한, 템플릿, Google Drive 업로드 대상, 이전 전/후 체크리스트를 추가했다.
- `.env.example`
  - 개인 서버 기본 경로를 `/opt/app/data` 기준으로 맞췄다.
  - Google Drive/rclone 백업 관련 placeholder 변수를 추가했다.
  - 이미지 파싱 월 35회 제한 변수를 예시에 추가했다.
- `devlog.md`
  - 이번 작업 요약 행을 추가했다.

## 확인 결과

- 문서와 예시 파일에는 실제 비밀번호, API key, OAuth secret, rclone token을 넣지 않았다.
- Google Drive는 운영 DB가 아니라 암호화된 백업 산출물 보관소라는 기준을 문서화했다.
- 기존 `scripts/verify_runtime_secrets.py`, `scripts/backup-runningmate-private-server.sh`, `scripts/encrypt-runningmate-backup.sh`, `scripts/runningmate_restore_rehearsal.py` 사용 흐름과 맞춰 검증 명령을 정리했다.

## 남은 리스크

- 실제 secret 값은 사용자가 비밀번호 관리자와 개인 서버에 직접 입력해야 한다.
- 개인 서버 이전 후 회사 서버에서 사용했던 임시 key, token, DB 비밀번호는 회전해야 한다.
- Google Drive rclone token은 개인 서버에서 생성하는 것이 안전하다.
