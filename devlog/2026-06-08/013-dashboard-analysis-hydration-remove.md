# 분석/기록 수분·훈련 부하 UI 제거

- **ID**: 013
- **날짜**: 2026-06-08
- **유형**: UX 수정

## 작업 요약
분석 탭에서 훈련 부하 카드와 수분 섭취 패턴 카드를 제거했다.
기록 화면에서는 저장된 기록의 수분 섭취 표시와 수분 섭취 입력 섹션을 제거하고, 설정의 휴식 추천 설명도 훈련 부하 용어가 노출되지 않도록 조정했다.

## 원문 요청사항
```text
작업 진행해줘

기록에서 분석 탭을 눌러서 보면 훈련 부하 섹션은 그냥 없애줘 그리고 수분 섭취 패턴도 없애줘 그리고 기록에서도 수분 섭취 입력하는 부분도 그냥 없애줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 기록 화면 수분 섭취 표시/입력 블록 제거, 분석 탭 훈련 부하/수분 섭취 패턴 카드 제거, 휴식 추천 설정 설명 문구 변경.
- `src/app/page.dashboard/view.ts`: 기본 회복 지표 안내 문구에서 훈련 부하 표현 제거.
- `devlog.md`: 013 작업 요약 행 추가.
- `devlog/2026-06-08/013-dashboard-analysis-hydration-remove.md`: 작업 상세 기록 추가.

## 확인 결과
- `rg -n "수분 섭취 패턴|수분 섭취|훈련 부하|hydration-section|run-hydration-detail|hydration-pattern-card|training-load-card" src/app/page.dashboard/view.pug src/app/page.dashboard/view.ts` 결과 없음.
- `wiz_project_build(clean=false)` 성공.

## 남은 리스크
수분 섭취와 훈련 부하 관련 백엔드 데이터 필드 및 API는 기존 기록/AI 컨텍스트 호환을 위해 유지했다.
