# Bundle ID 확정안 및 외부 접속/개발자 계정 상태 반영

- 날짜: 2026-06-17
- 작업 ID: 019
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"Bundle ID가 뭐고 확정을 어떻게 짓는거야? 그리고 외부 Mac/iPhone으로 해보니까 잘 들어가지던데 그리고 나 Apple Developer 이거 유료계정 있어"

## 변경 요약

Bundle ID의 의미와 확정 기준을 앱스토어 배포 체크리스트에 보강하고, 러닝메이트의 확정안으로 `com.myrunningmate.run`을 코드에 반영했다. 외부 Mac/iPhone 접속 정상과 Apple Developer 유료 계정 보유 상태도 문서에 반영했다.

## 변경 파일

- `capacitor.config.json`
  - `appId`를 `net.seasonai.run.matomabo`에서 `com.myrunningmate.run`으로 변경했다.
- `ios/App/App.xcodeproj/project.pbxproj`
  - Debug/Release `PRODUCT_BUNDLE_IDENTIFIER`를 `com.myrunningmate.run`으로 변경했다.
- `docs/app-store-release-checklist-2026-06-17.md`
  - Bundle ID 설명, 확정 기준, 권장값, Apple Developer 등록 절차를 보강했다.
  - Apple Developer 유료 계정 보유와 외부 Mac/iPhone 접속 정상 상태를 반영했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.

## 확인 결과

- Apple 공식 문서 기준 Explicit App ID의 Bundle ID는 Xcode target의 Bundle ID와 일치해야 함을 확인했다.
- HealthKit을 쓰는 앱이므로 wildcard가 아니라 Explicit App ID로 등록해야 하는 흐름을 문서화했다.
- `capacitor.config.json`과 Xcode project의 Bundle ID가 같은 값인지 확인했다.

## 검증

- `python -m json.tool capacitor.config.json` 성공.
- `grep -nE "appId|PRODUCT_BUNDLE_IDENTIFIER" capacitor.config.json ios/App/App.xcodeproj/project.pbxproj`로 `com.myrunningmate.run` 반영 확인.
- `git diff --check -- capacitor.config.json ios/App/App.xcodeproj/project.pbxproj docs/app-store-release-checklist-2026-06-17.md devlog.md devlog/2026-06-17/019-bundle-id-decision.md` 통과.
