# 목표 체중 표시 즉시 반영 및 로딩 파싱 보강

- **ID**: 021
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장 후 표시 영역이 계속 `-`로 남는 문제를 보강했다. 저장 버튼을 누르면 검증된 목표값을 화면 상태와 로컬 저장소에 즉시 반영하도록 했고, 새로고침 또는 재진입 시 로컬 목표값을 먼저 불러오도록 했다. 또한 서버 응답이 `settings`, `data.settings`, `data` 형태 중 어디로 내려와도 목표 체중을 정규화해서 적용하도록 체중 저장/삭제/조회 응답 파싱을 보강했다.

## 원문 요청사항
```text
여전히 - 이거 안 없어짐 제발 좀 고쳐봐바
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 즉시 반영, 로컬 저장/복원, 중첩 응답 파싱 보강
- `config/pwa/sw.js`: PWA 캐시 버전을 `runningmate-pwa-v9`로 갱신
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/021-weight-target-optimistic-display.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.weights/controller.py project/main/src/route/api.training-load/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js`에 `runningmate-weight-target-v1`, `data?.settings`, `normalizedWeightTarget` 반영 확인
- 운영 `sw.js` 캐시 버전 `runningmate-pwa-v9` 확인
- 비로그인 상태의 운영 `/api/weights?period=all` 요청이 JSON 401로 응답하는 것 확인
