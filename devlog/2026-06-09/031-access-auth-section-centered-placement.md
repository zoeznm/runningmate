# 031 접근 화면 인증 묶음 중앙 배치 보정

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "여전히 로그인 섹션이 위로 올라가있어 회원가입도 마찬가지이고 다 그래 수정해줘"
- 리뷰 내용: 모바일 접근 화면의 로그인, 회원가입, 비밀번호 찾기 세로 배치를 더 아래쪽으로 체감되도록 보정

## 변경 파일

- `src/app/page.access/view.pug`
- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/031-access-auth-section-centered-placement.md`

## 변경 내용

- 로그인, 비밀번호 찾기, 회원가입 방법 선택처럼 짧은 인증 화면은 `flex-start` + 큰 padding 방식 대신 `justify-content: center`로 화면 중앙 쪽에 배치했다.
- 이메일 회원가입 폼만 긴 입력 흐름으로 보고 `access-shell--signup` 클래스를 유지하도록 템플릿 조건을 정리했다.
- 이메일 회원가입 폼의 시작 위치는 기존보다 아래에서 시작하도록 `108px` 기준 상단 여백을 유지했다.
- 기존 viewport 높이 보정과 하단 배경 보정은 유지했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.pug src/app/page.access/view.scss` 통과
- 빌드 산출물에서 `justify-content:center`, `view === 'signup'` 조건, 회원가입 상단 padding 반영 확인

## 남은 리스크

- 실제 모바일 기기별 체감 위치는 배포 후 육안 확인이 필요하다.
