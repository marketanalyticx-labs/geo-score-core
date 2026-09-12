# geo-score-core

**Score any web page for AI-search readiness — the same 7-factor engine behind [marketanalyticx.com/tools/geo-lens](https://marketanalyticx.com/tools/geo-lens/), open-sourced.**

As more discovery moves from ten blue links to a single AI-generated answer (ChatGPT, Perplexity, Google AI Overviews), pages need to be structured for *extraction*, not just ranking. `geo-score-core` gives you a repeatable, open scoring model for that — no API key, no black box.

```bash
pip install geo-score-core
geo-score https://example.com
```

```
GEO Score for https://example.com
============================================================
Overall: 71.5/100  (71.5%)  Grade: B

Schema markup             13.0 / 20.0  (65.0%)
    - Found 2 JSON-LD block(s): Organization, Article
    - High-value types present: Article
Answer extractability     15.0 / 20.0  (75.0%)
    - 3 question-style heading(s) found
    - 8 concise (30-320 char) paragraph(s) in the first 10
...
```

## The 7 factors

| Factor | Weight | What it checks |
|---|---|---|
| Schema markup | 20 | Valid JSON-LD, high-value types (`FAQPage`, `HowTo`, `Article`...) |
| Answer extractability | 20 | Question-style headings, concise self-contained paragraphs |
| Heading architecture | 15 | Single H1, no skipped levels, adequate structure |
| Chunk quality | 15 | Paragraph length distribution (ideal: 200–600 chars) |
| Entity clarity | 12 | Organization/Person schema, `sameAs` links, stable `@id` anchors |
| Technical directives | 10 | Meta robots, canonical tags, AI-bot friendliness signals |
| Freshness signals | 8 | `datePublished` / `dateModified`, recency |

Full breakdown and rationale for the weighting: [marketanalyticx.com/tools/geo-lens](https://marketanalyticx.com/tools/geo-lens/).

## Usage as a library

```python
from geo_score_core import GEOScorer

scorer = GEOScorer()
result = scorer.score_url("https://example.com")

print(result.total_score, "/", result.max_score, result.grade)
for factor in result.factors:
    print(factor.name, factor.score, factor.findings)
```

You can also score raw HTML you already have (e.g. from a crawl):

```python
result = scorer.score_html(html_string, url="https://example.com")
```

## Try it without installing anything

Hosted demo (Hugging Face Space): **[huggingface.co/spaces/marketanalyticx/geo-score](https://huggingface.co/spaces/marketanalyticx/geo-score)**

## Why we built this

We built the scoring engine to audit our own clients' pages for citation-readiness in ChatGPT, Perplexity, and Google AI Overviews. We're open-sourcing the core scoring logic because a shared, transparent standard for "AI-search readiness" is more useful to the ecosystem than a black-box audit tool — and because we'd rather be judged on the quality of the methodology in the open.

If you use this and find gaps in the scoring model, [open an issue](https://github.com/marketanalyticx-labs/geo-score-core/issues) — we'd genuinely like to improve it.

## Installation from source

```bash
git clone https://github.com/marketanalyticx-labs/geo-score-core
cd geo-score-core
pip install -e .
```

## License

MIT — see [LICENSE](LICENSE).

---

Built by [Market Analyticx](https://marketanalyticx.com), a GEO/AEO marketing consultancy.
