"""Extraction helpers: pull the raw signals each factor needs out of a page."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Return all parsed JSON-LD blocks (schema.org structured data)."""
    blocks = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(data, list):
            blocks.extend(data)
        elif isinstance(data, dict) and "@graph" in data and isinstance(data["@graph"], list):
            blocks.extend(data["@graph"])
        else:
            blocks.append(data)
    return blocks


def schema_types(blocks: List[Dict[str, Any]]) -> List[str]:
    types = []
    for b in blocks:
        t = b.get("@type")
        if isinstance(t, list):
            types.extend(t)
        elif isinstance(t, str):
            types.append(t)
    return types


def get_headings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    headings = []
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            headings.append({"level": level, "text": tag.get_text(strip=True)})
    # preserve document order
    all_h = soup.find_all(re.compile(r"^h[1-6]$"))
    ordered = [{"level": int(t.name[1]), "text": t.get_text(strip=True)} for t in all_h]
    return ordered or headings


def get_paragraphs(soup: BeautifulSoup) -> List[str]:
    return [p.get_text(strip=True) for p in soup.find_all("p") if p.get_text(strip=True)]


def get_meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
    return tag.get("content") if tag else None


def has_canonical(soup: BeautifulSoup) -> bool:
    return soup.find("link", attrs={"rel": "canonical"}) is not None


def question_like_headings(headings: List[Dict[str, Any]]) -> int:
    q_words = ("what", "how", "why", "when", "where", "which", "who", "can", "does", "is")
    count = 0
    for h in headings:
        text = h["text"].strip().lower()
        if text.endswith("?") or text.startswith(q_words):
            count += 1
    return count
