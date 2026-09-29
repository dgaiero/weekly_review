from datetime import UTC, datetime

import pytest

from team_status.models import WeekMetadata, validate_week
from team_status.yaml_io import load_yaml


@pytest.mark.parametrize("value", ["2026-09-21", "2025-12-29", "2024-02-26"])
def test_monday_dates_are_valid(value):
    assert validate_week(value) == value


@pytest.mark.parametrize("value", ["2026-W39", "2026-09-22", "2025-02-30", "2026-9-21"])
def test_invalid_week_dates_are_rejected(value):
    with pytest.raises(ValueError, match="week"):
        validate_week(value)


@pytest.mark.parametrize("value", ["2026-09-21", "'2026-09-21'"])
def test_quoted_and_unquoted_yaml_dates_serialize_as_strings(value):
    metadata = WeekMetadata.model_validate(load_yaml(f"week: {value}"))
    assert metadata.model_dump(mode="json") == {"week": "2026-09-21"}


def test_datetime_is_not_a_week():
    with pytest.raises(ValueError):
        WeekMetadata(week=datetime(2026, 9, 21, tzinfo=UTC))


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (datetime(2026, 1, 1, tzinfo=UTC), "2025-12-29"),
        (datetime(2026, 9, 27, tzinfo=UTC), "2026-09-21"),
        (datetime(2026, 9, 28, tzinfo=UTC), "2026-09-28"),
    ],
)
def test_cli_defaults_to_current_utc_monday(tmp_path, monkeypatch, capsys, today, expected):
    import team_status.cli as cli

    class Clock:
        @classmethod
        def now(cls, tz):
            assert tz == UTC
            return today

    (tmp_path / "efforts").mkdir()
    monkeypatch.delenv("REPORT_WEEK", raising=False)
    monkeypatch.setattr(cli, "datetime", Clock)
    monkeypatch.setattr("sys.argv", ["team-status", "validate", "--root", str(tmp_path)])
    assert cli.main() == 0
    assert f"for {expected}" in capsys.readouterr().out
