# DB 런타임 secret 파일 생성 및 검증 통과

- **ID**: 019
- **날짜**: 2026-06-09
- **유형**: 설정 변경

## 작업 요약

서버 런타임 config 경로에 `/opt/app/config/database.env`를 생성하고 기존 DB 접속 항목을 값 출력 없이 주입했다.
파일 권한은 `600`으로 설정했고, 운영 secret 검증 스크립트가 통과하는지 확인했다.

## 원문 요청사항

```text
그냥 해주면 좋겠는데 ? db도 database.env 파일 만들어주고
```

## 변경 파일 목록

- `/opt/app/config/database.env`
  - DB 런타임 환경변수 파일 생성.
  - 비밀값은 devlog와 응답에 기록하지 않음.
  - 권한 `600` 적용.
- `docs/secret-audit-2026-06-09.md`
  - DB runtime secret 파일 생성 및 관리형 Secret 이관 권고 상태로 갱신.
- `devlog.md`, `devlog/2026-06-09/019-database-runtime-secret-env.md`
  - 작업 이력 추가.

## 확인 결과

- `python scripts/verify_runtime_secrets.py` 통과.
- `/opt/app/config/database.env` 권한 `600` 확인.
- DB 필수 환경변수 키는 모두 값이 설정된 상태로 확인했으며, 실제 값은 출력하지 않음.
- 프로젝트 내부 고신뢰 키 패턴 및 평문 비밀번호 할당 패턴 스캔 결과 `HITS=0`.
