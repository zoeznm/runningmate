# 타 사용자 프로필 API 파싱 오류 메시지 문구 수정

- **ID**: 029
- **날짜**: 2026-06-08
- **유형**: 버그 수정

## 작업 요약
공용 API 응답 파싱 실패 메시지가 이미지 OCR 실패 문구로 설정되어 있어, 타 사용자 프로필 상세 API가 JSON을 읽지 못할 때 "이미지를 읽지 못했어. 수동으로 입력할래?"가 노출됐다.
공용 파싱 오류 문구를 일반 API 응답 오류 문구로 바꾸고, 이미지 업로드 OCR 실패 안내는 업로드 처리 경로의 기존 문구로 유지했다.

## 원문 요청사항
```text
작업 진행해줘

이미지를 읽지 못했어. 수동으로 입력할래? 라는 문구가 왜 뜨는거야?
```

## 변경 파일 목록
- `src/angular/app/shared/api.ts`: 공용 `parse` 오류 기본 메시지를 OCR 전용 문구에서 일반 응답 파싱 실패 문구로 변경.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/029-api-parse-message-scope.md`: 작업 상세 기록 추가.

## 확인 결과
- `wiz_project_build(projectName="main", clean=false)` 성공.
- `rg -n "parse: '이미지를 읽지 못했어|응답을 읽지 못했어|이미지를 읽지 못했어" src/angular/app/shared build/src/app/shared bundle src/app/page.dashboard`로 공용 API 메시지와 빌드 산출물 반영을 확인했다.
