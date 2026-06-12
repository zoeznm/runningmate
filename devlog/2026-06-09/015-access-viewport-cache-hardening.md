# 015 접근 화면 모바일 viewport 및 PWA 캐시 갱신 보강

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "`100dvh` 기준과 루트 배경 통일로 수정했다고 했는데 실제로 들어가 보니 수정이 전혀 안 되어 있다. 프로젝트 높이가 실제 기기 화면보다 짧은 것 같은데 왜 여전히 같은 문제가 있을까?"
- 리뷰 내용: 모바일 앱 접근 화면 하단 배경 노출 원인 재점검 및 재발 방지 보강

## 변경 파일

- `src/app/page.access/view.scss`
- `src/app/page.access/view.ts`
- `src/angular/styles/styles.scss`
- `src/angular/index.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-09/015-access-viewport-cache-hardening.md`

## 원인 판단

- 운영 `main.js`에는 이전 `100dvh` 수정이 들어가 있었으므로 단순 미배포만의 문제는 아니었다.
- 일부 모바일 WebView에서는 `100dvh`도 실제 표시 영역과 다르게 계산될 수 있고, 부모인 `html/body/app-root`의 `#12121c` 배경이 하단에 다시 드러날 수 있다.
- PWA 번들 파일명이 고정되어 있어 서비스워커 캐시 버전이 유지되면 사용자 기기에서 오래된 앱 셸이 남을 수 있다.

## 변경 내용

- `/access` 컴포넌트 호스트를 `position: fixed; inset: 0`로 고정해 전역 배경이 하단에 끼어들지 않도록 했다.
- 접근 페이지 진입 시 `visualViewport.height`, `innerHeight`, `documentElement.clientHeight` 중 가장 큰 값을 `--access-visual-height` CSS 변수로 주입하도록 했다.
- 접근 페이지가 활성화된 동안 `html/body/app-root`에 `is-access-page` 클래스를 적용해 부모 배경도 `#05070c`로 맞췄다.
- CSS 캐시나 적용 순서 영향을 줄이기 위해 접근 페이지 활성화 중 `html/body/app-root`의 inline 배경도 `#05070c`로 맞추고 이탈 시 복구하도록 했다.
- 접근 페이지 진입 중 `theme-color`를 접근 화면 배경색으로 바꾸고 이탈 시 복구하도록 했다.
- PWA 서비스워커 캐시 버전을 `runningmate-pwa-v14`로 올리고 인덱스 갱신 키를 `rm-access-viewport-20260609`로 변경했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.scss src/app/page.access/view.ts src/angular/styles/styles.scss src/angular/index.pug config/pwa/sw.js` 통과
- 운영 `main.js`에 이전 `100dvh` 수정이 포함되어 있음을 확인
- 빌드 산출물에서 `runningmate-pwa-v14`, `rm-access-viewport-20260609`, `--access-visual-height`, `is-access-page` 반영 확인

## 남은 리스크

- 현재 작업 환경에는 Playwright/Chromium이 없어 실제 모바일 뷰포트 스크린샷 자동 검증은 수행하지 못했다.
- 배포 후 사용 중인 PWA/브라우저가 새 서비스워커를 적용하려면 첫 진입 이후 한 번의 새로고침이 필요할 수 있다.
