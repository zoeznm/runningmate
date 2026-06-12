# 모바일 하단 메뉴바 잘림 방지 방식 재수정

## 사용자 원본 요청

여전히 잘려~ 빡치게 하지 말고 제대로 수정해

## 처리 내용

- 잘림 원인이 될 수 있는 `safe-area-inset-bottom - 14px` 축소 방식을 제거했다.
- 하단 메뉴 컨테이너는 전체 safe-area를 확보하도록 되돌렸다.
- 메뉴를 아래로 보이게 하기 위해 컨테이너를 내리지 않고, 메뉴 버튼 시각 위치만 `translateY(8px)`로 내부 이동했다.
- 메뉴 버튼이 8px 내려가도 컨테이너 하단에 `8px + safe-area` 여유가 남도록 nav 높이/패딩 변수를 다시 계산했다.
- 콘텐츠와 AI 채팅 하단 padding은 새 nav 높이 기준으로 유지해 메뉴바가 스크롤/입력창을 덮지 않도록 했다.
- PWA 캐시 버전을 `runningmate-pwa-v27`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/013-mobile-nav-safe-area-no-clip-retune.md`

## 검증 결과

- `safe-area-inset-bottom - 14px`, `dashboard-mobile-nav-offset`, `z-index: 120`, `translateZ`가 남아 있지 않은지 확인
- `git diff --check -- src/app/page.dashboard/view.scss config/pwa/sw.js devlog.md devlog/2026-06-11` 통과
- `wiz_project_build(clean=false)` 성공
- WIZ 자식 프로세스 재시작 완료
- 번들에 `dashboard-mobile-nav-visual-nudge`와 `runningmate-pwa-v27` 반영 확인
- `curl http://127.0.0.1:3000/dashboard` 응답 200 확인

## 남은 리스크

- Playwright가 설치되어 있지 않아 자동 모바일 스크린샷 검증은 수행하지 못했다.
- 실제 iOS PWA 하단 safe-area와 홈 인디케이터 위치는 실기기에서 최종 육안 확인이 필요하다.
