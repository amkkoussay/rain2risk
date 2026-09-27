"""Risk engine data models with explicit availability semantics."""
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class FactorResult:
    score: float
    weight: float
    contribution: float
    explanation: str
    available: bool = True
    status: str = "available"
    raw_value: Any = None
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 1) if self.available else None,
            "weight": self.weight,
            "contribution": round(self.contribution, 1) if self.available else None,
            "available": self.available,
            "status": self.status,
            "value": self.raw_value if self.available else None,
            "unit": self.unit,
            "explanation": self.explanation,
        }

@dataclass(frozen=True)
class RiskResult:
    score: float
    level: str
    factors: dict[str, FactorResult]
    top_contributors: list[str]
    explanation: list[str]
    rainfall_window: str
    unavailable_factors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score),
            "level": self.level,
            "factors": {name: factor.to_dict() for name, factor in self.factors.items()},
            "top_contributors": self.top_contributors,
            "explanation": self.explanation,
            "rainfall_window": self.rainfall_window,
            "unavailable_factors": self.unavailable_factors or [],
        }
