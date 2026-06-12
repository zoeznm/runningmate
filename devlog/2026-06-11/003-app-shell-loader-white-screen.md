# 003 앱 재진입 시 흰 화면 대신 초기 로딩 셸 표시

## 사용자 요청

- Review ID: `apeekmrmpzepfkejsosbvomgtmclhaqi`
- 원 요청: "그리고 핸드폰에서 이 사이트를 아예 나갔다가 다시 들어오면 그냥 흰색 배경만 보이다가 갑자기 새로고침되면서 화면이 제대로 나오던데 왜 흰색배경만 오랫동안 보여주는거야?"

## 원인 판단

- 서비스워커 새 버전 적용 시 `controllerchange`에서 한 번 새로고침하도록 되어 있어, 재진입 시 캐시 갱신과 Angular 부트스트랩 사이의 빈 `app-root`가 먼저 그려질 수 있다.
- 기존 초기 HTML에는 `app-root` 내부 fallback UI가 없어 JS/CSS가 붙기 전 화면이 비어 보일 수 있었다.

## 변경 파일

- `src/angular/index.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/003-app-shell-loader-white-screen.md`

## 변경 내용

- Angular가 부트스트랩되기 전에도 보이는 `app-shell-loader`를 `app-root` 내부에 추가했다.
- 저장된 앱 테마 설정을 초기 HTML에서 먼저 읽어 라이트/다크 배경과 `theme-color`를 즉시 맞추도록 했다.
- 서비스워커 캐시 버전을 `runningmate-pwa-v21`로 올리고 index 갱신 키를 `rm-app-shell-loader-20260611`로 변경했다.

## 검증

- `git diff --check -- src/angular/index.pug config/pwa/sw.js` 통과
- `wiz_project_build(projectName="main", clean=false)` 성공
- 빌드 산출물에서 `app-shell-loader`, `rm-app-shell-loader-20260611`, `runningmate-pwa-v21` 반영 확인

## 남은 리스크

- 실제 모바일 브라우저/PWA 재진입 타이밍은 기기별 서비스워커 상태에 따라 달라질 수 있어 운영 실기기에서 최종 체감 확인이 필요하다.
- 서비스워커가 이미 설치된 기기에서는 새 캐시 적용을 위해 첫 진입 후 갱신이 필요할 수 있다.
