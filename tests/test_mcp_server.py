import json
from pathlib import Path

from server.mcp_server import trim_search_results

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_trim_search_results():
    trimmed = trim_search_results(load("sample_search"))

    assert trimmed["total_results"] == 1234
    assert len(trimmed["papers"]) == 3
    for paper in trimmed["papers"]:
        assert paper["title"]
        assert paper["scopus_id"].isdigit()
        assert isinstance(paper["cited_by"], int)
        assert isinstance(paper["open_access"], bool)


def test_first_paper():
    first = trim_search_results(load("sample_search"))["papers"][0]
    assert first == {
        "title": "A synthetic review of example methods",
        "first_author": "Example A.",
        "journal": "Journal of Synthetic Examples",
        "date": "2023-05-01",
        "cited_by": 950,
        "doi": "10.5555/example.001",
        "scopus_id": "00000000001",
        "doc_type": "Review",
        "open_access": True,
    }


def test_sorted_by_citations():
    cited = [p["cited_by"] for p in trim_search_results(load("sample_search"))["papers"]]
    assert cited == sorted(cited, reverse=True)


def test_missing_doi_is_none():
    third = trim_search_results(load("sample_search"))["papers"][2]
    assert third["doi"] is None
    assert third["doc_type"] == "Conference Paper"


def test_empty_result_set():
    raw = {"search-results": {"opensearch:totalResults": "0",
                              "entry": [{"error": "Result set was empty"}]}}
    assert trim_search_results(raw) == {"total_results": 0, "papers": []}
