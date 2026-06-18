# iOS 실기기 초기 로딩 무한 대기 방어 및 API base 보정

- 날짜: 2026-06-18
- 작업 ID: 001
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"iOS 실기기에서 앱은 실행되는데 “초기 데이터를 불러오는 중” 화면에서 무한 로딩됩니다..."

## 변경 요약

iOS Capacitor 실기기에서 초기 대시보드 로딩이 무한 지속될 수 있는 경로를 점검하고, API base URL fallback, 초기 로딩 timeout, 최종 에러 표시, CORS 허용 origin을 보강했다.

## 변경 파일

- `src/angular/app/shared/api-base.ts`
  - `capacitor://localhost`, `ionic://localhost`, `file://` origin에서 `/api/...` 요청을 `https://run.myrunningmate.com/api/...`로 보정하는 helper를 추가했다.
- `src/angular/app/shared/api.ts`
  - `apiFetch`가 보정된 API URL과 인증 헤더를 사용하도록 변경했다.
- `src/angular/app/shared/auth.ts`
  - fetch interceptor, `/api/auth/me`, `/api/auth/refresh`가 보정된 URL을 사용하도록 변경했다.
- `src/app/page.dashboard/view.ts`
  - `loadInitialDashboardData()`에 `try/catch/finally`를 추가해 예외가 나도 로딩이 종료되고 에러/재시도 화면으로 전환되도록 했다.
  - 초기 부가 데이터 작업에 9초 timeout을 추가했다.
  - 이미지 파싱 XHR에 운영 API URL fallback과 20초 timeout을 추가했다.
- `src/controller/base.py`
  - 허용 origin 요청에 CORS 응답 헤더를 내려주도록 추가했다.
- `src/model/security.py`
  - `capacitor://localhost`, `ionic://localhost`를 허용 origin 기본값에 포함했다.
- `.env.example`
  - 운영 도메인을 `https://run.myrunningmate.com` 기준으로 갱신하고 Capacitor origin 허용 예시를 추가했다.
- `/opt/app/config/runtime.env`
  - 실제 런타임 `RUNNINGMATE_ALLOWED_ORIGINS`에 `capacitor://localhost`, `ionic://localhost`를 추가했다.
- `docs/ios-initial-loading-troubleshooting-2026-06-18.md`
  - 요청한 1~6번 확인 결과와 `npm run ios:sync` 필요 여부를 문서화했다.
- `README.md`, `devlog.md`
  - 문서 링크와 작업 요약을 추가했다.

## 확인 결과

- `초기 데이터를 불러오는 중`은 `src/app/page.dashboard/view.pug`의 `wiz-component-loading-fullscreen`에서 렌더링된다.
- 초기 부트스트랩 API는 `GET /api/dashboard/bootstrap?limit=60`이다.
- `capacitor.config.json`은 `https://run.myrunningmate.com/dashboard`, `cleartext=false`로 되어 있다.
- 로컬 nginx 강제 해석 기준 `/api/dashboard/bootstrap?limit=60`은 HTML fallback이 아니라 JSON 401을 반환했다.
- 실제 `/opt/app/config/runtime.env`의 public base URL은 운영 도메인으로 맞아 있었고, allowed origins만 Capacitor origin을 추가했다.
- 이번 변경 뒤 Mac 프로젝트 `/Users/kimbomi/Desktop/app/project/main`에서 `npm run ios:sync`가 필요하다.

## 검증

- `python -m py_compile src/controller/base.py src/model/security.py` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공.
- `curl --resolve run.myrunningmate.com:443:127.0.0.1 https://run.myrunningmate.com/api/dashboard/bootstrap?limit=60` 결과 JSON 401 확인.
- 전체 Angular 빌드는 이 서버의 generated build 경로와 맞지 않아 실패했다. Mac 또는 WIZ 배포 환경에서 `npm run ios:sync` 전 최신 번들 생성이 필요하다.
