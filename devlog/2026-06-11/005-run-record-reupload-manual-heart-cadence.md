# 기존 러닝 기록 재업로드 및 수동 입력 심박/케이던스 추가

## 사용자 원본 요청

그리고 이미 올라간 기록날같은 것도 수정하기 버튼 누르면 기록 다시 업로드 할 수 있게 해줘  
그리고 만약에 이미지가 업로드가 안될 때 수동 입력을 할 수 있게 되어있던데 그때 케이던스랑 심박수도 사용자가 입력할 수 있게 해줘 지금은 심박수랑 케이던스를 입력하는 란이 없어

## 처리 내용

- 이미 기록이 있는 날짜의 기록 카드에 `기록 다시 업로드`와 `수동 수정` 액션을 추가했다.
- 기존 기록 재업로드 시 새 기록을 추가하지 않고 `/api/runs/{id}` PATCH로 해당 기록을 갱신하도록 연결했다.
- 수동 입력 폼에 평균 심박수(`bpm`)와 케이던스(`spm`) 입력란을 추가했다.
- 기존 기록을 수동 수정할 때 거리, 페이스, 시간, 칼로리, 심박수, 케이던스를 기존 값으로 채우도록 했다.
- 백엔드 기록 수정 API에서 거리, 페이스, 시간, 칼로리, 심박수, 케이던스, 이미지 URL, 원본 파싱 JSON 갱신을 허용했다.
- PWA 캐시 버전을 `runningmate-pwa-v22`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `src/app/page.dashboard/view.pug`
- `src/app/page.dashboard/view.scss`
- `src/model/runningmate.py`
- `src/route/api.runs.detail/controller.py`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/005-run-record-reupload-manual-heart-cadence.md`

## 검증 결과

- `git diff --check` 통과
- `wiz_project_build(clean=false)` 성공
- `python3 -m py_compile src/model/runningmate.py src/route/api.runs.detail/controller.py` 통과

## 남은 리스크

- 실제 이미지 재업로드와 수동 수정 저장은 로그인 세션 및 업로드 샘플이 필요한 브라우저 E2E 환경에서 추가 확인이 필요하다.
