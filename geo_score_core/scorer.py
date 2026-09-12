"""The GEOScorer: 7-factor GEO/AEO readiness scoring for a single page.

Factor weights mirror the live marketanalyticx.com/tools/geo-lens tool:
  Schema markup            20
  Answer extractability    20
  Heading architecture     15
  Chunk quality            15
  Entity clarity           12
  Technical directives     10
  Freshness signals         8
  ---------------------------
  Total                   100
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Optional

import requests

from .extractors import (
    extract_json_ld,
    get_headings,
    get_meta,
    get_paragraphs,
    has_canonical,
    parse_html,
    question_like_headings,
    schema_types,
)
from .models import FactorResult, ScoreResult

HIGH_VALUE_SCHEMA = {
    "FAQPage", "HowTo", "Article", "NewsArticle", "BlogPosting",
    "Organization", "Product", "Review", "QAPage",
}

DEFAULT_HEADERS = {
    "User-Agent": "geo-score-core/0.1 (+https://github.com/marketanalyticx-labs/geo-score-core)"
}


class GEOScorer:
    """Score a URL or raw HTML string for AI-search / GEO readiness."""

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    # -- public API ---------------------------------------------------

    def score_url(self, url: str) -> ScoreResult:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout)
        resp.raise_for_status()
        return self.score_html(resp.text, url=url)

    def score_html(self, html: str, url: str = "") -> ScoreResult:
        soup = parse_html(html)
        factors = [
            self._score_schema(soup),
            self._score_answer_extractability(soup),
            self._score_heading_architecture(soup),
            self._score_chunk_quality(soup),
            self._score_entity_clarity(soup),
            self._score_technical_directives(soup),
            self._score_freshness(soup),
        ]
        total = sum(f.score for f in factors)
        max_total = sum(f.max_score for f in factors)
        return ScoreResult(url=url, total_score=round(total, 1), max_score=max_total, factors=factors)

    # -- factor 1: schema markup (20) ----------------------------------

    def _score_schema(self, soup) -> FactorResult:
        max_score = 20.0
        blocks = extract_json_ld(soup)
        types = set(schema_types(blocks))
        findings = []

        if not blocks:
            findings.append("No JSON-LD structured data found")
            return FactorResult("Schema markup", 0.0, max_score, findings)

        score = 6.0  # baseline credit for having any valid JSON-LD
        findings.append(f"Found {len(blocks)} JSON-LD block(s): {', '.join(sorted(types)) or 'untyped'}")

        high_value_hits = types & HIGH_VALUE_SCHEMA
        score += min(len(high_value_hits) * 3.5, 10.5)
        if high_value_hits:
            findings.append(f"High-value types present: {', '.join(sorted(high_value_hits))}")

        if "Organization" in types or "Person" in types:
            score += 3.5
            findings.append("Entity (Organization/Person) schema present")

        return FactorResult("Schema markup", round(min(score, max_score), 1), max_score, findings)

    # -- factor 2: answer extractability (20) --------------------------

    def _score_answer_extractability(self, soup) -> FactorResult:
        max_score = 20.0
        headings = get_headings(soup)
        paragraphs = get_paragraphs(soup)
        findings = []

        q_headings = question_like_headings(headings)
        score = min(q_headings * 3.0, 12.0)
        findings.append(f"{q_headings} question-style heading(s) found")

        # short, self-contained early paragraphs read well as direct answers
        short_direct = sum(1 for p in paragraphs[:10] if 30 <= len(p) <= 320)
        score += min(short_direct * 1.0, 8.0)
        findings.append(f"{short_direct} concise (30-320 char) paragraph(s) in the first 10")

        return FactorResult("Answer extractability", round(min(score, max_score), 1), max_score, findings)

    # -- factor 3: heading architecture (15) ---------------------------

    def _score_heading_architecture(self, soup) -> FactorResult:
        max_score = 15.0
        headings = get_headings(soup)
        findings = []

        if not headings:
            findings.append("No headings found")
            return FactorResult("Heading architecture", 0.0, max_score, findings)

        h1s = [h for h in headings if h["level"] == 1]
        score = 0.0

        if len(h1s) == 1:
            score += 5.0
            findings.append("Exactly one H1 (good)")
        elif len(h1s) == 0:
            findings.append("No H1 found")
        else:
            findings.append(f"{len(h1s)} H1 tags found (should be exactly 1)")

        # check for skipped levels (e.g. H1 -> H3 with no H2)
        levels = [h["level"] for h in headings]
        skips = sum(1 for a, b in zip(levels, levels[1:]) if b - a > 1)
        if skips == 0:
            score += 6.0
            findings.append("No skipped heading levels")
        else:
            findings.append(f"{skips} skipped heading level transition(s)")
            score += max(6.0 - skips * 2.0, 0.0)

        if len(headings) >= 3:
            score += 4.0
            findings.append(f"{len(headings)} total headings — reasonable document structure")
        else:
            findings.append("Fewer than 3 headings — thin structure")

        return FactorResult("Heading architecture", round(min(score, max_score), 1), max_score, findings)

    # -- factor 4: chunk quality (15) -----------------------------------

    def _score_chunk_quality(self, soup) -> FactorResult:
        max_score = 15.0
        paragraphs = get_paragraphs(soup)
        findings = []

        if not paragraphs:
            findings.append("No paragraph text found")
            return FactorResult("Chunk quality", 0.0, max_score, findings)

        lengths = [len(p) for p in paragraphs]
        avg_len = sum(lengths) / len(lengths)
        ideal = sum(1 for l in lengths if 200 <= l <= 600)
        ratio = ideal / len(lengths)

        score = min(ratio * max_score, max_score)
        findings.append(f"{len(paragraphs)} paragraphs, avg {avg_len:.0f} chars, {ideal} in the ideal 200-600 range")

        return FactorResult("Chunk quality", round(score, 1), max_score, findings)

    # -- factor 5: entity clarity (12) -----------------------------------

    def _score_entity_clarity(self, soup) -> FactorResult:
        max_score = 12.0
        blocks = extract_json_ld(soup)
        findings = []
        score = 0.0

        entity_blocks = [b for b in blocks if b.get("@type") in ("Organization", "Person")]
        if entity_blocks:
            score += 5.0
            findings.append(f"{len(entity_blocks)} Organization/Person entity block(s)")
            for b in entity_blocks:
                same_as = b.get("sameAs")
                if same_as:
                    n = len(same_as) if isinstance(same_as, list) else 1
                    score += min(n * 1.0, 4.0)
                    findings.append(f"sameAs links present ({n})")
                if b.get("@id"):
                    score += 3.0
                    findings.append("Stable @id anchor present")
        else:
            findings.append("No Organization/Person entity schema found")

        return FactorResult("Entity clarity", round(min(score, max_score), 1), max_score, findings)

    # -- factor 6: technical directives (10) ------------------------------

    def _score_technical_directives(self, soup) -> FactorResult:
        max_score = 10.0
        findings = []
        score = 0.0

        robots_meta = get_meta(soup, "robots")
        if robots_meta and "noindex" not in robots_meta.lower():
            score += 4.0
            findings.append("Meta robots present and not noindex")
        elif robots_meta:
            findings.append("Meta robots is noindex — page won't be indexed")
        else:
            score += 2.0
            findings.append("No meta robots tag (defaults to indexable)")

        if has_canonical(soup):
            score += 3.0
            findings.append("Canonical link present")
        else:
            findings.append("No canonical link found")

        # crude check for llms.txt-style guidance link, or AI-bot friendliness markers
        ai_meta = get_meta(soup, "ai-content-declaration") or get_meta(soup, "generator")
        if ai_meta:
            score += 3.0
            findings.append("Additional generator/AI-related meta present")

        return FactorResult("Technical directives", round(min(score, max_score), 1), max_score, findings)

    # -- factor 7: freshness signals (8) ------------------------------------

    def _score_freshness(self, soup) -> FactorResult:
        max_score = 8.0
        blocks = extract_json_ld(soup)
        findings = []
        score = 0.0

        dates = []
        for b in blocks:
            for key in ("datePublished", "dateModified"):
                if b.get(key):
                    dates.append(b[key])

        if dates:
            score += 5.0
            findings.append(f"Found {len(dates)} date field(s) in schema: {', '.join(dates[:2])}")
            recent = any(self._is_recent(d) for d in dates)
            if recent:
                score += 3.0
                findings.append("At least one date is within the last 12 months")
        else:
            findings.append("No datePublished/dateModified schema fields found")

        return FactorResult("Freshness signals", round(min(score, max_score), 1), max_score, findings)

    @staticmethod
    def _is_recent(date_str: str, days: int = 365) -> bool:
        try:
            cleaned = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(cleaned)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).days <= days
        except (ValueError, TypeError):
            return False
