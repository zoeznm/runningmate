# iOS 원격 server.url 잔존 방지 및 네이티브 설정 추적

- 날짜: 2026-06-18
- 작업 ID: 007
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"여전히 아이콘은 옛날 아이콘으로 보이고 삭제 후에도 링크로 열려. Loading app at https://run.myrunningmate.com/dashboard..."

## 확인

- 현재 루트 `capacitor.config.json`에는 `server.url`이 없다.
- 현재 iOS 프로젝트에도 `https://run.myrunningmate.com/dashboard` 문자열은 남아 있지 않다.
- Xcode 로그의 `Loading app at https://run.myrunningmate.com/dashboard...`는 실행 중인 iOS 앱 번들 안에 아직 예전 Capacitor native config가 들어 있다는 뜻이다.
- `ios/.gitignore`가 `ios/App/App/capacitor.config.json`을 제외하고 있어, Mac 로컬에 예전 원격 URL이 들어간 생성 파일이 계속 남을 수 있었다.

## 변경

- `ios/App/App/capacitor.config.json`을 저장소에 포함해 Xcode가 읽는 native config도 원격 `server.url` 없이 고정했다.
- `ios/.gitignore`에서 `App/App/capacitor.config.json` 제외 규칙을 제거했다.
- `scripts/verify_ios_capacitor_config.mjs`를 추가해 루트/네이티브 Capacitor config에 `server.url`, `run.myrunningmate.com/dashboard`, `localhost`, `127.0.0.1`, `http://`가 남아 있으면 실패하게 했다.
- `npm run ios:sync` 뒤에 위 검증 스크립트를 자동 실행하도록 `package.json`을 수정했다.

## Mac 적용 순서

1. Mac 프로젝트에 최신 변경을 반영한다.
2. 기존 stale 파일을 확실히 지우려면 `rm ios/App/App/capacitor.config.json`을 한 번 실행한다.
3. `npm install`이 안 되어 있으면 먼저 실행한다.
4. `npm run ios:sync`를 실행한다.
5. Xcode에서 `Product > Clean Build Folder`를 실행한다.
6. iPhone에서 기존 앱을 삭제한다.
7. Xcode에서 다시 Run한다.

## 정상 로그

- 더 이상 `Loading app at https://run.myrunningmate.com/dashboard...`가 나오면 안 된다.
- 내부 번들 모드에서는 원격 dashboard URL이 아니라 Capacitor 로컬 번들이 로드되어야 한다.
