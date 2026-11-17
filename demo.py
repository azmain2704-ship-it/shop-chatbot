"""
Demo mode: a tiny keyword-matching stand-in used when no GEMINI_API_KEY is set.

It is NOT AI. It exists so the app still runs (and the page can be tried) without a key.
The web page shows a "Demo mode" badge whenever this is in use.
"""
import re


class DemoLLM:
    def __init__(self, facts):
        self.facts = facts

    def _lines_with(self, *words):
        found = []
        for line in self.facts.splitlines():
            text = line.strip("- ").strip()
            if text and any(w in line.lower() for w in words):
                found.append(text)
        return found

    def generate(self, system, messages):
        q = messages[-1]["text"].lower()
        if any(w in q for w in ("allerg", "gluten", "nut", "dairy")):
            return ("Allergen information changes daily, so please speak to a member of staff "
                    "before ordering and they'll check for you.")
        if re.search(r"\b(open|close|closing|hours|time|sunday|saturday|today)\b", q):
            return "Our opening hours: " + "; ".join(self._lines_with("monday", "saturday:", "sunday:")) + "."
        if any(w in q for w in ("where", "address", "find you", "station", "located")):
            return "You'll find us at " + self._lines_with("address:")[0].split(":", 1)[1].strip() + "."
        if any(w in q for w in ("vegan", "vegetarian", "plant")):
            return self._lines_with("vegan options")[0].rstrip(".") + "."
        for line in self.facts.splitlines():
            if "£" in line:
                item = line.strip("- ").split(":")[0].lower().split(" (")[0]
                names = [n.strip() for n in re.split(r" or |, | and ", item) if n.strip()]
                if any(n in q for n in names):   # "latte or cappuccino" matches "latte"
                    return line.strip("- ").strip() + "."
        return ("I'm in demo mode, so I can only answer simple questions about hours, prices, "
                "the address and vegan options. Add a Gemini API key for full answers.")
