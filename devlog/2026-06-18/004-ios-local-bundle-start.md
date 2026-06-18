# iOS 원격 server.url 제거 및 내부 번들 시작 전환

- 날짜: 2026-06-18
- 작업 ID: 004
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"iOS 앱이 https://run.myrunningmate.com/access 같은 원격 URL을 직접 열지 않게 바꿔주세요."

## 변경

- `capacitor.config.json`
  - `server.url`과 `allowNavigation`을 제거했다.
  - iOS 앱은 `webDir`의 `bundle/www`를 앱 내부 `capacitor://localhost`에서 로드한다.
- `src/angular/app/app-routing.module.ts`
  - 기본 라우트 `INDEX_PAGE`를 `dashboard`에서 `access`로 변경했다.
  - 앱 내부 번들 첫 화면이 `/access`가 되도록 했다.
- `src/angular/app/shared/api-base.ts`
  - `capacitor://localhost`, `ionic://localhost`, `file://`에서 `/api/...`를 `https://run.myrunningmate.com/api/...`로 보내도록 보정했다.
  - `capacitor:` URL의 `origin`이 `null`처럼 처리될 수 있어 protocol 기준으로 판별하도록 수정했다.
- `config/pwa/sw.js`, PWA SW route
  - 캐시 버전을 `runningmate-pwa-v54-ios-local-bundle-start`로 갱신했다.
- 문서
  - iOS 실행 방식을 원격 WebView가 아니라 내부 번들 + 운영 API origin 구조로 정리했다.

## 확인

- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- 실제 `api-base.ts`를 Node에서 transpile해 `capacitor://localhost/access` 환경으로 실행했고, `/api/auth/me`가 `https://run.myrunningmate.com/api/auth/me`로 변환되는 것을 확인했다.
- 번들 `main.js`에 기본 라우트 `access`, 운영 API origin, `capacitor:` fallback 문자열이 포함된 것을 확인했다.
- 보호 API 401 처리와 토큰 삭제 로직은 직전 작업의 공통 인증 모듈 변경이 그대로 번들에 포함되는 것을 확인했다.

## 남은 리스크

- `server.url` 제거는 native 설정 변경이므로 Mac 프로젝트에서 `npm run ios:sync`가 필요하다.
- 기존 앱에는 이전 Capacitor 설정과 WebView storage가 남을 수 있어 Xcode에서 앱 삭제 후 재설치를 권장한다.
