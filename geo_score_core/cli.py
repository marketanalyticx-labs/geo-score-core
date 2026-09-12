"""Command-line interface: `geo-score <url>`"""

from __future__ import annotations

import argparse
import json
import sys

from .scorer import GEOScorer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="geo-score",
        description="Score a web page for AI-search / GEO readiness (0-100, 7 factors).",
    )
    parser.add_argument("url", help="URL of the page to score")
    parser.add_argument(
        "--json", action="store_true", dest="as_json",
        help="Print raw JSON instead of a formatted report",
    )
    args = parser.parse_args()

    scorer = GEOScorer()
    try:
        result = scorer.score_url(args.url)
    except Exception as exc:  # noqa: BLE001 - CLI top-level error boundary
        print(f"Error scoring {args.url}: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print(f"\nGEO Score for {result.url}")
    print(f"{'=' * 60}")
    print(f"Overall: {result.total_score}/{result.max_score}  ({result.pct}%)  Grade: {result.grade}\n")
    for f in result.factors:
        print(f"{f.name:<24} {f.score:>5.1f} / {f.max_score:<5.1f} ({f.pct}%)")
        for finding in f.findings:
            print(f"    - {finding}")
    print()


if __name__ == "__main__":
    main()
