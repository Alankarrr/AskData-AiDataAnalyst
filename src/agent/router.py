import re

from src import config

VALID = {"SQL", "DOCS", "BOTH", "CHAT"}


def classify(question: str, llm) -> str:
    raw = llm.generate(question, system=config.read_prompt("router.txt")).upper()
    for tok in re.findall(r"[A-Z]+", raw):
        if tok in VALID:
            return tok
    return "BOTH"  # safest fallback: use all evidence
