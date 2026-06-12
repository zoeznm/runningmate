# 이미지 파싱 사용자별 월 35회 제한 추가

## 사용자 요청

이미지 파싱 월 한도 35회로 잡아줘. OpenAI 콘솔 설정 완료했어.

## 변경 파일

- `src/route/api.parse-image/controller.py`
  - `image_parse` 액션에 사용자별 월 35회 사용량 예약을 추가했다.
  - 월 한도 초과 시 업로드된 파일을 삭제하고 OpenAI/Codex 호출 전에 429 응답으로 차단한다.
  - 성공/실패 응답에 이미지 파싱 사용량 정보를 함께 반환한다.
- `src/route/api.ai-config/controller.py`
  - 관리자 설정 응답의 optional env 목록에 `RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT`를 추가했다.
- `docs/openai-production-ops-2026-06-09.md`
  - 이미지 파싱 월 35회 제한과 OpenAI 콘솔 설정 완료 상태를 운영 문서에 반영했다.

## 확인 결과

- `python -m py_compile`로 변경된 Python 라우트 문법을 확인했다.
- `wiz_project_build(clean=false)` 빌드가 성공했다.
- 앱을 재시작했고 `/healthz`가 200을 반환했다.
- `/api/ai-config`가 200을 반환했고 optional env 목록에 `RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT`가 포함됨을 확인했다.
- 임시 데이터 디렉터리에서 `reserve_ai_usage(action="image_parse", monthly_limit=35)`를 35회 호출한 뒤 36번째가 `monthly_limit`으로 차단되는 것을 확인했다.
