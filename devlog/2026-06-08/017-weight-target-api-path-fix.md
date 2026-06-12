# 목표 체중 저장 API 경로 단일화

- **ID**: 017
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
운영 URL에서 `/api/weight-settings`가 API JSON이 아니라 `index.html`을 반환하는 것을 확인했다. 목표 체중 저장 실패의 직접 원인은 프론트가 등록되지 않은 전용 라우트에 먼저 저장 요청을 보내면서 JSON 파싱 실패가 발생한 것이었다. 목표 체중 저장과 초기 설정 로드를 기존에 운영에서 살아 있는 `/api/weights`로 단일화하고, 사용하지 않는 `api.weight-settings` 라우트를 제거했다.

## 원문 요청사항
```text
왜 계속 목표 체중이 저장이 안되는거야?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장을 `/api/weights` POST로 고정하고 `/api/weight-settings` 초기 로드 제거
- `src/route/api.weight-settings/`: 미사용 전용 라우트 삭제
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/017-weight-target-api-path-fix.md`: 상세 devlog 추가

## 확인 결과
- 운영 `GET /api/weight-settings`가 `text/html` `index.html`을 반환하는 것 확인
- 운영 `POST /api/weights`가 JSON 응답을 반환하는 것 확인
- `python -m py_compile project/main/src/route/api.training-load/controller.py project/main/src/route/api.weights/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
- 소스/빌드 대상에서 `/api/weight-settings` 참조가 남아 있지 않은 것 확인
