# Slidely AEO Tracker

**Does AI recommend Slidely when a buyer asks for a PowerPoint AI tool?**
This repo measures it, explains why not, and lists what to fix. It re-runs every Monday on its own.

📊 **Dashboard:** https://aasthaghub.github.io/slidely-aeo-tracker/

> Independent analysis built for my application to Slidely AI's Founding Growth Engineer role.
> Not affiliated with Slidely.

## Findings (first run, 21 Oct 2026)

| | |
|---|---|
| AI answers that recommend Slidely | **0 of 120** |
| AI answers that recommend Gamma | **91%** (Beautiful.ai 84%, Microsoft Copilot 79%) |
| Top-ranking "best AI presentation tool" pages that list Slidely | **0 of 18** (Gamma: 13) |
| Answers to *"What is Slidely AI?"* that describe it correctly | **0 of 9** |

1. **AI doesn't recommend Slidely, even for Slidely's exact use case.** Across consulting, banking/PE,
   enterprise-template and "inside PowerPoint" questions, Slidely appeared in 0% of answers. The category
   leader was at 89–100% in every segment.
2. **The pages AI learns from don't list Slidely.** 16 pages list three or more competitors but not
   Slidely. Those are the outreach targets (see the dashboard).
3. **Name collision.** When asked about Slidely directly, Gemini mixed it up with the older Slidely
   photo/video app (3/9), assumed the user meant a different tool (2/9), or gave a generic guess (4/9).
   None of the answers said it's a PowerPoint add-in.

### What I'd do next
- Get Slidely onto the 16 outreach-target pages (ranked by how crowded they are).
- Publish a clear "Slidely AI is a PowerPoint add-in for consultants and enterprise teams" page and
  comparison pages (vs Gamma, vs Copilot) to fix the name collision for AI engines.
- Extend the tracker to ChatGPT, Perplexity and Claude, and add a Slack alert when the share moves.

## How it works

```
config/prompts.json  ─▶ ask_ai.py ─▶ results/answers/<date>.jsonl ─▶ analyze.py ─▶ results/summary.json ─┐
config/sources.json  ─▶ check_sources.py ─▶ results/sources.json ─────────────────────────────────────────┴▶ build_dashboard.py ─▶ docs/index.html
```

| Step | File | What it does |
|---|---|---|
| 1 | `ask_ai.py` | Asks Gemini 40 buyer questions (none name Slidely) + 3 brand questions, 3 runs each because answers vary. Resumable; switches to a lighter model if the main one is overloaded. |
| 2 | `analyze.py` | Mention rate, top-3 rate, named-first rate, per buyer segment, plus a check on how the AI describes Slidely. |
| 3 | `check_sources.py` | Downloads the top-ranking listicles and records which tools each one lists. |
| 4 | `build_dashboard.py` | Static HTML dashboard, hosted free on GitHub Pages. |
| ⏱ | `.github/workflows/weekly.yml` | Re-runs everything every Monday and commits the results, so the trend builds up on its own. |

`mentions.py` holds the brand matching (whole-word, alias-aware: "Slidely.ai", "Slidely AI" and "Slidely" all count).

## Things I got wrong first (and fixed)
- **Echo inflation.** Questions like *"Gamma's export breaks my formatting, what else?"* pushed Gamma's score up
  because the answer repeats the question. Tools named in the question no longer count for that answer
  (Gamma: 96% → 91% on partial data).
- **Keyword labels lied.** My first "does the AI know Slidely?" check flagged any answer containing "slideshow"
  as confusion with the old app. Reading all 9 answers showed generic answers use that word too. I rewrote
  the rules from what the answers actually said.

## Limits
- One model (Gemini Flash-Lite, no web search, which is not available on the free tier), one day of data.
- "Mention" means the name appears, not that the AI recommends it positively.
- The source list is 20 pages collected by hand from search results. 2 of them block automated reads.

## Run it yourself
```bash
pip install -r requirements.txt
# put GEMINI_API_KEY=... in a .env file (free key from aistudio.google.com)
python ask_ai.py && python analyze.py && python check_sources.py && python build_dashboard.py
```

Built in a day with Claude Code.
