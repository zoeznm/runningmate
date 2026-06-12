# 운영 nginx API/SW 정적 폴백 오류 진단 및 예시 보강

## 사용자 요청

- 리뷰 ID: `xyacypgnxkenansvzctubfxprpwtjhgw`
- 제목: 로그인 자동 무한 로딩
- 요청: 배포/재시작을 했는데도 여전히 로그인 오류가 나고 반영되지 않은 것 같다고 요청했다.

## 원인

- 운영 도메인 `https://run.myrunningmate.com`에서 `/api/auth/login`, `/auth/check`, `/sw.js`가 JSON/API 또는 service worker JS가 아니라 `index.html`을 반환하고 있었다.
- 이 상태에서는 프론트가 `/api/auth/login` 응답 HTML을 JSON으로 파싱하려 하므로 `응답을 읽지 못했어. 다시 시도해줘` 오류가 계속 발생한다.
- 리뷰 도메인 `https://matomabo.run.seasonai.net`은 `/api/auth/login` 실패 응답과 `/sw.js`를 정상 반환했다.

## 변경 파일

- `ops/nginx-runningmate.conf.example`
  - `/api/`, `/auth/`, `/sw.js`, `/manifest.json`, `/socket.io/`가 반드시 WIZ 앱 upstream으로 프록시되도록 예시를 보강했다.
  - API/SW가 정적 SPA root의 `index.html`로 fallback되면 로그인 parse 오류가 난다는 주석을 추가했다.

## 확인한 내용

- 운영 도메인 확인
  - `GET https://run.myrunningmate.com/sw.js`가 `index.html`을 반환했다.
  - `POST https://run.myrunningmate.com/api/auth/login`이 `content-type: text/html`의 `index.html`을 반환했다.
  - `GET https://run.myrunningmate.com/auth/check`도 `index.html`을 반환했다.
- 리뷰 도메인 확인
  - `GET https://matomabo.run.seasonai.net/sw.js` 첫 줄: `runningmate-pwa-v34-login-json-response`
  - `POST https://matomabo.run.seasonai.net/api/auth/login` 실패 응답은 JSON이었다.

## 남은 확인/배포 메모

- 현재 작업 환경에는 nginx가 설치되어 있지 않아 운영 서버의 `/etc/nginx` 파일은 직접 수정하지 못했다.
- Raspberry Pi 운영 서버에서 실제 nginx site 설정을 수정하고 `nginx -t`, `systemctl reload nginx`를 실행해야 한다.
