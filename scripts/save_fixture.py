"""Save one raw Scopus search response as a test fixture.

Usage:
    python scripts/save_fixture.py NAME "QUERY" [--count N] [--sort FIELD]

Never overwrites an existing fixture, so tests keep stable data.
"""
import argparse
import json
from pathlib import Path

from server.scopus_client import ScopusClient

parser = argparse.ArgumentParser(description="Save a Scopus search response as a test fixture.")
parser.add_argument("name", help="short name, e.g. uk_cancer -> tests/fixtures/search_uk_cancer.json")
parser.add_argument("query", help="Scopus Advanced Search query")
parser.add_argument("--count", type=int, default=25, help="number of results (default 25)")
parser.add_argument("--sort", default="-citedby-count", help="sort order (default: most cited first)")
args = parser.parse_args()

out = Path("tests/fixtures") / f"search_{args.name}.json"
if out.exists():
    raise SystemExit(f"{out} already exists. Delete it first if you really want to re-save it.")

with ScopusClient() as sc:
    data = sc.search(args.query, count=args.count, sort=args.sort)

out.write_text(json.dumps(data, indent=2))
results = data["search-results"]
print(f"Saved {out}")
print(f"  query:   {args.query}")
print(f"  total matches: {results['opensearch:totalResults']}")
print(f"  entries saved: {len(results.get('entry', []))}")
