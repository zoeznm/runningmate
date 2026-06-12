# 체중 기록 화면 차트 비교 방식 개선

- **ID**: 004
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
체중 기록 화면의 `체중 vs 러닝량` 차트를 단위가 다른 두 선이 겹치는 방식에서 체중 추세선과 주간 러닝량 막대를 분리한 비교 화면으로 변경했다. 기간별 체중 변화, 러닝 합계, 주당 평균을 요약 지표로 추가해 그래프를 보기 전에 핵심 맥락을 먼저 확인할 수 있게 했다.

## 원문 요청사항
```text
작업 진행해줘

기록에서 체중 화면에 체중 vs 러닝량 이렇게 나오는데 거기에 그래프도 같이 보여주거든? 그거 좀 그래프를 수정해든지 아니면 다른 방식으로 보여주는게 어떨까 싶은데 어떻게 생각해?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 체중 비교 요약 지표, 주간 러닝량 막대 데이터, 기간 축 라벨 계산 추가
- `src/app/page.dashboard/view.pug`: `체중 변화와 러닝량` 카드에 요약 지표와 분리형 체중/러닝 차트 구조 적용
- `src/app/page.dashboard/view.scss`: 요약 지표, 체중 추세 영역, 주간 러닝량 막대 영역 스타일 추가
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/004-weight-chart-comparison.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
