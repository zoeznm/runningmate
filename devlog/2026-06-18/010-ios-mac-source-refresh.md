# Mac Desktop 프로젝트 소스 최신화 필요 조건 문서화

- 날짜: 2026-06-18
- 작업 ID: 010
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"grep -n \"descriptor.serverURL = nil\" ios/App/App/RunningMateBridgeViewController.swift 아무것도 안 나와. 내 생각에는 Mac에 이는 Desktop안에 있는 app 파일을 최신화 시켜주면 되는거 아니야?"

## 결론

- 맞다. Mac의 `/Users/kimbomi/Desktop/app/project/main` 소스 폴더 자체가 최신화되어야 한다.
- `grep` 결과가 없으면 현재 Mac 폴더에는 iOS 원격 URL 차단 Swift 코드가 아직 들어오지 않은 상태다.
- 이 상태에서는 `npm run ios:sync`, Xcode Clean, 앱 삭제를 반복해도 예전 Swift 소스로 다시 빌드된다.

## 반영

- `docs/ios-mac-source-refresh-2026-06-18.md`를 추가해 Mac 프로젝트 소스 최신화 기준과 이후 iOS 재빌드 순서를 문서화했다.
