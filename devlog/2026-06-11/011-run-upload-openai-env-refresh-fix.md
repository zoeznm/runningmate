# 기록 업로드 OpenAI 파싱 환경값 갱신 문제 수정

## 사용자 원본 요청

스크린샷으로 보면 저런식으로 나오고 있어 기록 업로드를 하면

## 처리 내용

- 첨부 스크린샷의 오류 문구가 `OpenAI API 접근 권한이 없습니다...`로 표시되는 것을 확인했다.
- 보안 감사 로그에서 해당 시간대 이미지 파일 저장은 성공했으므로, 실패 지점을 업로드 저장 이후 OpenAI 이미지 파싱 단계로 분리했다.
- `/opt/app/config/openai.env`의 모델명은 이미 `gpt-5.4-mini`로 수정되어 있었지만, 라우트의 `_load_env_file()`이 기존 프로세스 환경값을 덮어쓰지 않아 이전 모델명이 계속 사용될 수 있는 구조를 확인했다.
- 이미지 파싱, AI 채팅, AI 설정 라우트의 env 로더가 env 파일 값을 매번 반영하도록 수정했다.
- OpenAI `model_not_found` 오류가 일반 권한/IP 제한 메시지로 보이지 않도록 이미지 파싱 오류 메시지를 별도로 분리했다.

## 변경 파일

- `src/route/api.parse-image/controller.py`
- `src/route/api.chat/controller.py`
- `src/route/api.ai-config/controller.py`
- `devlog.md`
- `devlog/2026-06-11/011-run-upload-openai-env-refresh-fix.md`

## 검증 결과

- 스테일 환경값 `RUNNINGMATE_VISION_MODEL=gpt-5.4-mini-2026-03-17`을 강제로 넣은 뒤 env 파일 로딩 시 `gpt-5.4-mini`로 갱신되는지 확인
- 갱신된 `gpt-5.4-mini`로 OpenAI Responses API 이미지 입력 스모크 테스트 성공
- `python -m py_compile`로 수정한 route controller 3개 문법 검사 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- 실제 사용자가 업로드하는 러닝 앱 캡처의 OCR 품질과 필드 추출 정확도는 캡처 화면 상태에 따라 달라질 수 있어 실사용 이미지로 최종 확인이 필요하다.
