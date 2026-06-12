# 체중 달력 입력 및 목표 체중 설정 추가

- **ID**: 007
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
체중 화면에 월별 달력을 추가해 날짜별 체중 기록을 선택/입력할 수 있게 했다. 저장된 체중은 달력 셀에 kg 값으로 표시되며, 선택한 날짜의 현재 체중을 바로 저장할 수 있다. 목표 체중 입력과 사용자별 목표 체중 저장 API를 추가하고 현재 체중 기준으로 목표까지 남은 kg를 요약 카드에 표시했다.

## 원문 요청사항
```text
체중도 달력 부분이랑 동일하게 달력 나오게 해주고 날마다 체중 입력하게 해줘 똑같이 대신 달력이랑 다른 점은 체중 화면에서 현재 체중을목표 체중 입력하게 해주고 현재 체중에서 몇키로를 빼야되는지 나오게 해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 체중 달력 셀, 선택일 입력, 목표 체중 상태/저장, 목표까지 남은 kg 계산 추가
- `src/app/page.dashboard/view.pug`: 체중 달력 UI, 선택일 체중 입력 패널, 목표 체중 입력 카드 추가
- `src/app/page.dashboard/view.scss`: 체중 달력 셀, 목표 카드, 선택일 입력 패널 스타일 추가
- `src/model/runningmate.py`: 사용자별 목표 체중 설정 저장소와 로드/저장 로직 추가
- `src/route/api.weights/controller.py`: 체중 설정 GET 응답 포함 및 PATCH 저장 처리 추가
- `src/route/api.weights.detail/controller.py`: 체중 삭제 응답에 설정 포함
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/007-weight-calendar-target.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/model/runningmate.py project/main/src/route/api.weights/controller.py project/main/src/route/api.weights.detail/controller.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
