# 대시보드 알림 정적 파일 및 훈련 부하 API 오류 수정

- **ID**: 016
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: lwvealbmshmxtxnczukrnzjagfmslrrh

## 작업 요약
`/dashboard`에서 `notification-settings.js` 요청이 SPA HTML로 fallback되어 `Unexpected token '<'`가 발생하지 않도록 알림 JS/CSS 전용 라우트를 추가했다. `/api/training-load`는 세션/모델/계산 예외가 HTML 500으로 노출되지 않도록 JSON 기본값 응답으로 방어했다.

## 원문 요청사항
```text
작업 진행해줘

Uncaught SyntaxError: Unexpected token '<' (at notification-settings.js?v=rm-notifications-20260604:1:1)이 오류 이해하기
reviewops-sdk.js:1351  GET https://matomabo.run.seasonai.net/api/training-load 500 (Internal Server Error)

이런 오류가 남 수정해줘
```

## 변경 파일 목록
- `src/angular/index.pug`: 알림 JS/CSS 요청을 절대 경로로 바꾸고 캐시 버전을 `rm-notifications-20260608`로 갱신
- `src/angular/angular.build.options.json`: 알림 정적 파일 asset 입력 경로를 `src/assets`로 변경
- `src/angular/angular.json`: 빌드 옵션 반영
- `src/angular/static/notification-settings.js`: 알림 아이콘 캐시 버전 갱신
- `src/assets/notification-settings.js`: 알림 JS를 라우트 서빙용 asset으로 추가
- `src/assets/notification-settings.css`: 알림 CSS를 라우트 서빙용 asset으로 추가
- `src/route/notification-settings-js/app.json`: `/notification-settings.js` 라우트 추가
- `src/route/notification-settings-js/controller.py`: 알림 JS를 올바른 MIME 타입으로 다운로드 응답
- `src/route/notification-settings-css/app.json`: `/notification-settings.css` 라우트 추가
- `src/route/notification-settings-css/controller.py`: 알림 CSS를 올바른 MIME 타입으로 다운로드 응답
- `src/route/api.training-load/controller.py`: 훈련 부하 API 예외 처리 및 JSON fallback 보강
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/016-dashboard-notification-training-load-errors.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.training-load/controller.py project/main/src/route/notification-settings-js/controller.py project/main/src/route/notification-settings-css/controller.py` 성공
- `python -m json.tool project/main/src/angular/angular.build.options.json` 성공
- `python -m json.tool project/main/src/angular/angular.json` 성공
- `cmp -s project/main/src/angular/static/notification-settings.js project/main/src/assets/notification-settings.js` 성공
- `cmp -s project/main/src/angular/static/notification-settings.css project/main/src/assets/notification-settings.css` 성공
- WIZ `wiz_project_build(projectName="main", clean=false)` 성공
- `bundle/src/assets/notification-settings.js` 첫 바이트가 `0x28`임을 확인해 HTML(`0x3c`) fallback이 아님을 확인
- `bundle/src/route/notification-settings-js`와 `bundle/src/route/notification-settings-css` 생성 확인
