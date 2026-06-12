# 모바일 하단 메뉴바 위치 원복 및 z-index 보정 제거

## 사용자 원본 요청

그리고 하단 메뉴바는 원래대로 해줘 z-index 그런거 없애주고

## 처리 내용

- 모바일 하단 메뉴바를 `bottom: 0` 기준으로 되돌렸다.
- 이전 보정에서 추가했던 모바일 전용 `z-index: 120`을 제거했다.
- 이전 보정에서 추가했던 `translateZ(0)` 합성 레이어 지정도 제거했다.
- 메뉴바를 아래로 내리던 `--dashboard-mobile-nav-offset` 계산과 `@supports (height: 100dvh)` override를 제거했다.
- 하단 safe-area는 다시 기본 safe-area 값을 사용하고, 메뉴바 하단 padding은 기본 `16px + safe-area` 기준으로 맞췄다.
- PWA 캐시 버전을 `runningmate-pwa-v25`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/010-mobile-nav-reset-remove-z-index.md`

## 검증 결과

- 모바일 하단 메뉴바 override에서 `dashboard-mobile-nav-offset`, `translateZ`, `z-index: 120` 제거 확인
- `git diff --check -- src/app/page.dashboard/view.scss config/pwa/sw.js devlog.md devlog/2026-06-11` 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- 실제 iOS Safari/PWA safe-area 렌더링은 기기별 차이가 있어 실기기에서 하단 간격 최종 확인이 필요하다.
