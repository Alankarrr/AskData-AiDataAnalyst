import hashlib

_CACHE: dict[str, dict] = {}


def _key(question: str) -> str:
    return hashlib.sha256(" ".join(question.lower().split()).encode()).hexdigest()


def get(question: str):
    return _CACHE.get(_key(question))


def put(question: str, value: dict) -> None:
    _CACHE[_key(question)] = value


def clear() -> None:
    _CACHE.clear()
