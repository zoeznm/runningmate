# 016 러닝메이트 내부 LLM/Codex 로직 문서 정정

## 사용자 요청

- Review ID: `lptoxpafhwybmeezgyifmkbxpqfeyvft`
- 원 요청: "리뷰옵스에서 codex의 로직을 말하는게 아니라 지금 러닝메이트라는 내 프로젝트 안에 있는 llm ai, codex의 로직에 대해서 물어보는거야"
- 리뷰 내용: 기존 문서에서 ReviewOps 작업 에이전트 설명을 제거하고, 러닝메이트 서비스 내부의 LLM AI/Codex 런타임 로직 중심으로 정정

## 변경 파일

- `docs/codex-runtime-flow.md`
- `devlog.md`
- `devlog/2026-06-09/016-runningmate-llm-codex-doc-correction.md`

## 변경 내용

- `docs/codex-runtime-flow.md`에서 ReviewOps 개발 에이전트 흐름과 해당 input token 설명을 제거했다.
- 문서 범위를 러닝메이트 앱 내부의 LLM AI, Codex CLI, OpenAI Responses API 실행 로직으로 명확히 좁혔다.
- 대시보드 UI의 `/api/ai-config`, `/api/chat`, `/api/parse-image` 호출 흐름을 프론트엔드 기준으로 보강했다.
- `/api/chat`의 페이서 프롬프트 구성, `_chat_context()`에 포함되는 러닝/체중/수분/목표/랭킹/훈련부하/주기 컨텍스트를 input token 기준으로 정리했다.
- `/api/parse-image`의 OCR/JSON 추출 프롬프트와 Codex/OpenAI 이미지 입력 구조를 구분해 정리했다.
- Codex 모드, OpenAI 모드, 로컬 규칙 fallback, 저장/후처리, 운영 보안 경계를 서비스 구현 기준으로 재작성했다.

## 확인 결과

- `wiz_workspace_status`로 현재 WIZ 프로젝트가 `main`임을 확인했다.
- `.github/custom/custom-instructions.md`는 존재하지 않음을 확인했다.
- `src/app/page.dashboard/view.ts`, `src/app/page.dashboard/view.pug`, `src/route/api.ai-config/controller.py`, `src/route/api.chat/controller.py`, `src/route/api.parse-image/controller.py` 구현을 기준으로 문서를 정정했다.
- 문서와 devlog 변경에 대해 `git diff --check`를 실행해 공백 오류가 없음을 확인했다.
- 문서 변경만 포함하므로 WIZ 빌드는 실행하지 않았다.

## 남은 리스크

- 문서는 현재 소스 기준의 설계/흐름 설명이므로, AI 라우트나 환경변수 정책 변경 시 함께 갱신해야 한다.
- 실제 운영 환경의 provider 값, Codex 로그인 상태, OpenAI API 키 유효성은 별도 운영 점검이 필요하다.
