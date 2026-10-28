"""Check that every role has a docs page, nav entry, and index link."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = ROOT / "roles"
DOCS_ROLES = ROOT / "docs" / "roles"
MKDOCS = ROOT / "mkdocs.yaml"
SNIPPET = '--8<-- "roles/{role}/README.md"'


def nav_paths(value: Any) -> list[str]:
    """Flatten the string leaves of the MkDocs nav tree."""
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(nav_paths(item))
        return result
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(nav_paths(item))
        return result
    if isinstance(value, str):
        return [value]
    return []


def main() -> int:
    """Validate role docs coverage and fail on drift."""
    roles = sorted(path.name for path in ROLES_DIR.iterdir() if (path / "README.md").is_file())
    pages = sorted(path.stem for path in DOCS_ROLES.glob("*.md") if path.name != "index.md")
    errors: list[str] = []

    for role in sorted(set(roles) - set(pages)):
        errors.append(f"missing docs page: docs/roles/{role}.md")
    for role in sorted(set(pages) - set(roles)):
        errors.append(f"docs page without a role: docs/roles/{role}.md")

    nav = set(nav_paths(yaml.safe_load(MKDOCS.read_text(encoding="utf-8"))))
    index = (DOCS_ROLES / "index.md").read_text(encoding="utf-8")

    for role in roles:
        page = DOCS_ROLES / f"{role}.md"
        if not page.is_file():
            continue
        if SNIPPET.format(role=role) not in page.read_text(encoding="utf-8"):
            errors.append(f"docs/roles/{role}.md must contain {SNIPPET.format(role=role)!r}")
        if f"roles/{role}.md" not in nav:
            errors.append(f"mkdocs.yaml nav is missing roles/{role}.md")
        if f"({role}.md)" not in index:
            errors.append(f"docs/roles/index.md is missing a link to {role}.md")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"docs role coverage OK ({len(roles)} roles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
