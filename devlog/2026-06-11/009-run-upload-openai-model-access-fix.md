# 기록 업로드 OpenAI 모델 접근 오류 수정

## 사용자 원본 요청

그리고 지금 여전히 기록 업로드를 하면 오류가 나는데 api 키 오류같거든? 확인해볼래?

## 처리 내용

- 기록 이미지 업로드 자체는 성공하지만, 이미지 파싱 단계의 OpenAI Responses API 호출이 실패하는 상태인지 확인했다.
- 런타임 OpenAI 키는 설정되어 있고 모델 목록 조회도 성공했으므로 키 누락/인증 실패가 아니라 모델 접근 오류로 분리했다.
- 기존 `gpt-5.4-mini-2026-03-17` 모델은 현재 프로젝트에서 접근 불가하고, 계정에 노출된 `gpt-5.4-mini`는 호출 가능한 것을 확인했다.
- 운영 런타임 설정의 `RUNNINGMATE_CHAT_MODEL`, `RUNNINGMATE_VISION_MODEL`을 `gpt-5.4-mini`로 교체했다.
- 프로젝트 기본값과 `.env.example`도 같은 모델명으로 맞춰 재배포/환경 재생성 시 같은 오류가 반복되지 않도록 했다.

## 변경 파일

- `/opt/app/config/openai.env`
- `.env.example`
- `src/route/api.parse-image/controller.py`
- `src/route/api.chat/controller.py`
- `src/route/api.ai-config/controller.py`
- `devlog.md`
- `devlog/2026-06-11/009-run-upload-openai-model-access-fix.md`

## 검증 결과

- `/opt/conda/envs/app/bin/python` 런타임에서 OpenAI SDK `2.33.0` 확인
- OpenAI 모델 목록 조회 성공, 사용 가능 모델이 `gpt-5.4-mini`임을 확인
- 기존 `gpt-5.4-mini-2026-03-17` 호출 시 `403 model_not_found` 재현
- 수정 후 `gpt-5.4-mini` 텍스트 Responses API 스모크 테스트 성공
- 수정 후 `gpt-5.4-mini` 이미지 입력 Responses API 스모크 테스트 성공
- `python -m py_compile`로 수정한 route controller 3개 문법 검사 통과
- `scripts/verify_runtime_secrets.py` 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- 실제 사용자가 업로드하는 러닝 앱 캡처의 OCR 품질은 이미지 종류와 해상도에 따라 달라질 수 있어, 실사용 업로드 1건으로 최종 확인이 필요하다.
- `/opt/app/config/openai.env`는 저장소 밖 운영 설정 파일이므로, 서버 재프로비저닝 시 같은 모델 설정이 별도로 유지되어야 한다.
