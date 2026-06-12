# 목표 체중 표시 정규화 수정

- **ID**: 020
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장 후 표시 영역이 `-`로 남을 수 있는 응답 정규화 문제를 수정했다. 저장 응답이 `data` 또는 `settings`로 한 번 더 감싸져 와도 `target_weight_kg`를 찾아 적용하도록 했고, 목표값이 없는 응답으로 기존 목표값을 `null`로 덮어쓰지 않도록 했다. 템플릿 표시 조건도 truthy 체크 대신 `null` 비교로 변경했다.

## 원문 요청사항
```text
여전히 목표체중을 입력해도 목표 체중보여주는 부분에 - 이렇게 보여
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 목표 체중 표시 조건을 `targetWeightKg !== null`로 변경
- `src/app/page.dashboard/view.ts`: 목표 체중 텍스트/입력값 표시 조건 및 중첩 응답 정규화 보강
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/020-weight-target-display-normalization.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.weights/controller.py project/main/src/route/api.training-load/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js` 갱신 확인
- 운영 `sw.js` 캐시 버전 `runningmate-pwa-v8` 유지 확인
