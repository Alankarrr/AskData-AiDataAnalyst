import pytest

from src.rag.chunking import chunk_text


def test_chunks_cover_text_and_respect_size():
    text = "word " * 1000
    chunks = chunk_text(text, size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)


def test_short_text_single_chunk():
    assert chunk_text("hello world") == ["hello world"]


def test_empty_text():
    assert chunk_text("   ") == []


def test_bad_overlap():
    with pytest.raises(ValueError):
        chunk_text("abc", size=10, overlap=10)
