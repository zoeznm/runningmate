# 운영 도메인 OAuth redirect URI 예시 추가

- **ID**: 008
- **날짜**: 2026-06-15
- **유형**: 운영 설정
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
현재 서버에는 `/opt/app/config/oauth.env` 실제 파일이 없어 옛 개발서버 Client ID/Secret 값을 직접 복구할 수 없었다.
대신 운영 도메인 `run.myrunningmate.com` 기준으로 현재 코드가 사용하는 OAuth redirect URI 예시 파일을 추가했다.

## 변경 파일 목록
- `config-sample/oauth.env.example`: 운영 도메인 기준 네이버/구글 redirect URI 예시 추가.
- `docs/private-server-secret-inventory-2026-06-10.md`: 운영 도메인 예시 파일 위치 안내 추가.
- `devlog.md`, `devlog/2026-06-15/008-oauth-production-redirect-template.md`: 작업 이력 기록.

## 확인 결과
- 현재 서버와 Codex 세션 기록에서 실제 `oauth.env` 값 파일은 발견되지 않았다.
- provider 콘솔에 등록할 redirect URI와 `/opt/app/config/oauth.env`에 넣을 redirect URI는 아래 값으로 맞추면 된다.
  - Naver: `https://run.myrunningmate.com/access`
  - Google: `https://run.myrunningmate.com/api/auth/oauth/google/callback`
