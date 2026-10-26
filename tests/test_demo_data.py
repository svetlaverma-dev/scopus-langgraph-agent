import json
from pathlib import Path

from server.demo_data import demo_search, first_year, query_topic
from server.mcp_server import trim_search_results

FIXTURE = Path(__file__).parent / "fixtures" / "sample_search.json"


def test_query_topic():
    assert query_topic('TITLE-ABS-KEY("machine learning" AND diagnosis)') == "machine learning diagnosis"


def test_query_topic_without_topic_field():
    assert query_topic("AUTHLASTNAME(Hinton)") == "your query"


def test_first_year():
    assert first_year("TITLE-ABS-KEY(cancer) AND PUBYEAR > 2019") == 2020
    assert first_year("TITLE-ABS-KEY(cancer)") == 2018


def test_papers_are_labelled_synthetic():
    for paper in demo_search("TITLE-ABS-KEY(cancer)")["papers"]:
        assert paper["title"].startswith("[Demo]")
        assert paper["doi"].startswith("10.5555/demo.")


def test_count_is_respected_and_capped():
    assert len(demo_search("TITLE(cancer)", count=3)["papers"]) == 3
    assert len(demo_search("TITLE(cancer)", count=25)["papers"]) == 5


def test_sorted_by_date():
    dates = [p["date"] for p in demo_search("TITLE(cancer)", sort="-coverDate")["papers"]]
    assert dates == sorted(dates, reverse=True)


def test_same_shape_as_real_results():
    real = trim_search_results(json.loads(FIXTURE.read_text()))
    demo = demo_search("TITLE(cancer)")
    assert demo.keys() == real.keys()
    assert demo["papers"][0].keys() == real["papers"][0].keys()
