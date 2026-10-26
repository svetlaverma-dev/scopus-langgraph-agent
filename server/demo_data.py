"""Synthetic search results for demo mode: no Scopus API calls, no Elsevier data."""
import re
from datetime import date
from typing import Any

TOPIC_FIELDS = r"(?:TITLE-ABS-KEY|TITLE|ABS|KEY)\s*\(([^)]*)\)"
DEMO_PAPERS = 5


def query_topic(query: str) -> str:
    match = re.search(TOPIC_FIELDS, query, re.IGNORECASE)
    if not match:
        return "your query"
    words = re.sub(r'["{}]|\b(AND|OR|NOT)\b', " ", match.group(1))
    return " ".join(words.split())


def first_year(query: str) -> int:
    match = re.search(r"PUBYEAR\s*>\s*(\d{4})", query, re.IGNORECASE)
    return int(match.group(1)) + 1 if match else 2018


def demo_search(query: str, count: int = 10, sort: str = "-citedby-count") -> dict[str, Any]:
    topic = query_topic(query)
    start = first_year(query)
    this_year = date.today().year
    papers = []
    for i in range(1, min(count, DEMO_PAPERS) + 1):
        papers.append({
            "title": f"[Demo] Synthetic study {i} on {topic}",
            "first_author": f"Example {chr(64 + i)}.",
            "journal": "Journal of Synthetic Examples",
            "date": f"{min(start + i - 1, this_year)}-01-01",
            "cited_by": 1000 // i,
            "doi": f"10.5555/demo.{i:03d}",
            "scopus_id": f"{i:011d}",
            "doc_type": "Article",
            "open_access": i % 2 == 1,
        })
    if sort == "-coverDate":
        papers.sort(key=lambda p: p["date"], reverse=True)
    return {"total_results": DEMO_PAPERS, "papers": papers}
