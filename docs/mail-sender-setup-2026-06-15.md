# 러닝메이트 메일 발신 설정

작성일: 2026-06-15

## 권장 방식

운영 도메인 `myrunningmate.com`이 있으므로 `no-reply@myrunningmate.com` 같은 앱 전용 발신 주소를 정하고, SendGrid의 Domain Authentication으로 SPF/DKIM을 DNS에 등록하는 방식을 권장한다.

SendGrid는 Domain Authentication에서 DKIM 서명과 SPF 인증을 CNAME 레코드로 관리할 수 있고, Mail Send API는 API Key를 Bearer Token으로 사용한다.

SendGrid는 메일함을 만들어주는 서비스가 아니라 인증된 도메인/발신 주소로 메일을 보내주는 발송 서비스다.
`no-reply@myrunningmate.com`을 발신 전용으로만 쓸 경우 실제 메일함을 만들지 않아도 되지만, 사용자의 답장이나 운영 알림 수신이 필요하면 도메인 메일 호스팅 또는 DNS 이메일 라우팅에서 메일함/별칭을 별도로 만든다.

권장 구분:

- 발신 전용: SendGrid Domain Authentication + `RUNNINGMATE_MAIL_FROM=no-reply@myrunningmate.com`
- 답장 수신 필요: 메일 호스팅에서 `support@myrunningmate.com` 또는 `hello@myrunningmate.com` 메일함/별칭 생성 후 `RUNNINGMATE_MAIL_FROM`에 사용
- SMTP 발송: 메일 호스팅에서 만든 계정의 SMTP 정보를 `mail.env`에 설정

## support 주소를 만드는 방법

### 선택 A. 별칭/라우팅만 만들기

사용자 답장을 개인 메일함으로 전달받기만 하면 되는 경우다.
앱 발송은 계속 SendGrid가 담당하고, `support@myrunningmate.com`으로 들어오는 메일만 기존 Gmail/Naver/개인 메일로 전달한다.

1. 도메인의 DNS를 관리하는 서비스에서 이메일 라우팅 또는 메일 포워딩 기능을 연다.
2. 수신 대상 주소를 먼저 등록한다. 예: 개인 Gmail 또는 운영자가 실제로 보는 메일함.
3. `support@myrunningmate.com` 라우팅 규칙을 만들고 수신 대상 주소로 전달한다.
4. 서비스가 요구하는 MX/TXT 레코드를 DNS에 추가한다.
5. 외부 메일에서 `support@myrunningmate.com`으로 보내 수신되는지 확인한다.
6. 앱 메일에 답장받을 주소로 쓰려면 `RUNNINGMATE_MAIL_FROM=support@myrunningmate.com` 또는 별도 Reply-To 지원을 추가한 뒤 사용한다.

주의: 이메일 라우팅은 보통 수신/전달 기능이다. 이 주소로 SMTP 로그인해서 보내는 계정은 아니다.

### 선택 B. 실제 메일함 만들기

`support@myrunningmate.com`으로 직접 로그인해서 메일을 읽고 보내고 싶거나, SMTP 계정으로 앱 발송까지 처리하고 싶을 때 쓴다.

1. 도메인 메일 호스팅 서비스를 선택한다.
2. 서비스에서 `myrunningmate.com` 도메인을 추가한다.
3. 서비스가 안내하는 MX, SPF, DKIM, DMARC 레코드를 DNS에 등록한다.
4. 사용자 또는 그룹/별칭으로 `support@myrunningmate.com`을 만든다.
5. 웹메일에서 송수신 테스트를 한다.
6. 앱도 SMTP로 보내려면 해당 계정의 SMTP host, username, password 또는 app password를 `/opt/app/config/mail.env`에 설정한다.

러닝메이트 운영에는 선택 A와 SendGrid 발송 조합이면 충분하다.
사용자가 답장한 메일을 받아보기만 하면 되고, 대량/트랜잭션 발송은 SendGrid가 맡는 구조가 단순하다.

## SendGrid 설정 순서

1. 발신 주소를 정한다. 기본값은 발신 전용 `no-reply@myrunningmate.com`이다.
2. 답장 수신이 필요하면 도메인 메일 호스팅에서 `support@myrunningmate.com` 같은 메일함/별칭을 만든다.
3. SendGrid에서 Sender Authentication > Authenticate a Domain을 연다.
4. 도메인은 `myrunningmate.com`으로 등록하고 Automated Security를 켠다.
5. SendGrid가 제시하는 CNAME 레코드를 도메인 DNS에 추가한다.
6. SendGrid에서 인증이 완료될 때까지 Verify를 반복한다.
7. Settings > API Keys에서 Mail Send 권한이 있는 API Key를 만든다.
8. 서버의 `/opt/app/config/mail.env`를 아래 형태로 채운다.

```env
RUNNINGMATE_MAIL_DOMAIN=myrunningmate.com
RUNNINGMATE_MAIL_FROM=no-reply@myrunningmate.com
RUNNINGMATE_MAIL_FROM_NAME=RunningMate
SENDGRID_API_KEY=<sendgrid_api_key>
```

9. 파일 권한을 `600`으로 제한한다.
10. `python scripts/verify_runtime_secrets.py`로 secret 구성을 확인한다.

## SMTP 대안

SendGrid 대신 도메인 메일 제공업체의 SMTP를 쓰려면 `/opt/app/config/mail.env`에 아래 값을 넣는다.

```env
RUNNINGMATE_MAIL_DOMAIN=myrunningmate.com
RUNNINGMATE_MAIL_FROM=no-reply@myrunningmate.com
RUNNINGMATE_MAIL_FROM_NAME=RunningMate
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=no-reply@myrunningmate.com
SMTP_PASSWORD=<smtp_password_or_app_password>
SMTP_USE_TLS=true
```

SMTP를 쓰더라도 도메인 DNS의 SPF, DKIM, DMARC 설정은 발송 성공률에 직접 영향을 준다.
