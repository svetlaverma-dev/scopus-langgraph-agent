"""Layer 1 debugging tool: call Scopus from Python, show results and quota,
save a test fixture (only once), and detect the access level."""
import json
from datetime import datetime
from pathlib import Path

from server.scopus_client import ScopusClient

QUERY = "TITLE-ABS-KEY(graphene AND battery) AND PUBYEAR > 2019"
FIXTURE = Path("tests/fixtures/search_graphene_battery.json")

with ScopusClient() as sc:
    # 1. A real search: the 5 most-cited results
    data = sc.search(QUERY, count=5, sort="-citedby-count")
    results = data["search-results"]
    print("Query:", QUERY)
    print("Total results:", results["opensearch:totalResults"])
    for entry in results.get("entry", []):
        year = (entry.get("prism:coverDate") or "")[:4]
        print(f"- {entry.get('dc:title')} ({year}) cited {entry.get('citedby-count')}")

    # 2. Quota, read from the response headers
    q = sc.quota
    reset = datetime.fromtimestamp(q.resets_at) if q.resets_at else "unknown"
    print(f"\nQuota: {q.remaining} of {q.limit} remaining, resets {reset}")

    # 3. Save the raw response as a test fixture - only the first time,
    #    so later runs don't change the data our tests rely on
    if FIXTURE.exists():
        print("Fixture already exists, not overwriting:", FIXTURE)
    else:
        FIXTURE.write_text(json.dumps(data, indent=2))
        print("Saved fixture:", FIXTURE)

    # 4. Detect the access level (uses one more request)
    print("Access level:", sc.probe_entitlement())
