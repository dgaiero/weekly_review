from unittest.mock import patch

import pytest

from team_status.delivery import send_report


@pytest.fixture
def report(tmp_path):
    week = tmp_path / "2026-09-21"
    week.mkdir()
    (week / "email.html").write_text("<p>Authored update</p>")
    (week / "email.md").write_text("Authored update\n")
    return tmp_path


@pytest.fixture
def settings():
    return {"SMTP_HOST": "smtp.example.com", "EMAIL_FROM": "reports@example.com", "EMAIL_TO": "a@example.com,b@example.com"}


def test_starttls_delivery(report, settings):
    settings.update(SMTP_USERNAME="user", SMTP_PASSWORD="test-secret")  # ruff: ignore[hardcoded-password-func-arg] - mock credential
    with patch("team_status.delivery.smtplib.SMTP") as factory:
        client = factory.return_value.__enter__.return_value
        client.send_message.return_value = {}
        send_report(report, settings)
    factory.assert_called_once_with("smtp.example.com", 587, timeout=30)
    assert [call[0] for call in client.method_calls] == ["starttls", "login", "send_message"]
    client.login.assert_called_once_with("user", "test-secret")
    message = client.send_message.call_args.args[0]
    assert message["Subject"] == "Weekly status — 2026-09-21"
    assert message.get_body(preferencelist=("html",)).get_content().strip() == "<p>Authored update</p>"
    assert message.get_body(preferencelist=("plain",)).get_content() == "Authored update\n"
    assert client.send_message.call_args.kwargs["to_addrs"] == ["a@example.com", "b@example.com"]


def test_implicit_tls_without_auth(report, settings):
    settings["SMTP_SECURITY"] = "ssl"
    with patch("team_status.delivery.smtplib.SMTP_SSL") as factory:
        client = factory.return_value.__enter__.return_value
        client.send_message.return_value = {}
        send_report(report, settings)
    assert factory.call_args.args == ("smtp.example.com", 465)
    client.starttls.assert_not_called()
    client.login.assert_not_called()


@pytest.mark.parametrize(
    "updates",
    [
        {"SMTP_HOST": ""},
        {"SMTP_PORT": "0"},
        {"SMTP_SECURITY": "none"},
        {"SMTP_USERNAME": "user"},
        {"EMAIL_TO": ""},
        {"EMAIL_FROM": "x@example.com\nBcc: y@example.com"},
    ],
)
def test_invalid_config_never_connects(report, settings, updates):
    settings.update(updates)
    with patch("team_status.delivery.smtplib.SMTP") as factory, pytest.raises(ValueError, match=r"SMTP|mailbox"):
        send_report(report, settings)
    factory.assert_not_called()


def test_missing_or_multiple_reports_never_connect(report, settings):
    (report / "2026-09-28").mkdir()
    (report / "2026-09-28/email.html").write_text("Other week")
    with patch("team_status.delivery.smtplib.SMTP") as factory, pytest.raises(ValueError, match="exactly one"):
        send_report(report, settings)
    factory.assert_not_called()


def test_partial_refusal_fails(report, settings):
    with patch("team_status.delivery.smtplib.SMTP") as factory:
        factory.return_value.__enter__.return_value.send_message.return_value = {"a@example.com": (550, b"rejected")}
        with pytest.raises(ValueError, match="recipients"):
            send_report(report, settings)


def test_missing_plain_text_never_connects(report, settings):
    (report / "2026-09-21/email.md").unlink()
    with patch("team_status.delivery.smtplib.SMTP") as factory, pytest.raises(FileNotFoundError):
        send_report(report, settings)
    factory.assert_not_called()


def test_main_does_not_log_server_details(capsys):
    import smtplib

    from team_status.delivery import main

    with patch("team_status.delivery.send_report", side_effect=smtplib.SMTPException("private-server-response")):
        assert main() == 1
    output = capsys.readouterr()
    assert "private-server-response" not in output.err
    assert "SMTPException" in output.err


def test_main_success():
    from team_status.delivery import main

    with patch("team_status.delivery.send_report") as send:
        assert main() == 0
    send.assert_called_once()
