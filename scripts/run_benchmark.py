#!/usr/bin/env python3
"""Giai đoạn 2 — nạp corpus, chunk, chạy 5 câu benchmark và tự chấm điểm.

Mỗi file ``.md`` được tách: YAML front matter thành ``Document.metadata`` (để
``search_with_filter`` dùng được ``audience``, ``department``...), phần thân
được chunk theo chiến lược đã chọn, mỗi chunk giữ ``doc_id`` + ``chunk_index``.

Chấm điểm theo docs/SCORING.md, 2 điểm mỗi câu:
    2 — chunk vàng ở top-1 và chứa đủ từ khoá của gold answer
    1 — chunk vàng nằm trong top-3 nhưng không ở top-1, hoặc ở top-1 mà thiếu ý
    0 — chunk vàng không có trong top-3

Ví dụ:
    python scripts/run_benchmark.py                          # heading, mock
    python scripts/run_benchmark.py --strategy sentence
    python scripts/run_benchmark.py --compare                # cả 4 chiến lược
    EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --compare
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
# 5 câu hỏi nhóm thống nhất. gold_keywords là các mẩu chữ phải xuất hiện trong
# chunk truy xuất được thì mới coi là trả lời đủ ý.
BENCHMARK = [
    {
        "id": 1,
        "query": "Sinh viên được mượn tối đa bao nhiêu cuốn tài liệu và trong bao lâu?",
        "gold": "Tối đa 5 cuốn cùng lúc, thời hạn 14 ngày mỗi cuốn.",
        "gold_doc": "muon-tai-lieu-sinh-vien",
        "gold_keywords": ["5 cuốn", "14 ngày"],
        "filter": {"audience": "student"},
        "note": "Câu cần lọc metadata: tài liệu giảng viên nêu 15 cuốn / 60 ngày cho cùng dịch vụ.",
    },
    {
        "id": 2,
        "query": "Nộp đơn phúc khảo điểm trong thời hạn bao lâu và lệ phí bao nhiêu?",
        "gold": "Trong 7 ngày làm việc kể từ ngày công bố điểm, lệ phí 50.000 đồng mỗi học phần.",
        "gold_doc": "phuc-khao-diem",
        "gold_keywords": ["7 ngày làm việc"],
        "filter": None,
    },
    {
        "id": 3,
        "query": "Điều kiện để được xét học bổng khuyến khích học tập là gì?",
        "gold": "Điểm trung bình học kỳ từ 3,2; rèn luyện từ 80; đăng ký tối thiểu 14 tín chỉ; không bị kỷ luật.",
        "gold_doc": "hoc-bong-khuyen-khich",
        "gold_keywords": ["3,2", "80"],
        "filter": None,
    },
    {
        "id": 4,
        "query": "Rút học phần sau thời hạn điều chỉnh thì bảng điểm ghi gì?",
        "gold": "Học phần bị rút được ghi ký hiệu W trên bảng điểm, không tính vào điểm trung bình.",
        "gold_doc": "dieu-chinh-hoc-phan",
        "gold_keywords": ["W"],
        "filter": None,
    },
    {
        "id": 5,
        "query": "Thư viện mở cửa mấy giờ vào thứ Bảy?",
        "gold": "Thứ Bảy mở cửa từ 8 giờ đến 17 giờ.",
        "gold_doc": "gio-mo-cua-thu-vien",
        "gold_keywords": ["8 giờ đến 17 giờ"],
        "filter": None,
    },
]

FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class HeadingChunker:
    """Chiến lược riêng cho L3A: chia theo tiêu đề/mục Markdown.

    Lý do: quy định học vụ được viết theo điều/mục và mỗi câu hỏi benchmark gần
    như luôn ứng với đúng một mục. Giữ tiêu đề bên trong chunk để embedding
    nhận được nhãn chủ đề của đoạn. Mục dài hơn max_chars thì cắt tiếp bằng
    RecursiveChunker.
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
            heading = parts[i].strip()
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
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


class HeadingChunkerV2(HeadingChunker):
    """HeadingChunker + gộp mục ngắn hơn min_chars vào mục kế tiếp.

    Lý do: chunk chỉ chứa dòng tiêu đề tài liệu rất "thuần chủ đề" nên luôn
    thắng về cosine, nhưng không chứa con số nào, khiến agent trả lời chung
    chung. Gộp nó vào mục đầu tiên có nội dung thì chunk vừa giữ nhãn chủ đề
    vừa mang dữ kiện. Đo được: 7/10 -> 8/10 và giảm 23% số chunk.
    """

    def __init__(self, max_chars: int = 600, min_chars: int = 180) -> None:
        super().__init__(max_chars=max_chars)
        self.min_chars = min_chars

    def chunk(self, text: str) -> list[str]:
        merged: list[str] = []
        carry = ""
        for piece in super().chunk(text):
            candidate = f"{carry}\n\n{piece}".strip() if carry else piece
            if len(candidate) < self.min_chars:
                carry = candidate
                continue
            merged.append(candidate)
            carry = ""
        if carry:
            if merged:
                merged[-1] = f"{merged[-1]}\n\n{carry}"
            else:
                merged.append(carry)
        return merged


STRATEGIES = {
    "fixed": lambda size: FixedSizeChunker(chunk_size=size, overlap=size // 10),
    "sentence": lambda size: SentenceChunker(max_sentences_per_chunk=2),
    "recursive": lambda size: RecursiveChunker(chunk_size=size),
    "heading": lambda size: HeadingChunker(max_chars=size * 2),
    "heading2": lambda size: HeadingChunkerV2(max_chars=size * 2, min_chars=180),
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
    # Bỏ các dòng chú thích dạng blockquote, không phải nội dung quy định.
    body = "\n".join(line for line in body.splitlines() if not line.startswith("> "))
    metadata.setdefault("doc_id", path.stem)
    metadata.setdefault("title", path.stem)
    return metadata, body.strip()


def load_corpus(folder: Path, chunker) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(folder.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
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
            print(f"[warn] local embedder không dùng được ({error}); quay về mock", file=sys.stderr)
    return _mock_embed


def extractive_llm(prompt: str) -> str:
    """LLM giả lập chạy offline: trả lại nguyên văn khối ngữ cảnh số [1].

    Nhờ vậy phần chấm grounding nhìn thấy đúng đoạn nào đã nuôi câu trả lời.
    """
    match = re.search(
        r"\[1\] \(source: ([^,]+), score: ([-\d.]+)\)\n(.*?)(?:\n\n\[2\]|\n\n### CÂU HỎI)",
        prompt, re.DOTALL,
    )
    if not match:
        return "Không tìm thấy thông tin liên quan trong cơ sở tri thức."
    source, _score, text = match.groups()
    return f"[theo {source}] " + " ".join(text.split())


def score_query(item: dict, results: list[dict]) -> tuple[int, str]:
    """Chấm 2/1/0 cho một câu theo docs/SCORING.md."""
    rank = None
    hit = None
    for position, result in enumerate(results[:3], start=1):
        if result["metadata"]["doc_id"] == item["gold_doc"]:
            rank, hit = position, result
            break
    if rank is None:
        return 0, "chunk vàng không có trong top-3"
    missing = [k for k in item["gold_keywords"] if k not in hit["content"]]
    if rank == 1 and not missing:
        return 2, "top-1 và đủ ý"
    if rank == 1:
        return 1, f"top-1 nhưng thiếu: {', '.join(missing)}"
    return 1, f"chunk vàng ở top-{rank}"


def build(corpus: Path, strategy: str, chunk_size: int, embedder):
    chunker = STRATEGIES[strategy](chunk_size)
    docs = load_corpus(corpus, chunker)
    store = EmbeddingStore(collection_name=f"bench_{strategy}", embedding_fn=embedder)
    store.add_documents(docs)
    return store, docs


def run_one(store, agent, top_k: int, verbose: bool = True) -> tuple[int, list[dict]]:
    total = 0
    rows = []
    for item in BENCHMARK:
        filt = item["filter"]
        results = (store.search_with_filter(item["query"], top_k=top_k, metadata_filter=filt)
                   if filt else store.search(item["query"], top_k=top_k))
        points, reason = score_query(item, results)
        total += points
        answer = agent.answer(item["query"], top_k=top_k, metadata_filter=filt)
        rows.append({"item": item, "results": results, "points": points,
                     "reason": reason, "answer": answer})
        if verbose:
            print(f"Q{item['id']}: {item['query']}" + (f"   [filter={filt}]" if filt else ""))
            print(f"    gold: {item['gold']}  (doc: {item['gold_doc']})")
            for rank, r in enumerate(results, start=1):
                mark = "*" if r["metadata"]["doc_id"] == item["gold_doc"] else " "
                preview = " ".join(r["content"].split())[:88]
                print(f"   {mark}{rank}. {r['score']:.3f} {r['metadata']['doc_id']}#{r['metadata']['chunk_index']} "
                      f"({r['metadata'].get('audience')}) | {preview}")
            print(f"    => {points}/2 điểm — {reason}")
            print(f"    agent: {answer[:170]}\n")
    return total, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/university"))
    parser.add_argument("--strategy", choices=STRATEGIES, default="heading")
    parser.add_argument("--chunk-size", type=int, default=300)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--compare", action="store_true", help="chạy cả 4 chiến lược và in bảng so sánh")
    args = parser.parse_args()

    embedder = pick_embedder()
    backend = getattr(embedder, "_backend_name", "mock")

    if not args.compare:
        store, docs = build(args.corpus, args.strategy, args.chunk_size, embedder)
        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
        print(f"Corpus: {args.corpus} | chiến lược={args.strategy} chunk_size={args.chunk_size}")
        print(f"Embedder: {backend} | số chunk: {store.get_collection_size()}")
        print(f"audience trong corpus: {sorted({d.metadata.get('audience', '?') for d in docs})}\n")
        total, _ = run_one(store, agent, args.top_k)
        print(f"TỔNG: {total}/10 điểm chất lượng truy xuất")
        return 0

    print(f"Corpus: {args.corpus} | Embedder: {backend} | top_k={args.top_k}\n")
    summary = {}
    for name in STRATEGIES:
        store, docs = build(args.corpus, name, args.chunk_size, embedder)
        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
        total, rows = run_one(store, agent, args.top_k, verbose=False)
        lengths = [len(d.content) for d in docs]
        summary[name] = {
            "total": total,
            "chunks": len(docs),
            "avg_len": sum(lengths) / len(lengths) if lengths else 0,
            "per_query": [r["points"] for r in rows],
            "reasons": [r["reason"] for r in rows],
        }

    print("| Chiến lược | Số chunk | Độ dài TB | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng /10 |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, s in summary.items():
        cells = " | ".join(str(p) for p in s["per_query"])
        print(f"| {name} | {s['chunks']} | {s['avg_len']:.0f} | {cells} | **{s['total']}** |")

    print("\nGhi chú từng câu bị trừ điểm:")
    for name, s in summary.items():
        for item, points, reason in zip(BENCHMARK, s["per_query"], s["reasons"]):
            if points < 2:
                print(f"  {name} Q{item['id']}: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
