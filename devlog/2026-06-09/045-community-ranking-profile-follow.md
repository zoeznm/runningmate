# 045. 커뮤니티 전체 랭킹 사용자 프로필/팔로우 연결

- 날짜: 2026-06-09
- 리뷰 ID: jhqbsxkzimsxwdbpwcjbnknkwrxxzmzd
- 요청 원문: "작업 진행해줘"
- 리뷰어 요청: 커뮤니티 랭킹 전체 탭의 사용자 순위 목록에서 사용자를 클릭해 팔로우할 수 있고, 공개 사용자는 피드를 볼 수 있으며 비공개 사용자는 맞팔일 때만 피드를 볼 수 있게 해달라는 요청.

## 변경 사항

- 랭킹 행을 클릭/키보드 진입 가능한 프로필 진입점으로 연결했다.
- 랭킹에서 열린 사용자 프로필에서도 기존 팔로우/언팔로우 버튼을 사용할 수 있게 하고, 팔로우 후 현재 프로필 상세를 다시 불러오도록 했다.
- 비공개 사용자 프로필의 통계, 뱃지, 팔로우 목록, 피드 미디어 노출 조건을 `공개 또는 본인 또는 맞팔`로 조정했다.
- 커뮤니티 피드도 비공개 사용자는 맞팔일 때만 공개 러닝 기록이 보이도록 조건을 맞췄다.
- 비공개 프로필 피드가 잠겨 있을 때 빈 상태 문구를 "맞팔이 되면 피드를 볼 수 있어"로 표시한다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/route/api.follows.detail/controller.py`
- `src/model/runningmate.py`
- `devlog.md`
- `devlog/2026-06-09/045-community-ranking-profile-follow.md`

## 확인 결과

- `wiz_project_build(projectName="main", clean=false)` 성공.

## 남은 리스크

- 실제 계정 간 공개/비공개/맞팔 조합의 브라우저 클릭 검증은 별도 수행이 필요하다.
