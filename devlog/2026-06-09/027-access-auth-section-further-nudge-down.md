# 027 접근 화면 인증 묶음 위치 추가 하향 조정

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "좀 더 아래로 내려줘"
- 리뷰 내용: 모바일 접근 화면의 인증 묶음을 이전 조정값보다 한 단계 더 아래로 이동

## 변경 파일

- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/027-access-auth-section-further-nudge-down.md`

## 변경 내용

- 로그인/비밀번호 찾기 계열의 상단 여백을 `88px` 기준에서 `108px` 기준으로 늘렸다.
- 회원가입 계열의 상단 여백을 `56px` 기준에서 `72px` 기준으로 늘렸다.
- 기존 viewport 높이 보정, 배경 보정, 상단 흐름 정렬은 유지했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.scss` 통과
- 빌드 산출물에서 `max(108px, ...)`, `max(72px, ...)` padding 반영 확인

## 남은 리스크

- 실제 모바일 기기별 체감 위치는 배포 후 육안 확인이 필요하다.
