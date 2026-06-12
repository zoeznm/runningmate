# 기록 업로드 OpenAI 재점검 및 모바일 하단 메뉴바 재보정

## 사용자 원본 요청

여전히 계속 똑같은 오류가 나
그리고 하단 메뉴바 때문에 스크롤이 잘 안돼. AI한테 채팅할 input도 가려져서 안 보이고 좀 하단으로 내려야겠어 지금 너무 올라왔어 상단으로 그렇다고 하단으로 내린다고 아까처럼 잘리는 현상이 나오게 하지 말고 수정을 좀 해줘
그리고 OpenAI API 좀 잘 해봐 계속 오류가 나잖아
하단 메뉴바도 잘 수정하고 실제 앱에 있는 메뉴바 위치로 잘 좀 맞춰줘

## 처리 내용

- WIZ 라우트 코드가 서버 메모리에 캐시되는 구조를 확인하고, 빌드 후 WIZ 자식 프로세스를 재시작해 최신 번들이 적용되도록 했다.
- OpenAI는 `/opt/app/config/openai.env`의 `gpt-5.4-mini`로 실제 러닝 이미지 입력 스모크 테스트가 성공하는 것을 재확인했다.
- 이미지 파싱 실패 시 다음 재현부터 `image_parse` 감사 로그에 `provider`, `model`, `error_code`, `message`가 남도록 추가했다.
- 모바일 하단 메뉴바는 `bottom: 0`을 유지해 잘림을 막고, safe-area와 패딩만 줄여 시각적으로 더 아래에 붙도록 조정했다.
- 콘텐츠/채팅 하단 padding을 메뉴바 실제 높이 변수 기준으로 맞춰 스크롤 영역과 AI 채팅 입력이 메뉴바에 가려지지 않도록 했다.
- PWA 캐시 버전을 `runningmate-pwa-v26`으로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `src/route/api.parse-image/controller.py`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/012-upload-openai-and-mobile-nav-retune.md`

## 검증 결과

- `python -m py_compile`로 수정한 route controller 문법 검사 통과
- `git diff --check -- src/app/page.dashboard/view.scss src/route/api.parse-image/controller.py config/pwa/sw.js devlog.md devlog/2026-06-11` 통과
- `wiz_project_build(clean=false)` 성공
- WIZ 자식 프로세스 재시작 완료
- 번들에 `image_parse` 감사 로그와 `runningmate-pwa-v26` 반영 확인
- OpenAI `gpt-5.4-mini`로 실제 러닝 이미지 입력 스모크 테스트 성공
- `curl http://127.0.0.1:3000/dashboard` 응답 200 확인

## 남은 리스크

- 실제 휴대폰 PWA safe-area와 키보드 동작은 기기/브라우저별 차이가 있어 실기기에서 메뉴바 간격과 AI 입력 노출을 최종 확인해야 한다.
- 사용자가 다시 업로드했을 때 실패하면 이번에 추가한 `image_parse` 감사 로그로 정확한 서버 측 오류 코드를 확인할 수 있다.
