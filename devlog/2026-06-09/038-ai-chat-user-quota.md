# 페이서 AI 사용자별 일/월 사용량 제한 추가

## 사용자 요청

```text
작업 진행해줘

리뷰 ID: jerowkcgqlamqzbokywpxkqozwbtkhdu
P1. 운영 비용/장애 방어 중 "페이서 AI 사용자별 일/월 사용량 제한 설정"을 먼저 진행.
```

## 변경 파일

- `src/model/runningmate.py`
- `src/route/api.chat/controller.py`
- `.env.example`
- `README.md`
- `docs/openai-production-ops-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/038-ai-chat-user-quota.md`

## 변경 내용

- `ai_usage.json` 기반 사용자별 AI 사용량 저장소를 추가했다.
- 페이서 채팅 사용량을 `user_id + action` 단위로 일/월 카운트하고, 일/월이 바뀌면 해당 기간 카운트를 초기화하도록 했다.
- `/api/chat` POST에서 메시지 검증 후 OpenAI/Codex/local 응답 생성 전에 사용량을 reserve하고, 제한 초과 시 비스트리밍은 HTTP 429 JSON, 스트리밍은 NDJSON error로 차단하도록 했다.
- 기본 한도는 일반 사용자 5회/일, 50회/월, 관리자 100회/일, 2000회/월로 두고 `RUNNINGMATE_AI_CHAT_*` 환경변수로 조정 가능하게 했다.
- 계정 삭제/스냅샷 대상에 AI 사용량 파일을 포함했다.
- 운영 env 예시와 OpenAI 운영 정책 문서에 새 한도 변수를 반영했다.

## 확인한 내용

- `python -m py_compile src/model/runningmate.py src/route/api.chat/controller.py` 통과.
- 임시 `RUNNINGMATE_DATA_DIR`에서 사용자별 일일 제한 2회 초과 시 `daily_limit`으로 차단되는 것을 확인.
- 임시 `RUNNINGMATE_DATA_DIR`에서 월 제한 2회 초과 시 `monthly_limit`으로 차단되는 것을 확인.
- WIZ 프로젝트 빌드 통과.
