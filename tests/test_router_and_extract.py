from src.agent.router import classify
from src.sql.generator import extract_sql


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply

    def generate(self, prompt, system="", temperature=0.0):
        return self.reply


def test_extract_sql_from_fence():
    assert extract_sql("```sql\nSELECT 1;\n```") == "SELECT 1"


def test_extract_sql_plain():
    assert extract_sql("SELECT 2;") == "SELECT 2"


def test_router_parses_word():
    assert classify("hi", FakeLLM("chat")) == "CHAT"
    assert classify("x", FakeLLM("The answer is: DOCS")) == "DOCS"


def test_router_falls_back_to_both():
    assert classify("x", FakeLLM("no idea")) == "BOTH"
