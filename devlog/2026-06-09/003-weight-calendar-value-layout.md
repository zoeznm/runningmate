# 체중 달력 날짜와 체중값 겹침 개선

- **ID**: 003
- **날짜**: 2026-06-09
- **유형**: UX 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
체중 달력에서 날짜 숫자 아래에 같이 보이던 작은 숫자는 해당 날짜에 저장된 체중값이었다. 기존에는 날짜 숫자, 체중값, 기록 표시 점이 작은 원형 날짜 버튼 안에 함께 들어가 겹쳐 보일 수 있었다. 체중 달력 전용 날짜 셀을 더 높은 세로형 셀로 조정하고, 중복 정보였던 기록 표시 점을 제거해 날짜와 체중값이 분리되어 보이도록 수정했다.

## 원문 요청사항
```text
지금 체중 기록하는 부분을 보면 달력에 달력 일 밑에 숫자가 같이 나오는데 뭔가 숫자랑 뭔가가 겹쳐진 거 같거든? 그게 뭔지 알려주고 수정해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 체중 달력 날짜 셀의 기록 표시 점 렌더링 제거
- `src/app/page.dashboard/view.ts`: 체중 달력 셀의 점 클래스 제거
- `src/app/page.dashboard/view.scss`: 체중 달력 날짜 셀 높이/간격/체중값 라벨 스타일 조정 및 점 스타일 제거
- `config/pwa/sw.js`: PWA 캐시 버전을 `runningmate-pwa-v13`으로 갱신
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-09/003-weight-calendar-value-layout.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js`에서 `weight-cal-dot` 문자열 제거 확인
- 운영 `main.js`에 체중 달력 스타일/체중값 라벨 반영 확인
- 운영 `sw.js` 캐시 버전 `runningmate-pwa-v13` 확인
