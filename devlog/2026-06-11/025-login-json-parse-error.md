# 로그인 응답 JSON 파싱 오류 수정

## 사용자 요청

- 리뷰 ID: `xyacypgnxkenansvzctubfxprpwtjhgw`
- 제목: 로그인 자동 무한 로딩
- 요청: 로그인 화면은 뜨지만 로그인 시 `응답을 읽지 못했어. 다시 시도해줘` 오류가 뜨는 원인을 알려주고 수정해달라고 요청했다.

## 원인

- 로그인 프론트는 `/api/auth/login` 응답을 JSON으로 읽는다.
- 서버 라우트의 실패 응답은 `_send_response()`에서 `wiz.response.status()`를 사용하고 있었고, 이 경로는 WIZ 기본 오류 응답이 JSON이 아닐 수 있다.
- 이 경우 실제 오류가 아이디/비밀번호 불일치 또는 요청 오류여도 프론트 공통 파서가 JSON 파싱 실패로 처리해 `응답을 읽지 못했어. 다시 시도해줘`만 보여준다.

## 변경 파일

- `src/route/api.auth.login/controller.py`
  - 로그인 실패/검증 실패 응답도 `application/json; charset=utf-8`로 고정했다.
  - no-store, nosniff 등 인증 응답 헤더를 JSON 응답에 직접 적용했다.
- `src/angular/app/shared/api.ts`
  - 4xx/5xx 응답이 비JSON으로 와도 parse 오류로 덮지 않고 텍스트를 정리해 client/server 오류 메시지로 처리하도록 했다.
- `src/angular/index.pug`
  - service worker refresh 키를 `rm-login-json-response-20260611`로 갱신했다.
- `config/pwa/sw.js`
  - 캐시 버전을 `runningmate-pwa-v34-login-json-response`로 올렸다.

## 확인한 내용

- `wiz_project_build(projectName="main", clean=false)` 성공
  - `EsBuild complete`
  - `Project 'main' build completed`
- 코드 확인
  - 로그인 라우트 JSON 응답 고정 확인
  - 공통 API 파서의 `textResponseMessage()` 적용 확인
  - service worker 캐시 버전 `runningmate-pwa-v34-login-json-response` 확인
- 로컬 HTTPS curl 확인 시도
  - 현재 작업 환경에서는 `127.0.0.1:443` 연결이 열려 있지 않아 연결 실패했다.

## 남은 확인/배포 메모

- 실제 Raspberry Pi 서버에서 빌드/재시작 후 모바일 로그인 실패 케이스와 성공 케이스를 모두 확인해야 한다.
- 재시작 후 `/sw.js` 첫 줄이 `runningmate-pwa-v34-login-json-response`인지 확인한다.
