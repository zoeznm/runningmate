# iOS 앱 시작 URL 및 401 인증 정리 보강

- 날짜: 2026-06-18
- 작업 ID: 003
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"iOS 앱을 실행하면 로그인 페이지가 아니라 Safari 또는 원격 run.myrunningmate.com/dashboard로 이동하고, DB에 없는 계정으로 로그인된 것처럼 보입니다."

## 원인

- `capacitor.config.json`의 `server.url`이 `https://run.myrunningmate.com/dashboard`라 iOS 앱 첫 로드가 로그인 화면이 아니라 dashboard였다.
- PWA manifest도 일부 경로에서 dashboard 또는 `/` 시작으로 남아 있었다.
- 보호 API 401 이후 클라이언트 토큰 저장소를 즉시 비우고 `/access`로 보내는 공통 처리가 부족했다.
- 로그인 화면의 세션 복구는 refresh 성공 후 `/api/auth/me` 재확인 없이 dashboard로 이동할 수 있었다.

## 변경

- `capacitor.config.json`
  - `server.url`을 `https://run.myrunningmate.com/access`로 변경했다.
  - `allowNavigation`에 `run.myrunningmate.com`을 명시했다.
- `src/angular/app/shared/auth.ts`, `src/angular/app/shared/api.ts`
  - 보호 API 401 시 `runningmate.auth.accessToken`, `runningmate.auth.refreshToken`, `runningmate.auth.autoLogin`을 local/session storage에서 삭제하고 `/access`로 이동하도록 공통 처리했다.
- `src/app/page.access/view.ts`
  - 자동 세션 복구는 refresh 뒤 `authenticatedUser()`가 다시 성공할 때만 dashboard로 이동하도록 변경했다.
  - 소셜 시작의 `window.open(..., '_top')`을 제거하고 같은 창 `location.assign()`으로 정리했다.
- `src/app/page.dashboard/view.ts`, `src/angular/app/app.component.ts`
  - 인증 실패 리다이렉트 시 프론트 토큰을 먼저 지우도록 변경했다.
- `src/model/struct/user.py`
  - 세션의 `user_id`가 DB에 없으면 current session이 아니도록 전역 세션 검사를 보강했다.
- `src/route/api.auth.refresh/controller.py`
  - refresh token 검증 실패 시 서버 세션도 clear하도록 변경했다.
- `config/pwa/sw.js`, PWA SW route
  - 캐시 버전을 `runningmate-pwa-v53-ios-auth-startup`으로 갱신했다.
- `config/pwa/manifest.json`, `src/route/manifest/controller.py`
  - `start_url`을 `/access`로 맞췄다.

## 확인

- `/api/auth/me`, `/api/dashboard/bootstrap`은 세션 user_id가 DB에 없으면 `session.clear()` 후 401을 반환하는 코드임을 확인했다.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `python -m py_compile`로 수정 Python 파일 문법 확인 성공.
- `node --check`로 `build/dist/build/main.js`, `bundle/www/main.js`, 운영 번들 `main.js`, SW 문법 확인 성공.
- 운영 `/main.js`에 토큰 키 삭제 처리와 `/access` 리다이렉트가 포함된 것을 확인했다.
- 운영 `/sw.js`가 `runningmate-pwa-v53-ios-auth-startup`을 반환하는 것을 확인했다.
- 운영 `/manifest.json`의 `start_url`이 `/access`임을 확인했다.
- 무인증 `/api/auth/me`, `/api/dashboard/bootstrap?limit=1`이 401 payload를 반환하는 것을 확인했다.

## 남은 리스크

- `capacitor.config.json` 변경은 native 앱에 반영되어야 하므로 Mac 프로젝트에서 `npm run ios:sync` 후 Xcode 재실행이 필요하다.
- 기존 iPhone WebView에 남은 쿠키/스토리지가 있으면 앱 삭제 후 재설치가 가장 확실하다.
