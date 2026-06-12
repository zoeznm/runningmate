# 설정 목표 섹션 라벨 문구 변경

## 요청

설정 화면의 `목표&알림` 문구를 `목표`로 변경.

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `devlog.md`
- `devlog/2026-06-09/022-settings-goal-section-label.md`

## 변경 내용

- 설정 화면 섹션 라벨 `목표 & 알림`을 `목표`로 변경했다.

## 확인

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `node --check bundle/www/main.js` 성공.
- `src/app/page.dashboard`와 `bundle/www/main.js`에서 `목표 & 알림` 문구가 남아있지 않은 것을 확인.
- `src/app/page.dashboard/view.html` 생성 부산물 없음.
- `notification-settings.js/css` 정적 파일 재생성 없음.
