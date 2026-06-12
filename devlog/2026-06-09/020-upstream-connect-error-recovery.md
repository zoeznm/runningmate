# upstream 연결 실패 UX 및 헬스체크 보강

- **ID**: 020
- **날짜**: 2026-06-09
- **유형**: 안정성/UX 개선
- **리뷰 ID**: cmrdrtopcgnxudglfagqpqxrgiuksqbu

## 작업 요약

게이트웨이가 앱 서버에 연결하지 못해 `upstream connect error or disconnect/reset before headers` 원문이 흰 화면에 노출되는 상황을 줄이기 위해 PWA 서비스워커의 네비게이션 실패 처리를 보강했다. 502, 503, 504 응답이나 네트워크 연결 실패를 만나면 캐시된 `/error.html`로 이동해 사용자용 안내와 재시도 버튼을 보여준다.

앱 서버 준비 상태를 외부 프록시/배포 헬스체크가 확인할 수 있도록 DB와 세션에 의존하지 않는 `/healthz` 라우트를 추가했다.

## 원문 요청사항

```text
작업 진행해줘

upstream connect error or disconnect/reset before headers. retried and the latest reset reason: remote connection failure, transport failure reason: delayed connect error: 111
이런 에러가 뜰 때도 저렇게 그냥 흰 바탕에 저런 에러가 뜨게하면 안되니까 사용자 편의성을 위해 잘 UI를 수정해봐 
그리고 왜 저런 에러가 뜨는지도 같이 알려줘 그리고 다시는 저런 에러가 뜨지 않게도 조치해줘
```

## 원인 판단

- 해당 문구는 앱 코드가 만든 에러가 아니라 게이트웨이/프록시가 앱 upstream에 TCP 연결을 열지 못했을 때 나오는 연결 실패 메시지다.
- `delayed connect error: 111`은 일반적으로 connection refused를 뜻하며, 앱 프로세스가 아직 준비되지 않았거나 재시작/배포 중이거나 기대 포트에서 리슨하지 않는 경우 발생한다.
- 이 단계에서는 앱이 요청을 받기 전이라 Angular 컴포넌트만으로는 첫 방문자의 원문 프록시 메시지를 완전히 가릴 수 없다. 그래서 정적 에러 페이지, 서비스워커 fallback, 헬스체크 라우트를 함께 보강했다.

## 변경 파일 목록

- `config/pwa/sw.js`
  - 캐시 버전을 `runningmate-pwa-v15`로 갱신.
  - `/error.html`을 앱 셸 캐시에 포함.
  - 네비게이션 요청에서 502/503/504 또는 네트워크 실패를 만나면 `/error.html?code=...&from=...`으로 안내.
- `src/assets/error.html`
  - 기본 안내를 503 연결 복구 상황에 맞게 변경.
  - 502/503 메시지를 앱 서버 재시작/준비 지연 상황에 맞게 보강.
- `src/route/healthz/app.json`
  - `/healthz` 경량 헬스체크 라우트 추가.
- `src/route/healthz/controller.py`
  - DB/세션 없이 200 JSON 상태를 반환하도록 구현.
- `devlog.md`, `devlog/2026-06-09/020-upstream-connect-error-recovery.md`
  - 작업 이력 추가.

## 확인 결과

- `python -m py_compile src/route/healthz/controller.py` 성공.
- `python -m json.tool src/route/healthz/app.json` 성공.
- `node --check config/pwa/sw.js` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `cmp -s src/assets/error.html build/dist/build/error.html` 성공.
- 빌드/번들 산출물에서 `runningmate-pwa-v15`, 503 안내 문구, `/healthz` 라우트 반영 확인.
- 별도 로컬 검증 서버 `wiz run --host=127.0.0.1 --port=3001`에서 `/healthz`가 200 JSON으로 응답함을 확인.
- 별도 로컬 검증 서버에서 `/error.html?code=503`과 `/sw.js`의 새 문구/버전 반영 확인.

## 남은 리스크

- 첫 방문자처럼 서비스워커가 아직 설치되지 않은 상태에서 프록시가 앱에 연결하지 못하면, 플랫폼 레벨에서 502/503/504를 `/error.html`로 매핑해야 원문 메시지를 완전히 막을 수 있다.
- 운영 배포 설정에서 readiness/liveness probe가 `/healthz`를 사용하도록 연결되어야 재시작/배포 직후 트래픽 유입을 더 확실히 막을 수 있다.
