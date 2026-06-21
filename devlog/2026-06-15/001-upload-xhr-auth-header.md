# 기록 업로드 XHR 인증 헤더 및 세션 재확인 보강

## 요청

- 리뷰 ID: `bfishjsomkhseqylwoxffdqrqjsgyzbu`
- 로그인 후 기록 업로드 시 `로그인이 필요합니다.`가 표시되는 원인 확인 및 자동 로그인/세션 확인 흐름 보강.

## 원인

- 대시보드 초기 데이터와 일반 API 요청은 `fetch` 인터셉터가 `Authorization: Bearer ...` 헤더를 붙이고 401 시 refresh token으로 복구한다.
- 이미지 파싱 업로드(`/api/parse-image`)만 진행률 표시 때문에 `XMLHttpRequest`를 직접 사용하고 있었고, 이 경로에는 인증 헤더가 붙지 않았다.
- 앱 재진입이나 브라우저 세션 만료로 서버 세션 쿠키가 사라진 상태에서는 로컬 자동 로그인 토큰이 남아 있어도 업로드 요청이 익명 요청으로 처리되어 401 `로그인이 필요합니다.`가 노출될 수 있었다.

## 변경

- `src/app/page.dashboard/view.ts`
  - `/api/parse-image` XHR 요청 전에 `ensureAuthenticated()`로 세션을 재확인해 만료된 access token을 refresh token으로 복구하도록 했다.
  - XHR 요청에도 `authHeaderForUrl('/api/parse-image')` 결과를 직접 주입해 서버 세션 쿠키가 없어도 bearer token으로 인증되도록 했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 모바일/PWA가 수정된 `main.js`를 다시 받도록 캐시 버전을 `runningmate-pwa-v37-upload-xhr-auth`로 갱신했다.

## 확인

- `python -m py_compile src/model/auth.py src/model/struct/user.py src/route/api.auth.login/controller.py src/route/api.parse-image/controller.py src/portal/season/model/session.py src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/src/app/page.dashboard/page.dashboard.component.ts`, `bundle/www/main.js.map`에 `/api/parse-image` 인증 헤더 주입 코드 반영 확인.
- WIZ 앱 재시작 후 `curl http://127.0.0.1:3000/sw.js` 응답이 `runningmate-pwa-v37-upload-xhr-auth`를 반환하는 것 확인.

## 남은 리스크

- 실제 운영 계정의 자동 로그인 토큰/세션 쿠키 조합은 브라우저 저장소 상태에 따라 달라 수동 실기기 재진입 테스트가 필요하다.
