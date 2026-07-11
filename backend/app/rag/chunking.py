def chunk_text(text: str, *, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits text into overlapping chunks of at most `chunk_size`
    characters, breaking only on word boundaries (BE5.1). Chunk N+1 starts
    with roughly the trailing `overlap` characters of chunk N, so a
    similarity match that lands near a chunk boundary doesn't lose the
    surrounding context entirely.

    Deterministic and side-effect free -- `chunk_index` is the caller's
    concern (enumerate the returned list), not this function's.
    """
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    words = normalized.split(" ")
    chunks: list[str] = []
    start = 0
    while start < len(words):
        current: list[str] = []
        length = 0
        end = start
        while end < len(words):
            word = words[end]
            added = len(word) + (1 if current else 0)
            if current and length + added > chunk_size:
                break
            current.append(word)
            length += added
            end += 1
        chunks.append(" ".join(current))

        if end >= len(words):
            break

        # How many trailing words of this chunk make up ~overlap chars --
        # the next chunk resumes from there instead of at `end`.
        overlap_len = 0
        overlap_word_count = 0
        for word in reversed(current):
            added = len(word) + (1 if overlap_word_count else 0)
            if overlap_len + added > overlap:
                break
            overlap_len += added
            overlap_word_count += 1
        start = end - overlap_word_count

    return chunks
