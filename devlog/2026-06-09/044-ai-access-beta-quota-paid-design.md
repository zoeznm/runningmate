# AI 베타·쿼터·유료화 접근 정책 설계

## 사용자 요청

AI 기능을 무료 전체 개방하지 말고 베타/쿼터/유료화 가능성까지 설계. 이거 그러면 설계 바로 해줘

## 변경 파일

- `docs/ai-access-beta-quota-paid-design-2026-06-09.md`
- `docs/openai-production-ops-2026-06-09.md`
- `README.md`
- `devlog.md`
- `devlog/2026-06-09/044-ai-access-beta-quota-paid-design.md`

## 변경 내용

- AI 기능을 전체 무료 무제한으로 개방하지 않기 위한 별도 설계 문서를 추가했다.
- 베타, 쿼터, rate limit, entitlement의 의미를 정리했다.
- `off`, `private_beta`, `public_beta`, `paid_ready`, `paid_enforced` 출시 모드를 정의했다.
- `free_beta`, `plus_manual`, `paid_plus`, `admin` 플랜과 기능별 쿼터 기준을 정리했다.
- 향후 `ai_entitlements`, `ai_usage_ledger`, `ai_access` API 응답 계약, 유료화 전환 단계를 설계했다.
- 기존 OpenAI 운영 문서와 README에서 새 설계 문서로 연결했다.

## 확인한 내용

- 새 설계 문서 생성 확인
- README 및 OpenAI 운영 문서의 설계 문서 링크 확인
- WIZ 프로젝트 빌드 통과
