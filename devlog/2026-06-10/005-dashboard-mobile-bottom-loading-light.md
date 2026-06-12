# 005 대시보드 모바일 하단 배경 및 초기 로딩 라이트 모드 문구 색상 수정

## 사용자 요청

- Review ID: `apeekmrmpzepfkejsosbvomgtmclhaqi`
- 원 요청: "내가 첨부파일로 스크린샷 하나를 같이 보냈는데 그 스크린샷을 보면 화면 하단에 검정색이 보일거야 저번이랑 같은 이슈인거 같은데 높이 문제인거 같거든? 확인해봐바 그리고 맞다면 수정해줘 그리고 라이트 모드에서는 초기 데이터 수집 중 ~ 하면서 날씨 데이터 이런 하단 텍스트가 흰색으로 나와서 잘 안 보여 수정해줘"

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `src/app/page.dashboard/view.ts`
- `src/app/component.loading.fullscreen/view.scss`
- `src/angular/styles/styles.scss`
- `src/angular/index.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-10/005-dashboard-mobile-bottom-loading-light.md`

## 변경 내용

- 대시보드 모바일 화면 높이를 `--dashboard-visual-height` 기준으로 동기화하고, 모바일에서는 대시보드 host와 phone frame을 같은 높이로 고정해 하단에 전역 다크 배경이 드러나는 상황을 줄였다.
- 대시보드 진입 중 `html`, `body`, `app-root`의 배경과 `theme-color`를 현재 테마 배경으로 맞추고, 이탈 시 기존 값으로 복구하도록 했다.
- 라이트/다크 테마에 `--text-muted`를 정의하고, 초기 로딩 상세 문구가 라이트 모드에서 흰색 fallback을 타지 않도록 공용 로딩 컴포넌트 fallback을 보강했다.
- 전역 스타일과 초기 index 스타일에 `is-dashboard-page` 배경 규칙을 추가했다.
- 서비스워커 캐시 버전을 `runningmate-pwa-v18`로 올리고 index 갱신 키를 `rm-dashboard-viewport-20260610`으로 변경했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.dashboard/view.scss src/app/page.dashboard/view.ts src/app/component.loading.fullscreen/view.scss src/angular/styles/styles.scss src/angular/index.pug config/pwa/sw.js` 통과

## 남은 리스크

- 현재 작업 환경에서는 운영 계정 로그인과 실제 모바일 WebView 캡처 자동 검증을 수행하지 못했다.
- 서비스워커가 이미 설치된 기기에서는 새 캐시 적용을 위해 첫 진입 후 한 번의 갱신이 필요할 수 있다.
