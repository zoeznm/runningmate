# 커스텀 서버 에러 페이지 추가

- **ID**: 002
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: lifgknmxmfratmbedolxnwprahpjkujz

## 작업 요약
서버 에러 발생 시 앱 번들 또는 외부 자원 없이 표시할 수 있는 단일 HTML 에러 페이지를 추가했다. 404, 500, 502, 503, 504 코드별 안내 메시지를 제공하고, `?code=503` 또는 `?status=503` 같은 쿼리로 상황별 문구를 전환할 수 있게 했다. 페이지에는 다시 시도 버튼과 홈으로 버튼을 포함하고, 모바일/데스크톱 반응형 레이아웃을 적용했다.

## 원문 요청사항
```text
작업 진행해줘

503, 500, 404 등 서버 에러 발생 시 보여줄 커스텀 에러 페이지를 만들어줘.

요구사항:
- 에러 코드와 상황에 맞는 안내 메시지 표시 (예: 503은 "서버 점검 중입니다. 잠시 후 다시 시도해주세요")
- 깔끔하고 반응형인 디자인 (모바일/데스크탑 대응)
- "다시 시도" 버튼과 "홈으로" 버튼 포함
- 외부 의존성 없이 단일 HTML 파일로 (CSS 인라인 또는 <style> 내장)
```

## 변경 파일 목록
- `src/assets/error.html`: 코드별 안내 메시지, 반응형 스타일, 다시 시도/홈으로 버튼을 포함한 단일 HTML 에러 페이지 추가
- `src/angular/angular.build.options.json`: `src/assets/error.html`을 빌드 루트 `/error.html`로 복사하는 asset 설정 추가
- `src/angular/angular.json`: 현재 Angular 빌드 설정에도 동일한 `/error.html` asset 복사 설정 반영
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/002-custom-error-page.md`: 상세 devlog 추가

## 확인 결과
- `python -m json.tool src/angular/angular.build.options.json` 성공
- `python -m json.tool src/angular/angular.json` 성공
- `git diff --check -- src/assets/error.html src/angular/angular.build.options.json src/angular/angular.json` 성공
- WIZ `wiz_project_build(clean=false)` 성공
- `build/dist/build/error.html` 생성 확인
- `rg -n "503 Service Unavailable|서버 점검 중입니다|다시 시도|홈으로" build/dist/build/error.html`로 핵심 문구 반영 확인
- `cmp -s src/assets/error.html build/dist/build/error.html` 성공
