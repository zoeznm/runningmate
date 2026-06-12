# 목표 체중 저장 후 편집 폼 자동 닫힘

- **ID**: 023
- **날짜**: 2026-06-08
- **유형**: UX 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
체중 화면에서 목표 체중을 입력하고 `목표 저장`을 누르면 `목표 체중 수정` 입력 폼이 바로 접히도록 수정했다. 저장 요청은 계속 진행하되, 검증된 목표값을 요약 카드에 즉시 반영한 뒤 편집 상태를 닫도록 했다. 편집 폼이 닫힌 상태에서도 저장 실패를 알 수 있도록 실패 시 토스트 메시지를 추가했다.

## 원문 요청사항
```text
목표 제충 저렇게 작성하고 목표 저장하면 저 목표 체중 수정 이라는 부분 없어지게 해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장 시 편집 폼 즉시 닫힘 및 실패 토스트 처리 추가
- `config/pwa/sw.js`: PWA 캐시 버전을 `runningmate-pwa-v10`으로 갱신
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/023-weight-target-editor-collapse.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js`에 `isWeightTargetEditing` 종료 코드 반영 확인
- 운영 `sw.js` 캐시 버전 `runningmate-pwa-v10` 확인
