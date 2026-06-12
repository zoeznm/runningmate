# OpenAI 사용량 모니터링 및 페이서 AI 한도 안내 보강

## 사용자 요청

```text
그 다음에는 OpenAI 프로젝트별 과금 한도, 알림, usage 모니터링 설정. 이거를 해주는데
사용자들도 저 제한에 대해서 알아야될텐데 미리 온보딩에서 먼저 설명을 해주고 만약에 온보딩을 건너뛰기 하는 사용자들도 있을테니까 AI 채팅에 들어가면 저런 제한에 대해서 써줘 알려주고 그리고 일 한도, 월 한도를 다 쓰면 알림을 알려줘 그리고 사용자 월 한도를 120회로 올려줘
```

## 변경 파일

- `src/route/api.chat/controller.py`
- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `scripts/check_openai_usage.py`
- `.env.example`
- `README.md`
- `docs/openai-production-ops-2026-06-09.md`
- `devlog.md`
- `devlog/2026-06-09/039-openai-usage-monitoring-and-quota-notice.md`

## 변경 내용

- 일반 사용자 페이서 AI 월 한도 기본값을 50회에서 120회로 올렸다.
- `/api/chat` GET/DELETE/POST 응답에 현재 AI 사용량 `usage`를 포함하도록 했다.
- AI 채팅 화면에 일/월 한도와 남은 횟수 배너를 추가하고, 한도 소진 시 입력을 막고 토스트/채팅 메시지로 안내하도록 했다.
- 온보딩 AI 단계에 베타 한도 안내를 추가하고, 온보딩을 건너뛴 사용자도 AI 채팅 화면에서 제한을 볼 수 있게 했다.
- OpenAI Admin API 기반 비용/usage 점검 스크립트 `scripts/check_openai_usage.py`를 추가했다.
- OpenAI 프로젝트 비용 알림, usage 모니터링, Admin API 운영 기준과 새 환경변수를 문서화했다.

## 확인한 내용

- OpenAI 공식 문서/스펙에서 Usage 권한, `/organization/costs`, `/organization/usage/completions`, `/organization/spend_alerts` Admin API를 확인했다.
- `python -m py_compile src/model/runningmate.py src/route/api.chat/controller.py scripts/check_openai_usage.py` 통과.
- `env OPENAI_ADMIN_KEY= python scripts/check_openai_usage.py`가 비밀값 없이 Admin key 필요 메시지를 반환하는 것을 확인.
- WIZ 프로젝트 빌드 통과.
