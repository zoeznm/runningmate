# 개인 서버 운영 저장 구조 전환 계획

작성일: 2026-06-09

이 문서는 기존 P0 항목의 `RDS 저장 구조 전환`, `S3 저장 구조 전환`을 AWS가 아닌 개인 서버 운영 기준으로 재정의한다.

## 결론

개인 서버로 운영한다면 다음 작업명은 `RDS 전환`이 아니라 `운영 DB 영속화 및 백업 구조 전환`으로 잡는 것이 맞다.

`S3 전환`도 반드시 AWS S3를 의미하지 않는다. 개인 서버에서는 `로컬 파일 저장소 + 백업`, 또는 향후 이전성을 고려한 `MinIO 같은 S3 호환 오브젝트 스토리지`로 바꿔 잡으면 된다.

우선순위는 다음 순서가 안전하다.

1. 러닝 기록 JSON 저장을 운영 DB 테이블로 이전한다.
2. 이미지/영상 파일 저장 경로를 운영 디스크 경로로 분리하고 백업 정책을 건다.
3. 로그인/세션/OAuth 보안을 점검한다.
4. 회원탈퇴 데이터 삭제 정책을 DB/파일 양쪽에 맞춰 구현한다.

## 2026-06-09 구현 상태

이번 작업에서 회원정보는 기존 DB 모델 구조를 유지하고, 러닝 기록 본문을 개인 서버 운영 DB에 저장하도록 1차 전환했다.

- `src/model/db/running_log.py`에 `running_logs` 테이블 모델을 추가했다.
- `src/model/struct.py`의 자동 테이블 생성 목록에 `running_log`를 포함했다.
- `src/model/runningmate.py`의 러닝 기록 읽기/쓰기 경로를 DB 우선으로 바꿨다.
- 최초 DB 접근 시 기존 `running_logs.json`을 `running_logs` 테이블로 자동 이관하고, `running_logs.json.db_migrated` 마커를 남긴다.
- 운영 초기 안전장치로 DB 저장 성공 후 `running_logs.json` 미러를 갱신한다.
- 장애 대응을 위해 `RUNNINGMATE_RUNS_STORAGE=json`으로 되돌릴 수 있게 했다.
- JSON 미러는 `RUNNINGMATE_RUNS_JSON_MIRROR=false`로 끌 수 있다.
- 회원탈퇴 데이터 삭제 흐름에서 `running_logs` DB row와 기존 JSON 미러가 함께 정리되도록 반영했다.

운영 권장값:

```env
RUNNINGMATE_DATA_DIR=/opt/app/data
RUNNINGMATE_RUNS_STORAGE=db
RUNNINGMATE_RUNS_JSON_MIRROR=true
```

초기 배포 후 DB 이관 결과를 확인하고 백업/복구 절차가 안정되면 `RUNNINGMATE_RUNS_JSON_MIRROR=false`로 바꿔 JSON 미러 의존을 줄인다.

## 현재 저장 구조

### DB에 이미 있는 데이터

현재 회원/인증 관련 일부 데이터는 Peewee DB 모델로 정의되어 있다.

- `user`
- `password_resets`
- `social_account`
- `user_agreements`
- `follows`

DB 접속 정보는 런타임 secret인 `RUNNINGMATE_DB_*` 또는 `/opt/app/config/database.env`로 주입하는 구조다.

### JSON 파일에 남아 있는 데이터

러닝메이트 핵심 서비스 데이터 상당수는 `RUNNINGMATE_DATA_DIR`, 기본값 `/opt/app/data` 아래 JSON 파일로 저장된다. `running_logs.json`은 DB 우선 저장으로 전환됐지만, 운영 초기 롤백과 검증을 위해 미러 파일로 남긴다.

- `running_logs.json` - DB 우선 전환 완료, 임시 미러
- `rest_days.json`
- `day_notes.json`
- `weight_logs.json`
- `weight_settings.json`
- `cycle_logs.json`
- `chat_history.json`
- `goals.json`
- `challenges.json`
- `ranking_social.json`
- `badges.json`
- `user_badges.json`
- `run_media.json`
- `run_reactions.json`
- `run_comments.json`
- `notifications.json`

이 상태는 개발/초기 테스트에는 빠르지만, 운영에서는 동시 쓰기, 백업, 복구, 회원탈퇴 삭제 추적, 데이터 무결성 면에서 취약하다.

### 로컬 파일에 저장되는 데이터

- 러닝 캡처 이미지는 `RUNNINGMATE_UPLOAD_DIR`, 기본값 `/opt/app/data/run_images`에 저장되고 `/api/run-images/<filename>`으로 제공된다.
- 러닝 사진/영상은 `RUNNINGMATE_MEDIA_UPLOAD_DIR`, 기본값 `/opt/app/data/run_media`에 저장되고 `/api/run-media/<filename>`으로 제공된다.
- 파일명은 UUID 기반이고 라우트에서 확장자/경로 traversal 방어를 한다.

## 개인 서버 기준 목표 구조

### DB

개인 서버에서는 RDS 대신 자체 운영 DB를 둔다. 현재 프로젝트와 맞추려면 MySQL 또는 MariaDB가 가장 적은 변경으로 간다. PostgreSQL도 가능하지만 ORM/운영 설정 검증 범위가 더 커진다.

권장 기준:

- DB는 앱 서버와 같은 머신 또는 내부망 전용 머신에 둔다.
- DB 포트는 외부 인터넷에 열지 않는다.
- 앱 전용 DB 사용자만 만든다.
- 앱 사용자는 필요한 DB 하나에만 권한을 둔다.
- DB 비밀번호는 저장소가 아니라 `/opt/app/config/database.env` 또는 프로세스 환경변수에만 둔다.
- 운영 전 DB dump 복구 테스트를 실제로 한 번 수행한다.

권장 경로:

```env
RUNNINGMATE_DB_TYPE=mysql
RUNNINGMATE_DB_NAME=runningmate
RUNNINGMATE_DB_USER=runningmate_app
RUNNINGMATE_DB_PASSWORD=<runtime-secret>
RUNNINGMATE_DB_HOST=127.0.0.1
RUNNINGMATE_DB_PORT=3306
RUNNINGMATE_DB_CHARSET=utf8mb4
```

### 러닝 데이터 DB 테이블화

다음 테이블을 추가하는 방향이 좋다.

| 영역 | 테이블 예시 | 현재 JSON |
| --- | --- | --- |
| 러닝 기록 | `running_logs` | `running_logs.json` |
| 휴식일 | `rest_days` | `rest_days.json` |
| 일기/메모 | `day_notes`, `journals` | `day_notes.json` |
| 체중 | `weight_logs`, `weight_settings` | `weight_logs.json`, `weight_settings.json` |
| 주기 기록 | `cycle_logs` | `cycle_logs.json` |
| AI 채팅 | `chat_sessions`, `chat_messages` | `chat_history.json` |
| 목표 | `goals` | `goals.json` |
| 챌린지 | `challenges`, `challenge_members`, `challenge_contributions` | `challenges.json` |
| 랭킹/소셜 | `ranking_social`, `run_reactions`, `run_comments` | `ranking_social.json`, `run_reactions.json`, `run_comments.json` |
| 미디어 메타데이터 | `run_media` | `run_media.json` |
| 알림 | `notifications` | `notifications.json` |
| 뱃지 | `badges`, `user_badges` | `badges.json`, `user_badges.json` |

전환 순서:

1. DB 모델을 먼저 추가한다.
2. JSON에서 DB로 옮기는 migration 스크립트를 만든다.
3. `runningmate.py`의 읽기/쓰기 경로를 DB 우선으로 바꾼다.
4. 이전 JSON은 일정 기간 읽기 전용 백업으로 보관한다.
5. 회원탈퇴 시 DB row와 관련 파일을 같은 트랜잭션 정책으로 삭제한다.

### 파일 저장소

AWS S3를 쓰지 않는다면 두 가지 선택지가 있다.

| 선택지 | 권장 상황 | 장점 | 주의점 |
| --- | --- | --- | --- |
| 로컬 파일 저장소 | 지금 바로 개인 서버 1대에서 운영 | 구현 변경이 작다 | 디스크 장애와 백업 실패가 곧 데이터 손실이다 |
| MinIO | 나중에 S3 또는 다른 서버로 옮길 가능성이 큼 | S3 호환 API로 이식성이 좋다 | 운영 컴포넌트가 하나 늘어난다 |

초기 개인 서버 운영은 로컬 파일 저장소로 시작해도 된다. 대신 저장 경로를 앱 코드/임시 디렉토리와 분리해야 한다.

권장 경로:

```env
RUNNINGMATE_DATA_DIR=/opt/app/data
RUNNINGMATE_UPLOAD_DIR=/opt/app/data/run_images
RUNNINGMATE_MEDIA_UPLOAD_DIR=/opt/app/data/run_media
RUNNINGMATE_MAX_UPLOAD_BYTES=10485760
RUNNINGMATE_MAX_MEDIA_UPLOAD_BYTES=52428800
```

운영 디렉토리 기준:

```text
/opt/app/data/
  run_images/
  run_media/
  backups/
```

파일 저장소 운영 기준:

- 앱 실행 사용자만 쓰기 권한을 갖는다.
- 웹 서버가 디렉토리 listing을 하지 못하게 한다.
- 업로드 파일은 기존처럼 UUID 파일명만 허용한다.
- 원본 파일은 백업 대상에 포함한다.
- 회원탈퇴 또는 러닝 기록 삭제 시 DB metadata와 파일을 함께 삭제한다.

## 백업 정책

개인 서버 운영에서 가장 중요한 차이는 장애 책임이 운영자에게 있다는 점이다. RDS/S3를 쓰지 않는 만큼 백업과 복구 훈련이 필수다.

권장 최소 기준:

- DB logical dump: 하루 1회 이상
- 공개 서비스 후 DB dump: 6시간마다 또는 binlog 기반 PITR 구성
- 미디어 파일: 매일 증분 백업
- 보관: 최근 7일 일별, 최근 4주 주별, 최근 3개월 월별
- 백업 암호화: 필수
- 백업 위치: 같은 디스크가 아닌 별도 디스크 또는 다른 장비
- 복구 테스트: 배포 전 1회, 이후 월 1회

클라우드를 전혀 쓰지 않는다면 최소한 외장 디스크 또는 다른 집/사무실 장비로 암호화 백업을 복제해야 한다.

## 보안 기준

- DB 포트는 외부 공개 금지, 앱 서버에서만 접근한다.
- SSH는 key 기반 로그인만 허용하고 비밀번호 로그인은 끈다.
- HTTP는 HTTPS로만 서비스한다.
- OAuth redirect URI는 운영 도메인 기준으로 고정한다.
- `/opt/app/data`와 `/opt/app/config/*.env`는 앱 사용자와 운영자만 읽을 수 있게 한다.
- 로그에 DB 비밀번호, OAuth secret, OpenAI key, 업로드 원본 경로를 남기지 않는다.
- 백업 파일에도 개인정보가 포함되므로 백업 접근 권한과 삭제 정책을 개인정보처리방침에 반영한다.

## 다음 구현 작업 제안

이번 작업으로 아래 P0의 1차 구현은 완료했다.

> `[P0] 회원정보/러닝기록 개인 서버 운영 DB 저장 구조 전환`

완료 범위:

1. `running_logs` DB schema를 추가했다.
2. 기존 JSON 러닝 기록을 DB로 자동 이관한다.
3. `runningmate.py`의 러닝 기록 읽기/쓰기 경로를 DB 우선으로 바꿨다.
4. 회원탈퇴 시 러닝 기록 DB row와 JSON 미러를 함께 삭제한다.

남은 후속 범위:

1. 미디어 metadata, 댓글/반응, 목표/챌린지, 알림, 채팅, 체중, 주기 기록을 DB 모델로 분리한다.
2. 마이그레이션 전후 레코드 수와 주요 화면 API 응답을 인증 세션으로 비교한다.
3. `/opt/app/data` 운영 경로와 백업 스크립트를 추가한다.
4. DB dump 복구 테스트와 JSON 미러 종료 시점을 정한다.

그 다음 P0는 아래 이름으로 진행한다.

> `[P0] 러닝 이미지/영상 개인 서버 파일 저장 및 백업 구조 전환`

초기에는 로컬 파일 저장소를 유지하되, 경로를 `/opt/app/data`로 고정하고 백업/복구/삭제 정책을 먼저 완성한다. 이후 필요하면 MinIO로 교체한다.
