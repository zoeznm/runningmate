# 011 접근 화면 모바일 하단 여백 및 세로 정렬 보정

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "이게 실제로 핸드폰 화면에서 보면 하단에 빈공간이 있고 위로 올라가져보이는데 왜그러는거야?"
- 리뷰 내용: 모바일 앱 화면에서 접근 페이지가 위로 떠 보이고 하단 여백이 크게 남는 현상 확인 및 수정

## 변경 파일

- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/011-access-mobile-bottom-spacing.md`

## 원인

- 접근 화면 셸이 `100dvh` 기반 `min-height`만 사용해 모바일 브라우저/WebView의 실제 표시 높이와 어긋날 수 있었다.
- 폼 영역이 남은 영역 안에서 세로 가운데 정렬되어, 로그인/비밀번호 찾기처럼 짧은 화면에서 하단 빈공간이 크게 보였다.

## 변경 내용

- 접근 화면 높이를 `100svh` 우선 기준으로 바꾸고, 미지원 환경은 `100dvh`로 대체했다.
- 바깥 페이지 스크롤 대신 모바일 앱 셸 내부에서 스크롤되도록 바꿨다.
- 짧은 인증 화면은 앱 셸 하단 쪽으로 배치하고, 회원가입 화면은 기존처럼 상단부터 자연스럽게 스크롤되도록 분기했다.
- 하단 safe-area 패딩을 줄여 실제 기기에서 불필요하게 큰 빈공간이 생기지 않도록 조정했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.scss` 통과
- 빌드 산출물에서 `100svh`, `--access-viewport-height`, `justify-content: flex-end` 반영 확인

## 남은 리스크

- 실제 iOS/Android WebView에서 홈 인디케이터, 상태바, 키보드 표시 상태별 최종 시각 확인은 별도 필요하다.
