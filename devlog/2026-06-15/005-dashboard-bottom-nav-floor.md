# 하단 메뉴바 바닥 밀착 강제 조정

## 요청

- 리뷰 ID: `flnsqmvfkhkjlodqiphupducsfbnjduo`
- 하단 메뉴바를 더 확실하게 아래로 내려 체감 변화가 크게 보이도록 조정.

## 변경

- `src/app/page.dashboard/view.scss`
  - 기본 `.nav-bar` 패딩을 `4px 0 0`으로 줄여 하단 여백을 제거했다.
  - `.nav-item` 최소 높이를 `50px`로 줄이고 `translateY(4px)`를 적용해 아이콘/텍스트 자체를 아래로 내렸다.
  - 모바일 safe-area bottom padding을 `0px`, 메뉴 높이를 `54px`로 고정해 safe-area 보정으로 메뉴가 위로 밀리지 않게 했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 캐시 버전을 `runningmate-pwa-v42-bottom-nav-floor`로 갱신했다.
- `src/angular/index.pug`
  - 서비스워커 refresh key를 `rm-bottom-nav-floor-20260615`로 갱신했다.

## 확인

- `python -m py_compile src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py build/src/route/portal.season.pwa.swjs/controller.py` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/dist/build/main.js`, `bundle/www/main.js`에 `padding: 4px 0 0`, `transform: translateY(4px)`, `--dashboard-mobile-nav-bottom-padding: 0px` 반영 확인.
- `bundle/www/index.html`, `bundle/config/pwa/sw.js`에 새 refresh/cache 버전 반영 확인.

## 남은 리스크

- iPhone/PWA 홈 인디케이터 안전영역 보정을 사실상 제거했으므로, 일부 기기에서는 하단 메뉴가 홈 인디케이터와 매우 가까워질 수 있다.
