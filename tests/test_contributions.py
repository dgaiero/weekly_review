import pytest
import yaml

from team_status.reports.summary import build_report
from team_status.repository import load_repository
from team_status.status import SECTIONS

WEEK = "2026-W39"
JANE = {"name": "Jane", "ntid": "jane"}
ALEX = {"name": "Alex", "ntid": "alex"}


def portfolio(root, team=None, status="active", effort_id="alpha", reporting=None):
    directory = root / "efforts" / effort_id
    directory.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "id": effort_id,
        "name": effort_id,
        "status": status,
        "lead": {"name": "Lead"},
        "dates": {},
        "team": [
            dict(person, commitment=0.6) for person in ([JANE, ALEX] if team is None else team)
        ],
    }
    if reporting is not None:
        metadata["reporting"] = reporting
    (directory / "effort.yaml").write_text(yaml.safe_dump(metadata))
    return directory


def submission(directory, filename, author=None, week=WEEK, text="Authored **detail**."):
    path = directory / "status" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"week": week}
    if author is not None:
        metadata["author"] = author
    body = "\n\n".join(f"## {section}\n\n{text}" for section in SECTIONS)
    path.write_text("---\n" + yaml.safe_dump(metadata) + "---\n\n" + body)
    return path


def test_collects_both_authors_in_identity_order_and_preserves_content(tmp_path):
    effort = portfolio(tmp_path)
    submission(effort, f"{WEEK}/a.md", JANE, text="Jane's **exact** contribution.")
    submission(effort, f"{WEEK}/z.md", ALEX, text="Alex's own contribution.")
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert repo.warnings == []
    report = build_report(repo, WEEK).model_dump()
    assert report["schema_version"] == 2
    updates = report["efforts"][0]["updates"]
    assert [u["author"]["ntid"] for u in updates] == ["alex", "jane"]
    assert updates[1]["sections"]["Accomplishments"] == "Jane's **exact** contribution."


@pytest.mark.parametrize(
    "author,missing",
    [
        ({"name": "Renamed", "ntid": " JANE "}, ["Alex"]),
        ({"name": "Jane"}, ["Jane", "Alex"]),
        ({"name": "Lead"}, ["Jane", "Alex"]),
        (None, ["Jane", "Alex"]),
    ],
)
def test_missing_members_warn_without_inferred_identity(tmp_path, author, missing):
    effort = portfolio(tmp_path)
    submission(effort, f"{WEEK}.md", author)
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == len(missing)
    for name in missing:
        assert any(name in warning and WEEK in warning for warning in repo.warnings)


def test_names_match_without_ntid_and_identifier_namespaces_do_not_collide(tmp_path):
    effort = portfolio(tmp_path, team=[{"name": " Jane "}, {"name": "Other", "ntid": "jane"}])
    submission(effort, f"{WEEK}/jane.md", {"name": "JANE"})
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == 1 and "Other" in repo.warnings[0]


@pytest.mark.parametrize(
    "status,team,want",
    [
        ("active", [JANE, ALEX], 2),
        ("on_hold", [JANE], 0),
        ("completed", [JANE], 0),
        ("active", [], 1),
    ],
)
def test_missing_requested_week_never_reuses_history(tmp_path, status, team, want):
    effort = portfolio(tmp_path, team=team, status=status)
    submission(effort, "2026-W38/jane.md", JANE, week="2026-W38")
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == want
    assert build_report(repo, WEEK).efforts[0].updates == []


def test_mixed_legacy_and_new_content_is_retained(tmp_path):
    effort = portfolio(tmp_path, team=[JANE])
    submission(effort, f"{WEEK}.md", text="Legacy words.")
    submission(effort, f"{WEEK}/jane.md", JANE, text="New words.")
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == repo.warnings == []
    updates = build_report(repo, WEEK).efforts[0].updates
    assert updates[0].author is None
    assert updates[0].sections["Accomplishments"] == "Legacy words."
    assert updates[1].sections["Accomplishments"] == "New words."


@pytest.mark.parametrize("first", [f"{WEEK}.md", f"{WEEK}/first.md"])
def test_duplicate_authors_report_both_paths_even_in_history(tmp_path, first):
    effort = portfolio(tmp_path)
    a = submission(effort, first, JANE)
    b = submission(effort, f"{WEEK}/second.md", {"name": "Changed", "ntid": "JANE"})
    repo = load_repository(tmp_path, "2026-W40")
    assert any(
        "duplicate" in error and str(a) in error and str(b) in error for error in repo.errors
    )
    with pytest.raises(ValueError):
        build_report(repo, "2026-W40")


@pytest.mark.parametrize(
    "team",
    [
        [JANE, {"name": "Different", "ntid": "JANE"}],
        [{"name": " Jane "}, {"name": "JANE"}],
    ],
)
def test_duplicate_team_identity_is_error(tmp_path, team):
    portfolio(tmp_path, team=team)
    errors = load_repository(tmp_path, WEEK).errors
    assert any("duplicate" in error and "effort.yaml" in error for error in errors)


@pytest.mark.parametrize(
    "filename,author,week,message",
    [
        (f"{WEEK}/jane.md", None, WEEK, "author"),
        (f"{WEEK}/jane.md", {}, WEEK, "name"),
        (f"{WEEK}/jane.md", {"name": " "}, WEEK, "name"),
        (f"{WEEK}/jane.md", {"name": "Jane", "ntid": " "}, WEEK, "ntid"),
        (f"{WEEK}/jane.md", {"name": "Jane", "gitlab": "jane"}, WEEK, "gitlab"),
        ("2026-W38/jane.md", JANE, WEEK, "week"),
        (f"{WEEK}/Jane.md", JANE, WEEK, "filename"),
        (f"{WEEK}/nested/jane.md", JANE, WEEK, "path"),
        (f"nested/status/{WEEK}/jane.md", JANE, WEEK, "path"),
        (f"status/{WEEK}.md", JANE, WEEK, "filename"),
        ("bad/jane.md", JANE, WEEK, "week"),
        ("2025-W53/jane.md", JANE, "2025-W53", "week"),
    ],
)
def test_invalid_submissions_are_not_silently_skipped(tmp_path, filename, author, week, message):
    effort = portfolio(tmp_path)
    path = submission(effort, filename, author, week)
    errors = load_repository(tmp_path, "2026-W40").errors
    assert any(str(path) in error and message in error for error in errors)


def test_staffing_uses_ntid_once_per_member_not_per_submission(tmp_path):
    for effort_id in ["alpha", "beta"]:
        effort = portfolio(tmp_path, team=[JANE], effort_id=effort_id)
        submission(effort, f"{WEEK}/jane.md", JANE)
        submission(effort, f"{WEEK}/guest.md", {"name": "Guest"})
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == 1
    assert "120%" in repo.warnings[0] and "jane" in repo.warnings[0]


@pytest.mark.parametrize("team", [[], [JANE]])
@pytest.mark.parametrize("reporting,want", [(None, 1), ("required", 1), ("optional", 0)])
def test_reporting_policy_controls_missing_update_warnings(tmp_path, team, reporting, want):
    effort = portfolio(tmp_path, team=team, reporting=reporting)
    submission(effort, "2026-W38/jane.md", JANE, week="2026-W38")
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == want
    assert build_report(repo, WEEK).efforts[0].updates == []


def test_optional_reporting_still_counts_staffing(tmp_path):
    portfolio(tmp_path, team=[JANE], reporting="optional")
    other = portfolio(tmp_path, team=[JANE], effort_id="beta")
    submission(other, f"{WEEK}/jane.md", JANE)
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == []
    assert len(repo.warnings) == 1
    assert "120%" in repo.warnings[0]


def test_optional_reporting_preserves_voluntary_content(tmp_path):
    effort = portfolio(tmp_path, team=[], reporting="optional")
    submission(effort, f"{WEEK}/jane.md", JANE, text="**Small task:** Finished cleanup.")
    repo = load_repository(tmp_path, WEEK)
    assert repo.errors == repo.warnings == []
    report = build_report(repo, WEEK).model_dump()
    assert report["efforts"][0]["effort"]["reporting"] == "optional"
    update = report["efforts"][0]["updates"][0]
    assert update["author"] == JANE
    assert update["sections"]["Accomplishments"] == "**Small task:** Finished cleanup."


@pytest.mark.parametrize("invalid", ["missing_author", "duplicate_author"])
def test_optional_reporting_still_validates_historical_updates(tmp_path, invalid):
    effort = portfolio(tmp_path, reporting="optional")
    author = None if invalid == "missing_author" else JANE
    path = submission(effort, "2026-W38/jane.md", author, week="2026-W38")
    if invalid == "duplicate_author":
        submission(effort, "2026-W38/duplicate.md", JANE, week="2026-W38")
    repo = load_repository(tmp_path, WEEK)
    assert any(str(path) in error and "author" in error for error in repo.errors)
    with pytest.raises(ValueError):
        build_report(repo, WEEK)


def test_invalid_reporting_policy_is_an_error(tmp_path):
    portfolio(tmp_path, reporting="sometimes")
    repo = load_repository(tmp_path, WEEK)
    assert any("reporting" in error and "effort.yaml" in error for error in repo.errors)
    with pytest.raises(ValueError):
        build_report(repo, WEEK)
