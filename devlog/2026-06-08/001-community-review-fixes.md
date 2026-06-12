# 커뮤니티 친구/피드/랭킹 UX 개선

- **ID**: 001
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: qsyhbejduakhojzdilblxtsefyvohwjk

## 작업 요약
커뮤니티 친구 화면의 팔로우 성공 표시와 자동 상세 노출을 제거하고, 언팔로우 버튼을 빨간색으로 변경했다. 피드에는 공개 러닝의 첨부 사진/영상이 표시되도록 했고, 랭킹 기간 순서를 이번달/이번주/지난주로 조정했다. 팔로우 대상자에게 커뮤니티 알림이 저장/표시되도록 알림 타입을 확장했으며, 설정의 프로필 진입을 인앱 프로필 화면으로 연결했다.

## 원문 요청사항
```text
작업 진행해줘

커뮤니티에서 친구 검색 후 팔로우하면 나오는 UI 수정:
1. 팔로우됨 표시 제거
2. 언팔로우 버튼 빨간색 변경
3. 친구 상세의 팔로잉 관계 표기를 피드 숫자로 변경
4. 친구 찾기 UI 간소화, 친구 상세는 친구를 눌렀을 때만 표시
랭킹은 이번달, 이번주, 지난주 순서로 표시
피드는 공개 러닝 사진/영상만 친구 피드에 표시하고 비공개는 본인에게만 표시
단방향 팔로우 문구 제거
팔로우 대상자에게 커뮤니티 알림 표시
설정 > 프로필에서 인스타그램처럼 내 프로필 표시
```

## 변경 파일 목록
- `src/app/page.dashboard/view.pug`: 커뮤니티 알림 패널, 피드 미디어 표시, 친구 검색 간소화, 친구 상세 조건부 표시, 인앱 프로필 화면 추가
- `src/app/page.dashboard/view.ts`: 알림 로드/읽음 처리, 팔로우 성공 표시 제거, 친구 자동 선택 제거, 랭킹 기본 기간/순서 조정, 프로필 통계/미디어 계산 추가
- `src/app/page.dashboard/view.scss`: 언팔로우 빨간 버튼, 커뮤니티 알림, 피드 미디어 그리드, 간소화 검색, 프로필 화면 스타일 추가
- `src/model/runningmate.py`: `follow` 알림 타입 정규화 및 팔로우 알림 생성 추가
- `src/route/api.follows.detail/controller.py`: 신규 팔로우 시 대상자 알림 생성 추가
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/001-community-review-fixes.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile /opt/app/project/main/src/model/runningmate.py /opt/app/project/main/src/route/api.follows.detail/controller.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
