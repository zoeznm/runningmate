# AI 채팅 페이서 페르소나 설정 화면 이동 및 사용자별 저장

## 사용자 요청

AI 채팅 톱니바퀴를 선택하면 기존 AI 설정 대신 설정 하단 정보 섹션에 있던 페이서 페르소나 선택을 보여주고, 설정 정보 섹션에서는 해당 선택 섹션을 제거한다. AI 채팅 톱니바퀴 화면에는 페르소나별 대화 예시와 저장 버튼을 함께 두고, 페르소나는 사용자마다 저장되도록 한다.

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.scss`
- `src/route/api.chat/controller.py`
- `devlog.md`
- `devlog/2026-06-09/035-ai-chat-pacer-persona-settings.md`

## 변경 내용

- AI 채팅 톱니바퀴 화면을 페이서 설정 화면으로 바꾸고, 페르소나 선택 카드, 대화 예시, 저장 버튼을 추가했다.
- 설정 > 정보 섹션에서 페이서 페르소나 선택 행을 제거했다.
- 페르소나 선택을 저장 전 드래프트 값과 저장된 값으로 분리하고, 사용자 식별자 기반 로컬 저장 키에 저장되도록 했다.
- 채팅 요청에 `pacer_persona`를 포함하고, `/api/chat` 프롬프트에 페르소나별 응답 지침을 반영했다.

## 확인한 내용

- `python -m py_compile src/route/api.chat/controller.py` 통과
- WIZ 프로젝트 빌드 통과
