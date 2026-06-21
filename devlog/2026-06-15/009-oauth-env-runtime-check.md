# 운영 OAuth 설정 파일 확인 및 권한 보정

- **ID**: 009
- **날짜**: 2026-06-15
- **유형**: 운영 설정
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
운영 서버의 `/opt/app/config/oauth.env` 파일이 생성되어 있음을 확인했다.
파일 안에는 운영 도메인 기준 `NAVER_REDIRECT_URI`, `GOOGLE_REDIRECT_URI`와 네이버/구글 Client ID/Secret 값이 들어 있었고, 앱의 OAuth 시작 라우트도 해당 설정을 읽어 provider 인증 URL로 리다이렉트했다.

파일 권한이 `664`라 secret 검증에 실패하던 부분은 `600`으로 보정했다.

## 변경 파일 목록
- `/opt/app/config/oauth.env`: 파일 권한을 `600`으로 조정. 값은 기록하지 않음.
- `devlog.md`, `devlog/2026-06-15/009-oauth-env-runtime-check.md`: 작업 이력 기록.

## 확인 결과
- `/api/auth/oauth/naver/start`가 네이버 인증 URL로 302 리다이렉트되는 것을 확인.
- `/api/auth/oauth/google/start`가 구글 인증 URL로 302 리다이렉트되는 것을 확인.
- `scripts/runningmate_healthcheck.py`가 `oauth_naver_redirect_ok`, `oauth_google_redirect_ok`로 통과.
- `scripts/verify_runtime_secrets.py`에서 OAuth 항목은 통과하고, 메일 설정 누락만 남는 것을 확인.
