# 로그인 화면 모바일 앱 쉘 스타일 적용

## 요청

- 리뷰 ID: `gswdqpqcrbcrlyylvmjuayeqcpotzbjv`
- 로그인 페이지가 웹사이트 카드처럼 보이지 않고 모바일 앱 느낌이 나도록 변경.

## 변경

- `src/app/page.access/view.scss`
  - 데스크톱 중앙 카드 테두리/격자 배경을 제거하고, 화면 전체 높이의 모바일 앱 쉘 형태로 조정.
  - 브랜드 영역을 앱 런치 화면처럼 크게 배치하고, 로그인 폼은 하단 입력 영역에 가깝게 정리.
  - 입력창, CTA, 자동 로그인 토글, 회원가입/비밀번호 찾기 링크의 밀도와 터치 타깃을 모바일 앱 톤으로 재조정.
  - 저작권 푸터 노출을 제거해 웹 로그인 페이지 느낌을 줄임.
- `src/app/page.access/view.ts`
  - 로그인 화면 진입 시 문서/앱 루트 배경과 theme-color를 새 앱 쉘 배경색으로 맞춤.
- `config/pwa/sw.js`, `bundle/config/pwa/sw.js`
  - PWA 캐시 키를 `runningmate-pwa-v36-access-app-login`으로 갱신.
- `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - `/sw.js` 응답에서 새 캐시 키가 강제로 주입되도록 버전 문자열 갱신.
- `build/src`, `build/dist/build`, `bundle/www`
  - 원본 변경을 생성 Angular 소스와 배포 번들에 반영.

## 확인

- `npm ci` 성공.
- `node build/wizbuild.js`는 기존 스크립트 특성상 exit code 1로 종료하지만 `EsBuild complete` 출력 및 산출물 갱신 확인.
- `node --check build/dist/build/main.js`, `node --check build/dist/build/vendor.js`, `node --check bundle/www/main.js`, `node --check bundle/www/vendor.js`, `node --check config/pwa/sw.js`, `node --check bundle/config/pwa/sw.js` 성공.
- `curl -I http://127.0.0.1:3000/access` 200 OK 확인.
- `bundle/www/main.js`에 새 `access-bg` 스타일과 기존 자동 로그인 타임아웃 로직(`auth_bootstrap_timeout`)이 함께 포함된 것 확인.
- WIZ 앱 재시작 후 `curl http://127.0.0.1:3000/sw.js` 응답이 `runningmate-pwa-v36-access-app-login`을 반환하는 것 확인.

## 남은 리스크

- Playwright Chromium 설치는 완료됐지만 현재 계정에 OS 라이브러리 설치 권한이 없어 브라우저 스크린샷 검증은 수행하지 못함.
- `npx tsc --noEmit --project build/tsconfig.app.json`는 기존 프로젝트 전반의 타입 오류로 실패함. 이번 변경 파일 고유 오류로 좁혀진 실패는 확인되지 않음.
