# 생리주기 자동 예상과 직접 입력 구분

- **ID**: 037
- **날짜**: 2026-06-08
- **유형**: 기능 개선

## 작업 요약
생리 시작/종료일을 직접 입력한 뒤 다음 달부터 평균 주기로 단계가 자동 예상되도록 확장했다.
달력에서는 직접 입력 구간과 자동 예상 구간을 구분해 표시하고, 선택한 날짜의 주기 문구도 `입력` 또는 `자동 예상` 기준으로 보여준다.

## 원문 요청사항
```text
생리 주기 입력을 하면 다음달부터는 자동으로 생리 주기를 알려주면 어떨까? 예를들어서 내가 이번 6월달 생리 주기를 입력을 한거야 그러면 그 다음날부터는 황체기, 배란기, 난포기, 생리기를 알려주는거야 자동으로 그리고 이제 그거랑 내가 입력하는거랑 두개가 있는거지
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 주기 달력 정보에 `manual/predicted` 출처를 추가하고, 마지막 생리 시작일 이후 6주기까지 자동 예상 단계를 생성하도록 수정.
- `src/app/page.dashboard/view.pug`: 달력 오버레이 범례에 `입력`과 `자동 예상` 구분 표시 추가.
- `src/app/page.dashboard/view.scss`: 자동 예상 셀은 더 은은하게, 직접 입력 셀은 링으로 구분되도록 스타일 추가.
- `src/model/runningmate.py`: 오늘 주기 단계 계산도 마지막 입력 이후 6주기 범위에서는 평균 주기로 자동 산출하도록 수정.
- `devlog.md`, `devlog/2026-06-08/037-cycle-prediction-manual-source.md`: 작업 이력 기록.

## 확인 결과
- Pug 템플릿 컴파일 성공.
- `python -m py_compile src/model/runningmate.py src/route/api.chat/controller.py` 성공.
- `git diff --check` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- 빌드 산출물에서 `자동 예상`, `cycle-source`, `phase_index` 반영을 검색 확인.
