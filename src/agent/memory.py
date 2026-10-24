from src import config


def condense(question: str, history: list[dict], llm) -> str:
    """Rewrite a follow-up as a standalone question. Skipped when there is no history."""
    if not history:
        return question
    convo = "\n".join(f"{t['role'].upper()}: {t['content'][:500]}" for t in history[-6:])
    prompt = f"Conversation:\n{convo}\n\nLast question: {question}"
    out = llm.generate(prompt, system=config.read_prompt("condense.txt")).strip()
    return out or question
