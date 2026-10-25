"""MCP server exposing Scopus search as tools for the agent (layer 2)."""
from typing import Any

from mcp.server.fastmcp import FastMCP

from server.scopus_client import ScopusClient

mcp = FastMCP("scopus")


def trim_search_results(data: dict) -> dict[str, Any]:
    """Reduce a raw Scopus search response to the fields the agent needs."""
    results = data["search-results"]
    papers = []
    for entry in results.get("entry", []):
        if "error" in entry:  # Scopus returns {"error": "Result set was empty"} for no hits
            continue
        papers.append({
            "title": entry.get("dc:title"),
            "first_author": entry.get("dc:creator"),
            "journal": entry.get("prism:publicationName"),
            "date": entry.get("prism:coverDate"),
            "cited_by": int(entry.get("citedby-count", 0)),
            "doi": entry.get("prism:doi"),
            "scopus_id": entry.get("dc:identifier", "").removeprefix("SCOPUS_ID:"),
            "doc_type": entry.get("subtypeDescription"),
            "open_access": entry.get("openaccessFlag", False),
        })
    return {"total_results": int(results["opensearch:totalResults"]), "papers": papers}


@mcp.tool()
def search_scopus(query: str, count: int = 10, sort: str = "-citedby-count") -> dict[str, Any]:
    """Search Scopus for papers using Scopus Advanced Search syntax.

    Field codes:
      TITLE-ABS-KEY(term)       term in title, abstract or keywords
      TITLE(term)               term in title only
      AUTHLASTNAME(name)        author surname
      AFFILCOUNTRY("country")   author affiliation country
      AFFILORG("organisation")  author affiliation organisation
      PUBYEAR > 2019            publication year (also <, =)
      DOCTYPE(ar)               article (re = review, cp = conference paper)
    Combine with AND, OR, AND NOT. Quote multi-word phrases.

    Example: TITLE-ABS-KEY(cancer) AND AFFILCOUNTRY("United Kingdom") AND PUBYEAR > 2019

    Args:
        query: the Scopus Advanced Search query.
        count: number of papers to return (1-25).
        sort: "-citedby-count" (most cited), "-coverDate" (newest) or "relevancy".

    Results list only the first few affiliations per paper, so do not conclude
    an author or country is absent from them. If total_results is very large,
    narrow the query rather than asking for more.
    """
    with ScopusClient() as sc:
        data = sc.search(query, count=count, sort=sort)
    return trim_search_results(data)


if __name__ == "__main__":
    mcp.run()
