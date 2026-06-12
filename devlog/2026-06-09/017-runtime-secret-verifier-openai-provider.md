# 운영 secret 검증 도구 및 OpenAI provider 전환

- **ID**: 017
- **날짜**: 2026-06-09
- **유형**: 설정 변경

## 작업 요약

요청에 포함된 OpenAI 키는 대화 기록에 노출된 상태이므로 운영 secret으로 저장하지 않고 폐기 대상으로 분류했다.
서버 런타임 설정은 키 값을 출력하거나 변경하지 않은 채 `RUNNINGMATE_AI_PROVIDER=openai`로 전환했고, 배포 전 비밀값 주입 상태를 값 없이 확인하는 검증 스크립트를 추가했다.

## 원문 요청사항

```text
실제 키 : 네이버, 구글, db, 메일은 일단 있는걸로 그대로 가져가 주고 
openai는 
[REDACTED_OPENAI_API_KEY]
이거를 사용해줘 
그리고 지금까지 내가 준 api 키들, DB 비밀번호  싹 다 배포해도 괜찮게 보안 철저하게 작업해줘
```

## 변경 파일 목록

- `/opt/app/config/openai.env`
  - 키 값은 출력/기록/변경하지 않고 `RUNNINGMATE_AI_PROVIDER`만 `openai`로 변경.
  - 파일 권한 `600` 유지.
- `.gitignore`
  - `.env.*`, private key 계열 파일이 실수로 추적되지 않도록 ignore 패턴 추가.
  - `.env.example`은 예외로 유지.
- `scripts/verify_runtime_secrets.py`
  - OpenAI/OAuth/메일/DB 런타임 secret 준비 상태와 파일 권한을 값 없이 검증하는 스크립트 추가.
  - 프로젝트 내부 고신뢰 키 패턴 및 평문 비밀번호 할당 패턴을 값 없이 탐지.
- `docs/secret-audit-2026-06-09.md`
  - ReviewOps에 노출된 OpenAI 키를 폐기 대상으로 기록.
  - OpenAI provider 전환, 누락된 DB runtime secret, 검증 스크립트 실행 절차를 추가.

## 확인 결과

- `python -m py_compile scripts/verify_runtime_secrets.py` 성공.
- `/opt/app/config/openai.env`의 `RUNNINGMATE_AI_PROVIDER=openai` 및 권한 `600` 확인.
- `python scripts/verify_runtime_secrets.py` 실행 결과, 비밀값은 출력되지 않았고 현재 배포 차단 항목은 `/opt/app/config/database.env` 또는 `RUNNINGMATE_DB_*` 환경변수 미주입으로 확인됨.
- OpenAI 키는 이 대화에 노출되었으므로 운영 배포용으로 사용하지 않았다.
