# 018 접근 화면 인증 섹션 세로 위치 재조정

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "높이 이슈는 사라졌는데 로고, 텍스트들 로그인 섹션이 좀 아래로 내려온 느낌이고, 회원가입/비밀번호 찾기도 하단에 있어서 수정해줘"
- 리뷰 내용: 모바일 접근 화면에서 로그인, 회원가입, 비밀번호 찾기 화면의 세로 위치를 위쪽으로 재조정

## 변경 파일

- `src/app/page.access/view.pug`
- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/018-access-auth-section-vertical-position.md`

## 변경 내용

- `.access-shell`을 하단 정렬(`flex-end`)에서 상단 흐름(`flex-start`)으로 변경했다.
- 로그인/비밀번호 찾기 계열은 상단 safe-area를 고려한 고정 상단 여백으로 조정했다.
- 회원가입과 회원가입 방법 선택 화면은 긴 폼/가입 흐름 특성에 맞춰 더 위에서 시작하도록 별도 상단 여백을 적용했다.
- `signupOptions` 화면도 회원가입 계열 shell 클래스를 사용하도록 템플릿 조건을 확장했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.pug src/app/page.access/view.scss` 통과
- 빌드 산출물에서 `signupOptions` 조건, `justify-content:flex-start`, 신규 상단 padding 반영 확인

## 남은 리스크

- 실제 iOS/Android WebView에서 화면 높이별 최종 체감 위치는 배포 후 육안 확인이 필요하다.
