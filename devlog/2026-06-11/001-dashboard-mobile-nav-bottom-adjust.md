# 001 대시보드 모바일 하단 메뉴바 위치 보정

## 사용자 요청

- Review ID: `apeekmrmpzepfkejsosbvomgtmclhaqi`
- 원 요청: "이제 검정 배경 노출이 안돼 대신에 검정 배경이었던 부분이 흰색배경으로 되면서 하단에 메뉴바가 좀 바닥이랑 간격이 넓어보이는데 메뉴바를 좀 내려서 그 간격을 좀 좁혀줄 수 있어?"

## 변경 파일

- `src/app/page.dashboard/view.scss`
- `src/angular/index.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/001-dashboard-mobile-nav-bottom-adjust.md`

## 변경 내용

- 모바일 대시보드에서 확장된 viewport 높이와 `100dvh` 차이를 계산해 하단 메뉴바를 최대 28px 아래로 내리도록 보정했다.
- iOS safe-area 하단 여백을 그대로 더하지 않고 일부 줄여 메뉴바와 화면 바닥 사이의 체감 간격을 좁혔다.
- 본문/차트/채팅 하단 padding도 같은 변수 기준으로 맞춰 메뉴바 보정 후 불필요한 하단 여백이 커지지 않도록 했다.
- 서비스워커 캐시 버전을 `runningmate-pwa-v19`로 올리고 index 갱신 키를 `rm-dashboard-nav-bottom-20260611`로 변경했다.

## 검증

- `git diff --check -- src/app/page.dashboard/view.scss src/angular/index.pug config/pwa/sw.js` 통과
- `wiz_project_build(projectName="main", clean=false)` 성공

## 남은 리스크

- 실제 운영 모바일 WebView 캡처 자동 검증은 현재 작업 환경에서 수행하지 못했다.
- 서비스워커가 이미 설치된 기기에서는 새 캐시 적용을 위해 첫 진입 후 갱신이 필요할 수 있다.
