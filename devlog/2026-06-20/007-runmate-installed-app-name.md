# 설치 앱 이름 RunMate 적용

## 배경
- Safari 홈 화면 추가와 Xcode/iOS 실기기 테스트 시 홈 화면에 표시되는 앱 이름을 `RunMate`로 통일해야 했다.

## 변경
- 웹 문서의 `title`, `application-name`, `apple-mobile-web-app-title`을 `RunMate`로 변경했다.
- PWA manifest의 `name`, `short_name`을 `RunMate`로 변경했다.
- Capacitor 설정과 iOS `Info.plist`의 표시 이름을 `RunMate`로 변경했다.
- PWA 캐시 갱신 버전을 변경해 홈 화면 관련 메타데이터 갱신을 유도했다.

## 확인
- Safari 홈 화면 추가에서 참조하는 Apple 메타 태그와 manifest 이름이 모두 `RunMate`를 반환하도록 정리했다.
- iOS 네이티브 표시 이름은 `CFBundleDisplayName`과 `CFBundleName` 모두 `RunMate`로 맞췄다.
