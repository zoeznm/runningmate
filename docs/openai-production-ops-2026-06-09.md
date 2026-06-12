# 러닝메이트 운영용 OpenAI Platform 프로젝트 정책

작성일: 2026-06-09

이 문서는 러닝메이트 운영 환경에서 OpenAI API를 사용할 때 필요한 프로젝트, 키, 모델, 과금 한도, 사용량 알림, rate limit 대응, 서버 측 비용 방어 기준을 정리한다. 실제 API 키 값은 문서에 기록하지 않는다.

## 현재 코드 기준

- OpenAI 호출 라우트는 `src/route/api.chat/controller.py`, `src/route/api.parse-image/controller.py`, `src/route/api.ai-config/controller.py`이다.
- 운영 키는 `OPENAI_API_KEY`로 읽고, 기본 env 파일은 `/opt/app/config/openai.env`이다.
- 운영 provider는 `RUNNINGMATE_AI_PROVIDER=openai`가 기준이다.
- 채팅 기본 모델은 `RUNNINGMATE_CHAT_MODEL` 우선, 없으면 `RUNNINGMATE_VISION_MODEL`, 없으면 `gpt-5.4-mini-2026-03-17`이다.
- 이미지 파싱 기본 모델은 `RUNNINGMATE_VISION_MODEL`, 없으면 `gpt-5.4-mini-2026-03-17`이다.
- 이미지 detail 기본값은 `RUNNINGMATE_IMAGE_DETAIL`, 없으면 `high`이다.
- 현재 서버 방어는 로그인 필수, 채팅 메시지 길이 제한, 페이서 채팅 사용자별 일/월 사용량 제한, 이미지 파싱 사용자별 월 35회 제한, 채팅/이미지 파싱 사용자별 쿨다운 및 윈도우 기반 과다 요청 차단, 이미지 형식 검증, 업로드 크기 제한, OpenAI 401/403/429/quota 오류 메시지 분기, OpenAI 429/5xx 재시도까지 구현되어 있다.
- OpenAI 프로젝트 비용/usage 점검은 `scripts/check_openai_usage.py`에서 Admin API 기반으로 수행한다.
- OpenAI 콘솔의 운영 프로젝트 예산/알림/usage 모니터링 설정은 2026-06-10 운영자가 완료했다.
- AI 베타, 쿼터, 유료화 확장 설계는 `docs/ai-access-beta-quota-paid-design-2026-06-09.md`에 정리한다.
- 아직 등급/구독별 세분화, OpenAI 응답 토큰 상한, 비용 원장, 비용 회로 차단기는 구현되어 있지 않다.

## OpenAI Platform 프로젝트 구성

| 항목 | 운영 기준 |
| --- | --- |
| 프로젝트 | OpenAI Platform에 `runningmate-prod` 또는 동일 의미의 운영 전용 프로젝트를 별도로 둔다. 개발/테스트 프로젝트와 키를 공유하지 않는다. |
| API 키 | 운영 서버 전용 프로젝트 키 1개를 사용한다. 키는 서버 환경변수 또는 `/opt/app/config/openai.env`처럼 권한 `600`인 런타임 파일에만 둔다. |
| 서비스 계정 | 가능하면 `runningmate-server-prod` 서비스 계정으로 키를 발급한다. 개인 계정 키나 Codex 개인 로그인 상태에 의존하지 않는다. |
| 권한 | Responses API 호출과 모델 요청에 필요한 최소 권한만 부여한다. 프로젝트 관리, 사용자 관리, rate limit 조정 권한은 운영자 계정에만 둔다. |
| IP 제한 | 집 서버에 고정 공인 IP를 할당해 운영한다면 OpenAI 프로젝트 또는 조직의 IP allowlist에 그 IP를 등록한다. IP가 바뀌면 배포 전 allowlist와 서버 설정을 함께 갱신한다. |
| 키 로테이션 | 키 노출, 담당자 변경, 서버 침해 의심, 정기 교체 시 즉시 폐기 후 재발급한다. 교체 이력에는 키 값이 아니라 발급일/폐기일/담당자만 기록한다. |

운영 env 기준:

```env
RUNNINGMATE_AI_PROVIDER=openai
OPENAI_API_KEY=<server-runtime-secret>
RUNNINGMATE_CHAT_MODEL=gpt-5.4-mini-2026-03-17
RUNNINGMATE_VISION_MODEL=gpt-5.4-mini-2026-03-17
RUNNINGMATE_IMAGE_DETAIL=high
RUNNINGMATE_MAX_CHAT_MESSAGE_CHARS=1200
RUNNINGMATE_AI_CHAT_DAILY_LIMIT=5
RUNNINGMATE_AI_CHAT_MONTHLY_LIMIT=120
RUNNINGMATE_AI_CHAT_ADMIN_DAILY_LIMIT=100
RUNNINGMATE_AI_CHAT_ADMIN_MONTHLY_LIMIT=2000
RUNNINGMATE_AI_CHAT_COOLDOWN_SECONDS=10
RUNNINGMATE_AI_CHAT_RATE_WINDOW_SECONDS=60
RUNNINGMATE_AI_CHAT_RATE_MAX_REQUESTS=6
RUNNINGMATE_AI_IMAGE_PARSE_COOLDOWN_SECONDS=30
RUNNINGMATE_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS=300
RUNNINGMATE_AI_IMAGE_PARSE_RATE_MAX_REQUESTS=5
RUNNINGMATE_AI_IMAGE_PARSE_MONTHLY_LIMIT=35
RUNNINGMATE_OPENAI_RETRY_MAX=2
RUNNINGMATE_OPENAI_BACKOFF_BASE_SECONDS=0.8
RUNNINGMATE_OPENAI_BACKOFF_MAX_SECONDS=8
OPENAI_ADMIN_KEY=<server-runtime-admin-key>
RUNNINGMATE_OPENAI_PROJECT_ID=<runningmate-prod-project-id>
RUNNINGMATE_OPENAI_DAILY_BUDGET_USD=1
RUNNINGMATE_OPENAI_MONTHLY_BUDGET_USD=30
RUNNINGMATE_OPENAI_ALERT_THRESHOLDS=50,80,95,100
RUNNINGMATE_MAX_UPLOAD_BYTES=10485760
```

`OPENAI_BASE_URL`은 공식 OpenAI API가 아닌 프록시를 거칠 때만 사용한다. 운영에서는 특별한 이유가 없으면 비워둔다.

## 모델 설정안

| 용도 | 1차 운영 설정 | 상위 품질 옵션 | 비고 |
| --- | --- | --- | --- |
| 페이서 채팅 | `gpt-5.4-mini-2026-03-17` | `gpt-5.5` + `reasoning.effort=low` + `text.verbosity=low` | 현재 코드는 모델명만 env로 바꿀 수 있다. reasoning/text/max output 파라미터는 추가 구현 필요. |
| 러닝 캡처 이미지 파싱 | `gpt-5.4-mini-2026-03-17`, `RUNNINGMATE_IMAGE_DETAIL=high` | `gpt-5.5` 또는 추후 평가된 vision 모델 | OCR 정확도가 중요하므로 초기에는 `high` 유지. 비용이 높으면 무료 사용자만 `low`로 낮춘다. |
| 관리자 점검/품질 비교 | `gpt-5.5` | `reasoning.effort=medium` | 관리자 기능도 전역 과금 한도와 rate limit을 우회하지 않는다. |

OpenAI 최신 모델 문서는 2026-06-09 기준 최신 모델을 `gpt-5.5`로 안내하고, Responses API, `reasoning.effort`, `text.verbosity`, prompt caching 평가를 권장한다. 러닝메이트 운영 기본 모델은 지정 모델인 `gpt-5.4-mini-2026-03-17`로 두고, 실제 사용량과 품질을 본 뒤 상위 모델을 부분 적용한다.

추가 구현 권장 env:

```env
RUNNINGMATE_OPENAI_MAX_OUTPUT_TOKENS=400
RUNNINGMATE_OPENAI_TIMEOUT_SECONDS=30
RUNNINGMATE_OPENAI_DAILY_BUDGET_USD=1
RUNNINGMATE_OPENAI_MONTHLY_BUDGET_USD=30
```

## 과금 한도와 사용량 알림

OpenAI의 rate limit과 usage limit은 사용자 단위가 아니라 조직/프로젝트/모델 단위로 적용된다. 따라서 OpenAI 대시보드의 프로젝트 한도와 러닝메이트 서버의 사용자별 한도를 함께 둬야 한다.

이번 구현 기준:

- 사용자에게 노출되는 페이서 채팅 한도는 일반 사용자 `5회/일`, `120회/월`이다.
- 사용자별 이미지 파싱 한도는 `35회/월`이다. 일 한도는 별도 설정하지 않고, 과도한 연속 요청은 쿨다운/rate limit으로 차단한다.
- `/api/chat`은 현재 사용량을 `usage`로 반환하고, 대시보드 AI 채팅 화면은 남은 일/월 횟수를 표시한다.
- 한도를 모두 사용하면 OpenAI 호출 전에 차단하고, 사용자에게 토스트/응답 메시지로 알린다.
- `/api/chat`과 `/api/parse-image`는 OpenAI/Codex 호출 전에 `ai_rate_limits.json`의 사용자별 쿨다운/윈도우 제한을 확인한다.
- 쿨다운 또는 윈도우 제한에 걸리면 OpenAI 호출과 페이서 채팅 일/월 사용량 차감 없이 HTTP 429 또는 NDJSON error로 실패 메시지를 반환한다.
- OpenAI 프로젝트 비용은 `scripts/check_openai_usage.py`가 Admin API의 `/organization/costs`와 `/organization/usage/completions`를 조회해 점검한다.
- `OPENAI_ADMIN_KEY`는 서버 런타임 secret으로만 주입하고 저장소에는 기록하지 않는다.

초기 베타 운영 권장값:

| 항목 | 권장값 |
| --- | --- |
| 프로젝트 월 hard cap | 운영자가 감당 가능한 최대 손실액으로 설정한다. 집 서버 초기 베타는 `20-50 USD/month` 범위에서 시작하고, 사용량 데이터를 보고 올린다. |
| 알림 구간 | 50%, 80%, 95%, 100% |
| 일 단위 내부 예산 | `월 한도 / 30`을 기본값으로 잡고, 80% 도달 시 무료 사용자 AI를 차단한다. |
| 월 80% 도달 | 관리자 알림, 무료 사용자 차단, 이미지 detail을 `low`로 낮추는 운영 모드 전환 |
| 월 95% 도달 | 관리자 외 AI 호출 차단 |
| `insufficient_quota` 발생 | 재시도하지 않고 즉시 AI 기능을 차단 상태로 전환한 뒤 관리자에게 알림 |

프로젝트 알림 설정:

1. OpenAI 콘솔에서 운영 전용 프로젝트를 선택한다.
2. Limits 또는 Billing 화면에서 월 hard cap을 운영자가 감당 가능한 금액으로 설정한다.
3. Spend alerts는 50%, 80%, 95%, 100%에 해당하는 금액으로 이메일 알림을 만든다.
4. Admin API를 사용할 수 있으면 `/organization/spend_alerts` 또는 `/organization/projects/{project_id}/spend_alerts`로 spend alert 구성을 조회/관리한다.
5. `scripts/check_openai_usage.py`를 cron 또는 배포 점검에 등록해 daily/monthly budget 초과 시 exit code로 실패를 감지한다.

운영자가 OpenAI 콘솔에서 확인해야 할 화면:

- API keys: https://platform.openai.com/settings/organization/api-keys
- Usage: https://platform.openai.com/settings/organization/usage
- Limits: https://platform.openai.com/settings/organization/limits
- Billing: https://platform.openai.com/settings/organization/billing/overview

## 사용자 등급별 사용량 제한안

현재 DB에는 `user.role`만 있고 무료/일반 사용자 구분 필드는 없다. 실제 적용 시 `user.plan` 또는 별도 구독 테이블을 추가해야 한다.
상세 접근 제어, 베타 운영 모드, 유료화 전환 단계는 `docs/ai-access-beta-quota-paid-design-2026-06-09.md`를 기준으로 한다.

| 등급 | 채팅 제한 | 이미지 파싱 제한 | 동시 요청 | 쿨다운 | 입력 제한 | 모델 정책 |
| --- | --- | --- | --- | --- | --- | --- |
| 무료 사용자 | 5회/일, 120회/월 | 35회/월 | 1 | 60초 | 메시지 600자, 이미지 5MB | `gpt-5.4-mini-2026-03-17`, image detail `low` 또는 필요 시 1회 `high` 재시도 |
| 일반 사용자 | 30회/일, 600회/월 | 10회/일, 200회/월 | 2 | 10초 | 메시지 1200자, 이미지 10MB | 기본 `gpt-5.4-mini-2026-03-17`, 품질 개선 구간만 상위 모델 |
| 관리자 | 100회/일, 2000회/월 | 50회/일, 500회/월 | 3 | 2초 | 메시지 2000자, 이미지 10MB | 점검 목적의 `gpt-5.5` 허용, 단 전역 hard cap 적용 |

정책 원칙:

- 미로그인 사용자는 OpenAI 호출을 허용하지 않는다.
- 관리자도 프로젝트 월 hard cap, 429 backoff, `insufficient_quota` 차단을 우회하지 않는다.
- 사용량 제한 초과 시 OpenAI API 호출 전에 차단한다.
- 무료 사용자는 서버 예산 경보가 울리면 가장 먼저 차단한다.

## 서버 측 과금 폭증 방어 기준

### 요청 전 방어

- `ai_usage_ledger` 테이블을 추가해 `user_id`, `plan`, `action`, `model`, `day`, `month`, `status`, `input_tokens`, `output_tokens`, `estimated_cost_usd`, `response_id`, `error_code`, `created_at`을 기록한다.
- OpenAI 호출 전 `user_id + action + day/month` 기준으로 한도 초과 여부를 검사한다.
- IP별 비정상 요청도 별도 카운터로 제한한다. 로그인 상태여도 같은 IP에서 많은 계정이 동시에 요청하면 차단한다.
- 채팅 입력 길이는 현재 1200자 제한을 유지하되, 무료 사용자는 600자로 낮춘다.
- 이미지 업로드는 현재 형식 검증과 10MB 제한을 유지하되, 무료 사용자는 5MB로 낮춘다.
- 이미지 파싱은 파일 SHA-256 해시를 저장해 같은 사용자가 같은 이미지를 반복 파싱하면 캐시된 결과를 반환한다.

### OpenAI 호출 방어

- Responses API 호출에 `max_output_tokens`를 추가해 채팅은 400, 이미지 JSON 파싱은 300 정도로 시작한다.
- 요청 timeout은 30초로 두고, 이미지 파싱은 비동기 큐로 전환하기 전까지 동시 요청을 낮게 유지한다.
- 현재 코드는 429, 500, 502, 503, 504를 exponential backoff + jitter로 최대 2회 재시도한다.
- 401, 403, `insufficient_quota`는 재시도하지 않는다.
- OpenAI rate limit 응답 헤더가 노출되면 남은 request/token과 reset 시간을 로그 메타데이터에 남긴다.

### 회로 차단기

| 조건 | 조치 |
| --- | --- |
| 10분 동안 OpenAI 429가 5회 이상 | 15분 동안 신규 AI 호출 차단, 사용자에게 잠시 후 재시도 안내 |
| 일 예산 80% 초과 | 무료 사용자 AI 차단 |
| 일 예산 100% 초과 | 일반 사용자 AI 차단, 관리자만 제한적으로 허용 |
| 월 예산 80% 초과 | 관리자 알림, 모델/detail 비용 절감 모드 전환 |
| 월 예산 95% 초과 | 모든 사용자 AI 호출 차단 |
| `insufficient_quota` 발생 | 모든 AI 호출 차단, OpenAI Billing/Limits 확인 전까지 해제 금지 |

### 로그와 개인정보

- 로그에는 API 키, prompt 원문, 이미지 base64, OAuth secret, DB 비밀번호를 남기지 않는다.
- 저장 대상은 `user_id`, 요청 종류, 모델, 토큰 수, 상태 코드, 에러 코드, 응답 시간, 비용 추정치 정도로 제한한다.
- 러닝 기록과 건강 컨텍스트가 prompt에 포함되므로 prompt 원문 저장은 기본 비활성화한다. 품질 분석이 필요하면 관리자 동의와 보존 기간을 별도로 둔다.

## Rate limit 대응 정책

OpenAI 문서 기준 429는 두 종류로 나눠 처리한다.

- `rate_limit_reached`: 너무 빠른 요청이다. 서버에서 pacing, backoff, 쿨다운으로 처리한다.
- `insufficient_quota` 또는 quota 메시지: 크레딧 소진 또는 월 사용 한도 도달이다. 재시도하지 않고 운영자 조치가 필요하다.

운영 처리:

1. 사용자별 제한을 먼저 확인한다.
2. 서버 전역 circuit breaker 상태를 확인한다.
3. 사용자별 쿨다운/윈도우 제한을 확인한다.
4. OpenAI 호출을 수행한다.
5. 429 rate limit 또는 5xx 계열이면 최대 2회 backoff 후 실패 처리한다.
6. `insufficient_quota`, 401, 403은 즉시 실패 처리하고 관리자 알림을 남긴다.

OpenAI 공식 rate limit 문서는 random exponential backoff를 권장하며, 실패한 요청도 분당 제한에 포함될 수 있다고 안내한다. 따라서 재시도 횟수는 낮게 유지하고, 재시도 전에 러닝메이트 자체 쿨다운/윈도우 제한으로 불필요한 API 호출을 줄인다.

## 배포 전 검증

```bash
python scripts/verify_runtime_secrets.py
python scripts/check_openai_usage.py
curl -sS http://127.0.0.1:3000/api/ai-config
```

확인 기준:

- `OPENAI_API_KEY` 값은 저장소와 로그에 출력되지 않는다.
- `/api/ai-config`가 `configured: true`, provider `OpenAI Responses API`, mode `openai`를 반환한다.
- OpenAI Usage와 Limits 화면에서 운영 프로젝트의 키별 사용량 추적이 보인다.
- `scripts/check_openai_usage.py`가 운영 프로젝트의 daily/monthly spend와 completions usage를 JSON으로 출력한다.
- 무료/일반/관리자별 한도 구현 전에는 공개 베타 트래픽을 받지 않는다.

## 공식 근거

- Latest model guidance: https://developers.openai.com/api/docs/guides/latest-model.md
- Rate limits: https://developers.openai.com/api/docs/guides/rate-limits
- Error codes: https://developers.openai.com/api/docs/guides/error-codes#api-errors
- Production best practices, API keys: https://developers.openai.com/api/docs/guides/production-best-practices#api-keys
- RBAC permissions: https://developers.openai.com/api/docs/guides/rbac#permissions
- Admin costs API: https://api.openai.com/v1/organization/costs
- Admin completions usage API: https://api.openai.com/v1/organization/usage/completions
- Admin spend alerts API: https://api.openai.com/v1/organization/spend_alerts
