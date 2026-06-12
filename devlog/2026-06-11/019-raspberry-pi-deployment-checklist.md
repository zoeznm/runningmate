# 라즈베리파이 배포 준비 체크리스트 문서화

- **ID**: 019
- **날짜**: 2026-06-11
- **유형**: 문서 업데이트

## 작업 요약

러닝메이트 WIZ 프로젝트를 라즈베리파이에 배포하기 전에 확인해야 할 프레임워크, 런타임, 실행/빌드 명령, 포트, 외부 서비스, 환경변수, Docker 가능성, ARM64 리스크, 서버 이전 대상 파일을 체크리스트로 정리했다.
실제 비밀값은 기록하지 않고 환경변수 이름만 문서화했다.

## 원문 요청사항

```text
# ReviewOps Codex 작업 요청

아래 요청을 현재 프로젝트 루트에서 처리하세요. 필요한 파일을 직접 수정하고, 마지막 응답은 한국어로 간결하게 작성하세요.
스트리밍 응답은 사용하지 않습니다. 작업이 끝난 뒤 변경 요약, 확인한 내용, 남은 리스크만 정리하세요.
이 작업의 세션 단위는 아래 리뷰 ID입니다. 리뷰 ID가 같으면 같은 Codex 히스토리 맥락으로 이어서 처리하세요.

## 사용자 요청

작업 진행해줘

## 리뷰 요약

- 리뷰 ID: jgxjzzuisfkxhadozuyrxdzoedizrybi
- 제목: 알아야할것
- 요청 링크: https://matomabo.run.seasonai.net/access
- Codex 요청자: 김보미
- 프로젝트 루트: /opt/app
- Codex 세션 ID: 신규
- 스크린샷 컨텍스트: 없음
- 에이전트 작업 지시서 컨텍스트: 포함됨
- HTML 문서 생성 규칙 컨텍스트: 없음
- HTML 문서 설정 컨텍스트: 없음
- HTML 프로젝트 인스트럭션 파일: 없음
- 첨부파일 컨텍스트: 0개

## 리뷰어 요청 내용

이 프로젝트를 라즈베리파이에 배포하려고 해.
배포 준비를 위해 아래 정보를 정리해줘.

1. 프론트엔드/백엔드 프레임워크가 뭔지
2. 사용 언어와 런타임 버전
3. package.json, requirements.txt, Dockerfile, docker-compose.yml 같은 실행 관련 파일이 있는지
4. 앱 실행 명령어
5. 빌드 명령어
6. 사용하는 포트
7. 데이터베이스나 Redis 같은 외부 서비스가 필요한지
8. 환경변수(.env)에 어떤 키가 필요한지, 값은 숨기고 이름만
9. 배포에 Docker를 쓸 수 있는 구조인지
10. 라즈베리파이 ARM64 환경에서 문제될 의존성이 있는지
11. 배포하려면 어떤 파일/폴더를 서버로 옮겨야 하는지

답변은 체크리스트 형태로 정리해줘.
```

## 변경 파일 목록

- `docs/raspberry-pi-deployment-checklist-2026-06-11.md`
  - 라즈베리파이 배포 준비 정보를 11개 항목 체크리스트로 신규 작성.
- `devlog.md`
  - 2026-06-11 ID 019 요약 행 추가.
- `devlog/2026-06-11/019-raspberry-pi-deployment-checklist.md`
  - 작업 상세 devlog 추가.

## 확인한 내용

- WIZ 워크스페이스 현재 프로젝트가 `main`임을 확인했다.
- `.github/custom/custom-instructions.md`는 존재하지 않음을 확인했다.
- `.github/task/todo.md`는 존재하지 않음을 확인했다.
- `package.json`, `.env.example`, `README.md`, `config/database.py`, `src/angular/package.json`, `ops/nginx-runningmate.conf.example`, `/opt/app/run.sh`, `/opt/app/config/boot.py`, `/opt/app/public/app.py`를 확인했다.
- `rg --files`로 `requirements.txt`, `Dockerfile`, `docker-compose.yml` 부재와 실행 관련 파일 목록을 확인했다.
- `python --version`, `node --version`, `npm --version`, `npm ls --depth=0`, `python -c "import season"`, `pip show ...`로 현재 런타임/주요 패키지 버전을 확인했다.

## 검증 결과

- 문서 변경만 수행했으므로 WIZ/Angular 빌드는 실행하지 않았다.
- 새 체크리스트 문서와 devlog 상세 파일을 생성했다.
