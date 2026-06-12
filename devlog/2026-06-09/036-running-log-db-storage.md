# 러닝 기록 개인 서버 운영 DB 저장 구조 전환

## 사용자 요청

회원정보/러닝기록 개인 서버 운영 DB 저장 구조 전환 작업을 진행하고, 무엇을 했는지도 알려달라는 요청.

## 변경 파일

- `src/model/db/running_log.py`: 개인 서버 운영 DB용 `running_logs` 테이블 모델 추가
- `src/model/struct.py`: `running_log` 테이블 자동 생성 목록 포함
- `src/model/runningmate.py`: 러닝 기록을 DB 우선 읽기/쓰기, 기존 JSON 자동 이관, JSON 미러, 회원탈퇴 삭제 연동으로 전환
- `config/database.py`: DB 기본 charset을 `utf8mb4`로 변경
- `.env.example`: 개인 서버 운영 데이터 경로와 러닝 기록 저장소 전환 env 예시 추가
- `docs/private-server-storage-plan-2026-06-09.md`: 이번 DB 전환 완료 범위와 남은 후속 범위 반영
- `devlog.md`, `devlog/2026-06-09/036-running-log-db-storage.md`: 작업 기록 추가

## 확인 결과

- `python -m py_compile config/database.py src/model/db/running_log.py src/model/struct.py src/model/runningmate.py` 성공
- `wiz_project_build(projectName="main", clean=false)` 성공
- WIZ 런타임 재시작 후 `http://127.0.0.1:3000/access` 200 확인
- WIZ 런타임 재시작 후 `http://127.0.0.1:3000/api/auth/me` 200 확인
- 변경 문서/설정/코드 범위에서 OpenAI, Google, SendGrid 형식의 실제 키 패턴 미검출

## 남은 리스크

- 이번 작업은 러닝 기록 본문 1차 DB 전환이며, 미디어 metadata, 댓글/반응, 목표/챌린지, 알림, 채팅, 체중, 주기 기록은 아직 JSON 저장소를 사용한다.
- 운영 초기 롤백을 위해 `running_logs.json` 미러를 기본 활성화했다. DB 이관과 백업/복구가 검증되면 `RUNNINGMATE_RUNS_JSON_MIRROR=false` 전환이 필요하다.
- 인증된 사용자 세션으로 실제 러닝 기록 생성/수정/삭제 E2E와 마이그레이션 레코드 수 대조가 추가로 필요하다.
