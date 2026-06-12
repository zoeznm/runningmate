# 030. 온보딩 건너뛰기 확인 모달 및 즉시 완료 처리

- 날짜: 2026-06-09
- 리뷰 ID: nezihocmsgkkkpynskojpstxfluaicmw
- 요청자: 김보미

## 사용자 원 요청

온보딩에서 건너뛰기 버튼을 눌러도 실제 건너뛰기가 아니라 다음으로 넘어가는 문제가 있음. 건너뛰기 버튼을 누르면 "가이드를 넘어가시겠습니까?" 같은 안내 모달을 띄우고, 확인하면 바로 온보딩을 끝내도록 수정 요청.

## 변경 파일

- `src/app/page.dashboard/view.ts`
  - `건너뛰기` 동작을 다음 단계 이동에서 확인 모달 표시로 변경.
  - `cancelOnboardingSkip`, `confirmOnboardingSkip` 추가.
  - 스킵 확인 시 `onboarded=true`만 저장하고 온보딩을 닫도록 `finishOnboarding(skipGuide)` 분기 추가.
  - 일반 완료는 기존처럼 목표 저장, 프로필 저장, 오늘 기록 화면 이동을 유지.

- `src/app/page.dashboard/view.pug`
  - 온보딩 내부에 건너뛰기 확인 모달 추가.
  - 문구: "가이드를 건너뛸까요? 지금 건너뛰면 온보딩은 완료 처리되고, 다음부터는 바로 앱을 사용할 수 있어요."
  - 액션: "계속 보기", "건너뛰기".

- `src/app/page.dashboard/view.scss`
  - 건너뛰기 확인 모달 배경, 패널, 아이콘, 버튼 스타일 추가.

- `devlog.md`
  - 이번 작업 요약 행 추가.

- `devlog/2026-06-09/030-dashboard-onboarding-skip-confirm.md`
  - 이번 작업 상세 기록 추가.

## 확인 결과

- `wiz_project_build(clean=false)` 실행 성공.
- `diff --check` 통과.
- `skipOnboardingStep`가 더 이상 다음 단계로 이동하지 않고 확인 모달을 표시함을 코드 검색으로 확인.

## 남은 리스크

- 실제 브라우저에서 클릭 플로우와 모달 시각 상태는 확인하지 못함.
- 스킵 완료는 목표/프로필 추가 설정을 저장하지 않고 `onboarded=true`만 저장하므로, 사용자가 입력 중이던 온보딩 폼 값은 반영되지 않음.
