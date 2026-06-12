# 주기 기록 패널 위치 이동 및 날씨 예보 표시 범위 확인

## 사용자 원본 요청

주기기록 입력하는걸 러닝기록 아래로 내려줘  
그리고 날씨 api 가 보여주는기간이 도대체 어떻게 돼?

## 처리 내용

- 달력 상세 영역에서 주기 기록 입력 패널을 러닝 기록 카드 목록 아래, 날씨 패널 위로 이동했다.
- 신규/기존 러닝 기록 입력 기능 자체는 변경하지 않고 렌더링 순서만 조정했다.
- PWA 캐시 버전을 `runningmate-pwa-v23`으로 갱신했다.
- 날씨 API 표시 범위를 코드 기준으로 확인했다.

## 날씨 API 표시 범위

- 프론트는 현재 달력의 `activeYearMonth`를 `/api/weather/monthly?year_month=YYYY-MM`로 요청한다.
- 백엔드는 확보한 예보 중 요청 월(`YYYY-MM`)에 속하는 날짜만 `days`로 내려준다.
- 공공데이터 단기예보는 응답에 포함된 가까운 예보일을 사용하고, 중기예보는 기준일 기준 `+3일`부터 `+10일`까지 채운다.
- 공공데이터 호출 실패 시 Open-Meteo fallback은 `forecast_days=16`으로 오늘부터 최대 `+15일`까지 제공한다.
- 응답의 `coverage.startDate/endDate`는 실제 확보된 전체 예보 범위이며, 화면은 선택일이 이 범위 밖이면 예보 범위 밖 문구를 사용한다.
- 날씨 캐시는 30분이다.

## 변경 파일

- `src/app/page.dashboard/view.pug`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/006-cycle-panel-below-run-weather-period.md`

## 검증 결과

- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- 실제 모바일 화면에서 스크롤 체감 순서는 로그인 세션이 있는 브라우저에서 최종 확인이 필요하다.
