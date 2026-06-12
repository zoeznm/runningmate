# 소셜 OAuth 리디렉션 URI를 access 콜백으로 통일

- **ID**: 002
- **날짜**: 2026-06-09
- **유형**: 오류 수정

## 작업 요약
Google `redirect_uri_mismatch`와 Naver 서비스 설정 오류를 줄이기 위해 OAuth 시작 요청의 `redirect_uri`를 공통 로그인 페이지인 `/access`로 통일했다.
Provider가 `/access?code=...&state=...`로 돌아오면 프론트가 공통 백엔드 콜백 라우트로 넘기고, 백엔드는 세션에 저장된 provider 정보로 기존 가입/로그인 처리를 이어가도록 수정했다.

## 원문 요청사항
```text
구글에서는 400 오류: redirect_uri_mismatch 페이지로 이동하고,
네이버는 RunMate 서비스 설정 오류 메시지가 보이는 페이지로 이동해.
```

## 변경 파일 목록
- `src/model/oauth.py`: 기본 OAuth redirect URI를 `/access`로 변경하고, provider 인자가 없는 공통 콜백에서도 세션의 provider를 사용하도록 수정.
- `src/app/page.access/view.ts`: `/access`로 돌아온 OAuth `code/state/error`를 `/api/auth/oauth/callback`으로 전달하는 로직 추가.
- `src/route/api.auth.oauth.callback/app.json`, `src/route/api.auth.oauth.callback/controller.py`: 공통 OAuth 콜백 라우트 추가.
- `devlog.md`, `devlog/2026-06-09/002-social-oauth-access-redirect.md`: 작업 이력 기록.

## 확인 결과
- `python -m py_compile src/model/oauth.py src/model/struct/user.py src/route/api.auth.oauth.callback/controller.py` 성공.
- `git diff --check` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- WIZ 앱 재시작 후 네이버/구글 OAuth 시작 URL의 `redirect_uri`가 `https://matomabo.run.seasonai.net/access`로 전송되는 것 확인.
- 공통 콜백 라우트 `/api/auth/oauth/callback` 응답 및 `/access` 응답 확인.

