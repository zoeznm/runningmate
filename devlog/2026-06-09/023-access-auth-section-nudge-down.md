# 023 접근 화면 인증 묶음 위치 소폭 하향 조정

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "너무 위로 올라간 느낌이야 살짝 아래로 내려줘"
- 리뷰 내용: 모바일 접근 화면의 로그인, 회원가입, 비밀번호 찾기 묶음을 현재 위치에서 소폭 아래로 조정

## 변경 파일

- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/023-access-auth-section-nudge-down.md`

## 변경 내용

- 로그인/비밀번호 찾기 계열의 상단 여백을 `76px` 기준에서 `88px` 기준으로 늘렸다.
- 회원가입 계열의 상단 여백을 `44px` 기준에서 `56px` 기준으로 늘렸다.
- 기존 viewport 높이 보정과 배경 보정 구조는 유지했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.scss` 통과
- 빌드 산출물에서 `max(88px, ...)`, `max(56px, ...)` padding 반영 확인

## 남은 리스크

- 실제 모바일 기기별 체감 위치는 배포 후 육안 확인이 필요하다.
