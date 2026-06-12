# AI 채팅 페이서 아바타 및 일별 대화 분리

- **ID**: 001
- **날짜**: 2026-06-09
- **유형**: 기능 추가

## 작업 요약
AI 채팅 헤더의 페이서 아바타를 플랫폼 이모티콘 대신 앱 내 FontAwesome 러닝 아이콘으로 교체했다.
대화 세션에 `day_key`를 저장하고, 하루가 지난 대화는 자동 이어쓰기 대신 새 대화 안내와 기록 보기 흐름으로 분리했다.

## 원문 요청사항
```text
작업 진행해줘

AI 채팅에 뭔가 수정해야되거나 추가해야될 점이 있을까? 
일단 내눈에는 
1. 페이서의 저 동그라미 안에 있는 이모티콘이 애플 이모티콘이라는거? 그거 수정이 필요해보여 
2. 내가 새 대화 시작을 하지 않으면 그 전에 대화했던 걸로 계속 남아있는다고 해야되나? 클로드나 gpt를 보면 하루가 지나면 새로운 대화를 시작하려냐고 뜨잖아 얘도 그렇게 해주면 좋겠어 대신 그 전의 대화는 하루단위로 기록되면 좋겠고 하루가 지나면 대화를 새롭게 시작할 수 있게 해주면 좋겠어 

내가 보이는건 이 정도인데 너가 생각하기에는 어떤게 추가해야되거나 수정해야될 요소라고 보여?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 페이서 아바타를 아이콘으로 교체하고, 새날 대화 안내 패널과 새 대화/기록 보기 액션을 추가.
- `src/app/page.dashboard/view.scss`: 채팅 아바타와 새날 안내 패널 스타일 추가.
- `src/app/page.dashboard/view.ts`: 채팅 세션 `day_key` 정규화, 오늘 세션 자동 선택, 이전 날짜 세션 안내, 전날 세션 전송 전 새 세션 전환, `client_date` 전송 로직 추가.
- `src/model/runningmate.py`: 채팅 세션 `day_key` 저장 및 기존 세션 날짜가 요청 날짜와 다르면 새 세션으로 분리.
- `src/route/api.chat/controller.py`: `/api/chat` POST/stream 저장 시 `client_date`를 모델에 전달.
- `devlog.md`, `devlog/2026-06-09/001-ai-chat-daily-session.md`: 작업 이력 기록.

## 확인 결과
- `python -m py_compile src/model/runningmate.py src/route/api.chat/controller.py` 통과.
- WIZ `wiz_project_build(clean=false)` 통과.
- 임시 `RUNNINGMATE_DATA_DIR` 모델 테스트에서 2026-06-08 세션 ID로 2026-06-09 메시지를 저장할 때 새 세션 ID가 생성되고 날짜별 세션이 분리되는 것을 확인.
