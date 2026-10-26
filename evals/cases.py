"""Eval cases: questions and the rules the agent's first Scopus query must satisfy.

Patterns are case-insensitive regular expressions matched against the query,
so several equally valid phrasings can pass.
"""

CASES = [
    {
        "id": "uk_cancer_most_cited",
        "question": "What are the most cited UK cancer papers since 2020?",
        "query_must_match": [
            r"cancer",
            r'AFFILCOUNTRY\s*\(\s*"?United Kingdom"?\s*\)',
            r"PUBYEAR\s*>\s*2019",
        ],
        "sort": "-citedby-count",
    },
    {
        "id": "graphene_batteries_recent",
        "question": "Find recent papers on graphene batteries",
        "query_must_match": [r"graphene", r"batter"],
        "sort": "-coverDate",
    },
    {
        "id": "crispr_not_reviews",
        "question": "Show me original research articles on CRISPR gene editing, not reviews",
        "query_must_match": [
            r"CRISPR",
            r"DOCTYPE\s*\(\s*ar\s*\)|AND\s+NOT\s+DOCTYPE\s*\(\s*re\s*\)",
        ],
    },
    {
        "id": "oxford_quantum",
        "question": "Papers on quantum computing by researchers at the University of Oxford",
        "query_must_match": [r"quantum", r"AFFIL(ORG)?\s*\([^)]*Oxford"],
    },
    {
        "id": "microplastics_2022",
        "question": "Papers published in 2022 about microplastics in drinking water",
        "query_must_match": [r"microplastic", r"water", r"PUBYEAR\s*=\s*2022"],
    },
    {
        "id": "author_hinton",
        "question": "Find papers by Geoffrey Hinton on deep learning",
        "query_must_match": [r"AUTH(LASTNAME|OR-NAME)?\s*\([^)]*Hinton", r"deep learning|neural"],
    },
    {
        "id": "germany_or_france_ml",
        "question": "Machine learning papers from Germany or France since 2021",
        "query_must_match": [
            r"machine learning",
            r"Germany.*\bOR\b.*France|France.*\bOR\b.*Germany",
            r"PUBYEAR\s*>\s*2020",
        ],
    },
    {
        "id": "off_topic_weather",
        "question": "What's the weather like in London today?",
        "expect_tool_call": False,
    },
    {
        "id": "greeting",
        "question": "Hi! What can you help me with?",
        "expect_tool_call": False,
    },
    {
        "id": "concept_definition",
        "question": "What is CRISPR?",
        "expect_tool_call": False,
    },
    {
        "id": "beyond_capability_pdf",
        "question": "Download the full PDF of the most cited graphene paper for me",
        "expect_tool_call": False,
    },
]
