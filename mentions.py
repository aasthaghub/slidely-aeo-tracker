"""Find which brands a piece of text mentions, and in what order.

Shared by analyze.py (AI answers) and check_sources.py (web pages).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent


def load_brands():
    cfg = json.loads((ROOT / "config" / "brands.json").read_text(encoding="utf-8"))
    return cfg["target"], cfg["brands"]


def _alias_pattern(alias):
    # Whole-word match that also treats "." as part of a word, so "gamma" does not
    # fire inside "gamma.app.example" twice and "slidely" matches "Slidely." at a
    # sentence end. Spaces in an alias match any run of whitespace.
    body = r"\s+".join(re.escape(part) for part in alias.split())
    return rf"(?<![\w-]){body}(?![\w-]|\.\w)"


def compile_brands(brands):
    """{brand: [aliases]} -> {brand: compiled regex matching any alias}."""
    return {
        name: re.compile("|".join(_alias_pattern(a) for a in aliases), re.IGNORECASE)
        for name, aliases in brands.items()
    }


def find_mentions(text, compiled):
    """Return brands mentioned in `text`, ordered by where they first appear."""
    first_seen = {}
    for name, pattern in compiled.items():
        match = pattern.search(text or "")
        if match:
            first_seen[name] = match.start()
    return sorted(first_seen, key=first_seen.get)
