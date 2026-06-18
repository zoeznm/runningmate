# iOS 앱 삭제 재설치 필요 사유 및 절차 정리

- 날짜: 2026-06-18
- 작업 ID: 005
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"여전히 링크로 들어가고 링크에서 로그인을 해도 앱에서는 아무런 변화가 없어 왜그러는거야? 앱을 어떻게 삭제해? 클린빌드 하고 npm run ios:sync 하고 실행하는 걸로 했었는데 앱을 삭제하고 해야되는거야?"

## 확인

- 현재 프로젝트의 `capacitor.config.json`에는 `server.url`이 없다.
- 현재 구조는 iOS 앱이 `bundle/www`를 내부 `capacitor://localhost`에서 로드하고, API 요청만 `https://run.myrunningmate.com/api/...`로 보내는 방식이다.

## 설명

- iPhone에 이미 설치된 앱은 이전 Capacitor 설정과 WebView 저장소를 계속 들고 있을 수 있다.
- Safari 또는 원격 `run.myrunningmate.com`에서 로그인한 세션은 iOS 앱 내부 WebView의 `capacitor://localhost` localStorage/sessionStorage와 다르다.
- 그래서 링크에서 로그인해도 앱 내부 로그인 상태는 바뀌지 않는다.
- Xcode Clean Build와 `npm run ios:sync`는 앱 컨테이너 저장소를 지우지 않는다.

## 권장 순서

1. Mac 프로젝트에서 최신 코드인지 확인한다.
2. `capacitor.config.json`에 `server.url`이 없는지 확인한다.
3. `npm run ios:sync`를 실행한다.
4. iPhone에서 기존 러닝메이트 앱을 삭제한다.
5. Xcode에서 다시 Run한다.

## iPhone 앱 삭제 방법

- 홈 화면에서 러닝메이트 앱 아이콘을 길게 누른다.
- `앱 제거`를 누른다.
- `앱 삭제`를 선택한다.
- 삭제 후 Xcode에서 다시 Run한다.

## 확인 방법

- 재설치 후 앱이 Safari가 아니라 앱 화면 자체에서 열린다.
- Safari Web Inspector로 확인하면 앱 origin이 `capacitor://localhost`여야 한다.
- 로그인 후 API 요청은 `https://run.myrunningmate.com/api/...`로 나가야 한다.
