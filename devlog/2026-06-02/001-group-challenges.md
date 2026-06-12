# 그룹 챌린지 기능 추가

- **ID**: 001
- **날짜**: 2026-06-02
- **유형**: 기능 추가

## 작업 요약
그룹 챌린지를 생성하고 초대코드로 참여할 수 있는 API와 대시보드 화면을 추가했다.
기간 내 러닝 저장/삭제 시 챌린지 기여도를 재계산하고, 상세 화면에서 전체 진행률, 참가자별 랭킹, D-day, 결과 상태를 확인할 수 있게 했다.

## 원문 요청사항
```text
작업 진행해줘

INSTRUCTIONS.md 참고해서 작업해.

그룹 챌린지 기능 추가해줘. (다같이 공동 목표)

[데이터]
challenges (
  id UUID PK,
  title VARCHAR(100),
  type VARCHAR(20),        total_distance|individual_distance|count
  goal_value DECIMAL,
  start_date DATE, end_date DATE,
  creator_id UUID FK,
  invite_code VARCHAR(10) UNIQUE,
  created_at
)
challenge_members (challenge_id, user_id, joined_at, contributed_value)

[챌린지 종류]
- total_distance: 참가자 거리 합산 (예: 다같이 500km)
- individual_distance: 각자 목표 달성 (예: 각자 50km)
- count: 러닝 횟수

[화면]
1. 챌린지 목록 (참여중/모집중/종료)
2. 챌린지 생성
   - 제목, 종류, 목표값, 기간 설정
   - 초대코드 자동 생성
3. 챌린지 참여
   - 초대코드 입력 또는 친구 챌린지에서 참여
4. 챌린지 상세
   - 전체 진행률 바(목표 대비)
   - 참가자별 기여도 랭킹
   - 남은 기간 D-day

[로직]
- 기간 내 러닝 저장 시 자동으로 챌린지 기여도 반영
- 종료 시 달성 여부 판정 + 결과 화면

[API]
POST /api/challenges, POST /api/challenges/join,
GET /api/challenges, GET /api/challenges/:id

섹션7 토큰. 다크/라이트.
```

## 변경 파일 목록
- `src/model/runningmate.py`: 챌린지 JSON 저장소, 생성/참여/목록/상세, 기여도 재계산, 결과 판정 추가
- `src/route/api.challenges/`: `GET/POST /api/challenges` 추가
- `src/route/api.challenges.join/`: `POST /api/challenges/join` 추가
- `src/route/api.challenges.detail/`: `GET /api/challenges/<challenge_id>` 추가
- `src/route/api.runs/controller.py`: 러닝 저장 시 세션 사용자 ID 보존 추가
- `src/app/page.dashboard/view.ts`: 챌린지 탭 상태, API 연동, 생성/참여 로직 추가
- `src/app/page.dashboard/view.pug`: 챌린지 목록/상세/생성/참여 화면 추가
- `src/app/page.dashboard/view.scss`: 다크/라이트 토큰 기반 챌린지 UI 스타일 추가
