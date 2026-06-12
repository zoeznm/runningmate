# 010 접근 화면을 모바일 앱 단일 레이아웃으로 재구성

## 사용자 요청

- Review ID: `wkrajahxqesvofpwbyndvvdawqidbmjv`
- 원 요청: "아니 모바일 앱으로 만들건데 왜 저렇게 만든거야 모바일 앱버전으로 만들어줘"
- 리뷰 내용: 로그인, 회원가입, 비밀번호 찾기 화면을 모바일 앱 배포 화면에 맞게 수정 필요

## 변경 파일

- `src/app/page.access/view.pug`
- `src/app/page.access/view.scss`
- `devlog.md`
- `devlog/2026-06-09/010-access-mobile-app-layout.md`

## 변경 내용

- 데스크톱 좌우 분할 히어로와 러닝 통계 영역을 제거했다.
- `/access`를 430px 폭의 단일 모바일 앱 캔버스 중심 레이아웃으로 바꿨다.
- 실제 모바일에서는 전체 화면, 넓은 화면에서는 중앙 모바일 앱 프레임처럼 보이도록 조정했다.
- 로그인, 회원가입, 비밀번호 찾기, 재설정, 약관 모달의 기존 기능 흐름은 유지했다.
- 회원가입처럼 긴 화면은 앱 캔버스 내부에서 스크롤되도록 구성했다.

## 검증

- `wiz_project_build(projectName="main", clean=false)` 성공
- `git diff --check -- src/app/page.access/view.pug src/app/page.access/view.scss src/app/page.access/view.ts` 통과
- 빌드 산출물에서 `app-brand`, `access-shell--signup` 반영 확인

## 남은 리스크

- 운영 URL 배포 후 실제 iOS/Android WebView 또는 Capacitor 앱 화면에서의 최종 시각 확인은 별도 필요하다.
