"""Quick command-line demo.  Run: python -m scripts.cli"""
from src.agent.graph import ask

if __name__ == "__main__":
    history: list[dict] = []
    while (q := input("\nAsk> ").strip()) not in {"", "exit", "quit"}:
        out = ask(q, history)
        print("\nROUTE:", out.get("route"))
        if out.get("sql"):
            print("SQL:", out["sql"])
        if out.get("error"):
            print("\nERROR DETAILS:", out["error"])
        print("\n" + out["answer"])
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": out["answer"]}]
