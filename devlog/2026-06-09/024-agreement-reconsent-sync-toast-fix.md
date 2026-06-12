# 약관 재동의 체크 동기화 및 완료 토스트 차단 수정

- 날짜: 2026-06-09
- 리뷰 ID: hcbeuqydmdrwryamizxodwwbgenclxbp
- 요청자: 김보미

## 사용자 원문

1. 전체 동의 체크 리스트를 선택해도 약간 느리게 나머지 4개가 체크된다.
2. 전체 동의 체크 리스트를 선택 해제해도 나머지 4개가 해제되지 않는다.
3. [선택] 체크 리스트를 선택하지 않고 동의하고 계속 버튼을 클릭하면 넘어가지 않는다.
4. 4개를 모두 선택하고 동의하고 계속을 누르면 넘어가는데 약관동의 완료했습니다. 라는 모달이 아래에 뜸 근데 그거를 x 버튼을 눌러서 없애고 싶은데 안 없어짐 그래서 온보딩 화면을 진행할 수가 없음.

이런 문제점들이 있는데 수정해줘

## 변경 파일

- `src/angular/app/app.component.pug`
- `src/angular/app/app.component.ts`
- `src/app/page.access/view.pug`
- `src/app/page.access/view.ts`
- `src/app/component.toast/view.pug`
- `src/app/component.toast/view.ts`
- `devlog.md`
- `devlog/2026-06-09/024-agreement-reconsent-sync-toast-fix.md`

## 작업 내용

- 전역 약관 재동의 모달의 전체/개별 체크박스를 `ngModelChange` 기반으로 변경해 체크 상태를 boolean 값으로 즉시 반영하도록 했다.
- 전체 동의 선택/해제 직후 change detection을 실행해 상단 체크박스와 4개 항목 표시가 같은 프레임에 맞도록 보강했다.
- 필수 3개 항목만 동의하면 `[선택]` 마케팅 동의 없이도 계속 진행할 수 있도록 기존 필수 판정 로직을 유지하면서 체크 동기화 문제를 제거했다.
- 약관 저장 성공 후 완료 토스트를 띄우지 않고 기존 토스트를 정리해 온보딩 진행을 막지 않도록 했다.
- 토스트 닫기 버튼이 컴포넌트 메서드를 통해 dismiss와 change detection을 같이 수행하도록 보강했다.
- `/access` 회원가입 단계의 약관 체크리스트도 동일한 `ngModelChange` 방식으로 맞췄다.

## 확인

- `wiz_project_build(clean=false)` 성공.
- `git diff --check` 성공.

## 남은 리스크

- ReviewOps 재현 계정으로 실제 회원가입 후 온보딩 진행까지의 브라우저 수동 검증은 수행하지 못했다.
