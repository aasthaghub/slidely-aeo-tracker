"""Step 2: turn the raw answers into numbers.

Reads the newest results/answers/<date>.jsonl and writes:
  results/summary.json  - latest numbers (what the dashboard shows)
  results/history.json  - one line per run date, so we can see trends week to week

Metrics, for the buyer prompts (everything except 'brand_knowledge'):
  mention_rate  - share of answers that mention the brand at all
  top3_rate     - share of answers where the brand is among the first 3 tools named
  first_rate    - share of answers where the brand is the first tool named
  prompt_reach  - share of prompts where the brand showed up in at least one run
"""
import json
from collections import defaultdict
from pathlib import Path

from mentions import compile_brands, find_mentions, load_brands

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"

# Phrases that tell us how the AI handled "What is Slidely AI?"-type questions.
# Rules written after reading the answers by hand. A single word like "slideshow"
# is NOT enough: generic descriptions use it too.
UNKNOWN_HINTS = ["not aware", "don't have information", "couldn't find", "could not find",
                 "no information", "not familiar", "unable to find"]
OTHER_TOOL_HINTS = ["likely referring", "assuming you mean", "assuming you are referring",
                    "you may be thinking", "you might mean"]
OLD_APP_HINTS = ["photo video", "photo/video", "photo and video", "collage", "promo.com", "defunct"]
CORRECT_HINTS = ["add-in", "plug-in", "plugin", "inside powerpoint", "within powerpoint"]


def judge_brand_answer(text):
    t = text.lower()
    if any(h in t for h in UNKNOWN_HINTS):
        return "doesn't know Slidely"
    if any(h in t for h in OTHER_TOOL_HINTS):
        return "thinks you mean a different tool"
    if any(h in t for h in OLD_APP_HINTS):
        return "mixes it up with the old Slidely photo/video app"
    if any(h in t for h in CORRECT_HINTS):
        return "knows it's a PowerPoint add-in"
    return "generic guess (no PowerPoint add-in, no enterprise focus)"


def pct(part, whole):
    return round(100 * part / whole, 1) if whole else 0.0


def main():
    files = sorted((RESULTS / "answers").glob("*.jsonl"))
    if not files:
        raise SystemExit("No answers yet. Run ask_ai.py first.")
    latest = files[-1]
    rows = [json.loads(line) for line in latest.read_text(encoding="utf-8").splitlines()]

    target, brands = load_brands()
    compiled = compile_brands(brands)

    buyer = [r for r in rows if r["category"] != "brand_knowledge"]
    branded = [r for r in rows if r["category"] == "brand_knowledge"]
    for r in buyer:
        # A tool named in the question itself ("Gamma's export breaks...") is echoed
        # back, not recommended, so it doesn't count for that answer.
        in_prompt = set(find_mentions(r["prompt"], compiled))
        r["mentions"] = [m for m in find_mentions(r["answer"], compiled) if m not in in_prompt]

    # Per-brand metrics
    counts = defaultdict(lambda: {"any": 0, "top3": 0, "first": 0, "prompts": set()})
    for r in buyer:
        for i, name in enumerate(r["mentions"]):
            c = counts[name]
            c["any"] += 1
            c["prompts"].add(r["prompt_id"])
            if i < 3:
                c["top3"] += 1
            if i == 0:
                c["first"] += 1
    n_answers = len(buyer)
    n_prompts = len({r["prompt_id"] for r in buyer})
    brand_rows = sorted(
        (
            {
                "name": name,
                "mention_rate": pct(c["any"], n_answers),
                "top3_rate": pct(c["top3"], n_answers),
                "first_rate": pct(c["first"], n_answers),
                "prompt_reach": pct(len(c["prompts"]), n_prompts),
            }
            for name, c in counts.items()
        ),
        key=lambda b: -b["mention_rate"],
    )
    if not any(b["name"] == target for b in brand_rows):
        brand_rows.append({"name": target, "mention_rate": 0.0, "top3_rate": 0.0,
                           "first_rate": 0.0, "prompt_reach": 0.0})

    # Per-category: how does the target do vs the category leader?
    by_cat = defaultdict(list)
    for r in buyer:
        by_cat[r["category"]].append(r)
    categories = {}
    for cat, items in by_cat.items():
        tally = defaultdict(int)
        for r in items:
            for name in r["mentions"]:
                tally[name] += 1
        leader = max(tally, key=tally.get) if tally else None
        categories[cat] = {
            "answers": len(items),
            "target_rate": pct(tally.get(target, 0), len(items)),
            "leader": leader,
            "leader_rate": pct(tally.get(leader, 0), len(items)) if leader else 0.0,
        }

    # Where the target DID show up (worth reading closely)
    target_hits = [
        {"prompt_id": r["prompt_id"], "prompt": r["prompt"], "run": r["run"],
         "position": r["mentions"].index(target) + 1}
        for r in buyer if target in r["mentions"]
    ]

    brand_knowledge = [
        {"prompt": r["prompt"], "run": r["run"], "verdict": judge_brand_answer(r["answer"]),
         "answer": r["answer"]}
        for r in branded
    ]

    summary = {
        "run_date": rows[0]["date"],
        "models": sorted({r["model"] for r in rows}),
        "answers": n_answers,
        "prompts": n_prompts,
        "runs_per_prompt": max(r["run"] for r in rows),
        "target": target,
        "brands": brand_rows,
        "categories": categories,
        "target_hits": target_hits,
        "brand_knowledge": brand_knowledge,
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # History: replace today's entry if we re-ran, then keep dates in order
    history_file = RESULTS / "history.json"
    history = json.loads(history_file.read_text(encoding="utf-8")) if history_file.exists() else []
    history = [h for h in history if h["date"] != summary["run_date"]]
    history.append({"date": summary["run_date"],
                    "rates": {b["name"]: b["mention_rate"] for b in brand_rows[:8] + [
                        b for b in brand_rows if b["name"] == target]}})
    history.sort(key=lambda h: h["date"])
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    top = brand_rows[0]
    me = next(b for b in brand_rows if b["name"] == target)
    print(f"{n_answers} answers to {n_prompts} buyer prompts ({latest.name})")
    print(f"{target}: mentioned in {me['mention_rate']}% of answers")
    print(f"Leader: {top['name']} at {top['mention_rate']}%")
    for b in brand_rows[:10]:
        print(f"  {b['name']:<18} {b['mention_rate']:>5}%  top3 {b['top3_rate']:>5}%")
    print("Brand-knowledge answers:", [k["verdict"] for k in brand_knowledge])


if __name__ == "__main__":
    main()
