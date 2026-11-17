"""
Checks the REAL chatbot (needs GEMINI_API_KEY) against a list of questions with expected answers.

Run from the project folder:   python evals/run_evals.py

Unit tests check my code. Evals check the AI's behaviour: does it get facts right, refuse to
guess, send allergy questions to staff, and resist "ignore your rules" tricks?
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from bot import FALLBACK, GeminiLLM, ShopBot, load_facts  # noqa: E402


FALLBACK_START = FALLBACK.split("{")[0]


def check(reply, case):
    if reply.startswith(FALLBACK_START):
        return False  # the AI didn't answer at all, so this can never count as a pass
    text = reply.lower()
    ok_any = any(s.lower() in text for s in case.get("any_of", [])) if case.get("any_of") else True
    ok_none = not any(s.lower() in text for s in case.get("none_of", []))
    return ok_any and ok_none


RESULTS_FILE = Path(__file__).resolve().parent.parent / "results_evals.txt"


def say(text=""):
    """Print live AND save to results_evals.txt as we go, so progress is never hidden."""
    print(text, flush=True)
    with RESULTS_FILE.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def main():
    load_dotenv()
    RESULTS_FILE.write_text("", encoding="utf-8")
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        sys.exit("Set GEMINI_API_KEY in .env first. Evals test the real AI.")
    # Check the key's shape without ever printing it
    problems = []
    if key != key.strip():
        problems.append("it has spaces before or after it")
    if key[0] in "\"'" or key[-1] in "\"'":
        problems.append("it has quote marks around it - remove them")
    if len(key.strip(" \"'")) < 30:
        problems.append("it looks too short - check you copied the whole key")
    say(f"Key check: {len(key)} characters" + (" - PROBLEM: " + "; ".join(problems) if problems else " - looks OK"))

    say("Asking Google which models your key can use...")
    try:
        llm = GeminiLLM()
    except Exception as exc:
        sys.exit(f"Couldn't connect to Gemini to pick a model.\nError: {type(exc).__name__}: {exc}")
    say(f"Model: {llm.model} (picked automatically; backups if it's busy: {', '.join(llm.models[1:]) or 'none'})")
    bot = ShopBot(load_facts(), llm)

    # One test call first, so a broken setup shows its real error instead of 12 identical failures
    say("Test call...")
    first = bot.answer("What time do you close?")
    if bot.last_error:
        say(f"\nThe very first AI call failed, so stopping here.\nError: {bot.last_error}")
        sys.exit(1)
    say(f"Connection OK via {llm.model}. Sample answer: {first}\n")
    cases = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))

    passed = 0
    for i, case in enumerate(cases, 1):
        time.sleep(4)  # stay inside the free tier's requests-per-minute limit
        reply = bot.answer(case["q"])
        ok = check(reply, case)
        passed += ok
        say(f"{i:>2}/{len(cases)} {'PASS' if ok else 'FAIL'}  [{case['type']}] {case['q']}\n      → {reply}")
        if bot.last_error:
            say(f"      (error: {bot.last_error})")
            bot.last_error = None
        say()
    say(f"{passed}/{len(cases)} passed")


if __name__ == "__main__":
    main()
