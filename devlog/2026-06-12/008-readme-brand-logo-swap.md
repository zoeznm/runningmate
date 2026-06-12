# README 상단 시즌 로고 제거 및 러닝메이트 아이콘 적용

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "시즌 로고를 없애고 사진은 내 로고 사진으로 변경해줘"

## 작업 요약

README 상단 히어로 영역에서 Season 로고 SVG 사용을 제거하고 러닝메이트 앱 아이콘 PNG를 대표 이미지로 적용했다. 상단 badge에서도 `WIZ-Season_Framework` 표기를 제거하고 러닝메이트 자체 프로젝트 badge로 교체했다.

## 변경 파일

- `README.md`
  - `src/assets/brand/logo-black.svg`, `src/assets/brand/logo-white.svg` 참조를 제거했다.
  - 대표 이미지를 `src/assets/brand/icon-512.png`로 변경했다.
  - `WIZ-Season_Framework` badge를 `RunningMate-Private_Running_OS` badge로 교체했다.
- `devlog.md`
  - 2026-06-12 ID 008 작업 요약 행을 추가했다.
- `devlog/2026-06-12/008-readme-brand-logo-swap.md`
  - 작업 상세 devlog를 추가했다.

## 확인한 내용

- `src/assets/brand/icon-512.png`가 러닝메이트 앱 아이콘 이미지인 것을 확인했다.
- `src/assets/brand/logo-black.svg`가 Season 로고 SVG인 것을 확인했다.
- README 상단에서 Season 로고 이미지와 Season framework badge 참조를 제거했다.

## 검증 결과

- 문서 변경만 수행했으므로 WIZ/Angular 빌드는 실행하지 않았다.
- `git diff --cached --check` 통과.
- 변경 커밋 생성 후 `git push origin main` 성공.
