# 014 Codex 작업 및 런타임 플로우 문서화

## 사용자 요청

- Review ID: `lptoxpafhwybmeezgyifmkbxpqfeyvft`
- 원 요청: "여기 프로젝트 안에서 codex가 하고있는 작업들이랑 어떤식으로 플로우가 흘러가는지 Input 토큰에 뭐가 들어가는지 codex가 돌아가고 있는 구조를 md 파일로 뽑아줘"
- 리뷰 내용: 현재 프로젝트의 Codex 작업 흐름, 서비스 런타임 Codex CLI 구조, input token 구성 문서화

## 변경 파일

- `docs/codex-runtime-flow.md`
- `devlog.md`
- `devlog/2026-06-09/014-codex-runtime-flow-doc.md`

## 변경 내용

- ReviewOps 작업 에이전트로서 Codex가 요청을 받고 파일을 수정하는 흐름을 정리했다.
- 런타임 서비스의 Codex CLI 경로를 `/api/ai-config`, `/api/chat`, `/api/parse-image` 기준으로 문서화했다.
- 채팅 input token에 들어가는 역할 지시, 러닝 컨텍스트 JSON, 최근 일기, 사용자 질문을 항목별로 설명했다.
- 이미지 파싱 input이 텍스트 프롬프트와 `--image` 이미지 입력의 조합이라는 점을 정리했다.
- Codex 모드와 OpenAI Responses API 모드의 차이, 운영/보안 경계를 문서에 포함했다.

## 확인 결과

- `wiz_workspace_status`로 현재 WIZ 프로젝트가 `main`임을 확인했다.
- `.github/copilot-instructions.md`를 확인했고, `.github/custom/custom-instructions.md`는 존재하지 않음을 확인했다.
- `src/route/api.ai-config/controller.py`, `src/route/api.chat/controller.py`, `src/route/api.parse-image/controller.py`를 읽고 실제 구현 기준으로 문서화했다.
- `docs/codex-runtime-flow.md` 파일 생성과 `devlog.md` 요약 행 추가를 확인했다.
- 문서 변경만 포함하므로 WIZ 빌드는 실행하지 않았다.

## 남은 리스크

- 문서는 현재 소스 기준의 정리이므로, AI 라우트나 환경변수 정책이 바뀌면 함께 갱신해야 한다.
- 실제 운영 환경의 Codex 로그인 상태, OpenAI API 키, 비밀값 설정은 문서화 범위에서 값 없이 다뤘고 별도 운영 점검이 필요하다.
