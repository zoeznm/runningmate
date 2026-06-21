# 앱 메일 발신 도메인 등록 가이드 추가

- **ID**: 010
- **날짜**: 2026-06-15
- **유형**: 운영 문서
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
러닝메이트 비밀번호 재설정/운영 알림 메일을 위해 앱 전용 발신 주소를 등록하는 절차를 정리했다.
현재 코드가 지원하는 SendGrid API 키 방식과 SMTP 대안을 모두 문서화하고, 운영 도메인 `myrunningmate.com` 기준 예시를 추가했다.

## 변경 파일 목록
- `config-sample/mail.env.example`: SendGrid 권장 설정과 SMTP 대안 예시 추가.
- `docs/mail-sender-setup-2026-06-15.md`: 도메인 인증, DNS, API Key, `mail.env` 등록 절차 추가.
- `docs/private-server-secret-inventory-2026-06-10.md`: `mail.env` 예시를 운영 도메인 기준으로 보강.
- `devlog.md`, `devlog/2026-06-15/010-mail-sender-domain-setup.md`: 작업 이력 기록.

## 확인 결과
- 비밀번호 재설정 API는 `SENDGRID_API_KEY`가 있으면 SendGrid를 먼저 사용하고, 없으면 SMTP 설정을 사용한다.
- secret 검증 스크립트는 `RUNNINGMATE_MAIL_FROM`과 `SENDGRID_API_KEY` 또는 `SMTP_HOST`+`SMTP_USERNAME`+`SMTP_PASSWORD` 중 하나를 요구한다.
