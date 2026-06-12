# 챌린지 생성 버튼 위치와 주최 판별 보강

- **ID**: 046
- **날짜**: 2026-06-08
- **유형**: UX/데이터 표시 수정
- **리뷰 ID**: phkpioshgocbdxgtzyuzkwitsdwigojp

## 작업 요약
챌린지 생성하기 버튼을 주최 탭에서만 노출하도록 변경했다.
챌린지 생성 화면에는 초대코드 참여 섹션을 추가했다.
주최 탭에서 기존 작성 챌린지가 누락되지 않도록 프로필의 id, username, display_id, email, 이름을 이용한 프론트 보조 판별을 추가했다.

## 원문 요청사항
```text
1. 참여중, 모집중, 종료에는 챌린지 생성하기 버튼 없앤다. 주최에만 챌린지 생성하기 버튼을 둔다.
2. 챌린지 생성하기 버튼을 눌렀을 때 나오는 페이지에 초대코드 관련한 부분이 없다. 추가해야된다.
3. 주최에 내가 만든 챌린지가 나와야하는데 만든 챌린지가 있는데 주최에 표시되지 않는다. 수정필요하다.
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 주최 탭에서만 챌린지 생성 버튼을 보이게 하고, 생성 화면에 초대코드 참여 폼을 추가했다.
- `src/app/page.dashboard/view.ts`: 프로필 username/display_id/display_name 보존과 현재 사용자 기준 챌린지 주최 여부 fallback 판별을 추가했다.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/046-challenge-host-create-button-owner-fallback.md`: 작업 상세 기록 추가.

## 확인 결과
- `python -m py_compile project/main/src/model/runningmate.py project/main/src/route/api.challenges/controller.py project/main/src/route/api.challenges.detail/controller.py project/main/src/route/api.challenges.join/controller.py` 성공.
- `rg`로 챌린지 생성 버튼 조건이 `activeChallengeTab === 'owned'`로 제한된 것을 확인했다.
- `rg`로 생성 화면에 `초대코드 참여` 섹션이 추가된 것을 확인했다.
- `wiz_project_build(projectName="main", clean=false)` 성공.
