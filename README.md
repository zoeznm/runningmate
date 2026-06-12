# 러닝메이트

러닝메이트는 개인 러닝 기록을 관리하고, 목표/챌린지/커뮤니티/AI 페이서 기능을 한 화면에서 사용할 수 있게 만든 WIZ 기반 웹 서비스입니다. 이미지 기록 업로드, 러닝 캘린더, 체중/훈련 분석, 친구/랭킹, 피드, AI 채팅, 개인 서버 운영을 함께 고려한 프로젝트입니다.

이 저장소는 더 이상 WIZ 샘플 프로젝트가 아니라 러닝메이트 서비스 코드와 운영 문서를 담는 프로젝트입니다.

## 핵심 기능

- 러닝 기록 업로드와 직접 입력
  - 거리, 페이스, 시간, 심박, 케이던스, 고도, 칼로리, 일기, 사진/영상 관리
  - 이미지 기반 기록 파싱과 사용자별 월간 파싱 한도
- 대시보드와 캘린더
  - 주간/월간 요약, 기록 달력, 날씨, 생리주기/컨디션 기록, 갤러리
- 목표와 챌린지
  - 월간 목표, 개인 목표, 그룹 챌린지, 초대코드, 진행률 관리
- 커뮤니티
  - 피드, 반응, 댓글, 친구코드, 팔로잉/팔로워, 전체/친구 랭킹
- 계정과 보안
  - 이메일 로그인, 회원가입, 비밀번호 재설정, Google/Naver OAuth, JWT/세션 보강
  - 약관/개인정보처리방침 동의와 재동의
- AI 페이서
  - OpenAI 기반 채팅, 기록 분석, 페르소나 설정, 일/월 사용량 제한
- 개인 서버 운영
  - MySQL/MariaDB, 로컬 미디어 저장소, 서명 URL, ClamAV 스캔, 백업/복구, 헬스체크, 로그 알림
- 모바일 배포 준비
  - PWA 설정과 Capacitor iOS shell

## 기술 스택

| 영역 | 사용 기술 |
| --- | --- |
| 앱 프레임워크 | WIZ / Season Framework |
| 프론트엔드 | Angular 18, TypeScript, Pug, SCSS, Tailwind CSS |
| 백엔드 | Python, Flask 기반 WIZ route/controller |
| 데이터 모델 | Peewee ORM, WIZ Struct 패턴 |
| 운영 DB | MySQL 또는 MariaDB 권장 |
| 파일 저장 | 개인 서버 로컬 디스크 경로 + 서명 URL + 백업 |
| AI | OpenAI API |
| 인증 | 이메일/비밀번호, JWT, Google/Naver OAuth |
| 모바일 | Capacitor iOS |
| 운영 | Nginx, healthcheck, log watch, backup scripts |

## 프로젝트 구조

```text
src/
├── app/                      # WIZ Source app: page, component, layout
│   ├── page.access/          # 로그인/회원가입/비밀번호 재설정
│   ├── page.dashboard/       # 러닝메이트 메인 앱 경험
│   ├── page.members/         # 관리자 멤버 관리
│   ├── page.mypage/          # 내 정보/탈퇴/계정 설정
│   └── component.*/          # 로딩, 오류, 토스트, 네비게이션 등
├── angular/                  # Angular build shell과 shared client utilities
├── controller/               # WIZ controller: base/user/admin guard
├── model/                    # 러닝메이트 도메인 모델, DB model, 보안/OAuth/helper
├── route/                    # REST API endpoint
├── assets/                   # 브랜드 이미지, 폰트, 오류 페이지
└── portal/                   # WIZ portal packages

docs/                         # 운영/보안/배포/AI/개인 서버 문서
ops/                          # nginx 등 운영 설정 예시
scripts/                      # 백업, 헬스체크, 로그 감시, secret 검증, migration
ios/                          # Capacitor iOS shell
devlog/                       # ReviewOps/Codex 작업 상세 로그
```

현재 WIZ 프로젝트 기준 app 수:

- page 6개
- component 7개
- layout 2개
- route 59개
- portal package 2개

## 실행과 빌드

현재 WIZ 런타임 기준 실행 흐름:

```bash
cd /opt/app
pip install -U season
wiz service regist app 3000
wiz service start app
```

프로젝트 빌드:

```bash
cd /opt/app
wiz bundle --project=main
```

Angular 단독 점검:

```bash
cd /opt/app/project/main/src/angular
npm install
npm run build
```

운영 재시작 helper:

```bash
cd /opt/app/project/main
scripts/runningmate_restart_wiz_app.sh
```

## 환경변수와 secret

예시 키 목록은 `.env.example`에 정리되어 있습니다. 실제 secret은 Git에 넣지 않고 `/opt/app/config/*.env` 또는 운영 환경변수로만 주입합니다.

주요 범주:

- 기본/세션/도메인: `WIZ_SECRET_KEY`, `RUNNINGMATE_PUBLIC_BASE_URL`, `RUNNINGMATE_ALLOWED_ORIGINS`
- DB: `RUNNINGMATE_DB_TYPE`, `RUNNINGMATE_DB_HOST`, `RUNNINGMATE_DB_NAME`, `RUNNINGMATE_DB_USER`, `RUNNINGMATE_DB_PASSWORD`
- 데이터/업로드: `RUNNINGMATE_DATA_DIR`, `RUNNINGMATE_UPLOAD_DIR`, `RUNNINGMATE_MEDIA_UPLOAD_DIR`, `RUNNINGMATE_FILE_URL_SECRET`
- AI/OpenAI: `OPENAI_API_KEY`, `RUNNINGMATE_AI_PROVIDER`, `RUNNINGMATE_CHAT_MODEL`, `RUNNINGMATE_VISION_MODEL`, quota/rate limit 변수
- OAuth: Google/Naver client id, secret, redirect URI
- 메일: SendGrid 또는 SMTP 설정
- 백업/운영: backup, rclone, healthcheck, log watch, restart command

운영 secret 검증:

```bash
cd /opt/app/project/main
python scripts/verify_runtime_secrets.py
```

## 주요 API

| 범주 | Endpoint 예시 |
| --- | --- |
| 인증 | `/api/auth/login`, `/api/auth/register`, `/api/auth/me`, `/api/auth/refresh`, `/api/auth/logout` |
| OAuth | `/api/auth/oauth/google/start`, `/api/auth/oauth/naver/start` |
| 러닝 기록 | `/api/runs`, `/api/runs/<run_id>`, `/api/runs/<run_id>/media` |
| 미디어 | `/api/run-images/<path>`, `/api/run-media/<path>`, `/api/media/<media_id>` |
| 커뮤니티 | `/api/feed`, `/api/follows/*`, `/api/friends/code`, `/api/ranking/weekly` |
| 목표/챌린지 | `/api/goals/<year_month>`, `/api/challenges`, `/api/challenges/join` |
| AI | `/api/chat`, `/api/parse-image`, `/api/ai-config` |
| 분석 | `/api/stats/*`, `/api/training-load`, `/api/weather/monthly`, `/api/weights` |
| 운영 | `/healthz`, `/sw.js`, `/manifest.json` |

## 개인 서버 배포

개인 서버 운영은 다음 기준으로 준비합니다.

- 앱 내부 포트: `3000`
- 공개: Nginx 80/443 reverse proxy
- 운영 DB: MySQL 또는 MariaDB
- 미디어 저장소: `/opt/app/data/run_images`, `/opt/app/data/run_media`
- 백업: `/opt/app/data/backups` + rclone/외부 저장소 권장
- 헬스체크: `/healthz`
- 로그 감시: `scripts/runningmate_log_watch.py`

Nginx 예시는 `ops/nginx-runningmate.conf.example`에 있습니다. 개인 서버를 ReviewOps에 등록하려면 `/api/`, `/auth/`, `/healthz`, `/sw.js`, `/manifest.json`, `/socket.io/`가 정적 SPA fallback이 아니라 WIZ 앱 upstream으로 가야 합니다.

## 배포 산출물 관리

`runningmate-deploy*.tar.gz`, split part, checksum, reassemble 안내 파일은 Git에 커밋하지 않습니다. 배포 기준 commit에 tag를 붙이고, 압축본과 checksum은 GitHub Release 또는 외부 artifact 저장소에 올립니다.

자세한 기준은 `docs/deployment-artifact-management-2026-06-12.md`를 참고합니다.

## iOS shell

Capacitor 기반 iOS shell이 포함되어 있습니다.

```bash
cd /opt/app/project/main
npm install
npm run ios:sync
npm run ios:open
```

Linux 서버에서는 Xcode가 없어 `.ipa` 생성과 TestFlight/App Store 업로드를 완료할 수 없습니다. `npm run ios:open` 이후 서명, Archive, 업로드는 macOS Xcode에서 진행합니다.

## 운영 문서

| 문서 | 내용 |
| --- | --- |
| `docs/raspberry-pi-deployment-checklist-2026-06-11.md` | 라즈베리파이/개인 서버 배포 준비 체크리스트 |
| `docs/private-server-storage-plan-2026-06-09.md` | 개인 서버 저장 구조 전환 계획 |
| `docs/private-server-ops-alert-rollback-2026-06-09.md` | 로그/알림/장애 대응/롤백 절차 |
| `docs/private-server-secret-inventory-2026-06-10.md` | secret 배치와 이전 전후 체크리스트 |
| `docs/private-server-p2-security-plan-2026-06-10.md` | 보안 작업 계획 |
| `docs/reviewops-private-server-registration-2026-06-12.md` | ReviewOps 개인 서버 등록 조건 |
| `docs/deployment-artifact-management-2026-06-12.md` | 배포 압축 산출물 관리 기준 |
| `docs/codex-runtime-flow.md` | 서비스 내부 AI/Codex 런타임 흐름 |
| `docs/openai-production-ops-2026-06-09.md` | OpenAI 운영 정책과 과금 방어 |

## Git 작업 원칙

- 기능별로 커밋합니다.
- 배포 산출물과 secret은 커밋하지 않습니다.
- 작업 기록은 `devlog.md`와 `devlog/YYYY-MM-DD/`에 남깁니다.
- 개인 서버 배포 기준 commit은 tag를 붙이고, release asset으로 압축본을 관리합니다.
