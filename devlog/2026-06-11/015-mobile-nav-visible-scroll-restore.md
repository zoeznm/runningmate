# 모바일 하단 메뉴바 미노출 및 스크롤 불가 수정

## 사용자 원본 요청

앱에서 하단 메뉴바가 안 보여  
그리고 스크롤이 안돼

## 처리 내용

- 모바일 viewport 높이 계산에서 실제 보이는 영역보다 큰 `window.screen.height`를 강제로 반영하던 로직을 제거했다.
- 모바일 하단 메뉴바를 `position: fixed`에서 화면 프레임 내부 flex 요소로 되돌려 화면 아래로 밀려 사라지지 않게 했다.
- 모바일 하단 메뉴의 padding과 safe-area 계산을 다시 줄여 메뉴가 잘리지 않으면서 실제 앱 하단 위치에 붙도록 조정했다.
- 모바일 활성 화면과 주요 스크롤 컨테이너에 터치 스크롤 옵션을 명시해 스크롤 동작을 복구했다.
- PWA 캐시 버전을 `runningmate-pwa-v29`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `src/app/page.dashboard/view.ts`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/015-mobile-nav-visible-scroll-restore.md`

## 검증 결과

- `git diff --check -- src/app/page.dashboard/view.scss src/app/page.dashboard/view.ts config/pwa/sw.js` 통과
- `wiz_project_build(clean=false)` 성공
- 번들에 `runningmate-pwa-v29`, 모바일 nav height, 터치 스크롤 CSS 반영 확인
- `curl http://127.0.0.1:3000/dashboard` 응답 200 확인

## 남은 리스크

- 실기기 PWA에서 이전 서비스워커 캐시가 즉시 교체되지 않으면 한 번 새로고침 또는 앱 재진입이 필요할 수 있다.
