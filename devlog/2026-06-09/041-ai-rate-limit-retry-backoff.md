# AI rate limit 재시도·백오프 및 과다 요청 차단 추가

## 사용자 요청

rate limit 대응: 재시도, backoff, 실패 메시지, 과도한 요청 차단. 이 작업 진행해줘

## 변경 파일

- `src/model/runningmate.py`
- `src/route/api.chat/controller.py`
- `src/route/api.parse-image/controller.py`
- `src/app/page.dashboard/view.ts`
- `.env.example`
- `README.md`
- `docs/openai-production-ops-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/041-ai-rate-limit-retry-backoff.md`

## 변경 내용

- 사용자별 AI 요청 속도 제한 상태를 `ai_rate_limits.json`에 저장하도록 추가했다.
- `/api/chat`은 일/월 사용량 상태 확인 뒤, 쿨다운/윈도우 제한을 통과한 경우에만 사용량을 차감하고 AI provider를 호출하도록 조정했다.
- `/api/parse-image`는 이미지 저장 후 OpenAI/Codex 호출 전에 사용자별 이미지 파싱 쿨다운/윈도우 제한을 확인하도록 추가했다.
- OpenAI Responses API 호출의 429, 500, 502, 503, 504 오류는 exponential backoff와 jitter로 최대 2회 재시도하도록 추가했다.
- 401, 403, `insufficient_quota`는 재시도하지 않고 사용자용 실패 메시지를 반환하도록 유지했다.
- 이미지 파싱 UI가 HTTP 429 응답의 서버 메시지를 사용자에게 표시하도록 보강했다.
- 운영 env 예시와 OpenAI 운영 정책 문서에 rate limit 및 backoff 설정값을 추가했다.

## 확인한 내용

- `python -m py_compile src/model/runningmate.py src/route/api.chat/controller.py src/route/api.parse-image/controller.py scripts/check_openai_usage.py` 통과
- 임시 데이터 디렉터리에서 `reserve_ai_rate_limit()` 쿨다운 및 burst 제한 동작 검증 통과
- WIZ 프로젝트 빌드 통과
