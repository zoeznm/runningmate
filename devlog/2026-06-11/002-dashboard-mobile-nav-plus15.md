# 002 대시보드 모바일 하단 메뉴바 15px 추가 하향 조정

## 사용자 요청

- Review ID: `apeekmrmpzepfkejsosbvomgtmclhaqi`
- 원 요청: "좀 더 내려줄 수 있어? 한 15px만 더"

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `src/angular/index.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/002-dashboard-mobile-nav-plus15.md`

## 변경 내용

- 모바일 하단 메뉴바 offset 상한을 `28px`에서 `43px`로 올려 이전 보정 대비 최대 15px 더 내려가도록 했다.
- 서비스워커 캐시 버전을 `runningmate-pwa-v20`으로 올리고 index 갱신 키를 `rm-dashboard-nav-bottom-plus15-20260611`로 변경했다.

## 검증

- `git diff --check -- src/app/page.dashboard/view.scss src/angular/index.pug config/pwa/sw.js` 통과
- `wiz_project_build(projectName="main", clean=false)` 성공

## 남은 리스크

- 실제 운영 모바일 WebView 캡처 자동 검증은 현재 작업 환경에서 수행하지 못했다.
- 서비스워커가 이미 설치된 기기에서는 새 캐시 적용을 위해 첫 진입 후 갱신이 필요할 수 있다.
