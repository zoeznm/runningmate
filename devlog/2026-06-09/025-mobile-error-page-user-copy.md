# 오류 페이지 모바일 사용자 안내 화면 개편

- **ID**: 025
- **날짜**: 2026-06-09
- **유형**: 디자인/UX 개선
- **리뷰 ID**: cmrdrtopcgnxudglfagqpqxrgiuksqbu

## 작업 요약

오류 페이지가 웹 데스크톱 카드처럼 보이고, `503 Service Unavailable`, 요청 경로, 지원 코드처럼 개발자에게 가까운 정보가 사용자 화면에 노출되는 문제를 수정했다. 모바일 앱 화면 폭을 기준으로 단일 컬럼 레이아웃을 재구성하고, 사용자가 이해할 수 있는 한국어 안내 문구와 재시도/홈 이동 버튼만 남겼다.

## 원문 요청사항

```text
여기 이거를 보면 지금 좀 이상한게 사용자가 봐야될 부분이거든 뭔가 앱이 멈췄거나 문제가 생겼을 때? 근데 꼭 내용이 개발자를 위한 내용같아 그래서 수정할 필요가 있어 
사용자가 보기에 아 지금 뭔가 문제가 있구나 라고 알아야되는데 이게 무슨 말이지? 싶게 써뒀어 
요청경로, 지원 코드 이런거가 좀 이상해 그리고 더 문제는 나는 모바일 앱을 기준으로 제작 중인데 지금 저거는 웹을 기준으로 레이아웃을 만든 거 같아 수정해줘
```

## 변경 파일 목록

- `src/assets/error.html`
  - 개발자용 에러 코드, 요청 경로, 지원 코드 노출 제거.
  - 기본 문구를 `앱을 다시 준비하고 있어요` 중심의 사용자용 안내로 변경.
  - 모바일 앱 기준 전체 화면 레이아웃으로 재구성.
  - 404/500/502/503/504 상황별 문구도 사용자 친화적인 문장으로 변경.
- `config/pwa/sw.js`
  - 캐시 버전을 `runningmate-pwa-v16`으로 갱신.
  - 캐시된 오류 페이지가 없을 때 사용하는 최후 fallback HTML 문구도 사용자용 문구로 변경.
- `devlog.md`, `devlog/2026-06-09/025-mobile-error-page-user-copy.md`
  - 작업 이력 추가.

## 확인 결과

- `node --check config/pwa/sw.js` 성공.
- `src/assets/error.html` HTML parser 검증 성공.
- `rg`로 `요청 경로`, `지원 코드`, `Service Unavailable` 등 개발자용 노출 문구 제거 확인.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `cmp -s src/assets/error.html build/dist/build/error.html` 성공.
- 빌드/번들 산출물에서 새 사용자 문구와 `runningmate-pwa-v16` 반영 확인.
- 운영 URL `https://matomabo.run.seasonai.net/error.html`에서 새 문구 반영 확인.
- 운영 `/sw.js`에서 `runningmate-pwa-v16` 반영 확인.
- Playwright 스크린샷으로 390x844 모바일, 1440x900 데스크톱 뷰포트 렌더링 확인.

## 남은 리스크

- 서비스워커 캐시는 기존 사용자의 브라우저 상태에 따라 새 버전 적용까지 한 번의 재진입 또는 새로고침이 필요할 수 있다.
- 첫 방문자의 upstream 프록시 에러 원문 노출을 완전히 막으려면 플랫폼 레벨 502/503/504 에러 매핑이 계속 `/error.html`로 유지되어야 한다.
