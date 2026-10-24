from pathlib import Path

from pypdf import PdfReader


def load_pages(path: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...]. Markdown/TXT count as a single page."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
    if suffix in {".md", ".txt"}:
        return [(1, path.read_text(encoding="utf-8"))]
    return []
