# 갤러리 일기 달력 빈 날짜 클릭 표시 보강

## 요청

갤러리 일기 달력에서 일기 없는 날짜를 눌러도 클릭되지 않는다는 요청.

## 변경

- 일기 없는 날짜도 클릭 가능한 버튼처럼 보이도록 `journal-cal-day` 커서를 `pointer`로 변경했다.
- 일기 없는 날짜를 선택했을 때 선택 색상과 굵기가 적용되도록 스타일을 추가했다.
- 운영 런타임 CSS에도 `!important` 오버라이드를 추가해 기존 컴포넌트 스타일보다 우선 적용되게 했다.
- PWA 캐시 버전을 `runningmate-pwa-v51-journal-clickable-days`로 올리고 WIZ 프로세스를 재시작했다.

## 확인

- `http://127.0.0.1:3000/main.css` 응답에 `journal-cal-day{cursor:pointer!important}`가 포함되는 것을 확인했다.
- `http://127.0.0.1:3000/main.js` 응답에 빈 날짜 선택 로직 `selectJournalDate(e){e.day`와 `journal-selected-empty`가 포함되는 것을 확인했다.
- `http://127.0.0.1:3000/sw.js` 응답에 `runningmate-pwa-v51-journal-clickable-days` 캐시 버전이 포함되는 것을 확인했다.

## 남은 리스크

- 정식 Angular 빌드는 기존 프로젝트 타입/스타일 오류가 남아 있어 아직 전체 성공하지 않는다.
