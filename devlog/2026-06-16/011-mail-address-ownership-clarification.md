# 앱 발신 이메일 생성 위치 설명 보강

- **ID**: 011
- **날짜**: 2026-06-16
- **유형**: 운영 문서
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
SendGrid가 메일함을 생성하는 서비스인지 혼동되지 않도록 앱 발신 이메일의 생성 위치를 문서에 명확히 추가했다.
발신 전용 주소는 SendGrid 도메인 인증만으로 사용할 수 있고, 답장 수신이 필요하면 도메인 메일 호스팅 또는 이메일 라우팅에서 메일함/별칭을 별도로 만들어야 한다.

## 변경 파일 목록
- `docs/mail-sender-setup-2026-06-15.md`: SendGrid 역할, 발신 전용/답장 수신/SMTP 방식 구분 추가.
- `config-sample/mail.env.example`: SendGrid는 메일함 생성 서비스가 아니라는 주석 추가.
- `devlog.md`, `devlog/2026-06-16/011-mail-address-ownership-clarification.md`: 작업 이력 기록.

## 확인 결과
- `mail.env`의 `RUNNINGMATE_MAIL_FROM`은 발신 주소 문자열이며, 실제 수신함이 필요한지는 운영 정책에 따라 별도로 결정하면 된다.
