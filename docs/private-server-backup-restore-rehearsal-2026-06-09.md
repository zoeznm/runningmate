# 개인 서버 백업/복구 리허설 결과

작성일: 2026-06-09

## 적용 기준

- DB 백업 계정: `runningmate_backup`
- DB 백업 host: `10.244.%`
- DB 백업 대상: `rundb`
- 백업 저장 위치: `/opt/app/data/backups`
- 파일 백업 대상:
  - `/opt/app/data` 중 `backups`, `run_images`, `run_media` 제외
  - `/opt/app/data/run_images`
  - `/opt/app/data/run_media`
- 복구 리허설 방식:
  - 백업 덤프를 임시 DB에 복원
  - 운영 DB와 임시 복구 DB의 테이블별 row count 비교
  - 미디어 tar archive 열람 가능 여부와 member 수 확인
  - 성공 후 임시 DB 삭제

## 생성된 백업

- 백업 디렉터리: `/mnt/data/data/backups/20260609T145458Z`
- 산출물:
  - `database.sql.gz`
  - `data.tar.gz`
  - `run_images.tar.gz`
  - `run_media.tar.gz`
  - `manifest.txt`
  - `restore-rehearsal-report.json`

## 복구 리허설 결과

- 결과: 성공
- 임시 복구 DB: `rundb_restore_rehearsal_20260609145519`
- 임시 복구 DB 삭제: 완료
- 운영 DB 테이블 수: 8
- 복구 DB 테이블 수: 8
- row count mismatch: 없음
- 파일 archive 확인:
  - `data.tar.gz`: member 101개
  - `run_images.tar.gz`: member 19개
  - `run_media.tar.gz`: member 3개

## 운영 절차

백업 생성:

```bash
cd /opt/app/project/main
scripts/backup-runningmate-private-server.sh
```

최신 백업 복구 리허설:

```bash
cd /opt/app/project/main
/opt/conda/envs/app/bin/python scripts/runningmate_restore_rehearsal.py
```

특정 백업 복구 리허설:

```bash
cd /opt/app/project/main
/opt/conda/envs/app/bin/python scripts/runningmate_restore_rehearsal.py --backup-dir /opt/app/data/backups/<timestamp>
```

## 보존 정책 권장

- 일별 백업: 30일
- 월별 백업: 6개월
- 월 1회 복구 리허설
- 개인 서버 전환 후에는 백업 파일을 같은 서버에만 두지 말고 별도 서버/NAS/외장 디스크에도 복사한다.
