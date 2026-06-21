# 갤러리 일기 달력 빈 날짜 선택 안내 보강

## 요청

갤러리 일기탭에서 일기가 작성된 날 외의 날짜가 클릭되지 않고, 일기가 없는 날짜를 누르면 안내 문구가 나오면 좋겠다는 요청.

## 변경

- 갤러리 일기 달력에서 실제 날짜는 일기 작성 여부와 관계없이 클릭 가능하도록 변경했다.
- 일기가 없는 날짜를 선택하면 `저장된 일기가 없어` 안내와 저장 위치 안내 문구를 표시하도록 추가했다.
- 운영 런타임 번들(`/opt/app/bundle/project/main/bundle/www/main.js`)에도 동일 변경을 반영했다.
- PWA 캐시 버전을 `runningmate-pwa-v51-journal-clickable-days`로 올리고 WIZ 프로세스를 재시작했다.

## 확인

- 운영 데이터의 `day_notes.json`에 `2026-06-15` 일기 메모가 남아 있는 것을 확인했다.
- `http://127.0.0.1:3000/main.js` 응답에 `journal-selected-empty`, `저장된 일기가 없어`, `cell.day ? cell.key === selectedJournalDate`가 포함되는 것을 확인했다.
- `http://127.0.0.1:3000/main.js` 응답에서 빈 날짜 비활성 조건 `!cell.day || !cell.journalCount`가 제거된 것을 확인했다.
- `http://127.0.0.1:3000/sw.js` 응답에 `runningmate-pwa-v51-journal-clickable-days` 캐시 버전이 포함되는 것을 확인했다.

## 남은 리스크

- 정식 Angular 빌드는 기존 프로젝트 타입/스타일 오류가 남아 있어 아직 전체 성공하지 않는다.
