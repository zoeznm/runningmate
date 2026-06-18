# iOS 실기기 초기 로딩 멈춤 점검

작성일: 2026-06-18
대상: iOS Capacitor 앱에서 `초기 데이터를 불러오는 중` 화면이 계속 유지되는 문제

## 1. 로딩 문구 위치

| 문구 | 렌더링 위치 |
| --- | --- |
| `초기 데이터를 불러오는 중` | `src/app/page.dashboard/view.pug`의 `wiz-component-loading-fullscreen` |
| 기본 로딩 컴포넌트 문구 | `src/app/component.loading.fullscreen/view.pug`, `view.ts` |
| 빈 layout fallback | `src/app/layout.empty/view.pug`, `src/app/layout.sidebar/view.pug` |

대시보드에서는 `isInitialLoading`이 `true`일 때 전체 로딩 화면이 보인다. 실패 시에는 같은 Pug 파일의 `dashboard-error-overlay`가 `initialErrorMessage`와 재시도 버튼을 보여야 한다.

## 2. 초기 API

대시보드 첫 부트스트랩 API는 아래다.

```text
GET /api/dashboard/bootstrap?limit=60
```

호출 위치:

```text
src/app/page.dashboard/view.ts
- loadInitialDashboardData()
- loadDashboardBootstrap()
```

부트스트랩 실패 시 fallback으로 확인하는 API:

| 단계 | API |
| --- | --- |
| 로그인 확인 | `/api/auth/me` |
| 러닝 기록 | `/api/runs?limit=60&fields=...&include_media=false` |
| 프로필 | `/api/profile` |

부트스트랩 성공 뒤 부가 데이터는 목표, 챌린지, 피드, 친구, 랭킹, AI, 체중, 메모 등을 병렬로 읽는다. 이 부가 호출 중 하나가 멈춰도 첫 화면을 막지 않도록 9초 timeout을 추가했다.

2026-06-18 추가 확인: iOS 실기기에서 detail이 `날씨를 불러오는 중`으로 멈출 수 있었다. 날씨 로딩은 위치 권한 프롬프트와 외부 IP 위치 조회를 포함해 지연될 수 있으므로 초기 전체 화면 로딩 step에서 분리했다.

## 3. iOS API base URL 확인

현재 기준:

| 항목 | 값 |
| --- | --- |
| `capacitor.config.json` server URL | 제거됨. iOS는 `webDir` 번들을 `capacitor://localhost`에서 로드 |
| `capacitor.config.json` cleartext | `false` |
| API fallback origin | `https://run.myrunningmate.com` |
| 금지해야 할 API base | `localhost`, `127.0.0.1`, `http://...` |

API 호출은 기본적으로 상대 경로 `/api/...`를 쓴다. iOS는 앱 내부 번들을 `capacitor://localhost`에서 실행하므로, 그대로 두면 `/api/...`가 로컬 WebView로 붙을 수 있다.

이를 막기 위해 `src/angular/app/shared/api-base.ts`를 추가했다. `capacitor://localhost`, `ionic://localhost`, `file://` origin에서 `/api/...` 요청은 `https://run.myrunningmate.com/api/...`로 보낸다.

## 4. 무한 로딩 방지 수정

| 파일 | 수정 |
| --- | --- |
| `src/app/page.dashboard/view.ts` | `loadInitialDashboardData()`에 `try/catch/finally`를 추가해 예외가 나도 `isInitialLoading=false`로 내려가게 했다. |
| `src/app/page.dashboard/view.ts` | 초기 부가 데이터 작업에 9초 timeout을 추가했다. |
| `src/app/page.dashboard/view.ts` | 날씨 로딩이 초기 전체 화면 로딩 step을 잡지 않도록 분리했다. |
| `src/app/page.dashboard/view.ts` | 위치 권한 프롬프트 6초 timeout, IP 위치 조회 4초 timeout, 월간 날씨 API 7초 timeout을 추가했다. |
| `src/app/page.dashboard/view.ts` | 이미지 파싱 XHR에도 운영 API URL fallback과 20초 timeout을 추가했다. |
| `src/angular/app/shared/api-base.ts` | Capacitor 로컬 origin일 때 API URL을 운영 서버로 보정한다. |
| `src/angular/app/shared/api.ts` | `apiFetch`가 보정된 URL로 요청하도록 변경했다. |
| `src/angular/app/shared/auth.ts` | fetch interceptor와 인증 헤더 판별이 보정된 API URL을 쓰도록 변경했다. |
| `src/controller/base.py` | 허용 origin에 CORS 헤더를 내려주도록 보강했다. |
| `src/model/security.py` | `capacitor://localhost`, `ionic://localhost`를 허용 origin 기본값에 포함했다. |
| `.env.example`, `/opt/app/config/runtime.env` | 운영 도메인과 Capacitor origin 허용 예시/런타임 값을 맞췄다. |

## 5. Xcode/Capacitor 설정 확인

| 파일 | 확인 |
| --- | --- |
| `capacitor.config.json` | `server.url` 제거. `webDir=bundle/www` 내부 번들 사용 |
| `ios/App/App/capacitor.config.json` | Xcode가 앱 리소스로 포함하는 native config. `server.url` 없이 루트 설정과 동일해야 함 |
| `ios/App/App/RunningMateBridgeViewController.swift` | 예전 native config가 남아 있어도 `serverURL`을 `nil`로 덮어써 내부 `public` 번들을 강제 사용 |
| `ios/App/App/Info.plist` | HTTP 예외는 추가하지 않음. HTTPS 운영 도메인 사용 |
| `ios/App/App/Info.plist` | HealthKit, 카메라, 사진, 마이크, 위치 목적 문구 포함 |
| `ios/App/App.xcodeproj/project.pbxproj` | Bundle ID `com.myrunningmate.run` |
| `/opt/app/config/runtime.env` | `RUNNINGMATE_PUBLIC_BASE_URL=https://run.myrunningmate.com` |
| `/opt/app/config/runtime.env` | `RUNNINGMATE_ALLOWED_ORIGINS=https://run.myrunningmate.com,capacitor://localhost,ionic://localhost` |

## 6. Mac에서 필요한 작업

초기 iOS 설정 변경을 Mac 프로젝트에 반영할 때는 `npm run ios:sync`가 필요하다.

중요: `npm run ios:sync`, Xcode `Clean Build Folder`, iPhone 앱 삭제는 Mac 로컬의 Swift 소스 파일을 최신으로 받아오지 않는다. `ios/App/App/RunningMateBridgeViewController.swift` 자체가 예전 코드라면 먼저 프로젝트 소스 최신본을 반영해야 한다.

이유:

- `capacitor.config.json`의 `server.url`과 iOS 프로젝트 설정이 Xcode 앱에 반영되어야 한다.
- `ios/App/App/Info.plist`가 바뀌었다.
- 로컬 번들 fallback까지 테스트하려면 최신 웹 번들이 iOS 프로젝트에 복사되어야 한다.

Mac에서 실행:

```bash
cd /Users/kimbomi/Desktop/app/project/main
npm install
rm -f ios/App/App/capacitor.config.json
npm run ios:sync
npm run ios:verify-config
npm run ios:open
```

`npm run ios:open`으로 열린 Xcode에서 `App > App > RunningMateBridgeViewController.swift`에 `descriptor.serverURL = nil`이 보여야 한다. 보이지 않으면 최신 소스가 Mac 프로젝트에 반영되지 않았거나 다른 프로젝트 폴더를 열고 있는 것이다.

Xcode에서는 기존 앱을 기기에서 삭제한 뒤 다시 Run하는 것을 권장한다. 기존 WebView 캐시나 오래된 Capacitor 설정이 남아 있으면 같은 로딩 화면이 재현될 수 있다.

2026-06-18 로컬 번들 전환 이후 앱은 원격 URL을 직접 열지 않고 내부 라우팅의 `/access`에서 시작한다. API 요청만 `https://run.myrunningmate.com/api/...`로 나간다. `server.url` 제거는 native 설정 변경이므로 Mac에서 `ios:sync`가 필요하다.

Xcode 콘솔에 `Loading app at https://run.myrunningmate.com/dashboard...`가 보이면 아직 예전 native config가 앱 번들에 들어간 상태다. 이 경우 위 순서대로 `ios/App/App/capacitor.config.json`을 지우고 다시 `npm run ios:sync`를 실행한 뒤, Xcode `Product > Clean Build Folder`, iPhone 앱 삭제, 재설치를 진행한다.

2026-06-18 추가 보강: `RunningMateBridgeViewController.instanceDescriptor()`에서 `serverURL`을 항상 `nil`로 덮어써 예전 `server.url`이 남아 있어도 iOS 앱이 원격 URL을 직접 로드하지 못하게 했다. 이 변경이 반영된 앱에서도 같은 로그가 나오면 Xcode가 최신 `ios/App/App/RunningMateBridgeViewController.swift`가 들어간 프로젝트를 빌드하고 있지 않은 것이다.

2026-06-18 적용 내용:

- `/opt/app/.venv/bin/wiz project build --project=main`
- `/opt/app/.venv/bin/wiz bundle --project=main`
- 서비스워커 캐시 버전 `runningmate-pwa-v52-ios-weather-loading-timeout`
- `https://run.myrunningmate.com/main.js`에서 기존 `setInitialLoadingStep('weather', ...)` 제거 확인
