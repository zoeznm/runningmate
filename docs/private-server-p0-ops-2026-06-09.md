# 개인 서버 배포 전 P0 운영 전환 기록

작성일: 2026-06-09

이 문서는 AWS RDS/S3 대신 개인 서버에서 러닝메이트를 운영하는 기준으로, 남은 P0 항목 3개를 구현/점검한 결과를 정리한다.

## 1. 러닝 이미지/영상 개인 서버 파일 저장 및 백업 구조 전환

적용한 기준:

- 러닝 캡처 이미지는 `RUNNINGMATE_UPLOAD_DIR`, 기본값 `/opt/app/data/run_images`에 저장한다.
- 러닝 사진/영상은 `RUNNINGMATE_MEDIA_UPLOAD_DIR`, 기본값 `/opt/app/data/run_media`에 저장한다.
- 앱 데이터 JSON 미러와 잔여 JSON 저장소는 `RUNNINGMATE_DATA_DIR`, 기본값 `/opt/app/data`에 둔다.
- 백업 산출물은 `RUNNINGMATE_BACKUP_DIR`, 기본값 `/opt/app/data/backups`에 만든다.
- 백업 스크립트는 `scripts/backup-runningmate-private-server.sh`로 추가했다.

운영 서버 권장 디렉토리:

```bash
sudo mkdir -p /opt/app/data/run_images /opt/app/data/run_media /opt/app/data/backups
sudo chown -R <app-user>:<app-user> /opt/app/data
sudo chmod 700 /opt/app/data /opt/app/data/backups
```

백업 실행 예:

```bash
RUNNINGMATE_DATA_DIR=/opt/app/data \
RUNNINGMATE_UPLOAD_DIR=/opt/app/data/run_images \
RUNNINGMATE_MEDIA_UPLOAD_DIR=/opt/app/data/run_media \
RUNNINGMATE_BACKUP_DIR=/opt/app/data/backups \
bash scripts/backup-runningmate-private-server.sh
```

DB 백업은 비밀번호를 커맨드라인에 직접 넣지 않도록 `RUNNINGMATE_DB_MYSQL_DEFAULTS_FILE`을 사용한다. 현재 서버는 `/opt/app/config/mysql-backup.cnf`에 `[client]` 설정을 두고 파일 권한을 `600`으로 제한한다.

## 2. 로그인/세션/OAuth 보안 설정 점검

확인 및 보강한 항목:

- Flask/WIZ 세션은 `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SECURE=true`, `SESSION_COOKIE_SAMESITE=Lax` 운영값을 사용한다.
- 인증 API는 `Cache-Control: no-store`, `Pragma: no-cache`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin` 헤더를 적용한다.
- OAuth 설정 파일은 `/opt/app/config/oauth.env`만 로드하도록 좁혔다.
- OAuth redirect URI는 `RUNNINGMATE_PUBLIC_BASE_URL`, provider별 redirect env, `RUNNINGMATE_ALLOWED_ORIGINS` 기준 host만 허용한다.
- OAuth state 검증은 `secrets.compare_digest`를 사용하고, TTL은 `RUNNINGMATE_OAUTH_STATE_TTL_SECONDS`로 제한한다.
- OAuth 실패 로그는 token, code, client secret 계열 값을 마스킹한다.
- Google OAuth는 이메일 인증 여부를 확인한다.
- 비밀번호 변경 시 세션 버전을 갱신해 기존 토큰/세션을 무효화할 수 있다.

운영 필수 env:

```env
WIZ_SECRET_KEY=<long-random-secret>
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=Lax
RUNNINGMATE_PUBLIC_BASE_URL=https://<production-domain>
RUNNINGMATE_ALLOWED_ORIGINS=https://<production-domain>
RUNNINGMATE_OAUTH_REQUIRE_PUBLIC_BASE_URL=true
RUNNINGMATE_OAUTH_STATE_TTL_SECONDS=600
```

## 3. 개인정보처리방침 및 회원탈퇴 데이터 삭제 정책 준비

적용한 기준:

- 개인정보처리방침 버전을 `1.2`, 시행일을 `2026-06-09`로 올렸다.
- 개인정보처리방침에 개인 서버 저장, 백업 보관, OAuth 연결 정보, 회원탈퇴 삭제/익명화 범위를 반영했다.
- 마이페이지 계정 삭제 안내 문구를 실제 삭제 범위와 맞췄다.
- 계정 삭제 시 소셜 로그인 연결과 비밀번호 재설정 토큰도 DB에서 삭제한다.
- 기존 삭제 흐름은 러닝 기록, 러닝 이미지/영상 파일, 휴식일, 메모, 체중, 주기, 목표, 뱃지, 채팅, 챌린지, 소셜 관계, 댓글/반응, 알림을 정리한다.

삭제/익명화 기준:

| 데이터 | 처리 |
| --- | --- |
| 회원 계정, 약관 동의, OAuth 연결, 비밀번호 재설정 토큰 | 삭제 |
| 러닝 기록 DB row와 JSON 미러 | 삭제 |
| 러닝 이미지/영상 파일 | 삭제 |
| 휴식일, 메모, 체중, 주기, 목표, 뱃지, 채팅, 알림 | 삭제 |
| 팔로우/친구 관계 | 삭제 |
| 챌린지 생성/참여 이력 | 탈퇴한 사용자로 익명화 또는 삭제 |
| 백업 내 과거 데이터 | 보관 주기 종료 시 순차 파기 |

## 배포 전 확인

1. `/opt/app/data` 하위 디렉토리 권한이 앱 실행 사용자 전용인지 확인한다.
2. 새 파일 업로드 후 `/api/run-images/<filename>`, `/api/run-media/<filename>` 응답이 200인지 확인한다.
3. 백업 스크립트를 실행하고 `data.tar.gz`, `run_images.tar.gz`, `run_media.tar.gz`, DB 백업 파일 생성 여부를 확인한다.
4. OAuth provider 콘솔의 redirect URI가 운영 도메인의 `/access`와 일치하는지 확인한다.
5. HTTPS 환경에서 session cookie가 `Secure`, `HttpOnly`, `SameSite=Lax`로 발급되는지 브라우저 개발자 도구에서 확인한다.
6. 테스트 계정으로 계정 삭제를 실행해 DB row, JSON 미러, 업로드 파일이 함께 삭제되는지 확인한다.
