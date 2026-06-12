# README를 고밀도 프로젝트 쇼케이스 스타일로 개선

## 사용자 요청

- 리뷰 ID: `eaftzjpafzoupkplisxwpehouzuquirq`
- 제목: 개인서버를 리뷰옵스에 등록
- 원문 요청: "좀 약간 개발에 미친 사람처럼 리드미를 꾸며줄 수 있어? 굳이 똑같이 따라할 필요는 없지만 https://github.com/HKUDS/OpenHarness 여기 리드미처럼 나오면 좋겠는데 여기는 영어로 했지만 나는 한국어로 저런 느낌이 나면 좋겠어"

## 작업 요약

러닝메이트 README를 단순 프로젝트 설명서에서 GitHub 첫 화면용 쇼케이스 문서로 재구성했다. 중앙 정렬 히어로, 배지, 섹션 내비게이션, 기능 지도, 빠른 시작, 아키텍처, API 지도, 운영 스위치보드, 개인 서버 운영, 배포 산출물 관리, iOS shell, 문서 허브, 개발 규칙을 한 번에 스캔할 수 있게 정리했다.

## 참고한 구조

- HKUDS/OpenHarness README의 히어로, 배지, Quick Start, Key Features, Architecture, 상세 기능 문서 흐름을 참고했다.
- 문구와 구성은 러닝메이트 실제 코드/문서 기준으로 새로 작성했다.

## 변경 파일

- `README.md`
  - 러닝메이트 로고, 배지, 섹션 링크를 상단에 추가했다.
  - 기능을 기록/대시보드/커뮤니티/계정/운영 관점으로 재정리했다.
  - 아키텍처, API, 환경변수, 개인 서버 운영, 배포 산출물, iOS shell, 문서 허브를 GitHub README용으로 재배치했다.
- `devlog.md`
  - 2026-06-12 ID 007 작업 요약 행을 추가했다.
- `devlog/2026-06-12/007-readme-showcase-polish.md`
  - 작업 상세 devlog를 추가했다.

## 확인한 내용

- WIZ 프로젝트 `main`의 app/route/package 구성을 확인했다.
- 현재 README, asset, docs, ops, scripts, iOS shell 구성을 확인했다.
- 참고 README는 구조적 분위기만 확인하고, 러닝메이트 실제 프로젝트 기준으로 내용을 새로 작성했다.

## 검증 결과

- 문서 변경만 수행했으므로 WIZ/Angular 빌드는 실행하지 않았다.
- `git diff --cached --check` 통과.
- 변경 커밋 생성 후 `git push origin main` 성공.
