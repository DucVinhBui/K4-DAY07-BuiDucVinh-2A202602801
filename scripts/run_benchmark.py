#!/usr/bin/env python3
"""Phase 2 helper — load a corpus folder, chunk it, run the 5 benchmark queries.

Each ``.md`` file is parsed: the YAML front matter becomes ``Document.metadata``
(so ``search_with_filter`` can use ``audience``, ``department``...), the body is
chunked with the chosen strategy, and every chunk keeps ``doc_id`` + ``title``.

Usage:
    python scripts/run_benchmark.py                          # data/university, recursive, mock
    python scripts/run_benchmark.py --corpus data/university --strategy sentence --top-k 3
    EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --strategy recursive
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import (  # noqa: E402
    LOCAL_EMBEDDING_MODEL,
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)

# ---------------------------------------------------------------- benchmark set
# Group-agreed 5 queries. Edit here once the group finalises the corpus.
# metadata_filter=None means plain search().
BENCHMARK = [
    {"query": "Sinh viên đăng ký học phần ở đâu và theo lịch nào?",
     "gold": "Trong cổng học vụ, theo lịch của từng học kỳ.",
     "filter": None},
    {"query": "Học phần tiên quyết là gì và sinh viên cần làm gì trước khi đăng ký?",
     "gold": "Kiểm tra điều kiện tiên quyết trước khi xác nhận đăng ký.",
     "filter": None},
    {"query": "Nếu bị trùng lịch học thì sinh viên xử lý thế nào?",
     "gold": "Điều chỉnh lớp học phần trước thời hạn điều chỉnh được công bố.",
     "filter": {"audience": "student"}},
    {"query": "Cần mang gì khi mượn tài liệu ở thư viện?",
     "gold": "Thẻ định danh hợp lệ.",
     "filter": None},
    {"query": "Yêu cầu ngoại lệ về đăng ký học phần gửi qua đâu?",
     "gold": "Qua kênh hỗ trợ học vụ chính thức.",
     "filter": {"audience": "student"}},
]

FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class HeadingChunker:
    """Custom L3A strategy: split a handbook/regulation on Markdown headings.

    Rationale: university regulations are organised by article/section, and a
    benchmark question almost always maps to exactly one section. Keeping the
    heading inside the chunk preserves the topic label for the embedder.
    Sections longer than ``max_chars`` fall back to RecursiveChunker.
    """

    HEADING = re.compile(r"^(#{1,6} .*)$", re.MULTILINE)

    def __init__(self, max_chars: int = 600) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        parts = self.HEADING.split(text)
        sections: list[str] = []
        buffer = parts[0].strip()
        for i in range(1, len(parts), 2):
            if buffer:
                sections.append(buffer)
            heading, body = parts[i].strip(), parts[i + 1].strip() if i + 1 < len(parts) else ""
            buffer = f"{heading}\n{body}".strip()
        if buffer:
            sections.append(buffer)

        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.max_chars:
                chunks.append(section)
            else:
                chunks.extend(self._fallback.chunk(section))
        return [c for c in chunks if c.strip()]


STRATEGIES = {
    "fixed": lambda size: FixedSizeChunker(chunk_size=size, overlap=size // 10),
    "sentence": lambda size: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda size: RecursiveChunker(chunk_size=size),
    "heading": lambda size: HeadingChunker(max_chars=size),
}


def parse_markdown(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    metadata: dict = {}
    match = FRONT_MATTER.match(raw)
    body = raw
    if match:
        for line in match.group(1).splitlines():
            if ":" not in line or line.strip().startswith("#"):
                continue
            key, value = line.split(":", 1)
            value = value.split(" #", 1)[0].strip().strip('"').strip("'")
            metadata[key.strip()] = value
        body = raw[match.end():]
    # Drop template call-out lines (blockquotes) that are not real content.
    body = "\n".join(line for line in body.splitlines() if not line.startswith("> "))
    metadata.setdefault("doc_id", path.stem)
    metadata.setdefault("title", path.stem)
    return metadata, body.strip()


def load_corpus(folder: Path, chunker) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(folder.glob("*.md")) + sorted(folder.glob("*.txt")):
        metadata, body = parse_markdown(path)
        for index, chunk in enumerate(chunker.chunk(body)):
            docs.append(Document(
                id=metadata["doc_id"],
                content=chunk,
                metadata={**metadata, "chunk_index": index, "source": str(path)},
            ))
    return docs


def pick_embedder():
    if os.getenv("EMBEDDING_PROVIDER", "mock").lower() == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as error:  # pragma: no cover
            print(f"[warn] local embedder unavailable ({error}); using mock", file=sys.stderr)
    return _mock_embed


def extractive_llm(prompt: str) -> str:
    """Offline stand-in for an LLM: echo the top context block so grounding is visible."""
    match = re.search(r"\[1\] \(source: ([^,]+), score: ([-\d.]+)\)\n(.*?)(?:\n\n\[2\]|\n\n### CÂU HỎI)", prompt, re.DOTALL)
    if not match:
        return "(no context)"
    source, score, text = match.groups()
    return f"[theo {source}] " + " ".join(text.split())[:160]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/university"))
    parser.add_argument("--strategy", choices=STRATEGIES, default="recursive")
    parser.add_argument("--chunk-size", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    embedder = pick_embedder()
    chunker = STRATEGIES[args.strategy](args.chunk_size)
    docs = load_corpus(args.corpus, chunker)
    store = EmbeddingStore(collection_name="benchmark", embedding_fn=embedder)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

    print(f"Corpus: {args.corpus}  | strategy={args.strategy} chunk_size={args.chunk_size}")
    print(f"Embedder: {getattr(embedder, '_backend_name', 'mock')}  | chunks stored: {store.get_collection_size()}")
    audiences = sorted({d.metadata.get('audience', '?') for d in docs})
    print(f"audience values in corpus: {audiences}\n")

    for number, item in enumerate(BENCHMARK, start=1):
        filt = item["filter"]
        results = (store.search_with_filter(item["query"], top_k=args.top_k, metadata_filter=filt)
                   if filt else store.search(item["query"], top_k=args.top_k))
        print(f"Q{number}: {item['query']}" + (f"   [filter={filt}]" if filt else ""))
        print(f"    gold: {item['gold']}")
        for rank, r in enumerate(results, start=1):
            preview = " ".join(r["content"].split())[:100]
            print(f"    {rank}. score={r['score']:.3f} doc={r['metadata']['doc_id']}#{r['metadata']['chunk_index']} "
                  f"audience={r['metadata'].get('audience')} | {preview}")
        print(f"    agent: {agent.answer(item['query'], top_k=args.top_k, metadata_filter=filt)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
