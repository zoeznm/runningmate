# 생리주기 연동 초기 구현 catch-up

- **ID**: 034
- **날짜**: 2026-06-08
- **유형**: 기능 추가

## 작업 요약
동일 ReviewOps 세션에서 앞서 처리된 생리주기 연동 초기 구현 이력을 보정 기록한다.
설정에서 명시적으로 켠 경우에만 달력 입력, 달력 오버레이, 분석 카드, AI 페이서 컨텍스트, `/api/cycles`가 동작하도록 구성했다.

## 원문 요청사항
```text
작업 진행해줘

생리주기 연동 기능 추가해줘. (선택적 기능, 설정에서 on/off)
```

## 변경 파일 목록
- `src/model/runningmate.py`: 생리주기 로컬 저장, 요약, 단계 계산, AI 컨텍스트 모델 로직 추가.
- `src/route/api.cycles/app.json`: `/api/cycles` 라우트 설정 추가.
- `src/route/api.cycles/controller.py`: 생리주기 GET/POST/DELETE API와 명시 동의 헤더 처리 추가.
- `src/route/api.chat/controller.py`: 사용자가 기능을 켠 경우에만 주기 컨텍스트를 AI 응답에 참고하도록 처리.
- `src/app/page.dashboard/view.ts`: 생리주기 상태, 달력 오버레이, 저장/삭제, 분석 데이터 구성 추가.
- `src/app/page.dashboard/view.pug`: 설정, 달력 입력, 주기 패턴 카드 UI 추가.
- `src/app/page.dashboard/view.scss`: 섹션7 토큰 기반 다크모드 주기 UI 스타일 추가.

## 확인 결과
- 당시 WIZ 빌드와 번들 반영을 확인했다.
- 로컬 `/api/cycles?enabled=1` 접근과 설정 화면 노출 여부를 확인했다.

