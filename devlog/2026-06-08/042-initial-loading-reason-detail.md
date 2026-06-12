# 초기 로딩 사유 표시

- **ID**: 042
- **날짜**: 2026-06-08
- **유형**: UX 수정
- **리뷰 ID**: yzebcyqgvswnblkfhvjciahsukglxdcu

## 작업 요약
대시보드 최초 진입/새로고침 시 전체 화면 로딩 문구 아래에 현재 처리 중인 초기화 사유를 함께 표시하도록 수정했다.
러닝 기록, 프로필, 위치, 날씨, 페이서 AI, 음악 연결, 대화 기록, 커뮤니티 피드, 랭킹 등 초기 로딩 단계별 문구를 갱신한다.
위치 조회 중에는 `위치 확인 중`, 날씨 API 호출 중에는 `날씨를 불러오는 중`, AI 상태 확인 중에는 `페이서 AI 연결 확인 중`이 표시되도록 했다.

## 원문 요청사항
```text
그러면 로딩할때 이유도 같이 말해주면 좋겠어 초기 데이터를 불러오는 중이라고만 하지 말고 뭐 날씨 불러오는 중 위치 불러오는 중 페이서 AI 연결하는 중 이런식으로 원인도 같이 얘기를 해주면 좋을 거 같애
```

## 변경 파일 목록
- `src/app/component.loading.fullscreen/view.ts`: 로딩 컴포넌트에 보조 설명 `detail` 입력을 추가했다.
- `src/app/component.loading.fullscreen/view.pug`: 메인 로딩 문구 아래에 보조 설명을 표시했다.
- `src/app/component.loading.fullscreen/view.scss`: 보조 설명 텍스트 스타일과 패널 폭/간격을 조정했다.
- `src/app/page.dashboard/view.pug`: 대시보드 초기 로딩 컴포넌트에 `initialLoadingDetail`을 연결했다.
- `src/app/page.dashboard/view.ts`: 초기 로딩 단계 추적 및 우선순위 기반 상세 문구 갱신을 추가했다.
- `devlog.md`: 작업 요약 행 추가.
- `devlog/2026-06-08/042-initial-loading-reason-detail.md`: 작업 상세 기록 추가.

## 확인 결과
- `wiz_project_build(projectName="main", clean=false)` 성공.
