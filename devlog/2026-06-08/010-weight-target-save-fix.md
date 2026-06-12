# 목표 체중 저장 POST 처리 보강

- **ID**: 010
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장 버튼이 기존 `PATCH /api/weights` 호출에 의존하던 부분을 `POST /api/weights` 호출로 변경했다. 백엔드 `/api/weights` POST 분기에서 `mode: target_weight` 또는 목표 체중 필드가 있는 요청은 일반 체중 기록 저장이 아니라 목표 체중 설정 저장으로 처리하도록 분기했다.

## 원문 요청사항
```text
목표 체중을 입력하고 저장하기 버튼을 눌러도 저장이 아노대 수정해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장 요청을 PATCH에서 POST로 변경하고 `mode: target_weight` payload 추가
- `src/route/api.weights/controller.py`: POST 목표 체중 저장 분기 추가 및 일반 체중 기록 저장 분리
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/010-weight-target-save-fix.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.weights/controller.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
