# 분석 막대그래프 값 라벨 표시

- **ID**: 022
- **날짜**: 2026-06-08
- **유형**: UX 수정

## 작업 요약
분석 화면의 주별/월별/전체 차트에서 거리와 평균 페이스 막대마다 값을 함께 표시하도록 수정했다.
거리 막대는 간결한 숫자 값을, 평균 페이스 막대는 페이스 값을 표시하며 막대가 짧을 때도 읽을 수 있도록 별도 스타일을 적용했다.

## 원문 요청사항
```text
분석 화면에서 주별, 월별, 전체 이렇게 누르면 나오는 주간 거리, 평균 페이스 추이 두 섹션에 그래프 나오잖아 그 그래프 안에 각각 막대그래프에 숫자도 같이 표시해주면 좋겠어 저렇게 그냥 저런식으로만 해두면 뭐가 뭔지 잘 모르겠어
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 분석 막대그래프 렌더링에 값 라벨을 추가.
- `src/app/page.dashboard/view.ts`: `ChartBar`에 `valueText`를 추가하고 거리/페이스별 표시 값을 생성.
- `src/app/page.dashboard/view.scss`: 막대 내부/상단 값 라벨 스타일과 차트 높이 여백 조정.
- `devlog.md`: 022 작업 요약 행 추가.
- `devlog/2026-06-08/022-analysis-bar-value-labels.md`: 작업 상세 기록 추가.

## 확인 결과
- `rg -n "valueText|bar-value|compactDistanceValue|compactPaceValue" src/app/page.dashboard/view.pug src/app/page.dashboard/view.ts src/app/page.dashboard/view.scss`로 반영 위치 확인.
- `wiz_project_build(clean=false)` 성공.

## 남은 리스크
브라우저 실화면 캡처 검증은 수행하지 않았다. 막대 수가 많아지는 전체 기간에서는 기존처럼 가로 스크롤 영역 안에서 값 라벨이 함께 표시된다.
