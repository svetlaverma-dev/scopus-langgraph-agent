"""
scopus_client.py - a thin Python wrapper around Elsevier's Scopus REST API.

This file knows nothing about MCP or LLMs. It only:
  1. adds your API key (and optional insttoken) to every request,
  2. calls Scopus endpoints,
  3. records your remaining quota from the response headers,
  4. turns HTTP errors into clear Python exceptions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()  # read .env into environment variables

BASE_URL = "https://api.elsevier.com"


# --------------------------------------------------------------------------
# Errors: one Python exception per kind of failure
# --------------------------------------------------------------------------
class ScopusError(Exception):
    """Base class for every error raised by this client."""


class NotEntitled(ScopusError):
    """HTTP 401/403: key invalid, or this data needs a subscription."""


class QuotaExceeded(ScopusError):
    """HTTP 429: weekly quota or rate limit reached."""

    def __init__(self, resets_at: int | None):
        self.resets_at = resets_at
        super().__init__(f"Scopus quota exceeded; resets at Unix time {resets_at}")


class InvalidQuery(ScopusError):
    """HTTP 400: Scopus rejected the request (usually bad query syntax)."""


# --------------------------------------------------------------------------
# Quota tracking
# --------------------------------------------------------------------------
@dataclass
class Quota:
    limit: int | None = None
    remaining: int | None = None
    resets_at: int | None = None  # Unix time, in seconds


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


# --------------------------------------------------------------------------
# The client
# --------------------------------------------------------------------------
class ScopusClient:
    def __init__(self, api_key: str | None = None, insttoken: str | None = None,
                 timeout: float = 30.0):
        api_key = api_key or os.environ.get("ELSEVIER_API_KEY")
        if not api_key:
            raise ValueError("ELSEVIER_API_KEY is not set. Add it to your .env file.")
        insttoken = insttoken or os.environ.get("ELSEVIER_INSTTOKEN") or None

        headers = {"X-ELS-APIKey": api_key, "Accept": "application/json"}
        if insttoken:
            headers["X-ELS-Insttoken"] = insttoken

        self._http = httpx.Client(base_url=BASE_URL, headers=headers, timeout=timeout)
        self.quota = Quota()

    # Lets you write `with ScopusClient() as sc:` so the connection closes itself
    def __enter__(self) -> "ScopusClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    # Every request goes through this one method
    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        resp = self._http.get(path, params=params)

        for field, header in (("limit", "X-RateLimit-Limit"),
                              ("remaining", "X-RateLimit-Remaining"),
                              ("resets_at", "X-RateLimit-Reset")):
            value = _to_int(resp.headers.get(header))
            if value is not None:
                setattr(self.quota, field, value)

        if resp.status_code == 200:
            return resp.json()

        detail = resp.text[:300]
        if resp.status_code in (401, 403):
            raise NotEntitled(f"HTTP {resp.status_code}: {detail}")
        if resp.status_code == 429:
            raise QuotaExceeded(self.quota.resets_at)
        if resp.status_code == 400:
            raise InvalidQuery(detail)
        raise ScopusError(f"HTTP {resp.status_code}: {detail}")

    # ---------------- Endpoints ----------------
    def search(self, query: str, start: int = 0, count: int = 25,
               sort: str | None = None, view: str | None = None) -> dict:
        """Scopus Search API. `query` uses Advanced Search syntax,
        e.g. 'TITLE-ABS-KEY(graphene) AND PUBYEAR > 2019'."""
        return self._get("/content/search/scopus",
                         {"query": query, "start": start, "count": count,
                          "sort": sort, "view": view})

    def abstract(self, scopus_id: str | None = None, doi: str | None = None,
                 view: str = "META") -> dict:
        """Abstract Retrieval API, by Scopus ID or DOI."""
        if scopus_id:
            path = f"/content/abstract/scopus_id/{scopus_id}"
        elif doi:
            path = f"/content/abstract/doi/{doi}"
        else:
            raise ValueError("Provide scopus_id or doi")
        return self._get(path, {"view": view})

    def author_search(self, query: str, count: int = 25) -> dict:
        """Author Search API (usually subscriber-only)."""
        return self._get("/content/search/author", {"query": query, "count": count})

    def author(self, author_id: str) -> dict:
        """Author Retrieval API (usually subscriber-only)."""
        return self._get(f"/content/author/author_id/{author_id}")

    def subjects(self) -> dict:
        """Subject Classifications API."""
        return self._get("/content/subject/scopus")

    def probe_entitlement(self) -> str:
        """Find out the access level with one tiny request.
        Returns 'subscriber' or 'free'."""
        try:
            self.search("TITLE(graphene)", count=1, view="COMPLETE")
            return "subscriber"
        except NotEntitled:
            return "free"
