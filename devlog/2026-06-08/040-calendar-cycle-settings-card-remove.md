# 기록 달력 생리주기 연동 카드 제거

- **ID**: 040
- **날짜**: 2026-06-08
- **유형**: 디자인 수정

## 작업 요약
기록 화면의 달력 탭에서 생리주기 연동 토글 카드 컴포넌트를 제거했다.
생리주기 활성화와 달력 오버레이 제어는 설정 화면의 생리주기 기능 영역에만 남겼다.

## 원문 요청사항
```text
달력에 생리주기 연동 토글이 있고 그 컴포넌트가 있잖아 근데 어차피 설정에서 토글로 활성화 시킬 수 있으니까 여기서는 굳이 또 있을 필요는 없을 거 같애 달력에서는 저 생리주기 연동 토글하는 컴포넌트 없애줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 달력 탭의 생리주기 연동 토글 카드 섹션 제거.
- `src/app/page.dashboard/view.scss`: 달력 카드 전용 selector와 `cycle-switch` 스타일 제거.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/040-calendar-cycle-settings-card-remove.md`: 작업 상세 기록 추가.

## 확인 결과
- `rg`로 달력 카드 전용 selector와 aria-label 참조가 제거된 것을 확인했다.
- `rg`로 설정 화면의 `생리주기 기능` 토글과 `달력 오버레이` 제어가 유지된 것을 확인했다.
- `wiz_project_build(projectName="main", clean=false)` 성공.
