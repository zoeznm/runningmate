# 러닝메이트 LLM AI 및 Codex 런타임 구조

- 작성일: 2026-06-09
- 리뷰 ID: `lptoxpafhwybmeezgyifmkbxpqfeyvft`
- 대상 프로젝트: WIZ `main` 프로젝트, 러닝메이트
- 범위: 러닝메이트 앱 내부의 LLM AI, Codex CLI, OpenAI Responses API 실행 로직

## 1. 전체 구조 요약

러닝메이트의 LLM 기능은 대시보드의 AI 화면과 업로드 화면에서 시작해 서버 API 3개로 이어진다.

```text
사용자
  -> src/app/page.dashboard/view.pug, view.ts
      -> GET  /api/ai-config      AI provider와 연결 상태 확인
      -> POST /api/ai-config      Codex 로그인 갱신 또는 상태 재확인
      -> GET  /api/chat           저장된 페이서 대화 기록 조회
      -> POST /api/chat           페이서 AI 채팅 답변 생성
      -> POST /api/parse-image    러닝 캡처 이미지 OCR/JSON 추출

서버 라우트
  -> src/route/api.ai-config/controller.py
  -> src/route/api.chat/controller.py
  -> src/route/api.parse-image/controller.py

도메인 컨텍스트
  -> src/model/runningmate.py
```

AI 실행 provider는 `RUNNINGMATE_AI_PROVIDER` 환경변수로 결정된다.

| provider | 실행 방식 | 용도 |
|---|---|---|
| `openai` | OpenAI Responses API 호출 | 운영 권장 기본값 |
| `codex` | 서버에 설치된 Codex CLI로 `codex exec` 실행 | 개발/임시 점검용 |
| 기타 값 | 서버 로컬 규칙 기반 `_reply()` 사용 | API 장애 시 제한적 fallback |

환경변수는 각 라우트에서 `/opt/app/config/openai.env`를 보강 로드한다. 기본값은 `openai`이며, 운영 배포는 개인 Codex 로그인 상태에 의존하지 않는 `OPENAI_API_KEY` 기반 구성을 권장한다.

## 2. 프론트엔드 진입 흐름

소스: `src/app/page.dashboard/view.ts`, `src/app/page.dashboard/view.pug`

### AI 연결 상태

앱 초기 로딩과 AI 설정 화면에서 `loadAiConnection()`이 실행된다.

```text
loadAiConnection()
  -> GET /api/ai-config
  -> provider, model, configured, codex_status 등을 aiConnection에 저장
  -> AI 설정 화면에 연결됨/갱신 필요 상태 표시
```

Codex 모드에서 사용자가 `로그인 갱신`을 누르면 `refreshCodexLogin()`이 실행된다.

```text
refreshCodexLogin()
  -> POST /api/ai-config { action: "refresh_login" }
  -> CODEX_ACCESS_TOKEN 로그인 또는 device auth 코드 발급 결과 수신
  -> 인증 URL, 사용자 코드, 만료 시간을 UI에 표시
```

### AI 채팅

사용자가 페이서 채팅 입력창에서 질문을 보내면 `sendChat()`이 실행된다.

```text
sendChat()
  -> 사용자 메시지를 화면에 먼저 추가
  -> POST /api/chat
     {
       message,
       session_id,
       client_date,
       stream: false,
       cycle_enabled
     }
  -> 서버 reply 또는 error message를 AI 말풍선에 표시
  -> session_id와 대화 기록 갱신
```

현재 프론트엔드가 보내는 채팅 요청은 `stream: false`다. 서버에는 NDJSON 스트리밍 처리 코드도 있지만, 현재 UI 전송 경로는 비스트리밍 JSON 응답을 사용한다.

### 이미지 파싱

사용자가 러닝 캡처 이미지를 업로드하면 `parseImageFile()`이 실행된다.

```text
parseImageFile(file, targetDate)
  -> FormData에 image와 target_date를 담음
  -> POST /api/parse-image
  -> 파싱된 러닝 JSON을 수신
  -> 날짜/거리 등 정규화된 값으로 러닝 기록 저장 흐름 진행
```

## 3. `/api/ai-config`: AI 설정 및 Codex 로그인 상태

소스: `src/route/api.ai-config/controller.py`

이 라우트는 모델 호출을 직접 수행하지 않는다. 대신 현재 AI provider와 인증 상태를 확인하고, Codex 모드에서 로그인 갱신을 처리한다.

### GET 흐름

```text
GET /api/ai-config
  -> /opt/app/config/openai.env 로드
  -> RUNNINGMATE_AI_PROVIDER 확인
  -> provider=codex이면 codex CLI 설치 여부 확인
  -> codex login status 실행
  -> provider, model, configured, codex_supported, codex_authenticated 반환
```

### POST 흐름

```text
POST /api/ai-config { action: "refresh_login" }
  -> same-origin 요청 확인
  -> 관리자 세션 또는 RUNNINGMATE_ADMIN_TOKEN 확인
  -> provider=codex이면 Codex 로그인 갱신
```

Codex 로그인 갱신은 두 방식이다.

- `CODEX_ACCESS_TOKEN`이 있으면 `codex login --with-access-token`에 토큰을 stdin으로 넣는다.
- 토큰이 없으면 `codex login --device-auth`를 백그라운드로 시작하고 `auth_url`, `user_code`, `expires_in_minutes`를 반환한다.

응답의 주요 필드는 다음과 같다.

| 필드 | 의미 |
|---|---|
| `configured` | 현재 provider가 실제 호출 가능한 상태인지 여부 |
| `provider` | `Codex CLI` 또는 `OpenAI Responses API` 표시명 |
| `model` | 현재 설정된 모델명 또는 `codex-cli` |
| `mode` | 실제 provider 값: `codex`, `openai` 등 |
| `codex_supported` | 서버에 Codex CLI가 설치되어 있는지 여부 |
| `codex_authenticated` | `codex login status` 기준 로그인 여부 |
| `login_refresh_supported` | Codex 로그인 갱신 UI 사용 가능 여부 |
| `setup_steps` | UI에 표시할 설정 안내 문구 |

## 4. `/api/chat`: 페이서 AI 채팅 로직

소스: `src/route/api.chat/controller.py`

이 라우트는 러닝메이트 LLM 채팅의 핵심이다. 사용자의 질문과 러닝 데이터를 합쳐 하나의 프롬프트를 만들고, provider에 따라 Codex CLI 또는 OpenAI Responses API에 전달한다.

### 요청 처리 흐름

```text
POST /api/chat
  -> 세션에서 user_id 확인, 없으면 401
  -> message 길이 검증
  -> cycle_enabled, session_id, client_date 확인
  -> _chat_reply(message, cycle_enabled) 실행
      -> provider=codex  : _codex_reply()
      -> provider=openai : _openai_reply()
      -> 기타 provider   : _reply() 로컬 규칙 답변
  -> running.save_chat_exchange()로 질문/답변 저장
  -> { success, reply, session_id, session } 반환
```

GET은 저장된 대화 세션을 반환하고, DELETE는 특정 대화 세션을 삭제한다.

### 채팅 input token에 들어가는 내용

`_chat_prompt(message, cycle_enabled)`가 모델에 들어가는 최종 텍스트 입력을 만든다. 실제 input token의 큰 구성은 다음과 같다.

```text
[역할 지시]
너는 러닝메이트 앱의 한국어 러닝 코치 '페이서'야.
사용자의 러닝 기록 컨텍스트와 질문을 보고 짧고 실용적으로 답해.
모르는 값은 지어내지 말고, 데이터가 없으면 업로드를 안내해.

[상담 규칙]
체중 데이터는 러닝량과 함께 참고하되 무리한 감량을 권하지 않기.
수분 데이터가 부족하면 러닝 전후 수분 보충을 짧게 안내하기.
목표 데이터가 있으면 진행률과 남은 값을 알려주기.
랭킹 데이터가 있으면 순위와 거리 차이를 자연스럽게 언급하기.
친구 반응/댓글이 있으면 짧게 언급하기.
훈련 부하가 높거나 휴식 질문이면 연속 러닝, 주간 증가율, 심박, 컨디션을 먼저 평가하기.
cycle_enabled=true일 때만 생리주기 컨텍스트를 참고하기.
최종 답변은 한국어 문장만 출력하고 표/코드블록은 쓰지 않기.

[러닝 데이터 JSON]
_chat_context(cycle_enabled)가 만든 JSON 문자열

[최근 일기 사용 규칙]
최근 일기 3개를 컨디션과 맥락 이해에 참고하기.

[사용자 질문]
사용자가 입력한 message
```

`_chat_context()`가 넣는 JSON 데이터는 아래와 같다.

| 키 | 내용 |
|---|---|
| `month_summary` | 이번 달 총 거리, 기록 수, 평균 페이스, 평균 심박, 최신 러닝, 수분/목표 요약 |
| `recent_runs` | 최근 월간 러닝 기록 최대 8개 |
| `recent_journals` | 최근 일기 3개 |
| `weight_context` | 체중 기록, 변화량, 러닝량과의 관계 |
| `hydration_context` | 러닝 전후 수분 기록, 장거리 대비 부족 여부 |
| `goals_context` | 거리/횟수/시간/평균 페이스 목표와 진행률 |
| `ranking_context` | 내 주간 랭킹, 1위와의 거리 차이, 동기부여 문구 |
| `social_cheer_context` | 친구 반응, 좋아요, 댓글 요약 |
| `training_load` | 연속 러닝, 주간 거리 증가율, 최근 심박, 컨디션 흐름, 휴식 권고 |
| `cycle_context` | `cycle_enabled=true`일 때만 포함되는 생리주기 컨텍스트 |

### 채팅 input token에 들어가지 않는 것

- `OPENAI_API_KEY`, `CODEX_ACCESS_TOKEN`, OAuth secret 같은 서버 비밀값
- 사용자의 전체 DB 원본 전체
- 파일 시스템 전체 내용
- 다른 사용자의 민감한 원자료 전체
- 프론트엔드 코드나 서버 소스 전체

랭킹이나 친구 반응처럼 다른 사용자와 관련된 정보는 `runningmate.py`가 만든 요약 컨텍스트 형태로만 들어간다.

## 5. Codex 채팅 실행 방식

provider가 `codex`이면 `_codex_reply()`가 `_chat_prompt()` 결과를 Codex CLI에 전달한다.

```text
codex exec
  --cd /tmp
  --skip-git-repo-check
  --ephemeral
  --color never
  -o <temporary-output-file>
  -- <chat-prompt>
```

실행 의도는 다음과 같다.

- `--cd /tmp`: 프로젝트 저장소가 아니라 임시 디렉터리에서 실행
- `--skip-git-repo-check`: git 저장소가 아닌 위치에서도 실행
- `--ephemeral`: 세션 상태를 남기지 않는 일회성 실행
- `--color never`: ANSI 컬러 제거가 쉬운 plain output 사용
- `-o`: Codex 최종 답변을 임시 파일로 저장하고 서버가 읽음

Codex 프로세스가 실패하거나 timeout이 나면 한국어 오류 메시지를 반환한다. timeout 기본값은 `RUNNINGMATE_CODEX_TIMEOUT` 또는 180초다.

서버에는 `codex exec --json` 기반 스트리밍 함수도 있다. 다만 현재 대시보드 `sendChat()`은 `stream: false`를 보내므로 일반 채팅에서는 비스트리밍 응답을 사용한다.

## 6. OpenAI 채팅 실행 방식

provider가 `openai`이면 `_openai_reply()`가 OpenAI Responses API를 호출한다.

```text
OpenAI(api_key=OPENAI_API_KEY)
  -> client.responses.create(
       model=_chat_model(),
       input=_chat_prompt(message, cycle_enabled)
     )
  -> response.output_text를 reply로 사용
```

모델 선택 우선순위는 다음과 같다.

1. `RUNNINGMATE_CHAT_MODEL`
2. `RUNNINGMATE_VISION_MODEL`
3. 기본값 `gpt-5.4-mini-2026-03-17`

OpenAI API quota, rate limit, 인증 오류, 권한 오류, 서버 오류는 각각 사용자에게 한국어 메시지로 정리되어 반환된다.

## 7. `/api/parse-image`: 러닝 캡처 이미지 파싱 로직

소스: `src/route/api.parse-image/controller.py`

이미지 파싱은 사용자가 업로드한 러닝 앱 캡처에서 러닝 기록을 JSON으로 뽑아내는 기능이다.

### 요청 처리 흐름

```text
POST /api/parse-image
  -> 로그인 세션 확인, 없으면 401
  -> 업로드 파일 확인
  -> 확장자, MIME, 파일 헤더, 파일 크기 검증
  -> RUNNINGMATE_UPLOAD_DIR에 이미지 저장
  -> provider=codex이면 _parse_with_codex(stored_path)
  -> provider=openai이면 _parse_with_openai(stored_path, content_type)
  -> 모델 응답에서 JSON 객체 추출
  -> running.normalize_run(parsed)로 날짜/거리 등 정규화
  -> date와 distance_km가 있으면 { success: true, data } 반환
```

이미지가 아니거나 날짜/거리 값을 확인하지 못하면 저장한 파일을 삭제하고 실패 메시지를 반환한다.

### 이미지 파싱 input token에 들어가는 내용

이미지 파싱의 텍스트 프롬프트는 `PROMPT`와 `CODEX_PROMPT`에 고정되어 있다.

```text
러닝 앱 캡처 이미지에서 러닝 기록을 추출해 JSON만 반환해.
이미지를 먼저 OCR로 읽고, 화면에 보이는 총 러닝 거리와 날짜를 가장 우선해서 판단해.
필드:
- date: YYYY-MM-DD
- distance_km: float
- avg_pace: MM'SS" 형식
- duration: HH:MM:SS 형식
- calories: int
- avg_heart_rate: int
- cadence: int
- elevation_gain: float 또는 null
- raw_text: OCR로 읽은 주요 텍스트 한 줄 요약
읽을 수 없는 필드는 null.
설명 없이 순수 JSON 객체 하나만 반환.
```

Codex 모드에서는 텍스트 프롬프트와 이미지 파일 경로가 함께 들어간다.

```text
codex exec
  --cd /tmp
  --skip-git-repo-check
  --ephemeral
  --color never
  -o <temporary-output-file>
  --image <stored-image-path>
  -- <image-parse-prompt>
```

OpenAI 모드에서는 이미지 파일을 base64 data URL로 바꿔 Responses API에 넣는다.

```text
client.responses.create(
  model=RUNNINGMATE_VISION_MODEL 또는 gpt-5.4-mini-2026-03-17,
  input=[
    {
      role: "user",
      content: [
        { type: "input_text", text: PROMPT },
        { type: "input_image", image_url: "data:<mime>;base64,...", detail: RUNNINGMATE_IMAGE_DETAIL }
      ]
    }
  ]
)
```

이미지는 텍스트 토큰으로 그대로 들어가는 것이 아니라 이미지 입력으로 전달된다. 텍스트 input token에는 추출 규칙과 JSON 스키마 지시가 들어간다.

## 8. 로컬 규칙 fallback

`RUNNINGMATE_AI_PROVIDER`가 `codex`도 `openai`도 아니면 `/api/chat`은 `_reply()`를 사용한다. 이 경로는 LLM 호출 없이 서버 코드의 규칙으로 답변한다.

- 기록이 없으면 캡처 업로드 안내
- 휴식 질문이면 훈련 부하 기반 문장 생성
- 목표/랭킹/응원/심박/이번주/체중/수분/이번달/최근 질문에 대해 정해진 템플릿 응답

이 fallback은 자연어 이해 범위가 제한적이므로 운영 AI 대체 수단이라기보다 장애 시 최소 응답 경로에 가깝다.

## 9. 저장과 후처리

채팅 응답이 만들어지면 `running.save_chat_exchange()`가 질문과 답변을 저장한다.

```text
message + reply + user_id + chat_day
  -> 대화 세션 생성 또는 기존 session_id에 추가
  -> session_id, title, preview, messages 반환
  -> 프론트엔드가 대화 기록 목록 갱신
```

이미지 파싱 결과는 바로 DB에 저장되는 것이 아니라, 먼저 정규화된 `data`로 프론트엔드에 반환된다. 이후 대시보드 업로드 흐름에서 러닝 타입, 수분, 음악, 공개 여부, 미디어 정보와 합쳐 러닝 기록 저장 API로 이어진다.

## 10. 운영 및 보안 경계

- 운영 권장 provider는 `openai`다.
- `codex` provider는 서버의 개인 Codex 로그인 상태나 `CODEX_ACCESS_TOKEN`에 의존하므로 개발/임시 점검용으로 제한하는 것이 안전하다.
- 비밀값은 모델 input token에 넣지 않는다.
- `/api/ai-config`의 로그인 갱신 POST는 same-origin과 관리자 권한을 확인한다.
- Codex CLI 실행 위치는 `/tmp`이며 `--ephemeral` 옵션으로 일회성 실행을 의도한다.
- 업로드 이미지는 파일 형식과 크기를 검증한 뒤 처리하고, 파싱 실패 시 삭제한다.
- 모델이 만든 JSON은 그대로 신뢰하지 않고 `_extract_json()`과 `running.normalize_run()`으로 후처리한다.

## 11. 관련 파일 맵

| 파일 | 역할 |
|---|---|
| `src/app/page.dashboard/view.pug` | AI 채팅, AI 설정, 업로드 UI |
| `src/app/page.dashboard/view.ts` | `/api/ai-config`, `/api/chat`, `/api/parse-image` 호출 |
| `src/route/api.ai-config/controller.py` | provider 상태 확인, Codex 로그인 상태/갱신 |
| `src/route/api.chat/controller.py` | 페이서 채팅 프롬프트 구성, LLM 호출, 대화 저장 |
| `src/route/api.parse-image/controller.py` | 러닝 캡처 이미지 검증, LLM OCR/JSON 추출 |
| `src/model/runningmate.py` | 러닝 기록, 목표, 랭킹, 수분, 훈련 부하, 채팅 세션 데이터 제공 |
| `README.md` | 운영 AI provider와 OpenAI API 키 설정 안내 |
