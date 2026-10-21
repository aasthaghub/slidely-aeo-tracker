"""Step 4: build a one-page dashboard (docs/index.html) from the results.

Plain HTML + CSS, no libraries, so GitHub Pages can host it for free.
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"

CATEGORY_LABELS = {
    "consulting": "Consulting", "banking_pe": "Banking & PE", "enterprise_brand": "Enterprise & brand",
    "powerpoint_native": "Inside PowerPoint", "general": "General", "india": "India / YC",
    "use_case": "Specific use cases",
}


def bar_rows(items, target, max_value, unit="%"):
    """items: [(label, value, tooltip)] -> HTML rows of horizontal bars."""
    out = []
    for label, value, tip in items:
        width = 0 if max_value == 0 else max(value / max_value * 100, 0.6)
        cls = "bar target" if label == target else "bar"
        out.append(
            f'<div class="row" title="{escape(tip)}">'
            f'<span class="label">{escape(label)}</span>'
            f'<span class="track"><span class="{cls}" style="width:{width:.1f}%"></span></span>'
            f'<span class="value">{value:g}{unit}</span></div>'
        )
    return "\n".join(out)


def main():
    s = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))
    src_file = RESULTS / "sources.json"
    src = json.loads(src_file.read_text(encoding="utf-8")) if src_file.exists() else None
    target = s["target"]
    me = next(b for b in s["brands"] if b["name"] == target)
    leader = next(b for b in s["brands"] if b["name"] != target)

    # Chart 1: share of AI answers mentioning each brand (top 12, target always shown)
    shown = [b for b in s["brands"] if b["name"] != target][:12] + [me]
    shown.sort(key=lambda b: -b["mention_rate"])
    chart_answers = bar_rows(
        [(b["name"], b["mention_rate"],
          f"{b['name']}: in {b['mention_rate']}% of answers, top-3 in {b['top3_rate']}%, "
          f"named first in {b['first_rate']}%") for b in shown],
        target, max(b["mention_rate"] for b in shown))

    # Table: by buyer category
    cat_rows = "\n".join(
        f"<tr><td>{escape(CATEGORY_LABELS.get(c, c))}</td><td>{v['answers']}</td>"
        f"<td class='num {'zero' if v['target_rate'] == 0 else ''}'>{v['target_rate']:g}%</td>"
        f"<td>{escape(v['leader'] or '-')}</td><td class='num'>{v['leader_rate']:g}%</td></tr>"
        for c, v in s["categories"].items())

    # Brand knowledge
    verdict_counts = {}
    for k in s["brand_knowledge"]:
        verdict_counts[k["verdict"]] = verdict_counts.get(k["verdict"], 0) + 1
    knowledge_items = "\n".join(
        f"<details><summary><b>{escape(k['verdict'])}</b> - “{escape(k['prompt'])}” (run {k['run']})</summary>"
        f"<p class='answer'>{escape(k['answer'][:900])}{'…' if len(k['answer']) > 900 else ''}</p></details>"
        for k in s["brand_knowledge"])
    main_verdict = max(verdict_counts, key=verdict_counts.get) if verdict_counts else "n/a"

    hits = "".join(
        f"<li>“{escape(h['prompt'])}” - run {h['run']}, named #{h['position']}</li>" for h in s["target_hits"]
    ) or "<li>None. Slidely was not named in any answer to a buyer question.</li>"

    # Sources section
    if src:
        presence = list(src["presence"].items())[:12]
        if target not in src["presence"]:
            presence.append((target, 0))
        presence.sort(key=lambda kv: -kv[1])
        chart_sources = bar_rows(
            [(name, n, f"{name}: listed on {n} of {src['pages_readable']} pages") for name, n in presence],
            target, max(n for _, n in presence) or 1, unit="")
        targets_html = "\n".join(
            f"<tr><td><a href='{escape(t['url'])}'>{escape(t['url'].split('//')[1][:70])}</a></td>"
            f"<td class='num'>{t['competitors_listed']}</td>"
            f"<td>{escape(', '.join(b for b in t['brands'] if b not in ('ChatGPT', 'Claude', 'Google Slides'))[:120])}</td></tr>"
            for t in src["outreach_targets"])
        sources_block = f"""
<section>
  <h2>Why: the pages AI learns from don't list {target}</h2>
  <p class="sub">{src['pages_readable']} of {src['pages_checked']} top-ranking “best AI presentation tool” pages were readable.
  {target} is listed on <b>{src['pages_listing_target']}</b> of them. Bars show how many pages list each tool.</p>
  <div class="chart">{chart_sources}</div>
  <h3>Outreach targets ({len(src['outreach_targets'])})</h3>
  <p class="sub">Pages that list 3+ competitors but not {target}, most crowded first. Getting added to these is the most direct lever on AI answers.</p>
  <div class="tablewrap"><table><thead><tr><th>Page</th><th>Tools listed</th><th>Who's on it</th></tr></thead>
  <tbody>{targets_html}</tbody></table></div>
</section>"""
        kpi_sources = f'<div class="kpi"><div class="big">{src["pages_listing_target"]}/{src["pages_readable"]}</div><div>ranking pages list {target}</div></div>'
    else:
        sources_block, kpi_sources = "", ""

    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Slidely AI Visibility</title>
<style>
:root {{ --bg:#f7f7f5; --card:#ffffff; --ink:#1d1d1f; --muted:#6b6b70; --line:#e4e4e0;
  --track:#efefec; --bar:#a3a6ad; --accent:#d9480f; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#141416; --card:#1d1d20; --ink:#ececee; --muted:#9a9aa2; --line:#2e2e33;
  --track:#26262a; --bar:#6c6f78; --accent:#ff7a3d; }} }}
:root[data-theme="dark"] {{ --bg:#141416; --card:#1d1d20; --ink:#ececee; --muted:#9a9aa2;
  --line:#2e2e33; --track:#26262a; --bar:#6c6f78; --accent:#ff7a3d; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:920px; margin:0 auto; padding:32px 16px 64px; }}
h1 {{ font-size:28px; line-height:1.2; margin:0 0 6px; }}
h2 {{ font-size:19px; margin:0 0 4px; }} h3 {{ font-size:15px; margin:22px 0 4px; }}
.sub {{ color:var(--muted); margin:0 0 14px; }}
section {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px; margin-top:16px; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-top:20px; }}
.kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; color:var(--muted); }}
.kpi .big {{ font-size:30px; font-weight:700; color:var(--ink); line-height:1.1; margin-bottom:4px; }}
.kpi.hl .big {{ color:var(--accent); }}
.row {{ display:grid; grid-template-columns:140px 1fr 52px; align-items:center; gap:10px; padding:3px 0; }}
.row:hover .label, .row:hover .value {{ color:var(--ink); font-weight:600; }}
.label {{ color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.value {{ text-align:right; font-variant-numeric:tabular-nums; color:var(--muted); }}
.track {{ background:var(--track); border-radius:4px; height:14px; overflow:hidden; }}
.bar {{ display:block; height:100%; background:var(--bar); border-radius:0 4px 4px 0; }}
.bar.target {{ background:var(--accent); }}
.row:has(.target) .label, .row:has(.target) .value {{ color:var(--accent); font-weight:700; }}
.tablewrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th, td {{ text-align:left; padding:8px 6px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--muted); font-weight:600; }}
td.num {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }}
td.zero {{ color:var(--accent); font-weight:700; }}
a {{ color:inherit; text-decoration-color:var(--muted); word-break:break-all; }}
details {{ border-top:1px solid var(--line); padding:8px 0; }}
summary {{ cursor:pointer; }}
.answer {{ color:var(--muted); white-space:pre-wrap; font-size:14px; }}
ol li, ul li {{ margin-bottom:6px; }}
footer {{ color:var(--muted); font-size:13px; margin-top:24px; }}
@media (max-width:560px) {{ .row {{ grid-template-columns:100px 1fr 46px; }} h1 {{ font-size:23px; }} }}
</style></head>
<body><main>
<h1>Does AI recommend {target}?</h1>
<p class="sub">I asked Gemini {s['prompts']} questions a real buyer would ask (“best AI tool for consulting decks in PowerPoint”, …),
{s['runs_per_prompt']}× each, and counted which tools it recommended. None of the questions name {target}.
Run on {s['run_date']} · model: {', '.join(s['models'])} · {s['answers']} answers.</p>

<div class="kpis">
  <div class="kpi hl"><div class="big">{me['mention_rate']:g}%</div><div>of AI answers mention {target}</div></div>
  <div class="kpi"><div class="big">{leader['mention_rate']:g}%</div><div>mention {escape(leader['name'])}, the leader</div></div>
  {kpi_sources}
  <div class="kpi"><div class="big" style="font-size:18px">{escape(main_verdict)}</div><div>when asked “What is {target} AI?”</div></div>
</div>

<section>
  <h2>Share of AI answers that mention each tool</h2>
  <p class="sub">Hover a bar for top-3 and named-first rates.</p>
  <div class="chart">{chart_answers}</div>
  <h3>Where {target} did show up</h3><ul>{hits}</ul>
</section>

<section>
  <h2>By buyer type</h2>
  <p class="sub">The segments {target} sells to, and who AI recommends there instead.</p>
  <div class="tablewrap"><table><thead><tr><th>Questions about</th><th>Answers</th><th>{target}</th><th>Most recommended</th><th>Rate</th></tr></thead>
  <tbody>{cat_rows}</tbody></table></div>
</section>
{sources_block}
<section>
  <h2>Does AI know what {target} is?</h2>
  <p class="sub">Questions that name {target} directly. Click to read the full answers.</p>
  {knowledge_items}
</section>

<footer>Built by an applicant for the Founding Growth Engineer role. Independent analysis, not affiliated with {target}.
Method: Gemini API without web search, {s['runs_per_prompt']} runs per question (answers vary run to run); a mention = the tool's name
appears in the answer (whole-word match). Code and raw answers are in the repository.</footer>
</main></body></html>
"""
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
