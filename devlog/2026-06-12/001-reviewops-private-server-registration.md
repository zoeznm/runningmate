# 개인 서버 ReviewOps 등록 조건 및 nginx 캡처 헤더 정리

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "작업 진행해줘"
- 리뷰어 요청: "개인서버를 리뷰옵스에 등록할 수 있나?"

## 작업 요약

개인 서버를 ReviewOps에 등록할 때 필요한 공개 URL, API 프록시, 서비스 워커, iframe 캡처 헤더, 테스트 계정 조건을 문서화했다.
운영 nginx 예시에 ReviewOps iframe 캡처가 필요한 경우의 `X-Frame-Options`/`Content-Security-Policy frame-ancestors` 처리 메모를 추가했다.

## 변경 파일

- `docs/reviewops-private-server-registration-2026-06-12.md`
  - 개인 서버 ReviewOps 등록 가능 여부, 필수 조건, 현재 점검 결과, 사전 점검 명령, 등록 입력값을 정리했다.
- `ops/nginx-runningmate.conf.example`
  - ReviewOps iframe 캡처가 필요한 경우 `X-Frame-Options`를 임시 제외하고 정확한 `frame-ancestors` CSP를 쓰라는 주석을 추가했다.
- `devlog.md`
  - 2026-06-12 ID 001 작업 요약 행을 추가했다.
- `devlog/2026-06-12/001-reviewops-private-server-registration.md`
  - 작업 상세 devlog를 추가했다.

## 확인한 내용

- WIZ 워크스페이스 현재 프로젝트가 `main`임을 확인했다.
- `.github/copilot-instructions.md`와 `.github/custom/custom-instructions.md`는 현재 루트에서 발견되지 않았다.
- 기존 `docs/raspberry-pi-deployment-checklist-2026-06-11.md`, `docs/private-server-p2-security-plan-2026-06-10.md`, `docs/private-server-ops-alert-rollback-2026-06-09.md`, `ops/nginx-runningmate.conf.example`을 확인했다.
- `https://run.myrunningmate.com/dashboard`는 200 HTML을 반환했다.
- `https://run.myrunningmate.com/sw.js`는 JavaScript로 반환됐지만 캐시 버전은 `runningmate-pwa-v32`였다.
- `POST https://run.myrunningmate.com/api/auth/login`은 `application/json`이 아니라 `text/html`의 `index.html`을 반환했다.
- `https://run.myrunningmate.com/healthz`도 헬스체크 JSON이 아니라 `text/html`의 `index.html`을 반환했다.
- `https://matomabo.run.seasonai.net/sw.js`는 `runningmate-pwa-v34-login-json-response` JavaScript를 반환했다.
- `POST https://matomabo.run.seasonai.net/api/auth/login`은 인증 실패를 JSON으로 반환했다.

## 검증 결과

- 문서와 nginx 예시 주석 변경만 수행했으므로 WIZ/Angular 빌드는 실행하지 않았다.
- 개인 서버는 대시보드 URL 등록 자체는 가능하지만, 현재 API와 헬스체크 fallback 상태를 고치기 전에는 ReviewOps에서 로그인/API 재현 및 상태 확인이 실패할 수 있음을 확인했다.
