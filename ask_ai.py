"""Step 1: ask Gemini every buyer question several times and save the raw answers.

AI answers are random: the same question can recommend different tools each time.
So each prompt runs RUNS times and we look at how often a brand shows up.

Output: results/answers/<date>.jsonl  (one JSON object per answer)
Safe to re-run: answers already saved for today are skipped, so a crash or a
rate limit halfway through just resumes where it stopped.
"""
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors

ROOT = Path(__file__).parent
RUNS = 3                                  # answers per prompt
MODEL = "gemini-flash-latest"             # what a typical Gemini user gets
FALLBACK_MODEL = "gemini-flash-lite-latest"  # used if MODEL stays overloaded
PAUSE_SECONDS = 4                         # stay under the free tier's per-minute limit


current_model = MODEL


def ask(client, prompt):
    """Ask one question, retrying on rate limits / overload. Returns (text, model)."""
    global current_model
    for attempt in range(1, 7):
        try:
            reply = client.models.generate_content(model=current_model, contents=prompt)
            return reply.text or "", current_model
        except errors.APIError as e:
            if e.code == 429:            # too many requests: wait for the quota window
                wait = 30 * attempt
            elif e.code in (500, 503):   # Google's side is busy
                wait = 5 * attempt
                if attempt >= 2 and current_model != FALLBACK_MODEL:
                    # Switch for the rest of the run, so one overloaded model
                    # doesn't make every question sit through retries.
                    print(f"    {current_model} overloaded, switching to {FALLBACK_MODEL}")
                    current_model = FALLBACK_MODEL
            else:
                raise
            print(f"    {e.code}, retrying in {wait}s (attempt {attempt})")
            time.sleep(wait)
    raise RuntimeError(f"Gave up on prompt after retries: {prompt[:60]}")


def main():
    load_dotenv(ROOT / ".env")
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        sys.exit("GEMINI_API_KEY is missing (put it in .env, or a GitHub secret).")
    client = genai.Client(api_key=key)

    prompts = json.loads((ROOT / "config" / "prompts.json").read_text(encoding="utf-8"))["prompts"]
    out_dir = ROOT / "results" / "answers"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{date.today().isoformat()}.jsonl"

    done = set()
    if out_file.exists():
        for line in out_file.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            done.add((row["prompt_id"], row["run"]))

    total = len(prompts) * RUNS
    print(f"{len(done)}/{total} answers already saved in {out_file.name}")

    with out_file.open("a", encoding="utf-8") as f:
        for p in prompts:
            for run in range(1, RUNS + 1):
                if (p["id"], run) in done:
                    continue
                print(f"[{len(done) + 1}/{total}] {p['id']} run {run}")
                text, model = ask(client, p["text"])
                row = {
                    "date": date.today().isoformat(),
                    "prompt_id": p["id"],
                    "category": p["category"],
                    "prompt": p["text"],
                    "run": run,
                    "model": model,
                    "answer": text,
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
                done.add((p["id"], run))
                time.sleep(PAUSE_SECONDS)

    print("Done.")


if __name__ == "__main__":
    main()
