"""One wrapper that serves any OpenAI-compatible endpoint (Groq, Gemini, Ollama, OpenAI...)."""
import time
from functools import lru_cache

from openai import OpenAI

from src import config
from src.llm.base import LLM


class OpenAICompatLLM(LLM):
    def __init__(self, model: str, base_url: str | None = None,
                 api_key: str | None = None, retries: int = 3):
        self.client = OpenAI(base_url=base_url, api_key=api_key or "missing-key")
        self.model = model
        self.retries = retries
        self.total_tokens = 0  # running usage counter, handy for logging

    def generate(self, prompt: str, system: str = "", temperature: float = 0.0) -> str:
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        last_err: Exception | None = None
        for attempt in range(self.retries):
            try:
                r = self.client.chat.completions.create(
                    model=self.model, messages=msgs, temperature=temperature)
                if r.usage:
                    self.total_tokens += r.usage.total_tokens or 0
                return r.choices[0].message.content or ""
            except Exception as e:  # rate limit, network, etc.
                last_err = e
                time.sleep(2 ** attempt)
        raise RuntimeError(f"LLM call failed after {self.retries} attempts: {last_err}")


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    return OpenAICompatLLM(config.LLM_MODEL, config.LLM_BASE_URL, config.LLM_API_KEY)
