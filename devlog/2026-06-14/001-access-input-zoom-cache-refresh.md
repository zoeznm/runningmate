# 로그인 입력 포커스 확대 방지 및 모바일 PWA 캐시 갱신 보강

## 사용자 요청

로그인할 때 앱에서 input 포커스 시 화면이 확대되는 동작을 없애고, 컴퓨터와 휴대폰에서 보이는 버전이 다른 이유도 확인해달라는 요청.

## 변경 파일

- `src/app/page.access/view.scss`
- `src/angular/index.pug`
- `src/route/portal.season.pwa.swjs/controller.py`
- `src/portal/season/route/pwa.swjs/controller.py`

## 변경 내용

- 로그인, 비밀번호 찾기, 비밀번호 재설정, 이메일 회원가입 입력창에 적용되는 `.field-input` 글자 크기를 `16px`로 조정해 iOS 입력 포커스 자동 확대 조건을 제거했다.
- 앱 viewport에 `maximum-scale=1, user-scalable=no`를 추가해 앱형 WebView/PWA에서 브라우저식 화면 확대를 줄였다.
- 앱 셸의 서비스워커 갱신 키를 `rm-ios-input-zoom-cache-20260614`로 변경해 모바일이 새 셸을 다시 받도록 했다.
- `/sw.js` 응답 시 서비스워커 캐시 버전을 `runningmate-pwa-v35-ios-input-zoom-cache`로 주입해 휴대폰에 남은 이전 PWA 캐시가 갱신되도록 보강했다.

## 확인 결과

- `wiz_project_build(clean=false)` 성공.
- WIZ 빌드 로그에서 EsBuild 완료 및 `Project 'main' build completed.` 확인.

## 비고

- 컴퓨터와 휴대폰 화면 버전 차이는 휴대폰 PWA/서비스워커/브라우저 캐시가 이전 JS/CSS를 유지하면서 발생할 수 있다.
- 배포 후에도 휴대폰에서 이전 화면이 보이면 앱 완전 종료 후 재실행, 브라우저 캐시/웹사이트 데이터 삭제, 또는 PWA 재설치가 필요할 수 있다.
