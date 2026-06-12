# 날씨 예보가 중기예보 시작일만 보이는 문제 보강

## 사용자 원본 요청

근데 지금 앱을 보면 오늘이 11일인데 오늘인 11일부터 날씨가 나오는게 아니라 15일부터 나온다고 되어있어

## 처리 내용

- 단기예보 호출이 성공하더라도 실제 `오늘` 날짜 예보가 비어 있으면 Open-Meteo 예보를 추가로 병합하도록 수정했다.
- Open-Meteo 병합 시 기존 기상청 데이터는 우선 유지하고, 비어 있는 날짜만 채우도록 했다.
- 오늘 날짜를 Open-Meteo로 보강한 경우 화면의 발표 기준도 Open-Meteo 기준으로 잡히도록 했다.

## 변경 파일

- `src/route/api.weather.monthly/controller.py`
- `devlog.md`
- `devlog/2026-06-11/007-weather-near-term-open-meteo-fill.md`

## 검증 결과

- `python3 -m py_compile src/route/api.weather.monthly/controller.py` 통과
- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공

## 남은 리스크

- Open-Meteo 네트워크 호출 자체가 실패하면 기존처럼 기상청 중기예보 범위부터만 보일 수 있다.
- 실제 `/api/weather/monthly` 응답은 운영 위치 권한/좌표와 외부 API 응답 상태에 따라 브라우저에서 추가 확인이 필요하다.
