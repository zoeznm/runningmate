# 대시보드 초기 로딩 차단 범위 축소

## 사용자 원본 요청

초기데이터를 불러오는 과정이 너무 오래걸리는데 어떻게 단축해? 나는 어플을 들어가면 바로 보이면 좋겠거든

## 처리 내용

- 기존 초기 로딩이 인증, 러닝 기록, 프로필뿐 아니라 AI, 음악, 채팅 기록, 메모, 휴식일, 체중, 뱃지, 목표, 챌린지, 피드, 알림, 랭킹, 주기, 날씨까지 모두 기다리는 구조임을 확인했다.
- 첫 화면을 막는 필수 로딩을 인증, 러닝 기록, 프로필로 축소했다.
- 러닝 기록 로딩 안에서 추가로 기다리던 훈련 부하 분석 호출도 초기 차단에서 제외했다.
- AI/음악/채팅/메모/체중/뱃지/목표/챌린지/피드/알림/랭킹/주기/날씨/훈련 부하는 첫 화면을 연 뒤 백그라운드로 불러오도록 분리했다.
- 백그라운드 작업 실패가 첫 화면 렌더링을 막지 않도록 개별 작업 오류를 흡수하게 했다.
- PWA 캐시 버전을 `runningmate-pwa-v28`로 갱신했다.

## 변경 파일

- `src/app/page.dashboard/view.ts`
- `config/pwa/sw.js`
- `devlog.md`
- `devlog/2026-06-11/014-dashboard-initial-load-fast-path.md`

## 검증 결과

- `git diff --check -- src/app/page.dashboard/view.ts config/pwa/sw.js devlog.md devlog/2026-06-11` 통과
- `wiz_project_build(clean=false)` 성공
- WIZ 자식 프로세스 재시작 완료
- 번들에 `loadDeferredDashboardData`, `loadRuns(true, false)`, `runningmate-pwa-v28` 반영 확인
- `curl http://127.0.0.1:3000/dashboard` 응답 200 확인

## 남은 리스크

- 첫 화면은 빨리 보이지만, 백그라운드 데이터인 날씨/랭킹/피드/AI 상태 등은 화면 진입 직후 순차적으로 채워질 수 있다.
- 실제 체감 속도는 사용자 기기, PWA 캐시 갱신, 네트워크 상태에 따라 다르므로 실기기에서 확인이 필요하다.
