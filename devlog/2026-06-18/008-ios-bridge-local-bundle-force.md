# iOS BridgeViewController에서 원격 serverURL 강제 차단

- 날짜: 2026-06-18
- 작업 ID: 008
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"여전히 이렇게 하고있어. 링크를 타고 들어가. Loading app at https://run.myrunningmate.com/dashboard..."

## 확인

- 현재 루트/네이티브 Capacitor config에는 `server.url`이 없다.
- 현재 iOS 프로젝트 파일에도 `https://run.myrunningmate.com/dashboard` 문자열은 남아 있지 않다.
- 반복 로그의 핵심은 `Loading app at https://run.myrunningmate.com/dashboard...`이며, 이는 실행 중인 앱이 여전히 remote server mode의 descriptor로 WebView를 시작하고 있다는 뜻이다.

## 변경

- `ios/App/App/RunningMateBridgeViewController.swift`에서 `instanceDescriptor()`를 override했다.
- `descriptor.serverURL = nil`로 고정해 예전 native config에 원격 URL이 남아 있어도 원격 서버를 로드하지 못하게 했다.
- `descriptor.appStartPath = nil`, `descriptor.allowedNavigationHostnames = []`로 원격 시작 경로/허용 네비게이션 흔적을 초기화했다.
- 앱 리소스의 `public` 폴더를 `descriptor.appLocation`으로 다시 지정해 내부 번들 로딩을 강제했다.

## 확인

- `npm run ios:verify-config` 통과.
- 현재 설정/네이티브 iOS 프로젝트 범위에서 `https://run.myrunningmate.com/dashboard` 문자열 없음.
- 현재 환경에는 `xcodebuild`가 없어 iOS 네이티브 컴파일은 실행하지 못했다.

## 정상 기준

- 최신 Swift 변경이 반영된 앱에서는 `Loading app at https://run.myrunningmate.com/dashboard...`가 나오면 안 된다.
- 계속 같은 로그가 나오면 Xcode가 최신 프로젝트가 아니라 이전 프로젝트/이전 DerivedData/다른 경로의 앱을 빌드 중인 것이다.
