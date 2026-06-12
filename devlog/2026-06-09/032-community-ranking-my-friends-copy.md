# 커뮤니티 랭킹 범위 문구를 내 친구로 변경

- **ID**: 032
- **날짜**: 2026-06-09
- **유형**: 디자인/UX 개선
- **리뷰 ID**: hafhrhsoxilhfhlrghtoanfieauudurx

## 작업 요약

커뮤니티 랭킹의 범위 토글과 관련 안내 문구에서 사용자에게 딱딱하게 보일 수 있는 `팔로잉` 표현을 `내 친구`로 바꿨다. 내부 API scope 값은 기존 `following`을 유지하고, 사용자에게 보이는 제목/라벨/설명/API 응답 라벨만 변경했다.

## 원문 요청사항

```text
팔로잉 이라고 하지 말고 내 친구 이런걸로 변경하면 어때?
```

## 변경 파일 목록

- `src/app/page.dashboard/view.ts`
  - 랭킹 범위 토글 라벨을 `팔로잉`에서 `내 친구`로 변경.
  - `내 친구 랭킹`, `내 친구 1위`, `내 친구 없음 · 내 기록만 표시` 등 랭킹 범위 설명 문구 변경.
  - 빈 상태 문구를 `내 친구` 기준으로 변경.
- `src/model/runningmate.py`
  - 랭킹 API 응답의 `scope_label`을 `내 친구 랭킹`으로 변경.
- `devlog.md`, `devlog/2026-06-09/032-community-ranking-my-friends-copy.md`
  - 작업 이력 추가.

## 확인 결과

- `rg`로 랭킹 범위 관련 `팔로잉` 문구 제거 확인.
- `python -m py_compile src/model/runningmate.py` 성공.
- `wiz_project_build(clean=false)` 성공.

## 남은 리스크

- 실제 브라우저에서 로그인 세션으로 토글 화면을 확인하지는 못했다.
- 친구 목록/프로필 영역의 기존 `팔로잉` 라벨은 이번 요청 범위 밖이라 유지했다.
