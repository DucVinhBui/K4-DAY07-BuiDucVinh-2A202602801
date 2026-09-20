# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Bùi Đức Vinh (2A202602801)
**Nhóm:** [Tên nhóm — điền sau khi chốt]
**Ngày:** 2026-09-19

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding "chỉ cùng một hướng" trong không gian ngữ nghĩa, tức là mô hình cho rằng hai đoạn văn bản nói về cùng một chủ đề/ý, bất kể độ dài của chúng. Giá trị 1.0 là trùng hướng hoàn toàn, 0 là không liên quan, âm là ngược hướng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Sinh viên phải đăng ký học phần trước hạn chót của học kỳ."
- Câu B: "Hạn cuối để sinh viên đăng ký môn học là trước khi học kỳ bắt đầu."
- Tại sao tương đồng: cùng chủ thể (sinh viên), cùng hành động (đăng ký học phần/môn học), cùng ràng buộc thời gian (hạn chót); chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Học bổng khuyến khích học tập xét theo điểm trung bình học kỳ."
- Câu B: "Món phở bò ngon nhất là ở Hà Nội."
- Tại sao khác: không chung chủ đề, chủ thể hay từ vựng; một câu về học vụ, một câu về ẩm thực.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ so sánh *hướng* của vector nên không bị ảnh hưởng bởi độ lớn (magnitude), trong khi độ lớn của embedding thường phụ thuộc vào độ dài văn bản hoặc tần suất từ chứ không phải ý nghĩa. Với vector đã chuẩn hoá (norm = 1), cosine chính là tích vô hướng nên tính rất rẻ, và đó là cách `EmbeddingStore.search` của tôi xếp hạng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Bước tiến mỗi chunk = 500 − 50 = 450 ký tự.
> Số chunk = ceil((10000 − 50) / 450) = ceil(22.11) = **23 chunks**.
> Kiểm chứng bằng `FixedSizeChunker(500, 50).chunk("a" * 10000)` cũng trả về 23.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Bước tiến giảm còn 400 nên số chunk = ceil(9900 / 400) = **25 chunks** (tăng 2). Overlap lớn hơn giúp một câu hoặc một ý bị cắt ở ranh giới chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, giảm rủi ro mất ngữ cảnh khi truy xuất; đổi lại tốn thêm bộ nhớ và chi phí embedding vì nội dung bị lưu lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` — tách tại khoảng trắng đứng *sau* dấu `.`, `!`, `?` (lookbehind) nên dấu câu vẫn nằm lại cuối câu và cả trường hợp `.\n` cũng được xử lý vì `\s` bao gồm xuống dòng. Sau khi tách, tôi `strip()` từng câu, loại câu rỗng, rồi gom mỗi `max_sentences_per_chunk` câu thành một chunk nối bằng khoảng trắng. Edge case: văn bản rỗng/chỉ có khoảng trắng trả về `[]`; `max_sentences_per_chunk < 1` được ép về 1 trong `__init__`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split(text, separators)` có hai base case: (1) text đã ≤ `chunk_size` thì trả về nguyên; (2) hết separator hoặc gặp separator rỗng `""` thì cắt cứng theo ký tự. Ngược lại nó tách theo separator đầu tiên, rồi **gom tham lam** (greedy merge) các mảnh lại sao cho chunk không vượt `chunk_size`; mảnh nào một mình vẫn quá lớn thì gọi đệ quy với các separator còn lại (mịn hơn). Nếu separator không xuất hiện trong text thì bỏ qua và thử separator kế tiếp. Nhờ đó `"word " * 200` với `chunk_size=100` cho 10 chunk 99 ký tự, và `separators=[]` vẫn chạy nhờ fallback cắt ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được `_make_record` chuyển thành dict `{id, doc_id, content, metadata, embedding}`; `doc_id` luôn được ghi vào metadata để sau này xoá theo tài liệu. Danh sách `self._store` là nguồn sự thật; nếu `chromadb` cài được thì record được mirror sang collection (metadata chỉ giữ giá trị scalar theo yêu cầu của Chroma) nhưng xếp hạng vẫn làm tại chỗ. `search` nhúng câu hỏi rồi tính `_dot(query, embedding)` với từng record — vì các embedder đều chuẩn hoá vector nên dot product chính là cosine — sắp xếp giảm dần và cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi **lọc trước, tìm sau**: `_matches` giữ lại record có mọi cặp key/value trong `metadata_filter` khớp (hỗ trợ cả giá trị dạng list để lọc "một trong các"), rồi mới đưa tập ứng viên vào `_search_records`. Lọc trước đảm bảo `top_k` kết quả trả về đều đúng điều kiện, thay vì lọc sau và bị thiếu kết quả. `delete_document` xây lại `self._store` bỏ mọi record có `metadata["doc_id"] == doc_id`, trả `True` nếu có ít nhất một record bị xoá, đồng thời gọi `collection.delete` trên Chroma nếu đang dùng.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent gọi `store.search` (hoặc `search_with_filter` nếu có `metadata_filter`) lấy `top_k` chunk, rồi `build_prompt` ghép chúng thành các khối đánh số `[n] (source: doc_id, score)` dưới tiêu đề NGỮ CẢNH, kèm chỉ dẫn "chỉ dùng thông tin trong ngữ cảnh, nếu không đủ thì nói không tìm thấy, trích dẫn số [n]". Prompt kết thúc bằng CÂU HỎI và nhãn TRẢ LỜI để LLM điền tiếp. Nếu store rỗng thì trả về thông báo "không tìm thấy" mà không gọi LLM; các chunk đã dùng được giữ ở `self.last_context` để truy vết nguồn.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
============================= test session starts ==============================
platform darwin -- Python 3.11.8, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================== 42 passed in 0.03s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Script: `scripts/similarity_predictions.py`. Cột "Điểm thực tế" đo bằng mô hình cục bộ `sentence-transformers/all-MiniLM-L6-v2` (chạy offline); cột "Mock" là `_mock_embed` mặc định của lab để đối chiếu.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Mock | Đúng? |
|------|-----------|-----------|---------|--------------|------|-------|
| 1 | Sinh viên phải đăng ký học phần trước hạn chót của học kỳ. | Hạn cuối để sinh viên đăng ký môn học là trước khi học kỳ bắt đầu. | cao | 0.871 | −0.124 | ✅ |
| 2 | Thư viện cho phép mượn tối đa 5 cuốn sách trong 14 ngày. | Mỗi người đọc được mượn 5 quyển, thời hạn hai tuần. | cao | 0.747 | −0.046 | ✅ |
| 3 | Sinh viên nộp đơn phúc khảo trong vòng 7 ngày sau khi công bố điểm. | Ký túc xá đóng cửa lúc 23 giờ mỗi ngày. | thấp | 0.581 | −0.071 | ⚠️ thấp hơn cặp 1–2 nhưng cao hơn kỳ vọng |
| 4 | Học bổng khuyến khích học tập xét theo điểm trung bình học kỳ. | Món phở bò ngon nhất là ở Hà Nội. | thấp | 0.326 | 0.033 | ✅ |
| 5 | Học phí học kỳ này tăng 10% so với năm ngoái. | Học phí học kỳ này giảm 10% so với năm ngoái. | trung bình (nghĩa ngược nhau) | **0.903** | −0.155 | ❌ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 5: hai câu **trái nghĩa** (tăng/giảm) lại có cosine cao nhất bảng (0.903), cao hơn cả cặp diễn giải lại đúng nghĩa (cặp 1). Embedding biểu diễn *chủ đề và bối cảnh* (học phí, học kỳ, 10%, năm ngoái) chứ không mã hoá tốt cực tính/phủ định — nên RAG có thể truy xuất đúng đoạn nhưng LLM vẫn phải đọc kỹ để không trả lời ngược. Cặp 3 cũng cao hơn dự đoán (0.581) vì cả hai đều là "quy định có mốc thời gian dành cho sinh viên"; điểm mock thì gần 0 và ngẫu nhiên vì nó chỉ băm chuỗi, không hiểu nghĩa — vì thế benchmark nhóm phải chạy với embedder thật.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong gói `src`. Bộ 5 câu này nằm trong hằng số `BENCHMARK` của `scripts/run_benchmark.py` nên mọi thành viên chạy đúng cùng một bộ; xem `REPORT_NHOM.md` mục 3.

Cấu hình của tôi: chiến lược riêng `HeadingChunkerV2(max_chars=600, min_chars=180)`, corpus `data/university/` gồm 10 tài liệu, embedder `paraphrase-multilingual-MiniLM-L12-v2`, `top_k=3`. Câu 1 dùng `metadata_filter={"audience": "student"}`.

```bash
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --compare
EMBEDDING_PROVIDER=local python scripts/ablation.py
```

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) | Điểm |
|---|-------|--------------------------------|-------|-----------|------------------------|---|
| 1 | Sinh viên được mượn tối đa bao nhiêu cuốn và trong bao lâu? | `muon-tai-lieu-sinh-vien#0`, tiêu đề gộp mục Hạn mức và thời hạn mượn | 0,821 | Có, đúng chunk vàng | Tối đa 5 cuốn, thời hạn 14 ngày mỗi cuốn (đúng gold) | 2 |
| 2 | Nộp đơn phúc khảo trong bao lâu và lệ phí bao nhiêu? | `phuc-khao-diem#1`, mục Lệ phí và quy trình | 0,510 | Đúng tài liệu, thiếu vế thời hạn | Nêu được lệ phí 50.000 đồng, thiếu mốc 7 ngày làm việc | 1 |
| 3 | Điều kiện xét học bổng khuyến khích học tập? | `hoc-bong-khuyen-khich#0`, tiêu đề gộp mục Điều kiện xét | 0,792 | Có, đúng chunk vàng | Nêu đủ ngưỡng 3,2 và 80 (đúng gold) | 2 |
| 4 | Rút học phần sau thời hạn điều chỉnh thì bảng điểm ghi gì? | `dieu-chinh-hoc-phan#0`, đoạn mở đầu | 0,641 | Đúng tài liệu, sai mục | Nói về thời hạn điều chỉnh hai tuần, không nêu ký hiệu W | 1 |
| 5 | Thư viện mở cửa mấy giờ vào thứ Bảy? | `gio-mo-cua-thu-vien#0`, tiêu đề gộp mục Giờ mở cửa | 0,878 | Có, đúng chunk vàng | Từ 8 giờ đến 17 giờ (đúng gold) | 2 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5. Cả 5 câu đều có tài liệu vàng ở **top-1**. Tổng điểm chất lượng truy xuất: **8/10**.

**Hai điểm bị trừ không phải do truy xuất sai tài liệu.** Ở câu 2, câu hỏi có hai vế nằm ở hai mục khác nhau nên không chunk đơn lẻ nào chứa đủ. Ở câu 4, chunk mở đầu thắng ở 0,641 còn chunk chứa ký hiệu W đứng ngay sau ở 0,584, vì câu hỏi lặp lại nguyên văn cụm "sau thời hạn điều chỉnh" vốn xuất hiện trong đoạn mở đầu.

### Chiến lược riêng và cải tiến tôi đã kiểm chứng

Bản đầu `HeadingChunker` của tôi chỉ đạt 7/10. Chẩn đoán: ở câu 3, chunk chỉ chứa dòng tiêu đề tài liệu đạt 0,832 và đè chunk chứa đáp án ở 0,637. Sau khi gộp, chunk hợp nhất đạt 0,792 và mang theo cả hai ngưỡng 3,2 và 80. Chunk tiêu đề "thuần chủ đề" nên thắng cosine, nhưng không chứa con số nào.

Cách sửa là gộp mọi mục ngắn hơn 180 ký tự vào mục kế tiếp:

| Biến thể | Số chunk | Độ dài TB | Tổng /10 |
|---|---|---|---|
| `HeadingChunker(600)` | 39 | 236 | 7 |
| `HeadingChunkerV2(600, 180)` | 30 | 307 | **8** |

Cải tiến sửa đúng câu đã chẩn đoán và giảm 23% số chunk.

### So với các chiến lược khác trên cùng bộ câu hỏi

| Chiến lược | Số chunk | Tổng /10 |
|---|---|---|
| `FixedSizeChunker(300, 30)` | 38 | 7 |
| `SentenceChunker(2)` | 47 | 8 |
| `RecursiveChunker(300)` | 46 | 7 |
| `HeadingChunkerV2(600, 180)` của tôi | 30 | 8 |

Điều tôi không ngờ: bốn chiến lược chỉ chênh nhau 1 điểm. Trong khi đó, chỉ cần đổi embedder từ `_mock_embed` sang mô hình thật, điểm nhảy từ 2 lên 7 hoặc 8. Cách chọn mô hình nhúng ảnh hưởng lớn hơn cách cắt văn bản nhiều lần, và tôi đã dành phần lớn thời gian tối ưu đúng thứ ít quan trọng hơn.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Điền sau buổi demo.]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 — 5/5 câu có chunk vàng ở top-1, 2 câu bị trừ vì chunk thiếu dữ kiện |
| **Tổng phần cá nhân** | **57 / 60** |
