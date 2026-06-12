# ReviewOps 개인 서버 등록 체크리스트

작성일: 2026-06-12
대상: 러닝메이트 개인 서버 등록 검토

## 결론

개인 서버도 ReviewOps에 등록할 수 있다. 다만 등록 URL이 공개 HTTPS로 접근 가능해야 하고, ReviewOps가 화면을 iframe으로 캡처하는 방식이라면 서버의 frame 정책을 ReviewOps origin에 맞춰야 한다.

현재 확인한 개인 서버 `https://run.myrunningmate.com/dashboard`는 대시보드 HTML을 200으로 반환한다. 하지만 `POST /api/auth/login`이 JSON API 응답이 아니라 `index.html`을 반환하고 있어, 이 상태로 등록하면 로그인/인증/API 재현이 실패할 가능성이 높다.

## 등록 전 필수 조건

1. 등록 URL
   - 권장 URL: `https://run.myrunningmate.com/dashboard`
   - HTTPS 인증서가 유효해야 한다.
   - 외부 네트워크에서 200 응답을 받아야 한다.

2. API와 PWA 프록시
   - `/api/`, `/auth/`, `/socket.io/`, `/healthz`, `/sw.js`, `/manifest.json`은 정적 SPA fallback이 아니라 WIZ 앱 upstream으로 가야 한다.
   - 특히 `/api/auth/login`은 실패하더라도 `application/json`으로 응답해야 한다.
   - `/healthz`는 `{"success": true, "status": "ok", ...}` 형태의 JSON이어야 한다.

3. ReviewOps 캡처 허용
   - 일반 운영 기본값은 `X-Frame-Options: SAMEORIGIN`을 유지한다.
   - ReviewOps가 iframe 캡처를 요구하면 해당 검토 기간에만 `X-Frame-Options`를 빼고 CSP `frame-ancestors`로 ReviewOps origin을 정확히 허용한다.
   - 예시:

```nginx
add_header Content-Security-Policy "frame-ancestors 'self' https://<reviewops-origin>" always;
```

4. 테스트 계정
   - 관리자 계정이나 운영 secret을 ReviewOps 요청 본문에 넣지 않는다.
   - 필요한 경우 권한이 제한된 일반 테스트 계정을 만든다.

5. 서비스 워커
   - `/sw.js`가 `text/javascript` 또는 `application/javascript`로 반환되어야 한다.
   - 배포 직후에는 캐시 버전이 현재 빌드와 맞는지 확인한다.

## 현재 확인 결과

| 대상 | 결과 | 메모 |
| --- | --- | --- |
| `https://run.myrunningmate.com/dashboard` | 200 HTML | 개인 서버 대시보드 진입 자체는 가능 |
| `https://run.myrunningmate.com/sw.js` | 200 JavaScript | 개인 서버는 `runningmate-pwa-v32` 응답 |
| `POST https://run.myrunningmate.com/api/auth/login` | 200 HTML | API가 `index.html`로 fallback되어 등록 전 수정 필요 |
| `https://run.myrunningmate.com/healthz` | 200 HTML | 헬스체크도 `index.html`로 fallback되어 등록 전 수정 필요 |
| `https://matomabo.run.seasonai.net/dashboard` | 200 HTML | ReviewOps 요청 링크 기준 정상 |
| `https://matomabo.run.seasonai.net/sw.js` | 200 JavaScript | `runningmate-pwa-v34-login-json-response` 응답 |
| `POST https://matomabo.run.seasonai.net/api/auth/login` | 200 JSON | 실패 응답도 JSON으로 정상 반환 |

## 사전 점검 명령

```bash
curl -I -L https://run.myrunningmate.com/dashboard
curl -sS -D - https://run.myrunningmate.com/sw.js -o /tmp/runningmate-sw.js
curl -sS -D - -X POST https://run.myrunningmate.com/api/auth/login \
  -H 'Content-Type: application/json' \
  --data '{"identifier":"invalid","password":"invalid"}'
curl -I -L https://run.myrunningmate.com/healthz
```

통과 기준:

- `/dashboard`는 200 HTML.
- `/sw.js`는 JavaScript MIME과 서비스 워커 본문.
- `/api/auth/login`은 인증 실패라도 JSON MIME과 JSON 본문.
- `/healthz`는 200 JSON과 `status: "ok"` 본문.
- iframe 캡처가 필요하면 응답 헤더에 `X-Frame-Options`가 없어야 하고, CSP `frame-ancestors`에 ReviewOps origin이 포함되어야 한다.

## ReviewOps 등록 시 입력할 정보

| 항목 | 권장값 |
| --- | --- |
| 서비스 이름 | 러닝메이트 개인서버 |
| 대상 URL | `https://run.myrunningmate.com/dashboard` |
| 헬스체크 URL | `https://run.myrunningmate.com/healthz` |
| 화면 크기 | `1440x900` |
| 로그인 방식 | 제한 권한 테스트 계정 사용 |
| 운영 메모 | 개인 서버이므로 API/SW 프록시와 iframe 허용 헤더를 먼저 확인 |

## 남은 작업

1. 개인 서버의 실제 nginx site 설정에 `ops/nginx-runningmate.conf.example`의 API/SW 프록시 규칙을 반영한다.
2. `nginx -t` 후 reload한다.
3. 위 사전 점검 명령으로 `/api/auth/login` JSON 응답을 확인한다.
4. ReviewOps가 iframe 캡처를 쓰는지 확인하고, 필요한 경우 검토 기간에만 frame 정책을 조정한다.
5. 등록 후 첫 리뷰에서 로그인, 대시보드, 이미지/미디어 API가 정상 재현되는지 확인한다.
