# 생리주기 컨디션 직접 입력 전환

- **ID**: 035
- **날짜**: 2026-06-08
- **유형**: 기능 개선

## 작업 요약
주기별 러닝 패턴 카드의 컨디션 분포가 러닝 기록 문구나 페이스에서 자동 추론되지 않도록 변경했다.
생리주기 기록 입력 시 사용자가 컨디션 이모지를 직접 선택하고, 저장된 값만 분석 카드와 API 컨텍스트에 반영되도록 수정했다.

## 원문 요청사항
```text
얘는 사용자가 직접 입력하게 하는게 낫겠지?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: `condition_emoji` 필드, 컨디션 선택 상태, 저장 payload, 직접 입력 기반 분포 집계, AI 안내 문구 수정.
- `src/app/page.dashboard/view.pug`: 생리주기 기록 입력 폼에 컨디션 이모지 선택 버튼과 최근 기록 표시 추가.
- `src/app/page.dashboard/view.scss`: 컨디션 선택 버튼과 최근 기록 표시 스타일 추가.
- `src/model/runningmate.py`: `condition_emoji` 정규화/저장 및 단계별 컨디션 분포 API 컨텍스트 추가.
- `src/route/api.chat/controller.py`: 주기 단계 안내 문구를 "입력한 기록 기준"으로 조정.
- `devlog.md`, `devlog/2026-06-08/034-cycle-feature-initial-catchup.md`, `devlog/2026-06-08/035-cycle-condition-direct-input.md`: 작업 이력 기록.

## 확인 결과
- Pug 템플릿 컴파일 성공.
- `python -m py_compile src/model/runningmate.py src/route/api.cycles/controller.py src/route/api.chat/controller.py` 성공.
- `git diff --check` 성공.
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `wiz bundle --project=main` 성공.
- 산출물에서 `cycle-condition`, `condition_emoji`, `입력한 기록 기준` 반영을 검색 확인.
- 로컬 API는 로그인 세션 없이 `/api/cycles` 접근 시 401을 반환해 민감 데이터 접근 차단을 확인했다.
