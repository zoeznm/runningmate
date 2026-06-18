# iOS 네이티브 앱 아이콘 최신 브랜드 아이콘으로 교체

- 날짜: 2026-06-18
- 작업 ID: 006
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"앱 아이콘을 보니까 옛날 아이콘이던데 왜 그게 된거지? 왜 옛날 아이콘을 쓰는거지?"

## 확인

- 웹/PWA 아이콘은 `src/assets/brand/icon-512.png`의 러닝메이트 러너 아이콘을 사용하고 있었다.
- iOS 네이티브 앱 아이콘은 웹 manifest 아이콘이 아니라 `ios/App/App/Assets.xcassets/AppIcon.appiconset`의 asset catalog를 사용한다.
- 해당 iOS asset catalog 안의 아이콘 파일들이 기존 `M` 형태의 구형 아이콘으로 남아 있었다.
- `npm run ios:sync`는 웹 번들과 Capacitor 설정을 동기화하지만, 기존 iOS AppIcon asset catalog를 자동으로 새 웹 아이콘으로 재생성하지 않는다.

## 변경

- `src/assets/brand/icon-512.png`를 기준으로 iOS AppIcon asset catalog의 모든 참조 PNG를 다시 생성했다.
- `Contents.json`이 참조하는 `icon-20.png`, `icon-29.png`, `icon-40.png`, `icon-58.png`, `icon-60.png`, `icon-76.png`, `icon-80.png`, `icon-87.png`, `icon-120.png`, `icon-152.png`, `icon-167.png`, `icon-180.png`, `icon-1024.png`를 최신 러닝메이트 아이콘으로 교체했다.
- 미참조 잔여 파일인 `AppIcon-512@2x.png`도 같은 최신 아이콘으로 맞췄다.

## 적용 방법

1. Mac 프로젝트에 최신 변경을 반영한다.
2. `npm run ios:sync`를 실행한다.
3. Xcode에서 `Product > Clean Build Folder`를 실행한다.
4. iPhone에 설치된 기존 앱을 삭제한다.
5. Xcode에서 다시 Run한다.

## 주의

- iPhone 홈 화면 아이콘은 캐시가 강하게 남을 수 있어 앱 삭제 후 재설치가 필요하다.
- App Store 제출용 1024 아이콘은 현재 512 원본을 기준으로 생성했으므로, 더 선명한 마케팅 아이콘이 필요하면 원본 1024 PNG를 별도로 준비하는 것이 좋다.
