# 049. 개인 서버 백업 생성 및 복구 리허설 완료

- 날짜: 2026-06-09
- 요청: "백업/복구 리허설도 해줘"

## 변경 파일

- `/opt/app/config/backup.env`
- `/opt/app/config/mysql-backup.cnf`
- `scripts/backup-runningmate-private-server.sh`
- `scripts/runningmate_restore_rehearsal.py`
- `docs/private-server-backup-restore-rehearsal-2026-06-09.md`
- `docs/private-server-p0-ops-2026-06-09.md`
- `docs/private-server-storage-plan-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/049-backup-restore-rehearsal.md`

## 변경 내용

- `runningmate_backup` 계정을 현재 앱/백업 실행 네트워크 대역 `10.244.%`에서 사용할 수 있게 설정했다.
- 백업 계정 설정 파일과 `mysqldump` defaults 파일을 생성하고 권한을 `600`으로 제한했다.
- 백업 스크립트 기본 경로를 현재 영속 저장소 `/opt/app/data` 기준으로 보정했다.
- 심볼릭 링크 경로를 실제 경로로 해석해 tar가 링크만 저장하지 않도록 수정했다.
- DB 덤프 옵션을 `single-transaction`, `skip-lock-tables`, `no-tablespaces`, `set-gtid-purged=OFF` 기준으로 정리했다.
- 임시 DB에 덤프를 복원하고 테이블 row count와 파일 archive를 검증하는 리허설 스크립트를 추가했다.
- 백업/복구 리허설 결과 문서를 추가했다.

## 확인 결과

- 백업 계정 DB 읽기 성공: `rundb` 테이블 8개 확인.
- 백업 생성 성공: `/mnt/data/data/backups/20260609T145458Z`.
- 백업 산출물 생성 확인: `database.sql.gz`, `data.tar.gz`, `run_images.tar.gz`, `run_media.tar.gz`, `manifest.txt`.
- 복구 리허설 성공: 임시 DB `rundb_restore_rehearsal_20260609145519`.
- 운영 DB 테이블 수 8개, 복구 DB 테이블 수 8개 일치.
- row count mismatch 없음.
- 파일 archive 확인: `data` 101개, `run_images` 19개, `run_media` 3개.
- 임시 복구 DB 삭제 완료.
