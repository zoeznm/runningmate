# 네이버/구글 OAuth 회원가입 연동

- **ID**: 039
- **날짜**: 2026-06-08
- **유형**: 기능 추가

## 작업 요약
회원가입 선택 화면의 네이버/구글 버튼을 OAuth 시작 라우트로 연결하고, 콜백에서 소셜 계정을 기존 사용자에 연결하거나 새 사용자로 생성하도록 구현했다.
OAuth 설정값은 프로젝트 소스가 아닌 `/opt/app/config/oauth.env`에 저장하고 파일 권한을 `600`으로 제한했다.

## 원문 요청사항
```text
네이버와 구글 OAuth Client ID/Secret을 전달했으니 연결해줘.
```

## 변경 파일 목록
- `src/app/page.access/view.pug`: 네이버/구글 회원가입 버튼에 OAuth 시작 이벤트 연결.
- `src/app/page.access/view.ts`: 네이버/구글 OAuth 시작 URL 이동 메서드 추가.
- `src/model/oauth.py`: OAuth 설정 로딩, 상태 검증, 토큰 교환, 프로필 조회, 로그인 세션 설정 구현.
- `src/model/db/social_account.py`: 소셜 계정 연결 테이블 모델 추가.
- `src/model/struct.py`: `social_account` 테이블 자동 생성 대상 추가.
- `src/model/struct/user.py`: 소셜 계정 조회/연결 및 소셜 사용자 생성 로직 추가.
- `src/route/api.auth.oauth.naver.start/app.json`, `src/route/api.auth.oauth.naver.start/controller.py`: 네이버 OAuth 시작 라우트 추가.
- `src/route/api.auth.oauth.naver.callback/app.json`, `src/route/api.auth.oauth.naver.callback/controller.py`: 네이버 OAuth 콜백 라우트 추가.
- `src/route/api.auth.oauth.google.start/app.json`, `src/route/api.auth.oauth.google.start/controller.py`: 구글 OAuth 시작 라우트 추가.
- `src/route/api.auth.oauth.google.callback/app.json`, `src/route/api.auth.oauth.google.callback/controller.py`: 구글 OAuth 콜백 라우트 추가.
- `/opt/app/config/oauth.env`: OAuth 환경 설정 파일 추가. 값은 devlog에 기록하지 않음.
- `devlog.md`, `devlog/2026-06-08/039-social-oauth-signup.md`: 작업 이력 기록.

## 확인 결과
- `python -m py_compile`로 신규/변경 Python 파일 문법 확인 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- 로컬 서버 재시작 후 `/api/auth/oauth/naver/start`가 네이버 인증 URL로 302 리다이렉트되는 것 확인.
- 로컬 서버 재시작 후 `/api/auth/oauth/google/start`가 구글 인증 URL로 302 리다이렉트되는 것 확인.
- `/access` 로컬 응답 200 확인.

