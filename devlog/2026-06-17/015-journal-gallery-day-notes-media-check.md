# 일기탭 날짜 메모 표시 및 사진 저장 경로 확인

## 요청

기록 화면에서 저장한 일기가 갤러리 일기탭에 보이지 않고, 내 사진도 저장되는지 확인해달라는 요청.

## 변경

- 갤러리 일기탭 집계가 러닝 기록의 `journal`뿐 아니라 날짜 메모(`/api/day-notes`)도 함께 보도록 변경했다.
- 러닝 기록이 없는 날짜의 일기는 `일기만 저장` 항목으로 표시되도록 했다.
- 러닝 기록이 있는 날짜의 날짜 메모는 해당 날짜 러닝 기록에 붙은 일기처럼 일기탭에 표시되도록 했다.
- 날짜 메모를 러닝 일기로 마이그레이션할 때, 매칭되는 러닝 기록이 없는 날짜 메모가 삭제되지 않도록 보존 로직을 수정했다.
- 현재 운영 런타임 번들(`/opt/app/bundle/project/main/bundle/www/main.js`)에도 동일 수정과 저장 버튼 수정이 반영되도록 동기화했다.
- PWA 캐시 버전을 `runningmate-pwa-v50-journal-empty-days`로 올리고 WIZ 프로세스를 재시작했다.

## 확인

- `http://127.0.0.1:3000/main.js` 응답에 `일기 저장`, `buildJournalRuns`, `journal_only`, `일기만 저장`이 포함되는 것을 확인했다.
- `http://127.0.0.1:3000/sw.js` 응답에 `runningmate-pwa-v50-journal-empty-days` 캐시 버전이 포함되는 것을 확인했다.
- 변경한 Python 모델/라우트 파일을 `py_compile`로 문법 확인했다.
- 사진/영상 저장은 `/api/runs/<run_id>/media`가 `save_run_media()`를 통해 `/opt/app/data/run_media`에 파일을 저장하고 `run_media.json`에 메타데이터를 기록하는 경로임을 확인했다.
- 운영 데이터 디렉터리 `/opt/app/data/run_media`와 `run_media.json`이 존재하고 파일도 보관되어 있음을 확인했다.

## 남은 리스크

- 정식 Angular 빌드는 기존 프로젝트 타입/스타일 오류가 남아 있어 아직 전체 성공하지 않는다.
