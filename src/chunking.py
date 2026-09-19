from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    # Split *after* a terminal punctuation mark that is followed by whitespace.
    # The lookbehind keeps the punctuation attached to the sentence it ends.
    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def split_sentences(self, text: str) -> list[str]:
        """Return the non-empty sentences of ``text`` with surrounding whitespace removed."""
        if not text or not text.strip():
            return []
        return [s.strip() for s in self._SENTENCE_BOUNDARY.split(text) if s.strip()]

    def chunk(self, text: str) -> list[str]:
        sentences = self.split_sentences(text)
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        return [
            " ".join(sentences[i : i + size])
            for i in range(0, len(sentences), size)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]

    Algorithm:
        1. If the text already fits in chunk_size, return it as one chunk.
        2. Otherwise split on the first separator and greedily merge the
           resulting pieces into chunks that stay within chunk_size.
        3. Any piece that is still too large is split again with the
           remaining separators (recursion).  The empty separator "" means
           "cut by characters", which is the guaranteed base case.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return [c for c in self._split(text, self.separators) if c.strip()]

    # ------------------------------------------------------------------ helpers
    def _hard_split(self, text: str) -> list[str]:
        """Base case: cut by characters when no separator can help."""
        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: already small enough.
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text else []

        # Base case 2: no separators left (or the "" separator) -> character cut.
        if not remaining_separators:
            return self._hard_split(current_text)

        separator, rest = remaining_separators[0], remaining_separators[1:]
        if separator == "":
            return self._hard_split(current_text)

        pieces = current_text.split(separator)
        if len(pieces) == 1:
            # Separator not present: try the next one.
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            if not piece:
                continue
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            # The buffer is full: flush it.
            if buffer:
                chunks.append(buffer)
                buffer = ""

            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                # Piece alone is still too big -> recurse with finer separators.
                chunks.extend(self._split(piece, rest))

        if buffer:
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    @staticmethod
    def _stats(chunks: list[str]) -> dict:
        count = len(chunks)
        avg_length = (sum(len(c) for c in chunks) / count) if count else 0.0
        return {
            "count": count,
            "avg_length": round(avg_length, 1),
            "min_length": min((len(c) for c in chunks), default=0),
            "max_length": max((len(c) for c in chunks), default=0),
            "chunks": chunks,
        }

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        overlap = max(0, min(50, chunk_size // 10))
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        return {name: self._stats(chunker.chunk(text)) for name, chunker in strategies.items()}
