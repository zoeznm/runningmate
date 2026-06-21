# 모바일 하단 메뉴바 안전영역 추가 여백 축소

## 요청

- 리뷰 ID: `flnsqmvfkhkjlodqiphupducsfbnjduo`
- 하단 메뉴바가 safe-area 때문에 바닥에서 떨어져 보이는 문제를 줄이기 위해 추가 내부 여백을 낮춰보기.

## 변경

- `src/app/page.dashboard/view.scss`
  - 모바일 하단 메뉴의 추가 bottom padding을 `8px + safe-area`에서 `4px + safe-area`로 축소했다.
  - 메뉴 높이 변수도 `70px + safe-area`에서 `66px + safe-area`로 맞춰 내부 버튼 영역이 실제로 4px 더 내려오게 했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 모바일/PWA가 새 `main.js`를 받도록 캐시 버전을 `runningmate-pwa-v40-fixed-bottom-nav-tight`로 갱신했다.
- `src/angular/index.pug`
  - 서비스워커 갱신 후 새로고침 키를 `rm-fixed-bottom-nav-tight-20260615`로 갱신했다.

## 확인

- `python -m py_compile src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py build/src/route/portal.season.pwa.swjs/controller.py` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/dist/build/main.js`, `bundle/www/main.js`에 `calc(4px + var(--dashboard-mobile-safe-bottom))`, `calc(66px + var(--dashboard-mobile-safe-bottom))` 반영 확인.
- `bundle/www/index.html`, `bundle/config/pwa/sw.js`에 새 refresh/cache 버전 반영 확인.

## 남은 리스크

- safe-area 자체는 홈 인디케이터 충돌 방지를 위해 유지했으므로, iPhone 계열에서는 기기 안전영역만큼의 여백은 계속 남는다.
