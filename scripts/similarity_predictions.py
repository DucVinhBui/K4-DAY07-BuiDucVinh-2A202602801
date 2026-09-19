#!/usr/bin/env python3
"""Exercise 3.3 — predict cosine similarity for 5 sentence pairs, then measure.

Usage:
    python scripts/similarity_predictions.py            # mock embedder (deterministic hash)
    EMBEDDING_PROVIDER=local python scripts/similarity_predictions.py
    LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
        EMBEDDING_PROVIDER=local python scripts/similarity_predictions.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import LOCAL_EMBEDDING_MODEL, LocalEmbedder, _mock_embed, compute_similarity  # noqa: E402

PAIRS = [
    ("cao",  "Sinh viên phải đăng ký học phần trước hạn chót của học kỳ.",
             "Hạn cuối để sinh viên đăng ký môn học là trước khi học kỳ bắt đầu."),
    ("cao",  "Thư viện cho phép mượn tối đa 5 cuốn sách trong 14 ngày.",
             "Mỗi người đọc được mượn 5 quyển, thời hạn hai tuần."),
    ("thấp", "Sinh viên nộp đơn phúc khảo trong vòng 7 ngày sau khi công bố điểm.",
             "Ký túc xá đóng cửa lúc 23 giờ mỗi ngày."),
    ("thấp", "Học bổng khuyến khích học tập xét theo điểm trung bình học kỳ.",
             "Món phở bò ngon nhất là ở Hà Nội."),
    ("bẫy",  "Học phí học kỳ này tăng 10% so với năm ngoái.",
             "Học phí học kỳ này giảm 10% so với năm ngoái."),
]


def pick_embedder():
    provider = os.getenv("EMBEDDING_PROVIDER", "mock").lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as error:  # pragma: no cover - depends on local setup
            print(f"[warn] local embedder unavailable ({error}); falling back to mock", file=sys.stderr)
    return _mock_embed


def main() -> None:
    embedder = pick_embedder()
    print(f"Embedding backend: {getattr(embedder, '_backend_name', 'mock')}\n")
    print("| Cặp | Dự đoán | Câu A | Câu B | Cosine |")
    print("|---|---|---|---|---|")
    for index, (prediction, a, b) in enumerate(PAIRS, start=1):
        score = compute_similarity(embedder(a), embedder(b))
        print(f"| {index} | {prediction} | {a} | {b} | {score:.3f} |")


if __name__ == "__main__":
    main()
