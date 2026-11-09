"""Check project rules that unit tests can't catch.

Run locally or in CI: python scripts/check_guardrails.py
Exits with status 1 if any rule is broken.
"""
import ast
import fnmatch
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files that must never be committed
FORBIDDEN_FILES = [
    ".env",                          # secrets
    "tests/fixtures/search_*.json",  # real Scopus responses (Elsevier terms)
]


def stdout_prints(path):
    """Yield the line number of each print() call that writes to stdout."""
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "print"
            and not any(kw.arg == "file" for kw in node.keywords)
        ):
            yield node.lineno


def main():
    failures = []

    # Rule 1: the MCP server speaks JSON-RPC over stdout, so a print() there breaks the protocol
    for path in sorted((ROOT / "server").glob("*.py")):
        for line in stdout_prints(path):
            failures.append(f"{path.relative_to(ROOT)}:{line}: print() to stdout in the MCP server; use file=sys.stderr")

    # Rule 2: secrets and real Scopus data never go into git
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    for pattern in FORBIDDEN_FILES:
        for name in fnmatch.filter(tracked, pattern):
            failures.append(f"{name}: must not be committed")

    for failure in failures:
        print(failure)
    print(f"{len(failures)} guardrail violation(s)" if failures else "All guardrails pass")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
