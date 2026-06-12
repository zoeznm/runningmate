# AI 채팅 페이서 답변 대기 인디케이터 디자인 개선

## 사용자 요청

AI에게 대화를 걸면 바 같은 것이 켜졌다 꺼지며 깜빡이는데, 그렇게 하지 말고 페이서와 잘 어울리는 디자인을 추가해달라.

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `devlog.md`
- `devlog/2026-06-09/040-ai-chat-pacer-thinking-indicator.md`

## 변경 내용

- AI 답변 대기 중 빈 말풍선에 표시되던 깜빡이는 막대 커서를 제거했다.
- 페이서 러닝 아이콘, 발걸음 점 애니메이션, `페이스 조율 중` 문구로 구성된 답변 대기 인디케이터를 추가했다.
- `prefers-reduced-motion: reduce` 환경에서는 새 인디케이터 애니메이션이 멈추도록 보강했다.

## 확인한 내용

- WIZ 프로젝트 빌드 통과
