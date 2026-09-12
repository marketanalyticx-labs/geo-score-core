from geo_score_core import GEOScorer

SAMPLE_HTML = """
<html>
<head>
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://example.com/page">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to Score GEO Readiness",
  "datePublished": "2026-06-01T00:00:00+00:00",
  "dateModified": "2026-08-01T00:00:00+00:00"
}
</script>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#org",
  "name": "Example Co",
  "sameAs": ["https://twitter.com/example", "https://linkedin.com/company/example"]
}
</script>
</head>
<body>
<h1>How to Score GEO Readiness</h1>
<p>GEO readiness measures how easily an AI search engine can extract and cite your content.</p>
<h2>What factors matter?</h2>
<p>Seven factors matter: schema, extractability, headings, chunking, entities, directives, and freshness.</p>
<h2>How is chunk quality measured?</h2>
<p>Chunk quality looks at whether paragraphs are self-contained and reasonably sized for extraction by a language model, generally between two hundred and six hundred characters long.</p>
</body>
</html>
"""


def test_score_html_returns_result():
    scorer = GEOScorer()
    result = scorer.score_html(SAMPLE_HTML, url="https://example.com/page")
    assert result.max_score == 100
    assert 0 <= result.total_score <= 100
    assert len(result.factors) == 7


def test_schema_factor_detects_json_ld():
    scorer = GEOScorer()
    result = scorer.score_html(SAMPLE_HTML)
    schema_factor = next(f for f in result.factors if f.name == "Schema markup")
    assert schema_factor.score > 0


def test_empty_html_scores_low():
    scorer = GEOScorer()
    result = scorer.score_html("<html><body></body></html>")
    assert result.total_score < 20


def test_grade_boundaries():
    scorer = GEOScorer()
    result = scorer.score_html(SAMPLE_HTML)
    assert result.grade in ("A", "B", "C", "D", "F")
