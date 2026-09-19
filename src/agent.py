from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    NO_CONTEXT_MESSAGE = "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn
        self.last_context: list[dict] = []

    def build_prompt(self, question: str, chunks: list[dict]) -> str:
        """Assemble a grounded prompt: numbered context blocks + the question."""
        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            meta = chunk.get("metadata", {}) or {}
            source = meta.get("doc_id") or meta.get("source") or "unknown"
            context_blocks.append(
                f"[{index}] (source: {source}, score: {chunk.get('score', 0.0):.3f})\n{chunk['content']}"
            )
        context = "\n\n".join(context_blocks)
        return (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Chỉ dùng thông tin trong phần NGỮ CẢNH bên dưới. Nếu ngữ cảnh không đủ, "
            "hãy nói rõ là không tìm thấy thông tin thay vì suy đoán. "
            "Khi trả lời, hãy trích dẫn số thứ tự [n] của đoạn đã dùng.\n\n"
            f"### NGỮ CẢNH\n{context}\n\n"
            f"### CÂU HỎI\n{question}\n\n"
            "### TRẢ LỜI\n"
        )

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        if metadata_filter:
            chunks = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            chunks = self.store.search(question, top_k=top_k)
        self.last_context = chunks

        if not chunks:
            return self.NO_CONTEXT_MESSAGE

        prompt = self.build_prompt(question, chunks)
        return self.llm_fn(prompt)
