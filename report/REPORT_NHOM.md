# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** Bùi Đức Vinh (2A202602801), [Thành viên 2], [Thành viên 3]
**Ngày:** 2026-09-19

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.
>
> **Trạng thái bản nháp:** các mục đánh dấu `[NHÓM ĐIỀN]` cần nhóm thống nhất; các mục còn lại đã điền sẵn từ kết quả chạy thử của Bùi Đức Vinh trên corpus khởi động `data/university/` và có thể chỉnh lại sau khi chốt corpus.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ / quy định đại học (bắt buộc theo K4-L3A) — mảng cụ thể: **đăng ký học phần & dịch vụ thư viện** `[NHÓM ĐIỀN: xác nhận hoặc đổi mảng]`

**Tại sao nhóm chọn chủ đề này?**
> Quy định học vụ và thư viện là tài liệu công khai, có cấu trúc rõ theo điều/mục, chứa nhiều con số và mốc thời gian (hạn đăng ký, số sách được mượn, ngày gia hạn) nên câu trả lời chuẩn dễ kiểm chứng. Cùng một trang thường tách rõ đối tượng (sinh viên / giảng viên / nhân viên) nên trường `audience` có việc thật để lọc.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Đăng ký học phần *(khởi động, cần thay bằng nguồn thật)* | https://example.edu/hoc-vu/dang-ky-hoc-phan | 2026-08-02 / 2026.1 | ~350 | audience=student, department=academic-affairs, language=vi |
| 2 | Dịch vụ thư viện *(khởi động, cần thay bằng nguồn thật)* | https://example.edu/thu-vien/dich-vu | 2026-08-02 / 2026.1 | ~300 | audience=all, department=library, language=vi |
| 3 | `[NHÓM ĐIỀN]` | | | | |
| 4 | `[NHÓM ĐIỀN]` | | | | |
| 5 | `[NHÓM ĐIỀN]` | | | | |

Cách thu thập: `cp scripts/urls.example.csv data/urls.csv` → điền URL được phép dùng → `python scripts/fetch_public_pages.py data/urls.csv --output-dir data/university` (script tự sinh front matter + `sources.csv`). Xem `docs/DATA_COLLECTION.md`.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum | `student` / `faculty` / `staff` / `all` | Bắt buộc theo L3A; loại bỏ đoạn quy định cho giảng viên khi sinh viên hỏi (ví dụ hạn mức mượn sách khác nhau). |
| `department` | string | `academic-affairs`, `library`, `finance` | Thu hẹp không gian tìm kiếm theo đơn vị ban hành; tránh nhầm "hạn nộp" học phí với "hạn" đăng ký học phần. |
| `category` | string | `registration`, `borrowing`, `scholarship` | Lọc theo loại thủ tục khi câu hỏi nêu rõ thủ tục. |
| `language` | enum | `vi` / `en` | Trang song ngữ: giữ đúng ngôn ngữ câu hỏi để embedding không bị lệch. |
| `source_url`, `retrieved_at`, `document_version` | string / date | `https://…`, `2026-09-19`, `2026.1` | Truy vết và kiểm tra độ mới; không dùng để lọc khi tìm nhưng hiển thị trong câu trả lời của agent. |
| `doc_id`, `chunk_index` | string / int | `course-registration`, `1` | `doc_id` để `delete_document` xoá trọn tài liệu; `chunk_index` để chỉ ra chunk nào đã dùng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=200)` trên 3 tài liệu mẫu trong `data/` (`fixed_size` dùng overlap 20):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| python_intro.txt (2 222 ký tự) | FixedSizeChunker (`fixed_size`) | 13 | 189.4 | Không — cắt giữa từ/câu, nhiều chunk bắt đầu bằng nửa từ |
| | SentenceChunker (`by_sentences`) | 5 | 442.6 | Có — mỗi chunk 3 câu trọn vẹn nhưng dài gấp đôi chunk_size |
| | RecursiveChunker (`recursive`) | 17 | 128.9 | Phần lớn có — tách theo đoạn/câu; vài chunk rất ngắn (9 ký tự) do dòng lẻ |
| rag_system_design.md (2 700 ký tự) | FixedSizeChunker | 15 | 198.7 | Không — tiêu đề Markdown bị tách khỏi nội dung |
| | SentenceChunker | 5 | 537.8 | Một phần — regex câu không nhận tiêu đề `##` nên chunk gộp cả tiêu đề lẫn đoạn sau |
| | RecursiveChunker | 22 | 120.9 | Có — `\n\n` tách đúng theo đoạn/tiêu đề |
| vi_retrieval_notes.md (1 667 ký tự) | FixedSizeChunker | 10 | 184.7 | Không |
| | SentenceChunker | 5 | 331.6 | Có |
| | RecursiveChunker | 13 | 126.3 | Có |

Kết luận baseline: `fixed_size` đều kích thước nhưng phá vỡ câu; `by_sentences` mạch lạc nhưng không kiểm soát được độ dài; `recursive` cân bằng nhất với văn bản Markdown nhờ ưu tiên `\n\n`.

### Chiến lược của từng thành viên

**Thành viên 1 — Bùi Đức Vinh**
- **Loại chiến lược:** custom — `HeadingChunker` (chia theo tiêu đề/mục Markdown, fallback `RecursiveChunker` khi mục quá dài) — đáp ứng yêu cầu L3A "ít nhất một thành viên chia theo heading/section".
- **Mô tả & lý do chọn cho chủ đề này:** Quy định học vụ và sổ tay sinh viên được viết theo điều/mục, và mỗi câu hỏi benchmark gần như luôn ứng với đúng một mục. Giữ tiêu đề ngay trong chunk giúp embedding "biết" chủ đề của đoạn (ví dụ "## Gia hạn sách" + nội dung), còn mục dài hơn 600 ký tự thì cắt tiếp bằng recursive để không vượt cửa sổ ngữ cảnh.
- **Code snippet:** (đầy đủ trong `scripts/run_benchmark.py`)
```python
class HeadingChunker:
    HEADING = re.compile(r"^(#{1,6} .*)$", re.MULTILINE)

    def __init__(self, max_chars: int = 600) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        parts = self.HEADING.split(text)          # [preamble, h1, body1, h2, body2, ...]
        sections, buffer = [], parts[0].strip()
        for i in range(1, len(parts), 2):
            if buffer:
                sections.append(buffer)
            body = parts[i + 1].strip() if i + 1 < len(parts) else ""
            buffer = f"{parts[i].strip()}\n{body}".strip()   # giữ tiêu đề trong chunk
        if buffer:
            sections.append(buffer)
        chunks = []
        for section in sections:
            chunks.extend([section] if len(section) <= self.max_chars else self._fallback.chunk(section))
        return [c for c in chunks if c.strip()]
```

**Thành viên 2 — `[NHÓM ĐIỀN]`**
- **Loại chiến lược:** (gợi ý: `SentenceChunker` với `max_sentences_per_chunk=2` để mỗi chunk đúng một ý)
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — `[NHÓM ĐIỀN]`**
- **Loại chiến lược:** (gợi ý: `RecursiveChunker(chunk_size=300)` làm baseline có tham số tinh chỉnh)
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Bùi Đức Vinh | HeadingChunker (+recursive fallback) | 10 (5/5 câu top-1 đúng, corpus khởi động) | Chunk = đúng một mục quy định, tiêu đề giữ chủ đề, score tách bạch | Phụ thuộc tài liệu có heading; trang crawl mất heading thì thoái hoá thành recursive |
| `[NHÓM ĐIỀN]` | | | | |
| `[NHÓM ĐIỀN]` | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `[NHÓM ĐIỀN sau khi so sánh]` — Quan sát ban đầu: trên cùng corpus và cùng embedder, chunk "đúng một ý" cho score cao và tách bạch nhất (câu 5: chunk một câu đạt 0.839 so với 0.735 khi gộp 2 câu), nhưng chunk quá nhỏ lại mất ngữ cảnh cho câu hỏi cần 2 ý liên tiếp (câu 3 rớt xuống top-2 với sentence chunking). Chia theo heading giữ được cả hai.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.
> Bộ dưới đây là **đề xuất** dựa trên corpus khởi động, đã cấu hình sẵn trong `scripts/run_benchmark.py` (`BENCHMARK`); nhóm sửa lại cho khớp corpus thật.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên đăng ký học phần ở đâu và theo lịch nào? | Trong cổng học vụ, theo lịch của từng học kỳ. | course-registration#0 |
| 2 | Học phần tiên quyết là gì và sinh viên cần làm gì trước khi đăng ký? | Kiểm tra điều kiện tiên quyết trước khi xác nhận đăng ký. | course-registration#0 |
| 3 | Nếu bị trùng lịch học thì sinh viên xử lý thế nào? *(filter `audience=student`)* | Điều chỉnh lớp học phần trước thời hạn điều chỉnh được công bố. | course-registration#1 |
| 4 | Cần mang gì khi mượn tài liệu ở thư viện? | Thẻ định danh hợp lệ. | library-services#0 |
| 5 | Yêu cầu ngoại lệ về đăng ký học phần gửi qua đâu? *(filter `audience=student`)* | Qua kênh hỗ trợ học vụ chính thức. | course-registration#1 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Đăng ký học phần ở đâu | heading ≈ sentence (0.768 / 0.767) | Có | Mọi chiến lược đều đúng top-1 |
| 2 | Học phần tiên quyết | heading (0.742) | Có | Mock embedder trả về sai tài liệu (library) → cần embedder thật |
| 3 | Trùng lịch | heading (top-1, 0.588) | Có | sentence chunking đẩy chunk đúng xuống top-2 |
| 4 | Mang gì khi mượn sách | sentence (0.647) | Có | Mock embedder trả về chunk "cần bổ sung quy định…" (nhiễu) |
| 5 | Yêu cầu ngoại lệ | sentence (0.839) | Có | Chunk một câu chứa đúng đáp án |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có ở câu 3 và 5: `metadata_filter={"audience": "student"}` loại hẳn hai chunk thư viện (`audience=all`) khỏi ứng viên nên top-3 chỉ còn đúng tài liệu đăng ký học phần, và với mock embedder (vốn xếp hạng ngẫu nhiên) đây là lý do duy nhất hai câu này vẫn trả về chunk liên quan. Đánh đổi: bộ lọc `audience=student` sẽ **bỏ sót** tài liệu `audience=all` nếu đáp án nằm ở đó (ví dụ quy định thư viện áp dụng cho mọi người), nên nhóm nên hỗ trợ lọc `audience in ["student", "all"]` — `search_with_filter` đã nhận giá trị dạng list.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Embedding không mã hoá phủ định: "học phí tăng 10%" và "giảm 10%" có cosine 0.903, cao hơn cả cặp diễn giải lại đúng nghĩa — retrieval đúng đoạn nhưng LLM phải đọc kỹ.
> 2. Metadata `audience` cứu retrieval khi embedder yếu (mock): lọc trước thu hẹp ứng viên nên top-3 luôn đúng tài liệu.
> 3. `[NHÓM ĐIỀN]` — so sánh chiến lược giữa các thành viên trên corpus thật.

**Bài học rút ra khi so sánh trong nhóm:**
> `[NHÓM ĐIỀN]`

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> `[NHÓM ĐIỀN]` — Gợi ý từ lần chạy thử: tách trang gộp nhiều đối tượng thành nhiều file (mỗi file một `audience`) ngay lúc crawl, và dùng embedder đa ngữ (`paraphrase-multilingual-MiniLM-L12-v2`) thay vì model tiếng Anh vì corpus tiếng Việt.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
