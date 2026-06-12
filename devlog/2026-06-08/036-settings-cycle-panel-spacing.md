# 설정 생리주기 패널 간격 및 라이트 모드 버튼 톤 조정

## 요청

생리주기 기능 표시 영역의 평균 주기, 현재 단계, 달력 오버레이 ON, 주기 데이터 삭제, 주기 기록 없음 사이 간격이 좁으니 넓히고, 라이트 모드에서 달력 오버레이 ON과 주기 데이터 삭제 버튼이 너무 밝게 보이는 문제를 수정.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `devlog.md`
- `devlog/2026-06-08/036-settings-cycle-panel-spacing.md`

## 변경 내용

- 설정 인라인 패널 안의 생리주기 요약칩 간격과 패딩을 늘렸다.
- 생리주기 액션 버튼 행에 여백과 버튼 높이를 추가해 상태 문구와의 간격을 넓혔다.
- 라이트 모드에서 달력 오버레이 버튼과 주기 데이터 삭제 버튼의 배경색을 더 차분한 톤으로 조정했다.

## 확인

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `node --check bundle/www/main.js` 성공.
- `bundle/www/main.js`에 설정 생리주기 패널 CSS와 라이트 모드 색상 오버라이드가 반영된 것을 확인.
- `src/app/page.dashboard/view.html` 생성 부산물 없음.
- 제거된 `notification-settings.js/css` 정적 파일이 다시 생성되지 않은 것을 확인.
