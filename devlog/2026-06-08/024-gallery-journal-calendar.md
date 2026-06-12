# 갤러리 일기 탭 달력 표시

- **ID**: 024
- **날짜**: 2026-06-08
- **유형**: 디자인/UX 수정
- **리뷰 ID**: eyyircqyzcnwbpxkpcnufiexkxuycohf

## 작업 요약
기록 > 갤러리 > 일기 탭의 러닝 일기 목록을 월간 달력 중심 UI로 변경했다. 일기가 작성된 날짜는 원형 표시와 개수 배지로 구분하고, 날짜를 누르면 해당 날짜의 작성된 일기를 하단에 보여주며 기존 일기 상세 모달도 열 수 있도록 했다.

## 원문 요청사항
```text
기록에서 갤러리 탭에서 일기 보여주는 부분 일기를 달력으로 표시해서 일기가 써진 날짜에는 뭐 원으로 표시해가지고 그거 누르면 작성한 일기 보여주게 하는게 어떨까?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 갤러리 일기 탭의 카드 목록을 일기 달력과 선택 날짜 일기 패널로 교체.
- `src/app/page.dashboard/view.ts`: 일기 전용 달력 셀, 선택 날짜 상태, 월별 일기 셀/선택 일기 파생 로직 추가.
- `src/app/page.dashboard/view.scss`: 일기 달력 원형 표시, 개수 배지, 선택 일기 카드 스타일 추가.
- `devlog.md`: 024 작업 요약 행 추가.
- `devlog/2026-06-08/024-gallery-journal-calendar.md`: 작업 상세 기록 추가.

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공.
- `rg -n "JournalCalendarCell|journal-calendar|journal-selected|journal-date-ring" src/app/page.dashboard/view.ts src/app/page.dashboard/view.pug src/app/page.dashboard/view.scss`로 반영 위치 확인.

## 남은 리스크
브라우저 실화면 캡처 검증은 수행하지 않았다.
