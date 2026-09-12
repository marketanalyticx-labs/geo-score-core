"""geo-score-core: 7-factor GEO/AEO readiness scoring for web pages."""

from .models import FactorResult, ScoreResult
from .scorer import GEOScorer

__version__ = "0.1.3"
__all__ = ["GEOScorer", "ScoreResult", "FactorResult"]
