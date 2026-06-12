# 소셜 회원가입 iframe 이동 및 오류 진단 보강

- **ID**: 048
- **날짜**: 2026-06-08
- **유형**: 오류 대응

## 작업 요약
ReviewOps 같은 iframe 환경에서 소셜 OAuth 화면이 iframe 내부로 열리며 provider에서 차단될 가능성을 줄이기 위해 네이버/구글 시작 버튼을 최상위 창으로 이동하도록 수정했다.
콜백 실패 시 로그인 화면에 오류 메시지를 표시하고, 서버 로그에는 provider 응답 단계별 실패 원인이 남도록 보강했다.

## 원문 요청사항
```text
네이버, 구글 둘 다 에러가 뜨면서 회원가입이 안된다고 해 구글은 403에러 뜨고 그러네
```

## 변경 파일 목록
- `src/app/page.access/view.ts`: 소셜 회원가입 버튼을 `_top` 대상 이동으로 변경하고, `social_error` 쿼리 메시지 표시/정리 로직 추가.
- `src/model/oauth.py`: provider 거부, state 실패, token/profile 조회 실패를 로그와 구체적인 오류 코드로 분리.
- `devlog.md`, `devlog/2026-06-08/048-social-oauth-error-diagnostics.md`: 작업 이력 기록.

## 확인 결과
- `python -m py_compile src/model/oauth.py src/model/struct/user.py` 성공.
- `git diff --check` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- WIZ 앱 재시작 후 `/api/auth/oauth/naver/start`가 네이버 인증 URL로 302 리다이렉트되는 것 확인.
- WIZ 앱 재시작 후 `/api/auth/oauth/google/start`가 구글 인증 URL로 302 리다이렉트되는 것 확인.
- `/access` 로컬 응답 200 확인.

