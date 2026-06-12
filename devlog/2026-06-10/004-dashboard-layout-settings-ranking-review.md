# 대시보드 표시 단위/권한/설정/랭킹 디자인 리뷰 반영

- 날짜: 2026-06-10
- ID: 004
- 리뷰 ID: apeekmrmpzepfkejsosbvomgtmclhaqi

## 사용자 원 요청

작업 진행해줘

리뷰 요청 항목:
- 위치 권한 안내를 앱 디자인과 통일
- 설정의 km/mile 단위 변경을 기존 기록 표시 전반에 반영
- 페이스/속도 표기 변경을 기존 기록 표시 전반에 반영
- 비밀번호 변경을 설정 개인정보 섹션이 아닌 프로필 진입 화면으로 이동
- 라이트 모드 설정 표시 섹션 활성 색상 보정
- 화면 하단 검정 영역으로 보이는 높이/배경 문제 확인 및 보정
- 전체 랭킹의 다른 사용자 실명 노출을 성 + `**` 형태로 마스킹

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/model/runningmate.py`

## 변경 내용

- 브라우저 위치 권한 호출 전에 앱 디자인의 위치 안내 모달을 먼저 표시하고, 거절 시 IP 기반 날씨 위치로 fallback 하도록 변경.
- 거리 단위와 페이스/속도 표기를 공용 표시 헬퍼로 통합해 홈, 피드, 랭킹, 프로필 통계, 목표, 차트, 갤러리, 일기 상세, 수동 입력 및 챌린지 표시가 현재 설정을 따르도록 보정.
- 수동 기록/목표/챌린지 입력은 현재 표시 단위를 기준으로 받되 저장 전 내부 km 및 초/km 기준으로 환산하도록 보정.
- 비밀번호 변경 패널을 설정 개인정보 섹션에서 제거하고 프로필 편집 화면 내부로 이동.
- 라이트 모드의 활성 세그먼트와 스위치 색상 대비를 강화.
- 모바일 하단 safe-area 배경/여백과 phone frame 높이 계산을 보정해 하단 검정 노출 가능성을 줄임.
- 랭킹 엔트리 생성 후 비열람자 이름을 성 + `**` 또는 첫 토큰 + `**` 형태로 마스킹.

## 검증 결과

- `python -m py_compile project/main/src/model/runningmate.py project/main/src/route/api.ranking.weekly/controller.py` 통과.
- `wiz_project_build(projectName="main", clean=false)` 통과.
- `git -C /opt/app/project/main diff --check` 통과.

## 남은 리스크

- 브라우저의 실제 권한 시스템 팝업 자체는 브라우저/OS 영역이라 스타일 변경이 불가능하며, 이번 변경은 앱 사전 안내 모달을 추가하는 방식임.
- 로그인 세션과 실제 데이터가 필요한 화면이라 자동 시각 회귀 테스트는 수행하지 못함.
