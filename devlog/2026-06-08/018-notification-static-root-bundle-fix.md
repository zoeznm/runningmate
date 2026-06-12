# 알림 정적 파일 웹 루트 번들 누락 수정

- **ID**: 018
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: lwvealbmshmxtxnczukrnzjagfmslrrh

## 작업 요약
운영 URL에서 `/notification-settings.js?v=rm-notifications-20260604`가 여전히 `index.html`로 응답되는 것을 확인했다. WIZ 정적 라우트 fallback보다 웹 루트 정적 파일 존재 여부가 우선이라, 알림 JS/CSS가 `bundle/www` 루트에 직접 생성되도록 Angular asset glob을 재귀 패턴으로 변경했다.

## 원문 요청사항
```text
오류가 여전히 똑같이 발생해 수정이 필요해
```

## 변경 파일 목록
- `src/angular/angular.build.options.json`: 알림 asset glob을 `**/notification-settings.*`로 변경
- `src/angular/angular.json`: 동일 asset glob 반영
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/018-notification-static-root-bundle-fix.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(projectName="main", clean=false)` 성공
- `build/dist/build/notification-settings.js`와 `build/dist/build/notification-settings.css` 생성 확인
- `bundle/www/notification-settings.js`와 `bundle/www/notification-settings.css` 생성 확인
- `bundle/www/notification-settings.js` 첫 바이트가 `0x28`, CSS 첫 바이트가 `0x2e`임을 확인
- 운영 URL `https://matomabo.run.seasonai.net/notification-settings.js?v=rm-notifications-20260604` 응답이 `content-type: text/javascript`, 첫 바이트 `0x28`인 것을 확인
- 운영 URL `https://matomabo.run.seasonai.net/notification-settings.css?v=rm-notifications-20260604` 응답이 `content-type: text/css`, 첫 바이트 `0x2e`인 것을 확인
- 운영 URL `https://matomabo.run.seasonai.net/api/training-load` 비로그인 응답이 HTML 500이 아닌 JSON 401 payload로 내려오는 것을 확인
