# 기록 달력 주기 출처/음악 섹션 제거 및 주기 기록 위치 이동

- **ID**: 044
- **날짜**: 2026-06-08
- **유형**: 디자인 수정

## 작업 요약
기록 화면 달력 탭에서 생리주기 범례 아래의 입력/자동 예상 출처 칩을 제거했다.
날짜 선택 시 표시되는 주기 기록 패널은 기록 업로드 폼 아래로 이동했고, 하단의 들은 음악 업로드 섹션은 제거했다.

## 원문 요청사항
```text
생리기 난포기 배란기 황체기 아래에 입력, 자동예상 이렇게 뜨는거 없애줘 그리고 날짜 클릭하면 주기 기록 섹션이 나오는데 그거 기록 업로드 아래로 내려줘 그리고 맨 아래에 들은 음악 섹션은 없애줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 생리주기 출처 칩 제거, 주기 기록 패널을 기록 업로드 아래로 이동, 들은 음악 업로드 섹션 제거.
- `src/app/page.dashboard/view.scss`: 생리주기 출처 칩 및 제거된 업로드 하단 카드 전용 스타일 정리.
- `src/app/page.dashboard/view.ts`: 달력 셀/선택 날짜 문구에서 입력/자동 예상 출처 라벨 제거.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/044-calendar-cycle-log-upload-order.md`: 작업 상세 기록 추가.

## 확인 결과
- `rg`로 `cycle-source-legend`, `cycle-source-chip`, `자동 예상`, `span 들은 음악`, `upload-subsection-card` 참조가 제거된 것을 확인했다.
- `rg`로 `기록 업로드`가 `주기 기록`보다 먼저 배치된 것을 확인했다.
- `wiz_project_build(projectName="main", clean=false)` 성공.
