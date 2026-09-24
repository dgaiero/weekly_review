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
    updates: dict[tuple[str, str], list[WeeklyStatus]] = field(default_factory=dict)
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
    allocations: dict[tuple[str, str], float] = {}
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
        sources: dict[tuple[str, tuple[str, str]], Path] = {}
        for status_path in sorted((directory / "status").rglob("*.md")):
            try:
                update = parse_status(status_path, status_root=directory / "status")
                if update.author:
                    key = (update.week, update.author.identity)
                    if key in sources:
                        raise ValueError(
                            f"duplicate author submission; first submitted in {sources[key]}"
                        )
                    sources[key] = status_path
                repo.updates.setdefault((effort.id, update.week), []).append(update)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                repo.errors.append(f"{status_path}: {exc}")
        if effort.status == EffortStatus.ACTIVE:
            updates = repo.updates.get((effort.id, week), [])
            submitted = {update.author.identity for update in updates if update.author}
            if effort.reporting == "required" and not effort.team and not updates:
                repo.warnings.append(f"{effort.id}: missing weekly update for {week}")
            for person in sorted(effort.team, key=lambda person: person.identity):
                if effort.reporting == "required" and person.identity not in submitted:
                    label = f"{person.name} (NTID: {person.ntid})" if person.ntid else person.name
                    repo.warnings.append(f"{effort.id}: missing weekly update for {week}: {label}")
                allocations[person.identity] = (
                    allocations.get(person.identity, 0) + person.commitment
                )
    for person, allocation in sorted(allocations.items()):
        if allocation > 1 + 1e-9:
            label = f"NTID: {person[1]}" if person[0] == "ntid" else person[1]
            repo.warnings.append(f"{label}: allocated at {allocation:.0%} across active efforts")
    return repo
