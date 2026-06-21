# 모바일 하단 메뉴바 업로드 중 고정 처리

## 요청

- 리뷰 ID: `flnsqmvfkhkjlodqiphupducsfbnjduo`
- 캡처 기록 업로드 등 진행 중 하단 메뉴바가 위로 올라오는 현상이 있어, 하단 메뉴바를 항상 화면 하단에 고정.

## 원인

- 모바일 대시보드의 `.nav-bar`가 flex 레이아웃 흐름 안에서 `position: relative`로 배치되어 있었다.
- 업로드 진행률/상태 영역이 추가되거나 viewport 높이 동기화가 일어날 때 메뉴가 콘텐츠 흐름 영향을 받아 위로 밀릴 수 있었다.

## 변경

- `src/app/page.dashboard/view.scss`
  - 모바일 `.nav-bar`를 `position: fixed; bottom: 0; left/right: 0`으로 변경했다.
  - 메뉴 높이를 `--dashboard-mobile-nav-height` 기준으로 고정하고, 콘텐츠/채팅 하단 패딩을 메뉴 높이만큼 늘려 메뉴에 가려지지 않게 했다.
  - 모바일 `.app-wrapper`에 고정 viewport 높이와 overflow 제어를 추가했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 새 `main.js`를 받도록 PWA 캐시 버전을 `runningmate-pwa-v39-fixed-bottom-nav`로 갱신했다.
- `src/angular/index.pug`
  - 서비스워커 갱신 후 재로딩 키를 `rm-fixed-bottom-nav-20260615`로 갱신했다.

## 확인

- `python -m py_compile src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공.
- `node build/wizbuild.js src/angular/index` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/dist/build/main.js`, `bundle/www/main.js`에 모바일 `.nav-bar` fixed 하단 고정 CSS 반영 확인.
- `bundle/www/index.html`, `bundle/config/pwa/sw.js`에 새 refresh/cache 버전 반영 확인.

## 남은 리스크

- 실제 iOS/Android PWA에서 업로드 진행 중 visual viewport 이벤트와 안전영역 조합은 실기기에서 한 번 더 확인하는 것이 좋다.
