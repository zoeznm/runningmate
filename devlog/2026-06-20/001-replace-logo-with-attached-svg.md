# 첨부 SVG 로고 전체 교체

- 날짜: 2026-06-20
- 작업 ID: 001
- 리뷰 ID: `cydytopqfvpvobnhlfmdslzncnndbtxk`

## 사용자 요청

"내가 첨부한 svg로 로고를 싹 변경해줘"

## 변경

- 첨부 파일 `running_logo_main_app.svg`를 `src/assets/brand/running_logo_main_app.svg`로 추가했다.
- 기존 `logo-black.svg`, `logo-white.svg`를 첨부 SVG와 같은 로고로 교체했다.
- 첨부 SVG를 기준으로 `icon-192.png`, `icon-512.png`, maskable 아이콘, `apple-touch-icon.png`, `icon.ico`를 재생성했다.
- 접근 화면, 초기 로딩 셸, 데스크톱 사이드바, 오류 페이지의 로고 참조를 새 SVG로 변경했다.
- favicon/PWA manifest 아이콘 캐시 버전을 `rm-main-logo-20260620`으로 갱신했다.
- 브랜드 요약 문서의 로고 핵심 컬러를 첨부 SVG 기준 `#24D6B5`로 갱신했다.

## 확인

- 첨부 SVG와 소스 SVG 파일이 동일한 내용인지 확인했다.
- 재생성된 `icon-512.png`를 시각 확인했다.
- `wiz project build --project=main`으로 번들 산출물 반영을 확인했다.
