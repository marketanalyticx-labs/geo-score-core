"""Example: score a live URL and print a breakdown."""

from geo_score_core import GEOScorer

if __name__ == "__main__":
    scorer = GEOScorer()
    result = scorer.score_url("https://marketanalyticx.com/")

    print(f"{result.url}")
    print(f"Overall: {result.total_score}/{result.max_score} ({result.pct}%) — Grade {result.grade}\n")

    for factor in result.factors:
        print(f"{factor.name}: {factor.score}/{factor.max_score}")
        for finding in factor.findings:
            print(f"  - {finding}")
        print()
