# iOS 날씨 초기 로딩 무한 대기 방어

- 날짜: 2026-06-18
- 작업 ID: 002
- 리뷰 ID: cffcsljsecovmosrwdemlskhtgambebz

## 사용자 원문

"날씨를 불러오는 중에서 지금 무한 로딩 걸림"

## 변경 요약

iOS 실기기에서 날씨 로딩이 초기 전체 화면 로딩 step을 붙잡지 않도록 분리하고, 위치 권한 프롬프트와 외부 IP 위치 조회, 월간 날씨 API에 timeout을 추가했다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
  - `loadWeatherForActiveMonth()`가 더 이상 초기 전체 화면 로딩에 `weather` step을 추가하지 않도록 변경했다.
  - 혹시 남아 있는 step을 정리하기 위해 `finally`에서 `location`, `weather` step을 모두 clear하도록 보강했다.
  - 위치 권한 프롬프트는 6초 후 자동으로 나중에 처리하도록 timeout을 추가했다.
  - IP 위치 조회는 4초 후 abort되도록 추가했다.
  - `/api/weather/monthly` 호출은 7초 timeout, retry 0으로 제한했다.
- `config/pwa/sw.js`, `src/route/portal.season.pwa.swjs/controller.py`, `src/portal/season/route/pwa.swjs/controller.py`
  - iOS WebView/PWA가 새 `/main.js`를 받도록 캐시 버전을 `runningmate-pwa-v52-ios-weather-loading-timeout`으로 갱신했다.
- `docs/ios-initial-loading-troubleshooting-2026-06-18.md`
  - 날씨 로딩 무한 대기 원인과 수정 내용을 추가했다.
- `devlog.md`
  - 작업 요약 행을 추가했다.

## 확인 결과

- 기존 `loadWeatherForActiveMonth()`는 초기 로딩 중 `setInitialLoadingStep('weather', '날씨를 불러오는 중')`를 호출했지만, 정상/실패/경쟁 상태에 따라 해당 step이 초기 로딩 UI에 오래 남을 수 있었다.
- 날씨는 필수 초기 데이터가 아니라 캘린더 보조 정보라서 전체 앱 진입을 막지 않도록 분리했다.
- Mac에서 `npm run ios:sync`와 앱 재설치를 해도 계속 재현된 이유는 iOS 앱이 원격 `server.url`의 운영 `/main.js`를 로드하는데, 운영 번들이 아직 이전 코드였기 때문이다.

## 검증

- `python -m py_compile src/controller/base.py src/model/security.py` 성공.
- `node build/wizbuild.js src/app/page.dashboard/view` 성공.
- `/opt/app/.venv/bin/wiz project build --project=main` 성공.
- `/opt/app/.venv/bin/wiz bundle --project=main` 성공.
- `grep -nE "날씨를 불러오는 중|setInitialLoadingStep\\('weather'|clearInitialLoadingStep\\('weather'|weatherPermissionPromptTimeoutMs|weatherIpLookupTimeoutMs|api/weather/monthly" src/app/page.dashboard/view.ts`로 `setInitialLoadingStep('weather')` 제거와 timeout 추가 확인.
- `git diff --check -- src/app/page.dashboard/view.ts docs/ios-initial-loading-troubleshooting-2026-06-18.md devlog.md devlog/2026-06-18/002-ios-weather-loading-timeout.md` 통과.
- `https://run.myrunningmate.com/main.js` 응답에 기존 weather step이 없고, 7초 timeout과 운영 API base fallback이 포함된 것을 확인했다.
- `https://run.myrunningmate.com/sw.js` 응답이 `runningmate-pwa-v52-ios-weather-loading-timeout`을 반환하는 것을 확인했다.
