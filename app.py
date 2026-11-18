"""Web chat page:  python app.py   then open http://127.0.0.1:5000"""
import os
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from bot import GeminiLLM, ShopBot, load_facts, shop_name
from demo import DemoLLM

RATE_LIMIT = 10        # messages...
RATE_WINDOW = 60       # ...per 60 seconds, per visitor (protects the free API quota)


def create_app(llm=None, facts=None):
    load_dotenv()
    facts = facts or load_facts()
    demo_mode = False
    if llm is None:
        if os.environ.get("GEMINI_API_KEY"):
            llm = GeminiLLM()
        else:
            llm, demo_mode = DemoLLM(facts), True

    bot = ShopBot(facts, llm)
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024
    if os.environ.get("RENDER"):
        # Behind Render's proxy every request comes from the proxy's address, so the rate limit would be shared by
        # everyone. ProxyFix reads the visitor's real address from the X-Forwarded-For header Render adds.
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    recent = defaultdict(deque)

    def rate_limited(key):
        now = time.monotonic()
        hits = recent[key]
        while hits and now - hits[0] > RATE_WINDOW:
            hits.popleft()
        if len(hits) >= RATE_LIMIT:
            return True
        hits.append(now)
        return False

    @app.get("/")
    def index():
        return render_template("index.html", shop=shop_name(facts), demo_mode=demo_mode)

    @app.post("/api/chat")
    def chat():
        data = request.get_json(silent=True) or {}
        message = data.get("message")
        if not isinstance(message, str):
            return jsonify(error="Send JSON like {\"message\": \"...\"}"), 400
        if rate_limited(request.remote_addr or "unknown"):
            return jsonify(reply="You're sending messages quite fast. Please wait a moment and try again."), 429
        return jsonify(reply=bot.answer(message, data.get("history")))

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
