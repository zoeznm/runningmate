# 커뮤니티 랭킹 전체/팔로잉 범위 분리

- **ID**: 026
- **날짜**: 2026-06-09
- **유형**: 디자인/UX 개선
- **리뷰 ID**: hafhrhsoxilhfhlrghtoanfieauudurx

## 작업 요약

커뮤니티 랭킹 화면의 제목이 `친구 랭킹`으로 고정되어 실제 노출 범위가 전체 사용자인지 팔로잉 사용자인지 알기 어려운 문제를 수정했다. 기본 진입은 `전체 랭킹`으로 두고, 같은 화면에서 `전체`/`팔로잉` 범위를 전환할 수 있게 API와 UI를 함께 분리했다.

## 원문 요청사항

```text
작업 진행해줘

지금 내가 내 새로운 네이버 계정으로 회원가입하고 로그인을 해봤는데 일단 하나의 문제가 뭐냐면 
새롭게 가입한 사용자니까 친구가 없을텐데 커뮤니티 - 랭킹에 들어가면 모든 사용자의 랭킹이 뜨는건지 아니면 친구 랭킹이라고 되어있는데 친구 랭킹이 뜨는건지 알수가 없어 
1. 이 앱을 사용하는 전체 사용자의 랭킹이 뜨는게 좋을까
2. 자신이 팔로잉한 사용자의 랭킹만 뜨는게 좋을까? 
뭐가 더 이 앱을 사용하면서 더 재밌을 거 같애? 두개 다 있으면 좋을 거 같은데 
그러면 두개의 기능을 어떻게 배치할지도 의문이야.
```

## 변경 파일 목록

- `src/route/api.ranking.weekly/controller.py`
  - `scope=global|following` 쿼리를 해석하도록 추가.
  - 전체 랭킹은 전체 사용자 ID를, 팔로잉 랭킹은 현재 사용자가 팔로잉한 사용자 ID를 랭킹 후보로 전달.
  - 참여 설정 PATCH 후에도 현재 범위 기준 랭킹을 다시 반환하도록 정리.
- `src/model/runningmate.py`
  - `weekly_ranking()`에 `target_user_ids`, `scope` 입력을 추가.
  - 명시된 후보 ID가 있으면 해당 사용자와 viewer만 랭킹 계산에 포함.
  - 응답에 `scope`, `scope_label`, `target_count` 메타데이터를 추가.
  - 팔로잉 범위 조회가 전체 주간 우승자 아카이브를 갱신하지 않도록 제한.
- `src/app/page.dashboard/view.ts`
  - 랭킹 범위 타입/옵션/상태 추가.
  - 랭킹 조회와 참여 설정 저장 호출에 현재 범위 `scope` 전달.
  - 제목, 설명, 1위 라벨, 빈 상태 문구를 현재 범위에 맞게 표시.
- `src/app/page.dashboard/view.pug`
  - 제목을 `전체 랭킹`/`팔로잉 랭킹`으로 동적 표시.
  - 기간 토글 위에 `전체`/`팔로잉` 범위 토글과 기준 설명 추가.
- `src/app/page.dashboard/view.scss`
  - 랭킹 범위 토글과 설명 텍스트 간격/폰트 스타일 추가.
- `devlog.md`, `devlog/2026-06-09/026-community-ranking-scope-tabs.md`
  - 작업 이력 추가.

## 확인 결과

- `python -m py_compile src/route/api.ranking.weekly/controller.py src/model/runningmate.py` 성공.
- `wiz_project_build(clean=false)` 성공.
- 수정된 API/모델/대시보드 랭킹 영역을 다시 읽어 범위 쿼리, 토글, 문구 반영을 확인.

## 남은 리스크

- 실제 운영 로그인 세션으로 `/api/ranking/weekly?scope=global|following` 응답 차이를 직접 호출하는 검증은 수행하지 못했다.
- 프로젝트 작업 전부터 대시보드와 여러 앱 파일에 큰 미커밋 변경이 존재해 전체 git diff는 이번 작업만 분리해서 보기 어렵다.
