# 028. OpenAI 기본 모델 변경

- 날짜: 2026-06-09
- 요청: "채팅, 이미지 파싱 기본 모델 gpt-5.4-mini-2026-03-17 이걸로 할거니까 다시 수정해줘"

## 변경 파일

- `src/route/api.chat/controller.py`
- `src/route/api.parse-image/controller.py`
- `src/route/api.ai-config/controller.py`
- `.env.example`
- `README.md`
- `docs/codex-runtime-flow.md`
- `docs/openai-production-ops-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/028-openai-default-model-update.md`

## 작업 내용

- 채팅 기본 모델과 이미지 파싱 기본 모델을 `gpt-5.4-mini-2026-03-17`로 변경했다.
- OpenAI 운영 env 예시와 운영 정책 문서의 기본 모델 기준을 새 모델명으로 갱신했다.
- 런타임 OpenAI env 파일에도 채팅 모델 값을 같은 모델명으로 맞추는 후속 검증을 진행했다.

## 확인 결과

- OpenAI models API에서 지정 모델 조회가 `http_200`으로 확인됐다.
- 런타임 secret 검증과 모델 문자열 검색을 통해 설정 반영 여부를 확인했다.
