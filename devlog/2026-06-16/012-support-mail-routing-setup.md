# support 메일 주소 생성 방식 문서화

- **ID**: 012
- **날짜**: 2026-06-16
- **유형**: 운영 문서
- **리뷰 ID**: aciypejgdrkzomvoztoafcsbqklxuacs

## 작업 요약
`support@myrunningmate.com` 같은 앱용 수신 주소를 만드는 절차를 별칭/라우팅 방식과 실제 메일함 방식으로 나누어 문서화했다.
러닝메이트 운영에서는 SendGrid 발송과 이메일 라우팅 수신 조합이면 충분하다는 권장 방향을 명시했다.

## 변경 파일 목록
- `docs/mail-sender-setup-2026-06-15.md`: support 주소 생성 방법, DNS 레코드, SMTP 사용 여부 설명 추가.
- `devlog.md`, `devlog/2026-06-16/012-support-mail-routing-setup.md`: 작업 이력 기록.

## 확인 결과
- 이메일 라우팅은 수신/전달 기능이며 SMTP 발송 계정이 아니라는 점을 문서에 분리했다.
- 실제 메일함을 만들 경우 MX/SPF/DKIM/DMARC와 SMTP credential이 필요하다는 점을 정리했다.
