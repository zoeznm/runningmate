# 러닝메이트 AI 베타·쿼터·유료화 설계

작성일: 2026-06-09

이 문서는 페이서 AI와 이미지 파싱을 모든 사용자에게 무제한 무료 개방하지 않기 위한 접근 제어, 쿼터, 유료화 확장 설계를 정리한다. 결제 구현 자체가 아니라, 결제를 붙일 수 있는 정책과 데이터 구조를 먼저 고정하는 것이 목적이다.

## 용어

- 베타: 정식 유료 상품 전 단계에서 AI 기능을 제한된 사용자, 제한된 기간, 제한된 사용량으로 제공하는 운영 모드다. 비용, 품질, 장애율, 사용자 반응을 관찰하기 위한 통제된 공개다.
- 쿼터: 사용자 또는 플랜별로 정한 사용 가능량이다. 예를 들어 페이서 채팅 `5회/일`, `120회/월`, 이미지 파싱 `3회/일`, `20회/월`이 쿼터다.
- rate limit: 짧은 시간 안에 반복 요청을 막는 속도 제한이다. 쿼터가 기간별 사용 총량이라면, rate limit은 초/분 단위 남용 방어다.
- entitlement: 특정 사용자가 어떤 AI 기능을 어떤 플랜/상태로 사용할 수 있는지 나타내는 권한이다.

## 운영 원칙

- 미로그인 사용자는 AI 호출을 할 수 없다.
- 무료 사용자는 AI를 무제한으로 쓰지 못한다.
- 베타 기간에도 일/월 쿼터와 rate limit을 모두 적용한다.
- 관리자도 OpenAI 프로젝트 과금 한도, circuit breaker, `insufficient_quota` 차단을 우회하지 않는다.
- 유료화 전에는 결제 버튼 대신 대기자 등록, 관심 표시, 관리자 수동 업그레이드만 둔다.
- 유료화 후에도 무료 플랜은 유지하되 기능과 쿼터를 낮게 유지한다.

## 출시 모드

| 모드 | 대상 | 동작 | 사용 시점 |
| --- | --- | --- | --- |
| `off` | 관리자 제외 전체 차단 | AI 메뉴는 안내만 표시하고 API 호출 차단 | 비용 사고, 장애, 점검 |
| `private_beta` | 초대/승인 사용자 | allowlist 사용자만 제한 쿼터 제공 | 초기 테스트 |
| `public_beta` | 로그인 사용자 전체 | 낮은 무료 베타 쿼터 제공 | 현재 권장 운영 |
| `paid_ready` | 무료 + 수동 유료 후보 | 결제 없이 플랜 구조와 CTA만 노출 | 유료화 검증 |
| `paid_enforced` | 무료 + 유료 구독자 | 결제 상태에 따라 플랜 쿼터 적용 | 정식 유료화 |

초기 권장값은 `public_beta`다. 지금 이미 로그인 필수, 채팅 일/월 쿼터, rate limit이 있으므로 전체 무료 무제한 상태는 아니다. 다음 단계는 이미지 파싱 일/월 쿼터와 플랜별 권한 분리다.

## 플랜 설계

| 플랜 | 접근 상태 | 페이서 채팅 | 이미지 파싱 | 모델/detail | 주요 메시지 |
| --- | --- | --- | --- | --- | --- |
| `blocked` | 차단 | 0 | 0 | 없음 | AI 기능을 사용할 수 없습니다. |
| `free_beta` | 기본 베타 | 5회/일, 120회/월 | 3회/일, 20회/월 | mini, image detail `low` 우선 | 베타 제공량 안에서 사용할 수 있습니다. |
| `plus_manual` | 수동 확장 | 30회/일, 600회/월 | 10회/일, 200회/월 | mini, 필요 시 `high` | 확장 베타 권한이 적용되었습니다. |
| `paid_plus` | 유료 후보 | 30회/일, 600회/월 | 10회/일, 200회/월 | mini, `high` 허용 | 유료 플랜에서 더 많은 AI 사용량을 제공합니다. |
| `admin` | 운영자 | 100회/일, 2000회/월 | 50회/일, 500회/월 | 점검용 상위 모델 가능 | 운영 점검 권한입니다. |

`paid_plus`는 지금 바로 결제를 붙이지 않아도 이름을 미리 둔다. 결제 전에는 `plus_manual`로 운영자가 특정 사용자에게 같은 수준의 권한을 수동 부여할 수 있게 한다.

## 기능별 쿼터 단위

초기에는 단순 횟수 기반으로 시작한다.

| action | 설명 | 초기 단위 | 추후 개선 |
| --- | --- | --- | --- |
| `chat` | 페이서 AI 대화 | 요청 1회 | 입력/출력 토큰 기반 가중치 |
| `image_parse` | 러닝 캡처 이미지 파싱 | 이미지 1장 | 이미지 detail, OCR 재시도 횟수별 가중치 |
| `training_plan` | 향후 훈련 계획 생성 | 생성 1회 | 계획 기간, 모델 등급별 가중치 |

비용이 커지면 `ai_usage_ledger`에 `estimated_cost_usd`, `input_tokens`, `output_tokens`, `image_detail`을 저장하고, 월 예산을 초과한 사용자를 자동 차단한다.

## 권한 데이터 모델

초기 JSON 또는 DB 테이블 설계:

```text
ai_entitlements
- user_id
- plan: blocked | free_beta | plus_manual | paid_plus | admin
- status: active | paused | expired
- beta_invited_at
- beta_expires_at
- paid_until
- quota_overrides_json
- created_at
- updated_at
```

사용량 원장 설계:

```text
ai_usage_ledger
- id
- user_id
- plan
- action
- model
- day_key
- month_key
- status: reserved | success | failed | blocked
- block_reason
- input_tokens
- output_tokens
- estimated_cost_usd
- response_id
- created_at
```

현재 `ai_usage.json`은 채팅 쿼터 카운터 역할을 한다. 다음 구현에서는 `ai_entitlements`와 `ai_usage_ledger`를 추가해 플랜, 기능별 쿼터, 비용 추정을 분리한다.

## API 응답 계약

AI API는 사용 가능 여부와 CTA를 같은 형태로 반환한다.

```json
{
  "success": false,
  "message": "오늘 무료 베타 AI 사용량을 모두 사용했습니다.",
  "ai_access": {
    "plan": "free_beta",
    "status": "active",
    "action": "chat",
    "allowed": false,
    "reason": "daily_limit",
    "daily_remaining": 0,
    "monthly_remaining": 84,
    "upgrade_available": false,
    "cta": "유료 플랜 준비 중입니다."
  }
}
```

프론트는 `usage`와 별개로 `ai_access`를 읽어 플랜 배지, 남은 사용량, 한도 소진 안내, 유료화 대기 CTA를 표시한다.

## 사용자 화면 정책

- 온보딩: AI는 베타 기능이며 일/월 제공량이 있다는 점을 설명한다.
- AI 채팅 진입: 현재 플랜, 남은 일/월 사용량, 베타 안내를 표시한다.
- 한도 소진: 일 한도는 다음 날 재사용 가능, 월 한도는 다음 달 재사용 가능 문구를 구분한다.
- 유료화 전 CTA: `더 많은 AI 사용량이 필요한가요? 유료 플랜 준비 알림 받기` 정도로 둔다.
- 유료화 후 CTA: 플랜 비교, 결제, 결제 상태 갱신으로 연결한다.
- 이미지 파싱: 채팅과 별도 쿼터임을 업로드 실패 메시지에 명확히 표시한다.

## 서버 판정 순서

AI 요청은 아래 순서로 차단한다.

1. 로그인 여부 확인
2. `ai_entitlements`에서 사용자 plan/status 확인
3. action별 일/월 쿼터 확인
4. rate limit 쿨다운/윈도우 확인
5. 서버 전역 예산/circuit breaker 확인
6. provider 호출
7. 성공/실패/차단 결과를 원장에 기록

이 순서가 중요한 이유는 유료화 후에도 비용을 쓰기 전에 무료/베타/차단 상태를 먼저 걸러야 하기 때문이다.

## 운영 예산 연동

| 조건 | 무료 베타 | plus/manual | admin |
| --- | --- | --- | --- |
| 일 예산 80% | 신규 AI 호출 차단 | 유지 | 유지 |
| 일 예산 100% | 차단 | 차단 | 제한 허용 |
| 월 예산 80% | 차단 또는 image detail `low` | image detail `low` | 유지 |
| 월 예산 95% | 차단 | 차단 | 제한 허용 |
| `insufficient_quota` | 전체 차단 | 전체 차단 | 전체 차단 |

예산 차단은 플랜보다 우선한다. OpenAI 프로젝트 자체 한도에 도달하면 유료 사용자도 실패할 수 있으므로, 유료화 전에는 결제 약관과 장애 안내 정책이 필요하다.

## 유료화 전환 단계

1. `public_beta`: 현재 상태를 유지하되 이미지 파싱 일/월 쿼터를 추가한다.
2. `paid_ready`: `ai_entitlements`와 `ai_access` 응답 계약을 추가하고, 프론트에 플랜/CTA만 표시한다.
3. `manual_plus`: 운영자가 특정 사용자에게 `plus_manual`을 부여해 유료 후보 쿼터를 검증한다.
4. `billing_shadow`: 결제 테이블과 webhook 수신 구조를 만들되 실제 과금은 막고 이벤트만 검증한다.
5. `paid_enforced`: 결제 활성 사용자에게 `paid_plus`를 부여하고 미결제/만료 시 `free_beta`로 강등한다.

## 다음 구현 순서

1. `ai_entitlements` 저장소 또는 DB 테이블 추가
2. `ai_access_policy` 공통 모델 추가
3. `/api/chat`, `/api/parse-image`에서 공통 정책 사용
4. 이미지 파싱 일/월 쿼터 추가
5. 대시보드 AI 화면에 plan/status/CTA 표시
6. 관리자용 사용자 AI 플랜 수동 변경 기능 추가
7. `ai_usage_ledger`와 비용 추정 필드 추가
8. 결제 provider 연동은 마지막 단계에서 별도 작업으로 진행

## 완료 기준

- 무료 사용자가 AI를 무제한 사용할 수 없다.
- 베타 사용량과 유료 후보 사용량이 같은 코드 경로에서 플랜만 다르게 적용된다.
- OpenAI 호출 전에 권한, 쿼터, rate limit, 예산 차단을 모두 검사한다.
- 유료 결제를 붙이기 전에도 UI와 API가 유료화 가능성을 표현할 수 있다.
- 결제 미구현 상태에서도 운영자가 수동으로 확장 베타 권한을 부여할 수 있다.
