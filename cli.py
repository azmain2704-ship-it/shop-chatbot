"""Chat with the bot in the terminal:  python cli.py   (type 'quit' to stop)"""
import os

from dotenv import load_dotenv

from bot import GeminiLLM, ShopBot, load_facts
from demo import DemoLLM


def main():
    load_dotenv()
    facts = load_facts()
    if os.environ.get("GEMINI_API_KEY"):
        llm = GeminiLLM()
        print(f"Using Gemini ({llm.model}).")
    else:
        llm = DemoLLM(facts)
        print("No GEMINI_API_KEY found, so running in DEMO MODE (keyword matching, not AI).")
    bot = ShopBot(facts, llm)
    history = []
    print("Ask about the shop. Type 'quit' to exit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in ("quit", "exit"):
            break
        reply = bot.answer(question, history)
        print(f"Bot: {reply}\n")
        history += [{"role": "user", "text": question}, {"role": "assistant", "text": reply}]


if __name__ == "__main__":
    main()
