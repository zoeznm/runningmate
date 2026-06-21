# 소셜 OAuth 운영 설정 누락 진단 및 헬스체크 보강

- **ID**: 007
- **날짜**: 2026-06-15
- **유형**: 오류 진단
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
네이버/구글 회원가입 시작 라우트가 provider 인증 URL이 아니라 `/access?social_error=social_config_missing`로 리다이렉트되는 것을 확인했다.
운영 서버의 `/opt/app/config/oauth.env` 파일이 없고 실행 중인 WIZ 프로세스 환경에도 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`가 없어 OAuth 설정 누락이 직접 원인이다.

동일 장애를 `/healthz`만으로는 감지하지 못해 운영 헬스체크에 OAuth start redirect 검사를 추가했다.

## 변경 파일 목록
- `scripts/runningmate_healthcheck.py`: 네이버/구글 OAuth 시작 라우트가 provider 인증 URL로 302 리다이렉트되는지 확인하고, `social_config_missing` 리다이렉트를 실패로 판정.
- `docs/private-server-secret-inventory-2026-06-10.md`: 현재 코드 라우트에 맞는 OAuth redirect URI 예시로 수정.
- `devlog.md`, `devlog/2026-06-15/007-social-oauth-runtime-config-diagnosis.md`: 작업 이력 기록.

## 확인 결과
- `curl --resolve run.myrunningmate.com:443:127.0.0.1 https://run.myrunningmate.com/api/auth/oauth/naver/start` 결과가 `/access?social_error=social_config_missing` 302임을 확인.
- `curl --resolve run.myrunningmate.com:443:127.0.0.1 https://run.myrunningmate.com/api/auth/oauth/google/start` 결과가 `/access?social_error=social_config_missing` 302임을 확인.
- `python scripts/verify_runtime_secrets.py`가 OAuth 필수 환경변수 누락을 보고함.
