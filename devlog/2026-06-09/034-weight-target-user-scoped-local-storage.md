# 목표 체중 로컬 저장 사용자별 분리

- **ID**: 034
- **날짜**: 2026-06-09
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
새로 가입한 사용자에게도 admin이 설정한 목표 체중이 보이는 문제를 수정했다. 원인은 프론트에서 목표 체중 임시값을 `runningmate-weight-target-v1` 전역 로컬 저장 키로 읽고 저장해, 같은 브라우저의 다른 사용자에게 값이 섞일 수 있는 구조였다. 생성자에서 전역 목표 체중을 먼저 읽는 동작을 제거하고, 프로필 로딩 후 사용자 식별자 기반 키로만 목표 체중을 읽고 저장하도록 변경했다. 기존 전역 키는 프로필 확인 시 제거한다.

## 원문 요청사항
```text
새롭게 회원가입한 사용자한테도 admin이 설정해둔 목표체중이 그대로 떠 
수정해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 로컬 저장소 키를 사용자별로 분리하고 legacy 전역 키 제거
- `config/pwa/sw.js`: PWA 캐시 버전을 `runningmate-pwa-v17`로 갱신
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-09/034-weight-target-user-scoped-local-storage.md`: 상세 devlog 추가

## 확인 결과
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js`에 `currentUserStorageIdentity`, `weightTargetStorageKeyForCurrentUser`, `removeLegacyWeightTargetLocal` 반영 확인
- 운영 `sw.js` 캐시 버전 `runningmate-pwa-v17` 확인
- 비로그인 운영 `/api/weights?period=all` 요청이 JSON 401로 응답하는 것 확인
