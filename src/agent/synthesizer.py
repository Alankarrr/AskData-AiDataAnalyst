from src import config


def format_passages(passages: list[dict]) -> str:
    if not passages:
        return "(no documents retrieved)"
    return "\n\n".join(
        f"<document>\nSOURCE: {p['source']}, page {p['page']}\n{p['text']}\n</document>"
        for p in passages)


def format_table(df) -> str:
    if df is None:
        return "(no database query was run)"
    if df.empty:
        return "(query returned 0 rows)"
    note = f"\n(showing first 50 of {len(df)} rows)" if len(df) > 50 else ""
    return df.head(50).to_csv(index=False) + note


def synthesize(state: dict, llm) -> str:
    question = state.get("standalone") or state["question"]
    if state.get("route") == "CHAT":
        return llm.generate(question, system=config.read_prompt("chat.txt"))
    notes = state.get("error") or "none"
    prompt = (config.read_prompt("synthesis.txt")
              .replace("{question}", question)
              .replace("{table_text}", format_table(state.get("table")))
              .replace("{passages}", format_passages(state.get("passages", [])))
              .replace("{notes}", notes))
    return llm.generate(prompt)
