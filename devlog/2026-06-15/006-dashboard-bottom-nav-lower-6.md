# 하단 메뉴바 버튼 위치 2px 추가 하향

## 요청

- 리뷰 ID: `flnsqmvfkhkjlodqiphupducsfbnjduo`
- 하단 메뉴바를 현재보다 조금 더 아래로 내리기.

## 변경

- `src/app/page.dashboard/view.scss`
  - `.nav-item`의 시각적 하향 이동을 `translateY(4px)`에서 `translateY(6px)`로 조정했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - 캐시 버전을 `runningmate-pwa-v44-bottom-nav-lower-6`으로 갱신했다.
- `src/angular/index.pug`
  - 서비스워커 refresh key를 `rm-bottom-nav-lower-6-20260615`로 갱신했다.

## 확인

- `python -m py_compile src/route/portal.season.pwa.swjs/controller.py src/portal/season/route/pwa.swjs/controller.py build/src/route/portal.season.pwa.swjs/controller.py` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `build/dist/build/main.js`, `bundle/www/main.js`에 `transform: translateY(6px)` 반영 확인.
- `bundle/www/index.html`, `bundle/config/pwa/sw.js`에 새 refresh/cache 버전 반영 확인.

## 남은 리스크

- 버튼 영역을 추가로 내렸으므로, 일부 기기에서는 하단 가장자리와 라벨이 가까워 보일 수 있다.
