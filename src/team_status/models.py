"""Canonical input and report contracts."""

import re
from datetime import date
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

Text = Annotated[str, Field(min_length=1)]


def validate_week(value: str) -> str:
    if not re.fullmatch(r"[0-9]{4}-W[0-9]{2}", value):
        raise ValueError("week must use YYYY-Www format")
    try:
        date.fromisocalendar(int(value[:4]), int(value[6:]), 1)
    except ValueError as exc:
        raise ValueError(f"invalid ISO week: {value}") from exc
    return value


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class EffortStatus(StrEnum):
    PROPOSED = "proposed"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Person(Model):
    name: Text
    gitlab: Text | None = None


class TeamMember(Person):
    commitment: Annotated[float, Field(ge=0, le=1, strict=True)]


class Customer(Model):
    organization: Text
    poc: Person | None = None


class Funding(Model):
    source: Text
    amount: Annotated[int, Field(ge=0, strict=True)]


class DateRange(Model):
    start: date | None = None
    end: date | None = None

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.start and self.end and self.end < self.start:
            raise ValueError("end date must be on or after start date")
        return self


class Effort(Model):
    schema_version: Literal[1]
    id: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
    name: Text
    status: EffortStatus
    lead: Person
    customer: Customer | None = None
    funding: list[Funding] = Field(default_factory=list)
    dates: DateRange
    team: list[TeamMember] = Field(default_factory=list)
    tags: list[Text] = Field(default_factory=list)

    @computed_field
    @property
    def funding_total(self) -> int:
        return sum(item.amount for item in self.funding)


class WeekMetadata(Model):
    week: str

    @field_validator("week")
    @classmethod
    def valid_week(cls, value: str) -> str:
        return validate_week(value)


class WeeklyStatus(WeekMetadata):
    sections: dict[str, str]


class ReportEffort(Model):
    effort: Effort
    update: WeeklyStatus | None


class WeeklyReport(WeekMetadata):
    schema_version: Literal[1] = 1
    efforts: list[ReportEffort]
    warnings: list[str]
