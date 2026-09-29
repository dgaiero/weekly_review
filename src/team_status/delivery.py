"""Send generated weekly report artifacts using SMTP configuration from CI."""

import os
import smtplib
import ssl
import sys
from collections.abc import Mapping
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from pathlib import Path

from team_status.models import validate_week


def _addresses(value: str) -> list[str]:
    addresses = [address.strip() for address in value.split(",")]
    if any(
        not address or address.count("@") != 1 or any(char.isspace() for char in address) or not all(address.split("@"))
        for address in addresses
    ):
        raise ValueError("Email addresses must be comma-separated bare mailbox addresses")
    return addresses


def send_report(root: Path, settings: Mapping[str, str]) -> None:
    """Send exactly one generated weekly report via certificate-verified TLS.

    Args:
        root: Directory containing one weekly report directory.
        settings: SMTP and email environment variables.

    Raises:
        ValueError: Configuration, report selection, or recipient acceptance is invalid.
    """
    host = settings.get("SMTP_HOST", "").strip()
    security = settings.get("SMTP_SECURITY", "starttls")
    port = int(settings.get("SMTP_PORT", "465" if security == "ssl" else "587"))
    username = settings.get("SMTP_USERNAME", "")
    password = settings.get("SMTP_PASSWORD", "")
    if not host or security not in {"starttls", "ssl"} or not 1 <= port <= 65535:
        raise ValueError("Invalid SMTP_HOST, SMTP_SECURITY, or SMTP_PORT")
    if bool(username) != bool(password):
        raise ValueError("Set both SMTP_USERNAME and SMTP_PASSWORD, or neither")
    sender = _addresses(settings.get("EMAIL_FROM", ""))
    recipients = _addresses(settings.get("EMAIL_TO", ""))
    if len(sender) != 1:
        raise ValueError("EMAIL_FROM must contain one mailbox")
    reports = list(root.glob("*/email.html"))
    if len(reports) != 1:
        raise ValueError("Expected exactly one generated weekly email")
    report = reports[0]
    week = validate_week(report.parent.name)
    html = report.read_text(encoding="utf-8")
    plain = report.with_suffix(".md").read_text(encoding="utf-8")
    if not html.strip() or not plain.strip():
        raise ValueError("Email artifacts must not be empty")
    message = EmailMessage()
    message["From"] = sender[0]
    message["To"] = ", ".join(recipients)
    message["Subject"] = f"Weekly status — {week}"
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid()
    message.set_content(plain)
    message.add_alternative(html, subtype="html")
    context = ssl.create_default_context()
    connection = (
        smtplib.SMTP_SSL(host, port, timeout=30, context=context) if security == "ssl" else smtplib.SMTP(host, port, timeout=30)
    )
    with connection as client:
        if security == "starttls":
            client.starttls(context=context)
        if username:
            client.login(username, password)
        refused = client.send_message(message, from_addr=sender[0], to_addrs=recipients)
        if refused:
            raise ValueError("SMTP rejected one or more recipients; some may already have received the email")


def main() -> int:
    """Send CI artifacts and return a process status without logging credentials.

    Returns:
        Zero on delivery, one on configuration or transport failure.
    """
    try:
        send_report(Path("build"), os.environ)
    except (ValueError, OSError, smtplib.SMTPException) as error:
        # SMTP responses can include private addresses or server details.
        print(f"Email delivery failed ({type(error).__name__}); check SMTP settings and artifacts.", file=sys.stderr)
        return 1
    print("Weekly email accepted by SMTP server.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
