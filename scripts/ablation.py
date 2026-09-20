#!/usr/bin/env python3
"""Hai thí nghiệm đối chứng cho báo cáo nhóm.

A. Lọc metadata có giúp không: chạy Q1 có lọc và không lọc.
B. Sửa lỗi "chunk tiêu đề thắng chunk chứa đáp án": HeadingChunkerV2 gộp mục
   quá ngắn vào mục kế tiếp, so điểm với HeadingChunker gốc.

    EMBEDDING_PROVIDER=local python scripts/ablation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import EmbeddingStore, KnowledgeBaseAgent  # noqa: E402
from scripts.run_benchmark import (  # noqa: E402
    BENCHMARK, HeadingChunker, HeadingChunkerV2, build, extractive_llm,
    load_corpus, pick_embedder, run_one, score_query,
)

CORPUS = Path("data/university")


def experiment_a(embedder) -> None:
    print("=== A. Lọc metadata trên Q1 ===")
    item = next(i for i in BENCHMARK if i["id"] == 1)
    store, _ = build(CORPUS, "heading", 300, embedder)
    for label, filt in [("KHÔNG lọc", None), ("CÓ lọc audience=student", item["filter"])]:
        results = (store.search_with_filter(item["query"], top_k=3, metadata_filter=filt)
                   if filt else store.search(item["query"], top_k=3))
        points, reason = score_query(item, results)
        print(f"\n  {label} -> {points}/2 ({reason})")
        for rank, r in enumerate(results, start=1):
            mark = "*" if r["metadata"]["doc_id"] == item["gold_doc"] else " "
            print(f"   {mark}{rank}. {r['score']:.3f} {r['metadata']['doc_id']}#{r['metadata']['chunk_index']} "
                  f"({r['metadata'].get('audience')}) | {' '.join(r['content'].split())[:80]}")


def experiment_b(embedder) -> None:
    print("\n\n=== B. HeadingChunker gốc vs V2 (gộp mục ngắn) ===")
    for label, chunker in [("heading gốc", HeadingChunker(max_chars=600)),
                           ("heading V2  ", HeadingChunkerV2(max_chars=600, min_chars=180))]:
        docs = load_corpus(CORPUS, chunker)
        store = EmbeddingStore(collection_name="ablation", embedding_fn=embedder)
        store.add_documents(docs)
        agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
        total, rows = run_one(store, agent, 3, verbose=False)
        per_query = " ".join(f"Q{r['item']['id']}={r['points']}" for r in rows)
        avg = sum(len(d.content) for d in docs) / len(docs)
        print(f"  {label}: {total}/10  ({per_query})  chunks={len(docs)} avg_len={avg:.0f}")
        for r in rows:
            if r["points"] < 2:
                print(f"      Q{r['item']['id']}: {r['reason']}")


def main() -> int:
    embedder = pick_embedder()
    print(f"Embedder: {getattr(embedder, '_backend_name', 'mock')}\n")
    experiment_a(embedder)
    experiment_b(embedder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
