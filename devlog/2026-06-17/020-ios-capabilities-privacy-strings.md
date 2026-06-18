# App Store capability 범위 및 iOS 개인정보 목적 문구 정리

- 날짜: 2026-06-17
- 작업 ID: 020
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"capability 여기에서 더 킬건 없어?"

## 변경 요약

현재 앱 기능 기준으로 Apple Developer capability는 HealthKit만 켜는 것으로 정리했다. Capability는 아니지만 iOS 심사와 런타임 권한에 필요한 카메라, 사진 보관함, 마이크, 위치 목적 문구를 `Info.plist`에 추가했다.

## 변경 파일

- `ios/App/App/Info.plist`
  - `NSCameraUsageDescription` 추가
  - `NSPhotoLibraryUsageDescription` 추가
  - `NSMicrophoneUsageDescription` 추가
  - `NSLocationWhenInUseUsageDescription` 추가
- `docs/app-store-release-checklist-2026-06-17.md`
  - HealthKit만 켜고, Associated Domains/Push Notifications/Sign in with Apple/In-App Purchase/Background Modes 등은 구현 전까지 끄는 기준을 추가했다.
  - Capability와 Info.plist 개인정보 목적 문구를 분리해 정리했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.

## 확인 결과

- 네이티브 iOS 코드는 `RunningMateHealthKitPlugin`만 별도 Apple capability가 필요했다.
- 앱 화면에는 `image/*`, `image/*,video/*` 파일 업로드가 있고, 날씨용 `navigator.geolocation` 사용이 있어 카메라/사진/마이크/위치 목적 문구가 필요하다고 판단했다.
- Push/APNs, Associated Domains, Sign in with Apple, IAP, Background Modes 구현은 현재 코드에서 확인되지 않았다.

## 검증

- Apple 공식 capability 문서와 Info.plist privacy key 문서를 확인했다.
- `python plistlib` 기반 `Info.plist` 파싱 검증 성공. 이 서버에는 `plutil`이 없어 fallback으로 확인했다.
- `grep -nE "NSCameraUsageDescription|NSPhotoLibraryUsageDescription|NSMicrophoneUsageDescription|NSLocationWhenInUseUsageDescription|com.apple.developer.healthkit" ios/App/App/Info.plist ios/App/App/App.entitlements`로 반영 확인.
- `git diff --check -- ios/App/App/Info.plist docs/app-store-release-checklist-2026-06-17.md devlog.md devlog/2026-06-17/020-ios-capabilities-privacy-strings.md` 통과.
