# iOS sync/clean/delete와 소스 최신화 범위 구분 문서화

- 날짜: 2026-06-18
- 작업 ID: 009
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"npm run ios:sync, Xcode Clean Build Folder, 앱 삭제 후 재설치가 필요합니다. 이거를 계속 하는데도 왜 예전 코드가 보이는거야?"

## 설명

- `npm run ios:sync`는 Capacitor 설정과 웹 번들을 iOS 프로젝트로 동기화한다.
- Xcode `Clean Build Folder`는 빌드 산출물을 지운다.
- iPhone 앱 삭제는 기기에 설치된 앱과 앱 컨테이너를 지운다.
- 위 작업들은 Mac 로컬의 Swift 소스 파일 자체를 최신 버전으로 받아오지 않는다.

## 확인 기준

- `ios/App/App/RunningMateBridgeViewController.swift`에 `descriptor.serverURL = nil`이 없으면 Mac 프로젝트 소스가 아직 예전 상태다.
- 이 상태에서는 sync/clean/delete를 반복해도 같은 예전 Swift 코드로 다시 빌드된다.

## 반영

- `docs/ios-initial-loading-troubleshooting-2026-06-18.md`에 sync/clean/delete가 소스 최신화를 대신하지 않는다는 설명을 추가했다.
