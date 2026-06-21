# 네이버/구글 소셜 회원가입 버튼 숨김 처리

- **ID**: 013
- **날짜**: 2026-06-17
- **유형**: UX
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
네이버/구글 회원가입 로그인을 나중에 다시 활성화하기 위해 로그인/회원가입 화면에서 소셜 버튼을 숨겼다.
이메일 회원가입만 회원가입 선택 화면의 기본 CTA로 남기고, 소셜 시작 함수는 플래그가 꺼져 있으면 동작하지 않도록 막았다.
숨긴 기능이 운영 헬스체크 실패 원인이 되지 않도록 OAuth provider 점검도 기본값에서 제외했다.

## 변경 파일 목록
- `src/app/page.access/view.pug`: 네이버/구글 소셜 버튼을 `socialLoginEnabled` 조건부 렌더링으로 전환하고 이메일 회원가입 버튼을 기본 CTA로 변경.
- `src/app/page.access/view.ts`: `socialLoginEnabled=false` 플래그 추가, 회원가입 안내 문구 수정, 소셜 시작 함수 가드 추가.
- `scripts/runningmate_healthcheck.py`: OAuth provider 헬스체크 기본값을 비활성화.
- `devlog.md`, `devlog/2026-06-17/013-hide-social-auth-buttons.md`: 작업 이력 기록.

## 확인 결과
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `https://run.myrunningmate.com/main.js`에 `socialLoginEnabled=!1`이 반영된 것을 확인.
- 기본 헬스체크가 OAuth provider 점검 없이 통과하는 것을 확인.
