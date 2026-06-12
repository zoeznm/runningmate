# 008 앱 배포용 접근 화면 디자인 및 이메일 가입 흐름 보강

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "이거 내가 앱으로 배포할건데 로그인 페이지를 좀 더 잘 만들어줄 수 있어?"
- 리뷰 내용: 로그인 페이지, 회원가입 페이지, 비밀번호 찾기 페이지 디자인이 이상해 수정 필요

## 변경 파일

- `src/app/page.access/view.pug`
- `src/app/page.access/view.scss`
- `src/app/page.access/view.ts`
- `devlog.md`
- `devlog/2026-06-09/008-access-auth-page-redesign.md`

## 변경 내용

- `/access` 화면을 앱 배포에 맞는 다크 인증 화면으로 재구성했다.
- 로그인, 회원가입 방식 선택, 이메일 회원가입, 비밀번호 찾기, 비밀번호 재설정, 약관 모달을 같은 스타일 시스템으로 정리했다.
- 모바일에서 긴 회원가입 폼이 잘리지 않도록 `100dvh` 고정/숨김 중심 구조를 스크롤 가능한 레이아웃으로 변경했다.
- 이메일 회원가입 단계에 이메일 입력 및 중복확인 상태 표시를 추가하고, 가입 payload에 이메일을 포함했다.
- 로그인 입력 문구를 아이디 또는 이메일 기준으로 보정했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.pug src/app/page.access/view.scss src/app/page.access/view.ts` 통과

## 남은 리스크

- 실제 기기와 운영 URL에서의 시각 회귀 확인은 별도 필요하다.
