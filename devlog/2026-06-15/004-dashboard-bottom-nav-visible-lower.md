# 하단 메뉴바 기본 패딩 및 safe-area 체감 위치 재조정

## 요청

- 리뷰 ID: `flnsqmvfkhkjlodqiphupducsfbnjduo`
- 이전 조정 후에도 하단 메뉴바 위치 변화가 체감되지 않는 문제 확인 및 추가 조정.

## 원인

- 이전 조정은 모바일 미디어쿼리의 내부 여백만 줄여, 넓은 화면 캡처에서는 기본 `.nav-bar`의 `padding: 10px 0 16px`가 그대로 적용될 수 있었다.
- iPhone 계열에서는 safe-area 값이 커서 4px 축소만으로는 체감 변화가 작을 수 있었다.

## 변경

- `src/app/page.dashboard/view.scss`
  - 기본 `.nav-bar` 패딩을 `10px 0 16px`에서 `8px 0 2px`로 줄였다.
  - 모바일 bottom padding을 `max(2px, calc(safe-area - 12px))`로 바꿔 safe-area를 일부 유지하면서 메뉴 버튼 영역이 더 내려오게 했다.
  - 모바일 메뉴 높이를 `calc(62px + bottom-padding)` 기준으로 재계산했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 캐시 버전을 `runningmate-pwa-v41-fixed-bottom-nav-lower`로 갱신했다.
- `src/angular/index.pug`
  - 서비스워커 refresh key를 `rm-fixed-bottom-nav-lower-20260615`로 갱신했다.

## 확인

- `python -m py_compile src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py build/src/route/portal.season.pwa.swjs/controller.py` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/dist/build/main.js`, `bundle/www/main.js`에 기본 `padding: 8px 0 2px`와 모바일 `max(2px, calc(var(--dashboard-mobile-safe-bottom) - 12px))` 반영 확인.
- `bundle/www/index.html`, `bundle/config/pwa/sw.js`에 새 refresh/cache 버전 반영 확인.

## 남은 리스크

- safe-area를 일부 줄였으므로, 일부 iPhone/PWA 환경에서는 홈 인디케이터와 메뉴가 가까워 보일 수 있다.
