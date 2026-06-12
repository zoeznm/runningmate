# 챌린지 주최 탭 및 초대코드 섹션 보정

- **ID**: 043
- **날짜**: 2026-06-08
- **유형**: UX/데이터 표시 수정
- **리뷰 ID**: phkpioshgocbdxgtzyuzkwitsdwigojp

## 작업 요약
챌린지 목록 화면의 초대코드 참여 섹션을 제거했다.
`내가 만든` 탭 라벨을 더 간결한 `주최`로 변경했다.
기존 챌린지 데이터처럼 작성자 ID가 세션 ID와 다른 형태로 저장된 경우에도 작성자 이름/username 계열을 함께 비교해 주최 탭에 표시되도록 소유자 판별을 보강했다.

## 원문 요청사항
```text
챌린지 참여중에 초대코드 참여라는 섹션도 없애줘 어차피 만들 때 있잖아
모집중 탭에서도 초대코드 참여라는 섹션이 있는데 없애줘
그리고 다같이 200km라는 챌린지는 내가 만들었는데 왜 내가 만든에 들어가서 보면 안 보여? 수정해줘
그리고 내가 만든 이라고 하지 말고 더 좋은 단어가 없을까?
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 챌린지 목록 상단의 초대코드 참여 폼 제거.
- `src/app/page.dashboard/view.ts`: `내가 만든` 탭 라벨과 요약 문구를 `주최`로 변경.
- `src/model/runningmate.py`: 챌린지 주최자 판별을 세션 ID, username, display ID, email, 이름 기준까지 확장하고 삭제 권한 문구 변경.
- `src/route/api.challenges/controller.py`: 챌린지 목록/생성 후 목록 조회에 사용자 객체를 전달하도록 변경.
- `src/route/api.challenges.join/controller.py`: 참여 후 목록 조회에 사용자 객체를 전달하도록 변경.
- `src/route/api.challenges.detail/controller.py`: 상세/삭제 조회에 사용자 객체를 전달하도록 변경.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/043-challenge-host-tab-invite-section-fix.md`: 작업 상세 기록 추가.

## 확인 결과
- `python -m py_compile project/main/src/model/runningmate.py project/main/src/route/api.challenges/controller.py project/main/src/route/api.challenges.detail/controller.py project/main/src/route/api.challenges.join/controller.py` 성공.
- `rg`로 챌린지 목록 템플릿에서 `초대코드 참여` 문구가 제거된 것을 확인했다.
- `wiz_project_build(projectName="main", clean=false)` 성공.
