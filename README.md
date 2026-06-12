<div align="center">
  <img src="src/assets/brand/icon-512.png" width="180" alt="RunningMate app icon" />

  <h1>RunningMate</h1>

  <p>
    <strong>러닝 기록, AI 페이서, 커뮤니티, 개인 서버 운영까지 한 번에 가져가는 WIZ 기반 러닝 플랫폼</strong>
  </p>

  <p>
    운동 기록 하나를 남기려고 대시보드, 캘린더, 이미지 파싱, 목표/챌린지, 피드, OAuth, signed media, 백업/복구, iOS shell까지 밀어 넣은 프로젝트입니다.
  </p>

  <p>
    <img alt="RunningMate" src="https://img.shields.io/badge/RunningMate-Private_Running_OS-7CFF86?style=for-the-badge" />
    <img alt="Angular" src="https://img.shields.io/badge/Angular_18-TypeScript-DD0031?style=for-the-badge&amp;logo=angular&amp;logoColor=white" />
    <img alt="Python" src="https://img.shields.io/badge/Python-Flask_Routes-3776AB?style=for-the-badge&amp;logo=python&amp;logoColor=white" />
    <img alt="OpenAI" src="https://img.shields.io/badge/OpenAI-AI_Pacer-412991?style=for-the-badge&amp;logo=openai&amp;logoColor=white" />
    <img alt="Private Server" src="https://img.shields.io/badge/Private_Server-Ready-0F766E?style=for-the-badge" />
  </p>

  <p>
    <a href="#빠른-시작">빠른 시작</a>
    · <a href="#기능-지도">기능 지도</a>
    · <a href="#아키텍처">아키텍처</a>
    · <a href="#api-지도">API 지도</a>
    · <a href="#개인-서버-운영">개인 서버 운영</a>
    · <a href="#문서-허브">문서 허브</a>
  </p>
</div>

---

## 프로젝트 정체성

러닝메이트는 단순 러닝 로그 앱이 아닙니다. 개인 서버에서 직접 운영할 수 있는 러닝 서비스 전체 세트를 목표로 합니다.

| 레이어 | 현재 들어있는 것 |
| --- | --- |
| 사용자 경험 | 러닝 업로드, 수동 입력, 월간 캘린더, 대시보드, 갤러리, 목표, 챌린지, 피드 |
| AI | OpenAI 기반 러닝 기록 이미지 파싱, AI 페이서 채팅, 페르소나, 사용량 제한 |
| 소셜 | 친구코드, 팔로우, 랭킹, 피드 반응, 댓글 |
| 계정 | 이메일 인증 흐름, Google/Naver OAuth, JWT/세션, 비밀번호 재설정, 약관 동의 |
| 운영 | MySQL/MariaDB, 로컬 미디어 저장소, signed URL, ClamAV, 백업/복구, healthcheck, log watch |
| 배포 | WIZ bundle, Nginx reverse proxy, ReviewOps 캡처 대응, Capacitor iOS shell |

현재 WIZ 프로젝트 구성:

| 종류 | 개수 |
| --- | ---: |
| page | 6 |
| component | 7 |
| layout | 2 |
| route | 59 |
| portal app | 8 |
| portal route | 2 |

## 기능 지도

### 러닝 기록 엔진

| 기능 | 설명 |
| --- | --- |
| 기록 업로드 | 러닝 스크린샷/이미지 기반 기록 파싱 |
| 수동 입력 | 거리, 시간, 페이스, 심박, 케이던스, 고도, 칼로리, 일기 입력 |
| 미디어 | 사진/영상 업로드, signed URL, 로컬 디스크 저장, 삭제 흐름 |
| 분석 | 주간/월간 요약, 훈련 부하, 체중, 날씨, 컨디션 데이터 |
| 제한 | 사용자별 AI 이미지 파싱/채팅 quota와 rate limit |

### 대시보드와 캘린더

| 화면 | 역할 |
| --- | --- |
| `page.dashboard` | 러닝메이트 메인 경험, 기록/목표/피드/AI 진입점 |
| 월간 캘린더 | 러닝 기록, 컨디션, 갤러리, 날씨를 날짜 축으로 확인 |
| 통계 카드 | 거리, 시간, 페이스, 연속 기록, 목표 진행률 요약 |
| 갤러리 | 러닝 이미지와 미디어를 기록 단위로 탐색 |

### 커뮤니티와 챌린지

| 기능 | 설명 |
| --- | --- |
| 피드 | 공개/친구 범위 러닝 기록 공유 |
| 반응/댓글 | 기록에 대한 소셜 액션 |
| 친구코드 | 개인 초대/친구 연결 |
| 랭킹 | 전체/친구 기준 주간 랭킹 |
| 챌린지 | 초대코드 기반 그룹 챌린지와 진행률 |

### 계정과 보안

| 기능 | 설명 |
| --- | --- |
| 인증 | 이메일/비밀번호, JWT refresh, 세션 보강 |
| OAuth | Google/Naver login start/callback |
| 약관 | 서비스 약관/개인정보처리방침 동의 및 재동의 |
| Secret | `.env.example` 기준으로 운영 secret 분리 |
| 미디어 보안 | signed URL, 경로 정규화, ClamAV 스캔 준비 |

## 빠른 시작

### 1. WIZ 런타임 실행

```bash
cd /opt/app
pip install -U season
wiz service regist app 3000
wiz service start app
```

### 2. 프로젝트 번들

```bash
cd /opt/app
wiz bundle --project=main
```

### 3. Angular 단독 점검

```bash
cd /opt/app/project/main/src/angular
npm install
npm run build
```

### 4. 운영 secret 검증

```bash
cd /opt/app/project/main
python scripts/verify_runtime_secrets.py
```

### 5. WIZ 앱 재시작 helper

```bash
cd /opt/app/project/main
scripts/runningmate_restart_wiz_app.sh
```

## 아키텍처

```text
Browser / ReviewOps / iOS WebView
        |
        v
Nginx 80/443
        |
        +-- static assets, manifest, service worker
        |
        v
WIZ app :3000
        |
        +-- src/app          Angular page/component/layout
        +-- src/route        REST endpoints
        +-- src/controller   auth/admin/base guards
        +-- src/model        domain logic, security, OAuth, DB models
        +-- src/portal       season/post reusable packages
        |
        +-- MySQL/MariaDB
        +-- local media storage
        +-- OpenAI API
        +-- backup/log/health scripts
```

### 디렉터리 지도

```text
src/
├── app/
│   ├── page.access/          # 로그인, 회원가입, 비밀번호 재설정
│   ├── page.dashboard/       # 러닝메이트 메인 앱
│   ├── page.members/         # 관리자 멤버 관리
│   ├── page.mypage/          # 내 정보, 탈퇴, 계정 설정
│   └── component.*/          # 토스트, 로딩, 오류, 네비게이션
├── angular/                  # Angular shell, routing, shared API client
├── controller/               # WIZ controller guard
├── model/                    # runningmate domain, auth, OAuth, security
├── route/                    # REST API endpoints
├── assets/                   # 브랜드, 폰트, 오류 페이지
└── portal/                   # season/post packages

docs/                         # 운영, 보안, 배포, AI 문서
ops/                          # nginx 예시 설정
scripts/                      # 백업, 헬스체크, 로그 감시, migration
ios/                          # Capacitor iOS shell
devlog/                       # ReviewOps/Codex 작업 로그
```

## API 지도

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

## 런타임 스위치보드

`.env.example`에 운영 환경변수 예시가 있습니다. 실제 secret은 Git에 넣지 않고 `/opt/app/config/*.env` 또는 서버 환경변수로만 주입합니다.

| 범주 | 대표 변수 |
| --- | --- |
| 기본 | `WIZ_SECRET_KEY`, `RUNNINGMATE_PUBLIC_BASE_URL`, `RUNNINGMATE_ALLOWED_ORIGINS` |
| DB | `RUNNINGMATE_DB_TYPE`, `RUNNINGMATE_DB_HOST`, `RUNNINGMATE_DB_NAME`, `RUNNINGMATE_DB_USER`, `RUNNINGMATE_DB_PASSWORD` |
| 업로드 | `RUNNINGMATE_DATA_DIR`, `RUNNINGMATE_UPLOAD_DIR`, `RUNNINGMATE_MEDIA_UPLOAD_DIR`, `RUNNINGMATE_FILE_URL_SECRET` |
| AI | `OPENAI_API_KEY`, `RUNNINGMATE_AI_PROVIDER`, `RUNNINGMATE_CHAT_MODEL`, `RUNNINGMATE_VISION_MODEL` |
| OAuth | Google/Naver client id, secret, redirect URI |
| 메일 | SendGrid 또는 SMTP 설정 |
| 운영 | backup, rclone, healthcheck, log watch, restart command |

## 개인 서버 운영

러닝메이트는 개인 서버 배포를 전제로 운영 문서를 쌓아둔 상태입니다.

| 항목 | 기준 |
| --- | --- |
| 앱 포트 | WIZ app `3000` |
| 공개 진입점 | Nginx `80/443` reverse proxy |
| DB | MySQL 또는 MariaDB 권장 |
| 미디어 | `/opt/app/data/run_images`, `/opt/app/data/run_media` |
| 백업 | `/opt/app/data/backups` + rclone/외부 저장소 권장 |
| 헬스체크 | `/healthz` |
| 로그 감시 | `scripts/runningmate_log_watch.py` |
| 방화벽 | `scripts/setup-private-server-firewall.sh` |

ReviewOps 캡처가 정상 동작하려면 `/api/`, `/auth/`, `/healthz`, `/sw.js`, `/manifest.json`, `/socket.io/`가 정적 SPA fallback이 아니라 WIZ app upstream으로 전달되어야 합니다.

Nginx 예시는 `ops/nginx-runningmate.conf.example`에 있습니다.

## 배포 산출물 관리

`runningmate-deploy*.tar.gz`, split part, checksum, reassemble 안내 파일은 Git에 커밋하지 않습니다.

권장 흐름:

```text
1. 배포 기준 commit 생성
2. tag 부여
3. tar.gz와 sha256 생성
4. GitHub Release 또는 외부 artifact 저장소에 업로드
5. 서버에서는 checksum 검증 후 배포
```

세부 기준은 `docs/deployment-artifact-management-2026-06-12.md`를 따릅니다.

## iOS shell

Capacitor 기반 iOS shell이 포함되어 있습니다.

```bash
cd /opt/app/project/main
npm install
npm run ios:sync
npm run ios:open
```

Linux 서버에서는 Xcode가 없어 `.ipa` 생성과 TestFlight/App Store 업로드를 완료할 수 없습니다. `npm run ios:open` 이후 서명, Archive, 업로드는 macOS Xcode에서 진행합니다.

## 문서 허브

| 문서 | 내용 |
| --- | --- |
| `docs/raspberry-pi-deployment-checklist-2026-06-11.md` | 라즈베리파이/개인 서버 배포 체크리스트 |
| `docs/private-server-storage-plan-2026-06-09.md` | 개인 서버 저장 구조 전환 계획 |
| `docs/private-server-ops-alert-rollback-2026-06-09.md` | 로그, 알림, 장애 대응, 롤백 |
| `docs/private-server-secret-inventory-2026-06-10.md` | secret 배치와 이전 전후 체크리스트 |
| `docs/private-server-p2-security-plan-2026-06-10.md` | 보안 작업 계획 |
| `docs/reviewops-private-server-registration-2026-06-12.md` | ReviewOps 개인 서버 등록 조건 |
| `docs/deployment-artifact-management-2026-06-12.md` | 배포 압축 산출물 관리 기준 |
| `docs/codex-runtime-flow.md` | 서비스 내부 AI/Codex 런타임 흐름 |
| `docs/openai-production-ops-2026-06-09.md` | OpenAI 운영 정책과 과금 방어 |

## 개발 규칙

| 규칙 | 이유 |
| --- | --- |
| 기능별 커밋 | 나중에 배포/롤백 단위를 정확히 잡기 위해 |
| secret 미커밋 | 개인 서버 운영 키와 OAuth 키 보호 |
| 배포 압축물 미커밋 | Git history 비대화 방지, Release artifact로 분리 |
| devlog 작성 | ReviewOps 세션별 작업 추적 |
| 운영 문서 동반 | 개인 서버 재현성과 장애 대응 속도 확보 |

## Git 원칙

```bash
# 변경 확인
git status -sb

# 기능 단위 커밋
git add <files>
git commit -m "type: concise summary"

# 개인 레포로 push
git push origin main
```

배포 기준 commit에는 tag를 붙이고, 압축 산출물은 GitHub Release 또는 외부 artifact 저장소에서 관리합니다.
