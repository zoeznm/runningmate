# 네이버 OAuth 리다이렉트 오류 및 구글 URI 분리 수정

- **ID**: 006
- **날짜**: 2026-06-09
- **유형**: 오류 수정

## 작업 요약
네이버 OAuth 가입 후 사용자는 생성되지만 내부 오류 화면이 노출되던 문제를 수정했다.
WIZ의 정상 리다이렉트 예외를 일반 실패로 다시 잡지 않도록 처리하고, OAuth 로그 함수가 WIZ logger와 충돌하지 않도록 수정했다.
구글은 네이버와 별도로 provider별 콜백 URI를 사용하도록 환경 설정을 추가했다.

## 원문 요청사항
```text
네이버 같은 경우에는 회원가입이 되는데 internal error 같은게 뜨다가 뒤로가기를 눌러서 돌아오면 회원가입 되었다고 하면서 전체 동의가 뜨고 온보딩이 시작해. 구글 회원가입은 여전히 400 오류: redirect_uri_mismatch 이렇게 떠.
```

## 변경 파일 목록
- `src/model/oauth.py`: WIZ redirect 예외를 정상 흐름으로 다시 전달하고, OAuth 로그 출력에서 `flush` 인자를 제거.
- `/opt/app/config/oauth.env`: 구글 전용 redirect URI를 provider별 콜백 경로로 명시.
- `devlog.md`, `devlog/2026-06-09/006-social-oauth-redirect-fixes.md`: 작업 이력 기록.

## 확인 결과
- `python -m py_compile src/model/oauth.py src/model/struct/user.py src/route/api.auth.oauth.callback/controller.py src/route/api.auth.oauth.google.callback/controller.py src/route/api.auth.oauth.naver.callback/controller.py` 성공.
- `git diff --check` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- WIZ 앱 재시작 후 네이버 OAuth 시작 URL은 `https://matomabo.run.seasonai.net/access`를 redirect URI로 전송 확인.
- WIZ 앱 재시작 후 구글 OAuth 시작 URL은 `https://matomabo.run.seasonai.net/api/auth/oauth/google/callback`을 redirect URI로 전송 확인.
- provider 거부 콜백 경로에서 `/access?social_error=access_denied`로 정상 리다이렉트 확인.

