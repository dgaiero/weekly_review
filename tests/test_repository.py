import json
import subprocess
import sys

import pytest

EFFORT = """schema_version: 1
id: alpha
name: Alpha
status: active
lead: {name: Jane, ntid: jane}
funding:
  - {source: IRAD, amount: 100}
  - {source: Customer, amount: 200}
dates: {start: 2026-01-01, end: 2026-12-31}
team:
  - {name: Jane, ntid: jane, commitment: 0.6}
"""
HEADINGS = [
    "Progress Overview",
    "Accomplishments",
    "Risks / Blockers / Mitigations",
    "Next Week",
    "Help / Decisions Needed",
]
STATUS = "---\nweek: 2026-W39\n---\n\n" + "\n\n".join(
    f"## {title}\n\nUpdate for {title}." for title in HEADINGS
)


@pytest.fixture
def repo(tmp_path):
    effort = tmp_path / "efforts/alpha"
    (effort / "status").mkdir(parents=True)
    (effort / "effort.yaml").write_text(EFFORT)
    (effort / "status/2026-W39.md").write_text(STATUS)
    return tmp_path


def cli(root, *args):
    return subprocess.run(
        [sys.executable, "-m", "team_status", *args, "--root", str(root)],
        capture_output=True,
        text=True,
    )


def test_build_normalized_report(repo):
    result = cli(repo, "build-week", "--week", "2026-W39")
    assert result.returncode == 0, result.stderr
    report = json.loads((repo / "build/2026-W39/report.json").read_text())
    assert report["week"] == "2026-W39"
    assert report["efforts"][0]["effort"]["funding_total"] == 300
    assert report["efforts"][0]["effort"]["links"] == []
    assert report["efforts"][0]["updates"][0]["sections"]["Accomplishments"] == (
        "Update for Accomplishments."
    )
    assert len(report["warnings"]) == 1  # Legacy content has no attributed author.
    assert "Jane" in report["warnings"][0]
    folder = repo / "build/2026-W39"
    assert (folder / "slides.md").read_text().startswith("---\nmarp: true")
    assert "Update for Accomplishments." in (folder / "email.md").read_text()
    assert "<html" in (folder / "email.html").read_text()


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("commitment: 0.6", "commitment: 40", "commitment"),
        ("amount: 100", "amount: -1", "amount"),
        ("2026-12-31", "2025-12-31", "end"),
        ("status: active", "status: unknown", "status"),
        ("id: alpha", "id: beta", "directory"),
        ("name: Alpha", "name: ''", "name"),
        ("name: Alpha", "name: Alpha\nname: Beta", "duplicate"),
    ],
)
def test_invalid_effort_rejected(repo, old, new, message):
    (repo / "efforts/alpha/effort.yaml").write_text(EFFORT.replace(old, new))
    result = cli(repo, "validate", "--week", "2026-W39")
    assert result.returncode == 1
    assert message in result.stderr


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (STATUS.replace("2026-W39", "2026-W38"), "filename"),
        (STATUS.replace("## Accomplishments", "## Unknown"), "section"),
        (STATUS + "\n## Accomplishments\nRepeated", "duplicate"),
        (STATUS.replace("2026-W39", "2025-W53"), "week"),
        ("No front matter", "front matter"),
    ],
)
def test_invalid_status_rejected(repo, content, message):
    (repo / "efforts/alpha/status/2026-W39.md").write_text(content)
    result = cli(repo, "validate", "--week", "2026-W39")
    assert result.returncode == 1
    assert message in result.stderr


def test_missing_update_warns_without_reusing_previous_week(repo):
    result = cli(repo, "build-week", "--week", "2026-W40")
    assert result.returncode == 0, result.stderr
    report = json.loads((repo / "build/2026-W40/report.json").read_text())
    assert report["efforts"][0]["updates"] == []
    assert "missing" in report["warnings"][0]


def test_overallocation_warns(repo):
    beta = repo / "efforts/beta"
    beta.mkdir()
    (beta / "effort.yaml").write_text(EFFORT.replace("id: alpha", "id: beta"))
    result = cli(repo, "validate", "--week", "2026-W39")
    assert result.returncode == 0, result.stderr
    assert "120%" in result.stdout


def test_invalid_repository_does_not_build(repo):
    (repo / "efforts/alpha/effort.yaml").write_text("[]")
    result = cli(repo, "build-week", "--week", "2026-W39")
    assert result.returncode == 1
    assert not (repo / "build").exists()


def test_effort_links_survive_yaml_to_report_json(repo):
    links = [
        {
            "name": "GitLab repository",
            "url": "https://gitlab/team/alpha",
            "description": "Source code and issues",
        },
        {"name": "SharePoint", "url": "https://example.sharepoint.com/sites/alpha"},
        {"name": "Internal docs", "url": "http://intranet/alpha", "description": None},
    ]
    (repo / "efforts/alpha/effort.yaml").write_text(EFFORT + "links: " + json.dumps(links))
    result = cli(repo, "build-week", "--week", "2026-W39")
    assert result.returncode == 0, result.stderr
    report = json.loads((repo / "build/2026-W39/report.json").read_text())
    assert report["efforts"][0]["effort"]["links"] == [
        {"description": None, **link} for link in links
    ]


@pytest.mark.parametrize(
    "link",
    [
        {"name": "Repo"},
        {"url": "https://gitlab/team/alpha"},
        {"name": "  ", "url": "https://gitlab/team/alpha"},
        {"name": "Repo", "url": "not a URL"},
        {"name": "Repo", "url": "ftp://gitlab/team/alpha"},
        {"name": "Repo", "url": "https://"},
        {"name": "Repo", "url": "https://gitlab/team/alpha", "description": 123},
    ],
)
def test_invalid_effort_link_prevents_report_generation(repo, link):
    (repo / "efforts/alpha/effort.yaml").write_text(EFFORT + "links: " + json.dumps([link]))
    result = cli(repo, "build-week", "--week", "2026-W39")
    assert result.returncode == 1
    assert "links" in result.stderr
    assert "effort.yaml" in result.stderr
    assert not (repo / "build").exists()


def test_missing_root_is_error(tmp_path):
    result = cli(tmp_path / "absent", "validate")
    assert result.returncode == 1
    assert "efforts" in result.stderr


def test_fenced_headings_are_content(repo):
    path = repo / "efforts/alpha/status/2026-W39.md"
    path.write_text(STATUS + "\n\n```markdown\n## Accomplishments\n```\n")
    result = cli(repo, "validate", "--week", "2026-W39")
    assert result.returncode == 0, result.stderr


def test_schema_export(tmp_path):
    result = cli(tmp_path, "schema")
    assert result.returncode == 0, result.stderr
    schema = json.loads((tmp_path / "schema/effort.schema.json").read_text())
    assert schema["additionalProperties"] is False


def test_empty_sections_allowed(repo):
    path = repo / "efforts/alpha/status/2026-W39.md"
    path.write_text(
        "---\nweek: 2026-W39\n---\n" + "\n\n".join(f"## {heading}" for heading in HEADINGS)
    )
    assert cli(repo, "validate", "--week", "2026-W39").returncode == 0


def test_exported_schemas_cover_new_and_legacy_metadata_and_match_repository(tmp_path):
    from pathlib import Path

    result = cli(tmp_path, "schema")
    assert result.returncode == 0, result.stderr
    generated = tmp_path / "schema"
    new = json.loads((generated / "weekly-status.schema.json").read_text())
    legacy = json.loads((generated / "legacy-weekly-status.schema.json").read_text())
    assert "author" in new["required"]
    assert "author" not in legacy["required"]
    assert "ntid" in new["$defs"]["Person"]["properties"]
    for path in generated.glob("*.json"):
        assert json.loads(path.read_text()) == json.loads((Path("schema") / path.name).read_text())


def test_cli_builds_two_attributed_files(repo):
    directory = repo / "efforts/alpha/status/2026-W39"
    directory.mkdir()
    for name in ["Jane", "Alex"]:
        content = STATUS.replace(
            "week: 2026-W39", f"week: 2026-W39\nauthor: {{name: {name}, ntid: {name.lower()}}}"
        )
        (directory / f"{name.lower()}.md").write_text(content)
    result = cli(repo, "build-week", "--week", "2026-W39")
    assert result.returncode == 0, result.stderr
    report = json.loads((repo / "build/2026-W39/report.json").read_text())
    assert report["schema_version"] == 2
    assert len(report["efforts"][0]["updates"]) == 3
    assert report["warnings"] == []
