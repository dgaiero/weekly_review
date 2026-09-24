"""Read the portfolio once, collecting actionable input errors."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .models import Effort, EffortStatus, WeeklyStatus, validate_week
from .status import parse_status
from .yaml_io import load_yaml


@dataclass
class Repository:
    efforts: list[Effort] = field(default_factory=list)
    updates: dict[tuple[str, str], WeeklyStatus] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_repository(root: Path, week: str) -> Repository:
    validate_week(week)
    repo = Repository()
    folder = root / "efforts"
    if not folder.is_dir():
        repo.errors.append(f"{folder}: efforts directory does not exist")
        return repo
    seen = set()
    allocations: dict[str, float] = {}
    for directory in sorted(folder.iterdir()):
        if directory.name.startswith(".") or not directory.is_dir():
            continue
        path = directory / "effort.yaml"
        try:
            effort = Effort.model_validate(load_yaml(path.read_text(encoding="utf-8")))
            if effort.id in seen:
                raise ValueError(f"duplicate effort ID: {effort.id}")
            seen.add(effort.id)
            if effort.id != directory.name:
                raise ValueError("effort ID must match directory name")
            repo.efforts.append(effort)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            repo.errors.append(f"{path}: {exc}")
            continue
        for status_path in sorted((directory / "status").glob("*.md")):
            try:
                update = parse_status(status_path)
                repo.updates[(effort.id, update.week)] = update
            except (OSError, ValueError, yaml.YAMLError) as exc:
                repo.errors.append(f"{status_path}: {exc}")
        if effort.status == EffortStatus.ACTIVE:
            if (effort.id, week) not in repo.updates:
                repo.warnings.append(f"{effort.id}: missing weekly update for {week}")
            for person in effort.team:
                key = f"@{person.gitlab.casefold()}" if person.gitlab else person.name.casefold()
                allocations[key] = allocations.get(key, 0) + person.commitment
    for person, allocation in sorted(allocations.items()):
        if allocation > 1 + 1e-9:
            repo.warnings.append(f"{person}: allocated at {allocation:.0%} across active efforts")
    return repo
