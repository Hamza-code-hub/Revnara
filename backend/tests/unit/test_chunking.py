import pytest

from app.rag.chunking import chunk_text


def test_short_text_is_a_single_chunk() -> None:
    assert chunk_text("hello world") == ["hello world"]


def test_empty_text_produces_no_chunks() -> None:
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_chunk_boundaries_never_split_a_word() -> None:
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 50
        # Every chunk is a clean set of whole words -- reconstructible by
        # splitting on whitespace with nothing left over.
        assert chunk == " ".join(chunk.split())


def test_consecutive_chunks_overlap() -> None:
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_text(text, chunk_size=50, overlap=20)

    first_words = set(chunks[0].split())
    second_words = set(chunks[1].split())
    assert first_words & second_words, "expected some overlap between consecutive chunks"


def test_known_input_produces_expected_chunk_count() -> None:
    # 10 five-char "wordN" tokens (N=0..9) joined by single spaces: each
    # "word" is 5 chars, so 10 of them plus 9 separators is a known,
    # hand-countable length -- chunk_size=12 fits at most 2 words per
    # chunk (5 + 1 + 5 = 11 <= 12, adding a 3rd would be 17 > 12).
    text = " ".join(f"word{i}" for i in range(10))
    chunks = chunk_text(text, chunk_size=12, overlap=0)

    assert len(chunks) == 5
    assert chunks[0] == "word0 word1"
    assert chunks[-1] == "word8 word9"


def test_overlap_must_be_smaller_than_chunk_size() -> None:
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=10, overlap=10)


def test_a_single_word_longer_than_chunk_size_does_not_infinite_loop() -> None:
    text = "a" * 500
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert chunks == ["a" * 500]


def test_whitespace_is_normalized() -> None:
    assert chunk_text("hello   \n\n  world") == ["hello world"]
