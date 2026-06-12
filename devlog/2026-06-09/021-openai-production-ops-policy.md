# 021. 운영용 OpenAI 프로젝트 및 과금 방어 정책 문서화

- 날짜: 2026-06-09
- 요청: "러닝메이트 운영용 OpenAI Platform 프로젝트를 기준으로 필요한 API 키, 모델 설정, 과금 한도, 사용량 알림, rate limit 대응 정책을 정리해주세요. 무료 사용자/일반 사용자/관리자 기준 사용량 제한안도 포함하고, 과금 폭증을 막기 위한 서버 측 방어 기준을 제안해주세요."

## 변경 파일

- `docs/openai-production-ops-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/021-openai-production-ops-policy.md`

## 작업 내용

- OpenAI Platform 운영 프로젝트, 서비스 계정, API 키 보관, 권한, IP allowlist, 키 로테이션 기준을 정리했다.
- 현재 러닝메이트 AI 호출 코드의 env 변수와 기본 모델 설정을 기준으로 채팅/이미지 파싱/관리자 점검 모델 정책을 문서화했다.
- OpenAI 프로젝트 과금 한도, 사용량 알림 구간, daily/monthly budget circuit breaker 기준을 제안했다.
- 무료 사용자, 일반 사용자, 관리자별 채팅/이미지 파싱 제한안을 정리했다.
- rate limit, `insufficient_quota`, 401/403/503 대응 정책과 서버 측 비용 폭증 방어 기준을 정리했다.

## 확인 결과

- OpenAI 공식 문서의 최신 모델, rate limit, error code, production API key, RBAC 내용을 확인해 문서 근거로 연결했다.
- 현재 코드의 OpenAI 관련 라우트와 사용자 role 구조를 확인하고, 이미 구현된 방어와 추가 구현 필요 항목을 분리했다.
