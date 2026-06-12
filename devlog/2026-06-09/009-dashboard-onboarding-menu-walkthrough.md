# 009. 회원가입 온보딩 메뉴별 안내 흐름 개편

- 날짜: 2026-06-09
- 리뷰 ID: nezihocmsgkkkpynskojpstxfluaicmw
- 요청자: 김보미

## 사용자 원 요청

회원가입 후 온보딩에서 "나이키런 캡처" 표현은 나이키런을 쓰지 않는 사용자에게 혼란을 줄 수 있으니 "운동 기록 사진 업로드"처럼 범용 표현으로 바꾸고, 권한 확인 단계는 제거하며, 실제 앱 메뉴를 하나씩 보여주면서 설명하는 흐름으로 바꾸고 싶다는 요청.

## 변경 파일

- `src/app/page.dashboard/view.ts`
  - 온보딩 단계 키와 문구를 `기록`, `목표`, `커뮤니티`, `AI`, `설정` 메뉴 설명 중심으로 재구성.
  - "나이키런 캡처" 표현을 "운동 기록 사진" 중심의 범용 표현으로 변경.
  - 권한 확인 온보딩 단계를 제거.
  - 온보딩 단계 이동 시 실제 대시보드의 활성 화면을 해당 메뉴로 전환하도록 `onboardingScreenMap`, `moveOnboardingTo`, `applyOnboardingScreen` 추가.
  - 설정 화면 알림 권한 호출에 맞춰 권한 요청 메서드를 `requestNotificationPermission`으로 정리.

- `src/app/page.dashboard/view.pug`
  - 기존 추상 가이드/권한 확인 슬라이드 마크업 제거.
  - 주요 메뉴, 기록 하위 메뉴, 목표 하위 메뉴, 커뮤니티 하위 메뉴, AI/설정 설명 블록 추가.
  - 완료 문구를 오늘 날짜 기록 화면과 운동 기록 사진 업로드 흐름에 맞게 수정.

- `src/app/page.dashboard/view.scss`
  - 온보딩을 전체 화면 차단형에서 실제 앱 화면 위 하단 안내 패널 형태로 조정.
  - 메뉴 안내 칩, 업로드 안내, 메뉴별 프리뷰 행 스타일 추가.
  - 더 이상 사용하지 않는 권한/구 가이드 스타일 제거.

- `devlog.md`
  - 이번 작업 요약 행 추가.

- `devlog/2026-06-09/009-dashboard-onboarding-menu-walkthrough.md`
  - 이번 작업 상세 기록 추가.

## 확인 결과

- `wiz_project_build(clean=false)` 실행 성공.
- 온보딩 코드에서 `나이키런`, `권한을 확인`, `permissions`, `requestOnboardingNotification`, `acknowledgeHealthKit`, `onboardingNotificationText` 잔여 참조가 없음을 확인.

## 남은 리스크

- 실제 브라우저 캡처 기반 시각 확인은 하지 못함.
- 온보딩 하단 패널 높이는 빌드 기준으로만 확인했으며, 작은 모바일 화면에서 텍스트 밀도는 추가 실기기 확인이 필요할 수 있음.
