import json
import html
import datetime
import os
import smtplib
import urllib.request
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid, parseaddr
from urllib.parse import quote, urlparse


struct = wiz.model("struct")
config = wiz.model("portal/season/config")
request = wiz.server.package.flask.request
security = wiz.model("security")
security.auth_headers()

GENERIC_MESSAGE = "가입된 이메일이라면 재설정 링크를 발송했습니다. 메일함을 확인해주세요."
MAIL_FROM_NAME = "RunMate"
DEFAULT_MAIL_DOMAIN = "matomabo.run.seasonai.net"


def _load_env_file():
    env_files = [
        os.environ.get("RUNNINGMATE_MAIL_ENV_FILE"),
        "/opt/app/config/mail.env",
        os.environ.get("RUNNINGMATE_OPENAI_ENV_FILE", "/opt/app/config/openai.env"),
    ]

    for env_file in [path for path in env_files if path]:
        if not os.path.exists(env_file):
            continue

        try:
            with open(env_file, "r", encoding="utf-8") as fp:
                for line in fp:
                    key, _, value = line.strip().partition("=")
                    if key and value and key not in os.environ:
                        os.environ[key] = value.strip().strip('"').strip("'")
        except Exception:
            continue


def _payload():
    try:
        data = request.get_json(silent=True)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    raw = request.get_data(as_text=True)
    if not raw:
        email = request.args.get("email") or wiz.request.query("email", "")
        return {"email": email} if email else {}

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}

    return {}


def _response(status_code=200, success=True, message=GENERIC_MESSAGE):
    payload = {"success": success, "message": message}
    if status_code >= 400:
        return wiz.response.status(status_code, **payload)
    return wiz.response.json(payload)


def _base_url():
    configured = os.environ.get("RUNNINGMATE_PASSWORD_RESET_BASE_URL") or os.environ.get("RUNNINGMATE_PUBLIC_BASE_URL")
    if configured:
        return configured.rstrip("/")

    scheme = str(request.headers.get("X-Forwarded-Proto") or request.scheme or "https").split(",")[0].strip()
    host = str(request.headers.get("X-Forwarded-Host") or request.host or "").split(",")[0].strip()
    return f"{scheme}://{host}".rstrip("/")


def _reset_url(token):
    return f"{_base_url()}/access?reset_token={quote(token)}"


def _mail_domain():
    configured = os.environ.get("RUNNINGMATE_MAIL_DOMAIN")
    if configured:
        return configured.strip().split(":")[0] or DEFAULT_MAIL_DOMAIN

    host = ""
    base_url = os.environ.get("RUNNINGMATE_PUBLIC_BASE_URL") or os.environ.get("RUNNINGMATE_PASSWORD_RESET_BASE_URL")
    if base_url:
        host = urlparse(base_url).netloc or base_url
    if not host:
        host = str(request.headers.get("X-Forwarded-Host") or request.host or "")

    host = host.split(",")[0].strip().split(":")[0]
    if not host or host in ("localhost", "127.0.0.1", "0.0.0.0") or host.replace(".", "").isdigit():
        return DEFAULT_MAIL_DOMAIN
    return host


def _default_sender_address():
    return f"no-reply@{_mail_domain()}"


def _sender():
    return (
        os.environ.get("RUNNINGMATE_MAIL_FROM")
        or os.environ.get("SENDGRID_FROM_EMAIL")
        or os.environ.get("SMTP_SENDER")
        or os.environ.get("SMTP_FROM")
        or config.smtp_sender
    )


def _sender_name():
    return (
        os.environ.get("RUNNINGMATE_MAIL_FROM_NAME")
        or os.environ.get("SMTP_FROM_NAME")
        or MAIL_FROM_NAME
    ).strip() or MAIL_FROM_NAME


def _sender_address():
    sender = _sender()
    if not sender:
        return ""
    _name, address = parseaddr(str(sender))
    return address or str(sender).strip()


def _sender_header(sender=None):
    sender = sender or _sender() or _default_sender_address()
    if not sender:
        return ""
    _name, address = parseaddr(str(sender))
    if not address:
        return str(sender).strip()
    return formataddr((_sender_name(), address))


def _mail_configured():
    sender = _sender_address()
    if os.environ.get("SENDGRID_API_KEY") and sender:
        return True
    host = os.environ.get("SMTP_HOST") or config.smtp_host
    return bool(host and sender)


def _email_html(name, reset_url):
    display_name = html.escape(str(name or "러닝메이트 사용자").strip())
    safe_url = html.escape(str(reset_url or ""), quote=True)
    return f"""
<div style="font-family:Arial,sans-serif;line-height:1.6;color:#0f172a">
  <h2>비밀번호 재설정 안내</h2>
  <p>{display_name}님, 비밀번호 재설정을 요청하셨습니다.</p>
  <p>아래 버튼을 눌러 30분 안에 새 비밀번호를 설정해주세요.</p>
  <p><a href="{safe_url}" style="display:inline-block;background:#4f46e5;color:#fff;padding:12px 18px;border-radius:8px;text-decoration:none;font-weight:700">비밀번호 재설정</a></p>
  <p>요청하지 않았다면 이 메일을 무시해도 됩니다.</p>
</div>
"""


def _message(to, subject, html, sender):
    msg = MIMEText(html, "html", _charset="utf-8")
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg["From"] = _sender_header(sender)
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=_mail_domain())
    return msg


def _mask_email(email):
    name, address = parseaddr(str(email or ""))
    if not address or "@" not in address:
        return "unknown"
    local, domain = address.split("@", 1)
    if len(local) <= 2:
        return f"{local[:1]}***@{domain}"
    return f"{local[:2]}***@{domain}"


def _log_mail(message):
    safe_message = security.mask_sensitive(message)
    line = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [forgot-password] {safe_message}"
    log_path = os.environ.get("RUNNINGMATE_MAIL_LOG", "/var/log/wiz/mail.log")
    try:
        with open(log_path, "a", encoding="utf-8") as fp:
            fp.write(line + "\n")
    except Exception:
        pass
    security.safe_log("forgot-password", safe_message)


def _send_sendgrid(to, subject, html):
    api_key = os.environ.get("SENDGRID_API_KEY")
    sender = _sender_address()
    if not api_key or not sender:
        return False

    body = json.dumps({
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": sender, "name": _sender_name()},
        "subject": subject,
        "content": [{"type": "text/html", "value": html}],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return 200 <= int(resp.status) < 300


def _send_smtp(to, subject, html):
    host = os.environ.get("SMTP_HOST") or config.smtp_host
    port = int(os.environ.get("SMTP_PORT") or config.smtp_port or 587)
    sender = _sender_address()
    password = os.environ.get("SMTP_PASSWORD") or os.environ.get("SMTP_PASS") or config.smtp_password
    username = os.environ.get("SMTP_USERNAME") or os.environ.get("SMTP_USER") or sender
    use_tls = str(os.environ.get("SMTP_USE_TLS", "true")).strip().lower() not in ("0", "false", "no")

    if not host or not sender:
        return False

    msg = _message(to, subject, html, sender)

    mailserver = smtplib.SMTP(host, port, timeout=10)
    try:
        mailserver.ehlo()
        if use_tls:
            mailserver.starttls()
            mailserver.ehlo()
        if password:
            mailserver.login(username, password)
        mailserver.sendmail(sender, to, msg.as_string())
        return True
    finally:
        mailserver.quit()


def _direct_mx_enabled():
    value = str(os.environ.get("RUNNINGMATE_DIRECT_MX_ENABLED", "true")).strip().lower()
    return value not in ("0", "false", "no", "off")


def _mx_hosts(domain):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX")
        hosts = sorted((int(row.preference), str(row.exchange).rstrip(".")) for row in answers)
        return [host for _priority, host in hosts]
    except Exception:
        return [domain]


def _send_direct_mx(to, subject, html):
    if not _direct_mx_enabled():
        return False

    _name, recipient = parseaddr(str(to or ""))
    if not recipient or "@" not in recipient:
        return False

    sender = _sender_address() or _default_sender_address()
    domain = recipient.rsplit("@", 1)[1].lower()
    msg = _message(recipient, subject, html, sender)
    helo_host = _mail_domain()
    timeout = int(os.environ.get("RUNNINGMATE_DIRECT_MX_TIMEOUT", "15"))
    last_error = ""

    for host in _mx_hosts(domain)[:5]:
        mailserver = None
        try:
            mailserver = smtplib.SMTP(host, 25, timeout=timeout)
            mailserver.ehlo(helo_host)
            if mailserver.has_extn("starttls"):
                mailserver.starttls()
                mailserver.ehlo(helo_host)
            refused = mailserver.sendmail(sender, [recipient], msg.as_string())
            if refused:
                last_error = f"{host} refused recipient"
                continue
            return True
        except Exception as exc:
            last_error = f"{host}: {type(exc).__name__} {exc}"
        finally:
            if mailserver is not None:
                try:
                    mailserver.quit()
                except Exception:
                    pass

    if last_error:
        _log_mail(f"direct MX failed for {_mask_email(recipient)} - {last_error}")
    return False


def _send_reset_email(to, name, reset_url):
    subject = "[러닝메이트] 비밀번호 재설정 안내"
    html = _email_html(name, reset_url)

    try:
        if _send_sendgrid(to, subject, html):
            _log_mail(f"reset email sent to {_mask_email(to)} via SendGrid")
            return True
    except Exception as exc:
        _log_mail(f"SendGrid failed for {_mask_email(to)} - {type(exc).__name__} {exc}")

    try:
        if _send_smtp(to, subject, html):
            _log_mail(f"reset email sent to {_mask_email(to)} via SMTP")
            return True
    except Exception as exc:
        _log_mail(f"SMTP failed for {_mask_email(to)} - {type(exc).__name__} {exc}")

    try:
        if _send_direct_mx(to, subject, html):
            _log_mail(f"reset email sent to {_mask_email(to)} via direct MX")
            return True
        return False
    except Exception as exc:
        _log_mail(f"direct MX failed for {_mask_email(to)} - {type(exc).__name__} {exc}")
        return False


_load_env_file()

if request.method != "POST":
    wiz.response.status(405, success=False, message="지원하지 않는 요청입니다.")
else:
    payload = _payload()
    user = struct.user
    valid, email, _ = user.validate_email(payload.get("email", ""))
    _log_mail(f"reset request received for {_mask_email(email) if email else 'missing-email'}")

    if valid:
        issued = user.issue_password_reset(email)
        if issued:
            sent = _send_reset_email(
                issued["user"].get("email") or email,
                issued["user"].get("name"),
                _reset_url(issued["token"]),
            )
            if not sent:
                _log_mail(f"reset email was not sent to {_mask_email(email)}")
        else:
            _log_mail(f"reset requested for unknown email {_mask_email(email)}")

    _response()
