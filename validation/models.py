from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


@dataclass
class Measurement:
    test: str
    stimulus: float
    stimulus_unit: str
    value: float
    unit: str
    note: str = ""


@dataclass
class TestResult:
    name: str
    status: Status
    summary: str
    measurements: list[Measurement] = field(default_factory=list)
    limits: dict[str, Any] = field(default_factory=dict)
    duration_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

