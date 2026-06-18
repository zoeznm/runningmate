# App ID 생성 이후 Xcode/TestFlight/App Review 진행 순서 보강

- 날짜: 2026-06-17
- 작업 ID: 021
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"그러면 다 만들었어 그 후엔 뭘 해야돼?"

## 변경 요약

Apple Developer 계정, Bundle ID, HealthKit capability, 운영 도메인 확인이 끝난 다음 바로 진행할 Mac/Xcode/App Store Connect/TestFlight/App Review 순서를 배포 체크리스트에 추가했다.

## 변경 파일

- `docs/app-store-release-checklist-2026-06-17.md`
  - "지금부터 바로 할 일" 섹션을 추가했다.
  - Mac에서 `npm install`, `npm run ios:sync`, `npm run ios:open` 후 Xcode Signing, 실기기 실행, Archive, App Store Connect 업로드, TestFlight 내부 테스트, 심사 제출로 이어지는 순서를 정리했다.
  - App Review Notes 예시를 추가했다.
  - TestFlight 내부 테스터와 심사 제출 공식 문서 링크를 추가했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.

## 확인 결과

- Apple 공식 Xcode 배포, 빌드 업로드, TestFlight 내부 테스터, App Review 제출 문서를 기준으로 순서를 확인했다.
- 현재 프로젝트는 Linux 서버에서 Archive/upload를 완료할 수 없으므로 Mac/Xcode 단계로 명확히 분리했다.

## 검증

- `git diff --check -- docs/app-store-release-checklist-2026-06-17.md devlog.md devlog/2026-06-17/021-after-app-id-next-steps.md` 통과.
