# 008. 프로필 피드 사진 상세 좋아요/댓글 기능 추가

## 사용자 원본 요청

피드에 있는 사진 누르면 인스타그램처럼 좋아요 누를 수 있게 해주고 댓글도 달 수 있게 해주면 좋겠어

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/route/api.runs.reactions/controller.py`

## 변경 내용

- 프로필 피드 사진/영상 타일을 클릭하면 전용 피드 상세 화면이 열리도록 변경했다.
- 상세 화면에 좋아요 버튼, 좋아요/댓글 수, 댓글 목록, 댓글 입력/삭제 UI를 추가했다.
- 기존 커뮤니티 반응/댓글 저장 로직을 재사용하고, 프로필 상세 진입 시 현재 좋아요/댓글 상태를 불러오도록 반응 API의 GET 응답을 추가했다.

## 확인 결과

- `wiz_project_build(projectName="main", clean=false)` 성공.
- `python -m py_compile project/main/src/route/api.runs.reactions/controller.py` 성공.
