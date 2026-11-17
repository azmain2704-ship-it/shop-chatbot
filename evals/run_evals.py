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

from bot import GeminiLLM, ShopBot, load_facts  # noqa: E402


def check(reply, case):
    text = reply.lower()
    ok_any = any(s.lower() in text for s in case.get("any_of", [])) if case.get("any_of") else True
    ok_none = not any(s.lower() in text for s in case.get("none_of", []))
    return ok_any and ok_none


def main():
    load_dotenv()
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Set GEMINI_API_KEY in .env first. Evals test the real AI.")
    bot = ShopBot(load_facts(), GeminiLLM())
    cases = json.loads(Path(__file__).with_name("questions.json").read_text(encoding="utf-8"))

    passed = 0
    for i, case in enumerate(cases, 1):
        reply = bot.answer(case["q"])
        ok = check(reply, case)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  [{case['type']}] {case['q']}\n      → {reply}\n")
        time.sleep(4)  # stay inside the free tier's requests-per-minute limit
    print(f"{passed}/{len(cases)} passed")


if __name__ == "__main__":
    main()
