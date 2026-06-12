# 목표 체중 저장 전용 API 분리

- **ID**: 012
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장이 기존 `/api/weights` 라우트와 날짜 상세 라우트 구조에 영향을 받을 수 있어, 목표 체중 설정만 담당하는 `/api/weight-settings` 라우트를 추가했다. 체중 화면의 목표 저장 버튼과 초기 목표 설정 로드를 새 라우트로 연결했다.

## 원문 요청사항
```text
여전히 목표가 저장이 안돼.
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장 요청을 `/api/weight-settings`로 변경하고 초기 설정 전용 로드 추가
- `src/route/api.weight-settings/app.json`: 목표 체중 설정 전용 라우트 추가
- `src/route/api.weight-settings/controller.py`: 목표 체중 설정 GET/POST/PATCH 처리 추가
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/012-weight-target-settings-route.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.weight-settings/controller.py project/main/src/route/api.weights/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
