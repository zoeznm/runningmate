# 목표 체중 저장 및 훈련 부하 API 오류 방어

- **ID**: 014
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장 시 `/api/weight-settings` 호출이 실패하면 기존 `/api/weights` 목표 저장 분기로 fallback하도록 변경했다. `/api/training-load`와 `/api/weight-settings` 라우트는 내부 계산/파일 처리 오류가 발생해도 HTML 500 페이지가 아니라 JSON 응답으로 끝나도록 방어했다.

## 원문 요청사항
```text
Uncaught SyntaxError: Unexpected token '<'이 오류 이해하기
api/training-load:1  Failed to load resource: the server responded with a status of 500 ()

이런 에러가 뜨고 목표 체중을 저장하지 못했어. 라고 떠
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장을 `jsonRequest` 기반으로 변경하고 실패 시 `/api/weights` fallback 추가
- `src/route/api.training-load/controller.py`: 훈련 부하 계산 실패 시 JSON 기본값 응답 추가
- `src/route/api.weight-settings/controller.py`: 목표 체중 설정 라우트 예외를 JSON 실패 응답으로 처리
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/014-weight-target-api-error-guard.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.training-load/controller.py project/main/src/route/api.weight-settings/controller.py project/main/src/route/api.weights/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
