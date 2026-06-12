# 모바일 자동 로그인 확인 무한 로딩 방어

## 사용자 요청

- 리뷰 ID: `xyacypgnxkenansvzctubfxprpwtjhgw`
- 제목: 로그인 자동 무한 로딩
- 요청: 모바일 브라우저에서 `/access` 접속 시 `자동 로그인 확인 중` 화면에서 계속 로딩되는 원인을 찾아 수정하고, 캐시를 지우지 않아도 새 버전이 적용되도록 service worker/cache 버전 처리를 확인해달라고 요청했다.

## 변경 파일

- `src/app/page.access/view.ts`
  - `/access` 인증 부트스트랩에 10초 타임아웃을 추가했다.
  - 저장된 세션 확인/refresh token 복구가 실패하거나 지연되면 `isSessionChecking`을 해제하고 로그인 화면으로 내려오도록 했다.
  - 로그인 직후 세션 확인도 같은 타임아웃을 적용해 버튼 로딩이 고착되지 않게 했다.
- `src/angular/app/shared/auth.ts`
  - `/api/auth/me`, `/api/auth/refresh` 요청에 10초 타임아웃과 `credentials: same-origin`을 명시했다.
  - `/api/auth/me`에는 저장된 access token을 `Authorization: Bearer`로 직접 붙여 cookie 제한 환경에서도 세션 동기화가 되도록 했다.
- `src/portal/season/libs/util/request.ts`
  - WIZ 공통 `Request.post()`에 기본 10초 Ajax 타임아웃을 추가했다.
- `src/portal/season/libs/src/auth.ts`
  - `/auth/check` 응답 파싱을 방어적으로 바꾸고, 실패/timeout에도 `loading`을 반드시 해제하도록 했다.
- `src/angular/index.pug`
  - service worker refresh 키를 `rm-auth-bootstrap-20260611`로 갱신했다.
  - `sessionStorage` 접근 실패에도 갱신 스크립트가 중단되지 않도록 예외 처리했다.
  - `updateViaCache: "none"`으로 service worker 스크립트 갱신 캐시 우회를 명시했다.
- `config/pwa/sw.js`
  - 캐시 버전을 `runningmate-pwa-v33-auth-bootstrap`로 올렸다.
  - `/access`를 app shell 캐시에 포함했다.

## 확인한 내용

- `wiz_project_build(projectName="main", clean=false)` 성공
  - `EsBuild complete`
  - `Project 'main' build completed`
- 코드 확인
  - `/access`의 `auth_bootstrap_timeout`, `resumeAuthenticatedSession` 적용 확인
  - `AUTH_REQUEST_TIMEOUT_MS = 10000` 적용 확인
  - service worker 캐시 버전 `runningmate-pwa-v33-auth-bootstrap` 확인
- 로컬 HTTPS curl 확인 시도
  - `curl --resolve run.myrunningmate.com:443:127.0.0.1 https://run.myrunningmate.com/access`
  - 현재 작업 환경에서는 `127.0.0.1:443` 연결 자체가 열려 있지 않아 연결 실패했다.

## 남은 확인/배포 메모

- 실제 Raspberry Pi 배포 서버에서 빌드 후 `runningmate.service`를 재시작해야 한다.
- 재시작 후 아래를 확인한다.
  - `/access` 200 응답
  - `/sw.js` 응답 첫 줄의 `runningmate-pwa-v33-auth-bootstrap`
  - 모바일 브라우저에서 캐시 삭제 없이 1회 자동 reload 후 로그인 화면 또는 대시보드로 진행되는지
