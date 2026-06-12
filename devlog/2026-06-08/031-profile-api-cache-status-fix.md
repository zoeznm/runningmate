# 타 사용자 프로필 API 캐시 및 오류 배너 수정

- **ID**: 031
- **날짜**: 2026-06-08
- **유형**: 버그 수정

## 작업 요약
타 사용자 프로필 상세 API가 JSON을 읽지 못할 때 상단 상태 배너에 "응답을 읽지 못했어. 다시 시도해줘"가 노출되는 문제를 수정했다.
서비스워커가 `/api/` GET 응답을 런타임 캐시에 저장하던 구조를 제거해 오래된 HTML/오류 응답이 API 응답으로 재사용되지 않도록 했고, 상세 로딩 실패 시 이미 목록에서 받은 기본 프로필이 있으면 오류 배너를 비웠다.

## 원문 요청사항
```text
응답을 읽지 못했어. 다시 시도해줘 라는 문구가 뜨지 않게 오류를 수정해주면 안될까?
```

## 변경 파일 목록
- `config/pwa/sw.js`: 서비스워커 캐시 버전을 `runningmate-pwa-v12`로 올리고 `/api/`, `/auth/` GET 요청을 캐시 없는 `networkOnly` 처리로 변경.
- `src/angular/index.pug`: 새 서비스워커 적용 시 기존 컨트롤러 페이지가 한 번 새로고침되도록 refresh key 갱신.
- `src/app/page.dashboard/view.ts`: 타 사용자 프로필 상세 로딩 실패 시 기본 프로필이 이미 있으면 상단 오류 상태를 표시하지 않도록 변경.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/031-profile-api-cache-status-fix.md`: 작업 상세 기록 추가.

## 확인 결과
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `https://matomabo.run.seasonai.net/sw.js` 응답에서 `runningmate-pwa-v12` 및 `/api/` `networkOnly` 처리 확인.
- `https://matomabo.run.seasonai.net/api/follows/dudgns5599` 비로그인 호출이 HTML이 아닌 JSON 401 응답을 반환하는 것을 확인.
- `rg`로 `src`와 `build` 산출물에 프로필 상세 오류 배너 방어 및 서비스워커 refresh key 반영을 확인했다.
