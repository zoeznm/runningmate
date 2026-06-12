# 기록 달력 날씨 지역 표시 태그화

- **ID**: 047
- **날짜**: 2026-06-08
- **유형**: 디자인 수정

## 작업 요약
날짜 선택 후 표시되는 날씨 섹션의 오른쪽 상단 지역명을 전용 태그 UI로 변경했다.
기존 `서울 근처`, `서울 기준`처럼 붙던 suffix는 제거하고 지역명만 태그로 표시되도록 정리했다.

## 원문 요청사항
```text
날짜 선택하고 날씨 보여주는 섹션에서 오른쪽 상단에 지역 이름 나오고 예를 들어서 서울 근처 이런식으로 나오는데 그러지 말고 그거 혼자만 텍스트 디자인 이상해서 차라리 뭐 태그 형식으로 디자인 수정해주면 좋겠어, 서울 태그, 세종 태그, 대전 이런식으로
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 날씨 위치 표시를 `weather-location-tags` 태그 렌더링 구조로 변경.
- `src/app/page.dashboard/view.scss`: 날씨 지역 태그 전용 스타일 추가.
- `src/app/page.dashboard/view.ts`: 날씨 위치명 suffix 제거 및 태그 배열 getter 추가.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/047-calendar-weather-location-tags.md`: 작업 상세 기록 추가.

## 확인 결과
- `rg`로 `weatherLocationTags`, `weather-location-tag` 템플릿/스타일 반영을 확인했다.
- `setWeatherDays`에서 위치명을 `근처/기준` 없이 저장하도록 변경된 것을 확인했다.
- `wiz_project_build(projectName="main", clean=false)` 성공.
