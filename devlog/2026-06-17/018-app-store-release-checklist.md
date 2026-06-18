# iOS 앱스토어 첫 배포 순서 문서화 및 운영 도메인 반영

- 날짜: 2026-06-17
- 작업 ID: 018
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"이제 도메인 연결하고 그랬는데 애플 앱스토어에 배포를 하고싶거든? 방법이랑 순서 좀 알려줘 나한테 남은 순서"

## 변경 요약

새 운영 도메인 `https://run.myrunningmate.com/` 기준으로 Capacitor iOS shell 접속 URL을 갱신하고, Apple App Store 첫 배포까지 남은 순서를 프로젝트 문서로 정리했다.

## 변경 파일

- `capacitor.config.json`
  - iOS WebView 대상 URL을 `https://run.myrunningmate.com/dashboard`로 변경했다.
- `docs/app-store-release-checklist-2026-06-17.md`
  - 현재 프로젝트 상태, 첫 업로드 전 결정 사항, 운영 도메인 점검, Mac/Xcode 준비, App ID, App Store Connect, Archive, TestFlight, 심사 제출 순서를 문서화했다.
  - Bundle ID 확정, HealthKit, 계정 삭제, App Privacy, 스크린샷, 심사용 테스트 계정 리스크를 별도로 정리했다.
- `README.md`
  - iOS shell 섹션과 문서 허브에 앱스토어 배포 체크리스트 링크를 추가했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.

## 확인 결과

- 기존 iOS 프로젝트가 `ios/`에 존재하는 것을 확인했다.
- `ios/App/App/Assets.xcassets/`에 AppIcon과 Splash 자산이 있는 것을 확인했다.
- `ios/App/App/App.entitlements`에 HealthKit entitlement가 있는 것을 확인했다.
- `ios/App/App/Info.plist`에 HealthKit 사용 목적 문구가 있는 것을 확인했다.
- 현재 Xcode 프로젝트의 Bundle ID가 `net.seasonai.run.matomabo`, version `1.0`, build `1`, iOS deployment target `15.0`인 것을 확인했다.
- 기존 devlog에서 `/privacy`, `/terms`, `/account/delete` 공개 페이지 구현 이력을 확인했다.
- `http://127.0.0.1:3000/healthz`와 `/dashboard`가 정상 응답하는 것을 확인했다.
- `--resolve run.myrunningmate.com:443:127.0.0.1` 기준으로 `/healthz`, `/dashboard`, `/sw.js`, `/api/auth/login`이 nginx를 거쳐 정상 응답하는 것을 확인했다.
- 이 서버에서 공인 DNS `49.165.96.213` 경유 `https://run.myrunningmate.com/*` curl은 timeout이었다. 외부 브라우징 경로에서는 루트 HTML이 열려 hairpin NAT 또는 서버 내부 네트워크 경로 이슈 가능성으로 문서에 남겼다.

## 검증

- Apple Developer, App Store Connect, Capacitor 공식 문서를 확인해 배포 순서를 작성했다.
- `python -m json.tool capacitor.config.json` 성공.
- `git diff --check -- capacitor.config.json README.md docs/app-store-release-checklist-2026-06-17.md devlog.md devlog/2026-06-17/018-app-store-release-checklist.md` 통과.
