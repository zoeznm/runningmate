# WIZ Sample Project

WIZ 프레임워크 기반 샘플 프로젝트입니다.  
게시판, 사용자 관리, 대시보드 등의 기본 기능을 **Struct 패턴**과 **Portal 패키지** 구조로 구현한 레퍼런스 애플리케이션입니다.

---

## 데모 계정

| 이메일 | 비밀번호 | 이름 | 역할 |
|--------|----------|------|------|
| admin@example.com | admin1234 | 관리자 | admin |
| alice@example.com | alice1234 | Alice Kim | user |
| bob@example.com | bob12345 | Bob Park | user |
| carol@example.com | carol123 | Carol Lee | editor |
| dave@example.com | dave1234 | Dave Choi | viewer |

---

## 프로젝트 구조

```
src/
├── app/                          # Angular Page/Layout/Component
│   ├── layout.sidebar/           # 사이드바 레이아웃 (h-screen, 회색 배경, 스크롤)
│   ├── component.nav.sidebar/    # 사이드바 네비게이션 컴포넌트
│   ├── page.access/              # 로그인 페이지
│   ├── page.dashboard/           # 대시보드 (통계 + 최근 게시물)
│   ├── page.posts/               # 게시물 목록 (라우팅 전용 → post 패키지)
│   ├── page.posts.item/          # 게시물 상세 (라우팅 전용 → post 패키지)
│   ├── page.members/             # 멤버 관리
│   └── page.mypage/              # 내 프로필 / 비밀번호 변경
│
├── controller/                   # 백엔드 전처리 (인증 체인)
│   ├── base.py                   # 세션 초기화
│   └── user.py                   # 로그인 검증 (base 상속)
│
├── model/                        # 프로젝트 고유 Model
│   ├── struct.py                 # 루트 Struct (User + 패키지 동적 로드)
│   ├── struct/
│   │   └── user.py               # User Sub-Struct (인증, CRUD)
│   └── db/
│       └── user.py               # User DB Model (peewee)
│
└── portal/                       # 재사용 패키지
    ├── season/                   # 코어 패키지 (ORM, 세션, Service)
    └── post/                     # 게시물 패키지
        ├── portal.json
        ├── app/
        │   ├── list/             # 게시물 목록 UI 컴포넌트
        │   └── detail/           # 게시물 상세 UI 컴포넌트
        └── model/
            ├── struct.py         # Post Composite Struct
            ├── struct/
            │   ├── post.py       # Post Sub-Struct
            │   └── comment.py    # Comment Sub-Struct
            └── db/
                ├── post.py       # Post DB Model
                └── comment.py    # Comment DB Model
```

---

## 아키텍처 패턴

### Struct 패턴

```
api.py → wiz.model("struct") → src/model/struct.py (Root Struct)
                                  ├── @property user → struct/user.py (Sub-Struct)
                                  └── __getattr__ → wiz.model("portal/{name}/struct")
                                                    └── portal/post/struct.py
                                                        ├── @property post → Post Sub-Struct
                                                        └── @property comment → Comment Sub-Struct
```

### 패키지 기반 컴포넌트

Post 관련 UI는 `portal/post/app/`에 패키지 컴포넌트로 구현되어 있고,  
`page.posts`와 `page.posts.item`은 라우팅 역할만 수행합니다:

```pug
//- page.posts/view.pug (라우팅 전용)
wiz-portal-post-list

//- page.posts.item/view.pug (라우팅 전용)
wiz-portal-post-detail
```

### 레이아웃 구조

- **layout.sidebar**: `h-screen overflow-hidden` + 콘텐츠 영역 `h-full overflow-auto`
- 모든 페이지가 회색(`#f4f5f5`) 배경 위에서 스크롤됩니다.
- 각 페이지의 `nav.sticky` 헤더는 스크롤 영역 상단에 고정됩니다.

---

## 데이터베이스

| DB 파일 | namespace | 테이블 | 용도 |
|---------|-----------|--------|------|
| data/base.db | base | user | 사용자 관리 |
| data/post.db | post | post, comment | 게시물/댓글 |

**설정**: `config/database.py`에서 namespace별 SQLite 경로를 정의합니다.

---

## 주요 API

### 인증
- `POST /wiz/api/page.access/login` — 이메일/비밀번호 로그인

### 게시물 (portal/post 패키지)
- `GET /wiz/api/portal.post.list/categories` — 카테고리 목록
- `GET /wiz/api/portal.post.list/search` — 게시물 검색 (page, dump, text, category)
- `GET /wiz/api/portal.post.detail/get` — 게시물 상세 (id)
- `POST /wiz/api/portal.post.detail/save` — 게시물 저장/수정
- `POST /wiz/api/portal.post.detail/delete` — 게시물 삭제

### 멤버
- `GET /wiz/api/page.members/list` — 멤버 목록 (text, role)
- `POST /wiz/api/page.members/invite` — 멤버 초대
- `POST /wiz/api/page.members/remove` — 멤버 삭제

### 마이페이지
- `GET /wiz/api/page.mypage/get` — 내 프로필 조회
- `POST /wiz/api/page.mypage/update_profile` — 프로필 수정
- `POST /wiz/api/page.mypage/change_password` — 비밀번호 변경

### 러닝메이트 AI 연결
- 운영 배포는 `RUNNINGMATE_AI_PROVIDER=openai`로 설정하고, 운영 OpenAI API 프로젝트에서 발급한 키를 서버 환경 변수 `OPENAI_API_KEY`로 주입합니다.
- `RUNNINGMATE_AI_PROVIDER=codex`는 개발/임시 점검 용도로만 사용합니다. 운영 서비스는 개인 Codex 로그인 상태에 의존하지 않아야 합니다.
- 이미지 파싱은 OpenAI Responses API의 이미지 입력을 사용합니다.
- 기본 모델은 `gpt-5.4-mini-2026-03-17`이며, `RUNNINGMATE_CHAT_MODEL`과 `RUNNINGMATE_VISION_MODEL`로 채팅/이미지 파싱 모델을 각각 변경할 수 있습니다.
- 기본 이미지 상세도는 작은 텍스트 OCR 정확도를 위해 `RUNNINGMATE_IMAGE_DETAIL=high`를 사용합니다. 비용을 줄여야 하면 `low`로 낮출 수 있습니다.
- `insufficient_quota` 오류는 API 크레딧 소진 또는 월 사용 한도 도달 상태입니다. Billing에서 크레딧을 충전하거나 한도를 올린 뒤 다시 시도해야 합니다.
- AI를 전체 무료 무제한으로 개방하지 않기 위한 베타, 쿼터, 유료화 확장 설계는 `docs/ai-access-beta-quota-paid-design-2026-06-09.md`를 기준으로 합니다.

```bash
install -m 600 /dev/null /opt/app/config/openai.env
printf '%s\n' 'OPENAI_API_KEY=<server-injected-openai-api-key>' \
  'RUNNINGMATE_AI_PROVIDER=openai' \
  'RUNNINGMATE_CHAT_MODEL=gpt-5.4-mini-2026-03-17' \
  'RUNNINGMATE_VISION_MODEL=gpt-5.4-mini-2026-03-17' \
  'RUNNINGMATE_IMAGE_DETAIL=high' \
  'RUNNINGMATE_AI_CHAT_DAILY_LIMIT=5' \
  'RUNNINGMATE_AI_CHAT_MONTHLY_LIMIT=120' \
  'RUNNINGMATE_AI_CHAT_ADMIN_DAILY_LIMIT=100' \
  'RUNNINGMATE_AI_CHAT_ADMIN_MONTHLY_LIMIT=2000' \
  'RUNNINGMATE_AI_CHAT_COOLDOWN_SECONDS=10' \
  'RUNNINGMATE_AI_CHAT_RATE_WINDOW_SECONDS=60' \
  'RUNNINGMATE_AI_CHAT_RATE_MAX_REQUESTS=6' \
  'RUNNINGMATE_AI_IMAGE_PARSE_COOLDOWN_SECONDS=30' \
  'RUNNINGMATE_AI_IMAGE_PARSE_RATE_WINDOW_SECONDS=300' \
  'RUNNINGMATE_AI_IMAGE_PARSE_RATE_MAX_REQUESTS=5' \
  'RUNNINGMATE_OPENAI_RETRY_MAX=2' \
  'RUNNINGMATE_OPENAI_BACKOFF_BASE_SECONDS=0.8' \
  'RUNNINGMATE_OPENAI_BACKOFF_MAX_SECONDS=8' \
  'RUNNINGMATE_OPENAI_PROJECT_ID=<runningmate-prod-project-id>' \
  'RUNNINGMATE_OPENAI_DAILY_BUDGET_USD=1' \
  'RUNNINGMATE_OPENAI_MONTHLY_BUDGET_USD=30' \
  'RUNNINGMATE_OPENAI_ALERT_THRESHOLDS=50,80,95,100' \
  'RUNNINGMATE_CODEX_TIMEOUT=180' > /opt/app/config/openai.env
wiz bundle --project=main
wiz service restart app
```

연결 상태는 `GET /api/ai-config` 또는 대시보드 업로드 탭에서 확인할 수 있습니다.
OpenAI 사용량 점검은 Admin API 키를 런타임에만 주입한 뒤 `python scripts/check_openai_usage.py`로 확인합니다.

---

## iPhone 다운로드형 앱 배포

홈 화면 추가(PWA)가 아니라 TestFlight/App Store에서 내려받는 앱으로 배포하려면 iOS 네이티브 패키지가 필요합니다.
이 프로젝트에는 Capacitor 기반 iOS 래퍼가 추가되어 있으며, 앱은 `러닝메이트` 이름과 `net.seasonai.run.matomabo` 번들 ID를 사용합니다.

현재 설정은 iOS 앱 shell 안에서 운영 서비스 URL을 엽니다.

```bash
npm install
npm run ios:sync
npm run ios:open
```

`npm run ios:open` 이후 단계는 macOS의 Xcode에서 진행합니다.

1. Xcode에서 Apple Developer Team을 선택합니다.
2. Bundle Identifier가 `net.seasonai.run.matomabo`인지 확인합니다.
3. 실제 iPhone 연결 후 Run으로 테스트합니다.
4. `Product > Archive`로 아카이브를 만들고 TestFlight 또는 App Store Connect로 업로드합니다.

Linux 서버에서는 Xcode와 Apple 서명 도구가 없어 `.ipa` 생성과 App Store/TestFlight 업로드까지는 할 수 없습니다.

참고:
- Apple Xcode 배포 안내: https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases/
- App Store Connect 빌드 업로드 안내: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
