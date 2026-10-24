from src import config


def chunk_text(text: str, size: int = config.CHUNK_SIZE,
               overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    """Character chunks with overlap; prefers to cut at a paragraph break."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    text = text.strip()
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start + size // 2, end)
            if cut != -1:
                end = cut
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks
