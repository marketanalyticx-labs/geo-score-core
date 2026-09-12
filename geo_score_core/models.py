"""Result types returned by GEOScorer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class FactorResult:
    """Score for a single one of the 7 GEO-readiness factors."""

    name: str
    score: float          # points earned
    max_score: float       # points available for this factor
    findings: List[str] = field(default_factory=list)  # human-readable notes

    @property
    def pct(self) -> float:
        return round((self.score / self.max_score) * 100, 1) if self.max_score else 0.0


@dataclass
class ScoreResult:
    """Full GEO-readiness score for one page."""

    url: str
    total_score: float
    max_score: float
    factors: List[FactorResult]

    @property
    def pct(self) -> float:
        return round((self.total_score / self.max_score) * 100, 1) if self.max_score else 0.0

    @property
    def grade(self) -> str:
        p = self.pct
        if p >= 90:
            return "A"
        if p >= 75:
            return "B"
        if p >= 60:
            return "C"
        if p >= 40:
            return "D"
        return "F"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "total_score": self.total_score,
            "max_score": self.max_score,
            "pct": self.pct,
            "grade": self.grade,
            "factors": [
                {
                    "name": f.name,
                    "score": f.score,
                    "max_score": f.max_score,
                    "pct": f.pct,
                    "findings": f.findings,
                }
                for f in self.factors
            ],
        }
