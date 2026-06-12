# 프로필 편집 버튼 인앱 개인정보 편집 패널로 변경

- **ID**: 005
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: gsosldnkrgxiyaijbhcxviodnmllahbx

## 작업 요약
프로필 화면의 편집 버튼이 별도 `/mypage` 화면으로 이동하던 동작을 제거하고, 현재 모바일 대시보드 프로필 화면 안에서 개인정보 편집 패널이 열리도록 변경했다. 편집 항목은 실제 `/api/profile`에서 저장 가능한 프로필 사진, 이름, 연락처, 러닝 시작일, 공개 프로필 여부로 구성하고, 이메일은 계정 식별용 읽기 전용 필드로 표시했다.

## 원문 요청사항
```text
프로필 화면에서 편집 버튼을 누르면 나오는 버튼이거든? 이거 수정해줘 완전 이상한 페이지가 나오고 있거든? 다시 해줘 편집 버튼을 누르면 개인정보를 편집할 수 있어야되는데 어떤걸 넣는게 좋을지의문이야
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: `/mypage` 이동 제거, 프로필 편집 draft 상태/사진 선택/공개 토글/저장 로직 추가
- `src/app/page.dashboard/view.pug`: 프로필 화면 내부 개인정보 편집 패널 추가
- `src/app/page.dashboard/view.scss`: 프로필 편집 패널, 사진 선택, 입력 필드, 공개 토글, 저장 액션 스타일 추가
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/005-profile-edit-panel.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
