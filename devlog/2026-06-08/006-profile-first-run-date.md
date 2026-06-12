# 프로필 러닝 시작일을 첫 러닝 기록 날짜 기준으로 보정

- **ID**: 006
- **날짜**: 2026-06-08
- **유형**: UX 개선
- **리뷰 ID**: gsosldnkrgxiyaijbhcxviodnmllahbx

## 작업 요약
프로필 화면과 프로필 편집 패널의 러닝 시작일이 프로필 저장값이 없을 때 오늘 날짜로 표시되던 문제를 수정했다. 앱에 저장된 러닝 기록 중 가장 오래된 날짜를 계산해 프로필 표시와 편집 폼의 기본 러닝 시작일에 우선 반영하도록 변경했다.

## 원문 요청사항
```text
러닝 프로필 편집 누르면 나오는 섹션인데 
러닝 시작일이 오늘로 되어있는데 어플 기록에서 처음 기록한 날로 수정을 해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 가장 이른 러닝 기록 날짜 계산 헬퍼 추가, 프로필 표시/편집 draft 러닝 시작일에 우선 적용
- `src/app/page.dashboard/view.pug`: 프로필 시작일 표시를 보정된 날짜 getter로 변경
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/006-profile-first-run-date.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
