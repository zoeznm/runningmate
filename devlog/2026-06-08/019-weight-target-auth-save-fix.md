# 목표 체중 저장 세션/토큰 처리 보강

- **ID**: 019
- **날짜**: 2026-06-08
- **유형**: 버그 수정
- **리뷰 ID**: wcxchygmddyvhyeurbnoeicrmorhhuvt

## 작업 요약
목표 체중 저장이 계속 실패하는 원인으로 세션 쿠키와 Bearer 토큰 인증 경계, 그리고 저장 후 응답 생성 중 실패 가능성을 확인했다. `/api/weights`가 세션 쿠키가 없을 때도 `Authorization: Bearer` 토큰을 검증해 사용자 ID를 복구하도록 보강했다. 목표 체중 저장 응답은 체중 목록/요약 계산을 제거하고 설정 저장 결과만 반환하도록 단순화했다. 프론트는 401 실패 시 토큰 갱신 후 한 번 재시도하고, 중첩 응답에서도 목표 설정값을 적용하도록 수정했다. 서비스워커 캐시 버전도 올려 이전 번들 캐시를 비우도록 했다.

## 원문 요청사항
```text
여전히 저장이 안되는데 오류 수정하고 저장되게 해줘
```

## 변경 파일 목록
- `src/app/page.dashboard/view.ts`: 목표 체중 저장 401 재시도 및 중첩 응답 설정 적용 보강
- `src/route/api.weights/controller.py`: Bearer 토큰 기반 사용자 복구 및 목표 저장 응답 단순화
- `src/route/api.training-load/controller.py`: Bearer 토큰 기반 사용자 복구 추가
- `config/pwa/sw.js`: PWA 캐시 버전 갱신
- `devlog.md`: 작업 요약 행 추가
- `devlog/2026-06-08/019-weight-target-auth-save-fix.md`: 상세 devlog 추가

## 확인 결과
- `python -m py_compile project/main/src/route/api.weights/controller.py project/main/src/route/api.training-load/controller.py project/main/src/model/runningmate.py` 성공
- WIZ `wiz_project_build(clean=false)` 성공
- 운영 `main.js`가 갱신되고 `/api/weight-settings` 참조가 없는 것 확인
- 운영 `sw.js`의 캐시 버전이 `runningmate-pwa-v8`로 갱신된 것 확인
- 운영 `/api/weights`가 JSON API로 응답하는 것 확인
