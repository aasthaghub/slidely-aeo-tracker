"""Step 3: check the web pages AI answers are built from.

For each 'best AI presentation tools' page in config/sources.json, download it and
see which brands it lists. A page that lists competitors but not Slidely is an
outreach target: get Slidely onto it and AI answers have one more reason to
recommend it.

Output: results/sources.json
"""
import html
import json
import re
import urllib.request
from datetime import date
from pathlib import Path

from mentions import compile_brands, find_mentions, load_brands

ROOT = Path(__file__).parent
HEADERS = {
    # Identify honestly; some sites block unknown clients, which we record as 'blocked'.
    "User-Agent": "Mozilla/5.0 (compatible; slidely-aeo-tracker/1.0; research)",
    "Accept-Language": "en",
}


def page_text(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
    raw = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", raw)
    return html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))


def main():
    target, brands = load_brands()
    compiled = compile_brands(brands)
    urls = json.loads((ROOT / "config" / "sources.json").read_text(encoding="utf-8"))["pages"]

    pages = []
    for url in urls:
        entry = {"url": url}
        try:
            text = page_text(url)
            if len(text.split()) < 200:      # probably a JS-only page or a block screen
                entry["status"] = "unreadable"
            else:
                found = find_mentions(text, compiled)
                entry.update(status="ok", brands=found, lists_target=target in found,
                             competitors=len([b for b in found if b != target]))
        except Exception as e:  # network error, 403, timeout...
            entry["status"] = "blocked"
            entry["error"] = str(e)[:120]
        print(f"{entry['status']:<10} {url}")
        pages.append(entry)

    ok = [p for p in pages if p["status"] == "ok"]
    targets = sorted((p for p in ok if not p["lists_target"] and p["competitors"] >= 3),
                     key=lambda p: -p["competitors"])
    competitor_presence = {}
    for p in ok:
        for b in p["brands"]:
            competitor_presence[b] = competitor_presence.get(b, 0) + 1

    result = {
        "checked": date.today().isoformat(),
        "pages_checked": len(pages),
        "pages_readable": len(ok),
        "pages_listing_target": sum(p["lists_target"] for p in ok),
        "presence": dict(sorted(competitor_presence.items(), key=lambda kv: -kv[1])),
        "outreach_targets": [{"url": p["url"], "competitors_listed": p["competitors"],
                              "brands": p["brands"]} for p in targets],
        "pages": pages,
    }
    (ROOT / "results" / "sources.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"\n{len(ok)}/{len(pages)} pages readable; {target} listed on {result['pages_listing_target']}")
    print("Brand presence across pages:", result["presence"])
    print(f"Outreach targets: {len(targets)}")


if __name__ == "__main__":
    main()
