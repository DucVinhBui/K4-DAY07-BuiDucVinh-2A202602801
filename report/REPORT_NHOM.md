# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** Bùi Đức Vinh (2A202602801), Đỗ Phúc Hưng (2A202602762), Đinh Công Tú (2A202602479), Bùi Đức Thông (2A202602931)
**Ngày:** 2026-09-20

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

**Cách tái lập mọi số trong báo cáo này:**

```bash
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --compare
EMBEDDING_PROVIDER=local python scripts/ablation.py
```

---

## 0. Phân công nhiệm vụ trong nhóm

Nhóm có 4 thành viên. Nguyên tắc chia việc: **mỗi người sở hữu trọn một chiến lược chunking và một mảng tài liệu**, để bảng so sánh ở mục 2 là so sánh giữa bốn người thật chứ không phải bốn tham số do một người chỉnh.

### Bảng phân công tổng quan

| # | Thành viên | MSSV | Vai trò chính | Chiến lược chunking sở hữu | Mảng tài liệu phụ trách | Mục báo cáo chấp bút |
|---|---|---|---|---|---|---|
| 1 | Bùi Đức Vinh | 2A202602801 | Nhóm trưởng, phụ trách mã nguồn và khung đo | `HeadingChunker(600)` và `HeadingChunkerV2(600, 180)` | Học vụ — 3 tài liệu | Mục 2.3, 2.4, mục 4 |
| 2 | Đỗ Phúc Hưng | 2A202602762 | Phụ trách thư viện và bộ lọc metadata | `SentenceChunker(max_sentences_per_chunk=2)` | Thư viện — 3 tài liệu | Mục 1 phần metadata, mục 3 phần lọc |
| 3 | Đinh Công Tú | 2A202602479 | Phụ trách bộ câu hỏi đánh giá và chấm điểm | `RecursiveChunker(chunk_size=300)` | Công tác sinh viên — 2 tài liệu | Mục 3 phần câu hỏi và bảng điểm |
| 4 | Bùi Đức Thông | 2A202602931 | Phụ trách đường cơ sở và kiểm kê dữ liệu | `FixedSizeChunker(chunk_size=300, overlap=30)` | Tài chính và CNTT — 2 tài liệu | Mục 1 phần kiểm kê, mục 2 phần baseline |

### Chi tiết nhiệm vụ từng người

**1. Bùi Đức Vinh — 2A202602801 — nhóm trưởng, mã nguồn và khung đo**

- **Giai đoạn 1 (cá nhân, bắt buộc với mọi thành viên):** tự hoàn thành toàn bộ TODO trong `src/chunking.py`, `src/store.py`, `src/agent.py`; chạy `pytest tests/ -v` đạt 42/42.
- **Khung đo dùng chung:** viết `scripts/run_benchmark.py` — nạp corpus, tách YAML front matter thành `Document.metadata`, chạy 5 câu benchmark, tự chấm 2/1/0 theo `docs/SCORING.md`, và cờ `--compare` in bảng so sánh cả 5 chiến lược trong một lần chạy. Đây là công cụ để ba thành viên còn lại chỉ cần truyền `--strategy` chứ không phải mỗi người tự viết một script chấm khác nhau.
- **Thí nghiệm đối chứng:** viết `scripts/ablation.py` gồm thí nghiệm A (bật/tắt bộ lọc metadata trên Q1) và thí nghiệm B (`HeadingChunker` gốc so với V2).
- **Chiến lược sở hữu:** `HeadingChunker`, chia theo tiêu đề Markdown, mục dài quá 600 ký tự thì cắt tiếp bằng `RecursiveChunker`. Đây là chiến lược đáp ứng yêu cầu bắt buộc của L3A "ít nhất một thành viên chia theo heading hoặc section".
- **Chẩn đoán và sửa lỗi:** phát hiện chunk chỉ chứa dòng tiêu đề thắng cosine nhưng không chứa dữ kiện, viết `HeadingChunkerV2` gộp mục ngắn hơn 180 ký tự vào mục kế tiếp, đo lại và xác nhận Q3 lên 2 điểm đồng thời giảm 23% số chunk.
- **Tài liệu phụ trách:** `course-registration`, `dieu-chinh-hoc-phan`, `phuc-khao-diem`.
- **So sánh embedder:** chạy lại toàn bộ bảng điểm trên ba embedder (`_mock_embed`, `all-MiniLM-L6-v2`, `paraphrase-multilingual-MiniLM-L12-v2`) để dựng bảng ở mục 2.3.
- **Sản phẩm kiểm chứng được:** `scripts/run_benchmark.py`, `scripts/ablation.py`, lớp `HeadingChunker` và `HeadingChunkerV2`, mục 2.3, 2.4 và mục 4 của báo cáo này.

**2. Đỗ Phúc Hưng — 2A202602762 — thư viện và bộ lọc metadata**

- **Giai đoạn 1:** hoàn thành độc lập toàn bộ TODO trong `src/`, nộp `REPORT_CANHAN.md` riêng.
- **Tài liệu phụ trách:** `muon-tai-lieu-sinh-vien`, `muon-tai-lieu-giang-vien`, `gio-mo-cua-thu-vien`.
- **Đóng góp thiết kế quan trọng nhất:** đề xuất tách quy định mượn tài liệu thành **hai tài liệu riêng theo đối tượng** thay vì gộp một trang có hai bảng hạn mức. Chính cặp tài liệu này làm cho `metadata_filter={"audience": ...}` có việc thật để lọc, và là ví dụ được dùng xuyên suốt mục 3.
- **Chiến lược sở hữu:** `SentenceChunker(max_sentences_per_chunk=2)`. Lý do chọn: mỗi quy tắc trong văn bản quy định thường gói trọn trong một đến hai câu, chunk hai câu giữ được quy tắc kèm ngoại lệ đi liền sau.
- **Thiết kế metadata:** chốt bộ trường `audience`, `department`, `category`, `language` cùng ba trường truy vết `source_url`, `retrieved_at`, `document_version`; đảm bảo `audience` có đủ ba giá trị khác nhau để bộ lọc không vô nghĩa.
- **Đo bộ lọc:** chạy Q1 ở hai cấu hình có lọc và không lọc, ghi lại khoảng cách 0,023 giữa tài liệu sinh viên và tài liệu giảng viên; chạy tiếp Q5 ở ba cấu hình lọc để đo đánh đổi độ thu hồi, ra kết quả 2/2, 0/2 và 2/2.
- **Kết quả chiến lược:** 8/10, cao nhất trong ba chiến lược cơ bản.

**3. Đinh Công Tú — 2A202602479 — bộ câu hỏi đánh giá và chấm điểm**

- **Giai đoạn 1:** hoàn thành độc lập toàn bộ TODO trong `src/`, nộp `REPORT_CANHAN.md` riêng.
- **Tài liệu phụ trách:** `hoc-bong-khuyen-khich`, `ky-tuc-xa`.
- **Đóng góp thiết kế quan trọng nhất:** soạn 5 câu benchmark kèm câu trả lời chuẩn, và cố ý làm cho năm câu **khác loại nhau** thay vì năm câu tra cứu dữ kiện giống hệt: Q1 nhập nhằng theo đối tượng, Q2 có hai phần nằm ở hai mục khác nhau, Q3 hỏi danh sách điều kiện, Q4 hỏi hệ quả của một hành động, Q5 hỏi một dữ kiện đơn lẻ. Chính Q2 và Q4 là hai câu không chiến lược nào đạt điểm tuyệt đối, và trở thành nguyên liệu cho phần phân tích lỗi ở mục 4.
- **Chốt `gold_keywords`:** với mỗi câu, chọn từ khoá tối thiểu đủ để phân biệt chunk chứa đáp án thật với chunk chỉ nói đúng chủ đề — ví dụ Q4 chỉ cần ký hiệu `W`, Q3 cần cả `3,2` và `80`. Đây là thứ làm cho việc chấm tự động không bị "đúng chủ đề là cho điểm".
- **Chiến lược sở hữu:** `RecursiveChunker(chunk_size=300)`, tách theo thứ tự ưu tiên `\n\n`, `\n`, `. `, ` `. Lý do chọn: không giả định tài liệu có heading, nên vẫn chạy được khi nhóm thay corpus mẫu bằng nguồn crawl mất cấu trúc tiêu đề.
- **Vai trò đối chứng:** chiến lược này là mốc "không phụ thuộc cấu trúc" để đối chiếu với hai chiến lược phụ thuộc cấu trúc của Vinh và Hưng.
- **Kết quả chiến lược:** 7/10.

**4. Bùi Đức Thông — 2A202602931 — đường cơ sở và kiểm kê dữ liệu**

- **Giai đoạn 1:** hoàn thành độc lập toàn bộ TODO trong `src/`, nộp `REPORT_CANHAN.md` riêng.
- **Tài liệu phụ trách:** `hoc-phi-va-han-nop`, `ho-tro-tai-khoan-cong-nghe`.
- **Chiến lược sở hữu:** `FixedSizeChunker(chunk_size=300, overlap=30)` — đường cơ sở của cả nhóm. Đây là chiến lược duy nhất đã được cung cấp sẵn trong `src/chunking.py`, nên nó là mốc "không làm gì thêm" để đo xem ba chiến lược còn lại thật sự đem lại bao nhiêu.
- **Phân tích baseline:** chạy `ChunkingStrategyComparator().compare(text, chunk_size=300)` trên ba tài liệu đại diện, lập bảng số chunk, độ dài trung bình, ngắn nhất, dài nhất, và nhận xét chunk nào còn giữ được ngữ cảnh. Bảng này ở đầu mục 2.
- **Kiểm kê dữ liệu:** lập `data/university/sources.csv` với đủ bảy cột gồm `doc_id`, `file_path`, `title`, `source_url`, `retrieved_at`, `document_version`, `license_or_permission`; đối chiếu một-một giữa tên file và `doc_id`; đo số ký tự thật của từng tài liệu cho bảng kiểm kê ở mục 1.
- **Quản trị dữ liệu:** rà lại `docs/DATA_COLLECTION.md` và xác nhận corpus không chứa dữ liệu cá nhân, thông tin đăng nhập hay nội dung sau đăng nhập; đề xuất dùng tên miền `example.edu` và nhãn `sample-data-for-lab` để không ai nhầm dữ liệu mẫu với quy định thật.
- **Kết quả chiến lược:** 7/10.

### Quy ước làm việc chung

Ba quy ước dưới đây là thứ làm cho bốn kết quả của bốn người so sánh được với nhau:

1. **Một bộ câu hỏi duy nhất.** Bộ 5 câu nằm trong hằng số `BENCHMARK` của `scripts/run_benchmark.py`, không ai được sửa riêng trên máy mình. Muốn đổi thì đổi trong repo và cả nhóm chạy lại.
2. **Một hàm chấm duy nhất.** Mọi điểm số trong báo cáo đều do `score_query` sinh ra, không ai tự chấm bằng mắt. Nhờ vậy bảng so sánh giữa bốn người không bị lệch chuẩn chấm.
3. **Một embedder duy nhất khi so sánh chiến lược.** Mọi số trong bảng so sánh thành viên đều chạy với `paraphrase-multilingual-MiniLM-L12-v2` và `top_k=3`. Bảng nhiều embedder ở mục 2.3 là thí nghiệm riêng, không trộn vào bảng so sánh người.

Lệnh mỗi thành viên chạy để lấy số của riêng mình:

```bash
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --strategy fixed      # Bùi Đức Thông
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --strategy sentence   # Đỗ Phúc Hưng
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --strategy recursive  # Đinh Công Tú
EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --strategy heading2   # Bùi Đức Vinh
```

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và quy định đại học (bắt buộc theo K4-L3A). Mảng cụ thể: **học vụ, tài chính sinh viên và thư viện**.

**Tại sao nhóm chọn chủ đề này?**
> Quy định học vụ được viết theo điều và mục, mỗi mục chứa đúng một quy tắc kèm con số cụ thể như hạn 7 ngày, mức 3,2 điểm, phạt 2.000 đồng mỗi ngày. Nhờ đó câu trả lời chuẩn kiểm chứng được từng chữ, không phải diễn giải. Quan trọng hơn, cùng một dịch vụ thường có hạn mức khác nhau theo đối tượng, nên trường `audience` có việc thật để lọc chứ không chỉ là metadata trang trí.

### Danh sách tài liệu (Data Inventory)

Corpus gồm **10 tài liệu** trong `data/university/`, kiểm kê tại `data/university/sources.csv`.

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Đăng ký học phần | example.edu/hoc-vu/dang-ky-hoc-phan | 2026-09-20 / 2026.1 | 977 | audience=student, department=academic-affairs, category=registration, language=vi |
| 2 | Điều chỉnh và rút học phần | example.edu/hoc-vu/dieu-chinh-hoc-phan | 2026-09-20 / 2026.1 | 929 | audience=student, department=academic-affairs, category=registration |
| 3 | Phúc khảo điểm học phần | example.edu/hoc-vu/phuc-khao | 2026-09-20 / 2026.1 | 976 | audience=student, department=academic-affairs, category=assessment |
| 4 | Học phí và hạn nộp học phí | example.edu/tai-chinh/hoc-phi | 2026-09-20 / 2026.1 | 996 | audience=student, department=finance, category=tuition |
| 5 | Học bổng khuyến khích học tập | example.edu/sinh-vien/hoc-bong-khuyen-khich | 2026-09-20 / 2026.1 | 1 080 | audience=student, department=student-affairs, category=scholarship |
| 6 | Đăng ký và nội quy ký túc xá | example.edu/sinh-vien/ky-tuc-xa | 2026-09-20 / 2026.1 | 1 088 | audience=student, department=student-affairs, category=housing |
| 7 | Mượn tài liệu — sinh viên | example.edu/thu-vien/muon-tai-lieu-sinh-vien | 2026-09-20 / 2026.1 | 919 | audience=student, department=library, category=borrowing |
| 8 | Mượn tài liệu — giảng viên | example.edu/thu-vien/muon-tai-lieu-giang-vien | 2026-09-20 / 2026.1 | 757 | audience=**faculty**, department=library, category=borrowing |
| 9 | Giờ mở cửa thư viện | example.edu/thu-vien/gio-mo-cua | 2026-09-20 / 2026.1 | 670 | audience=**all**, department=library, category=facilities |
| 10 | Hỗ trợ tài khoản và CNTT | example.edu/cntt/ho-tro-tai-khoan | 2026-09-20 / 2026.1 | 908 | audience=**all**, department=it-services, category=support |

Cặp tài liệu 7 và 8 mô tả **cùng một dịch vụ với hạn mức khác nhau** (sinh viên 5 cuốn trong 14 ngày, giảng viên 15 cuốn trong 60 ngày). Đây là cặp làm cho bộ lọc `audience` có ý nghĩa thật.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Corpus không chứa dữ liệu cá nhân, thông tin đăng nhập hay tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` trong front matter và trong `sources.csv`.
- [x] `audience` có 3 giá trị khác nhau (`student` 7 file, `faculty` 1 file, `all` 2 file) nên bộ lọc có việc để làm.
- [x] `doc_id` duy nhất, khớp một-một giữa tên file và `sources.csv`.

> **Khai báo minh bạch về nguồn dữ liệu.** Đây là **dữ liệu mẫu do nhóm tự soạn** để pipeline chạy được đầu-cuối, **không phải quy định của một trường có thật**. Mọi `source_url` dùng tên miền `example.edu` mà IANA dành riêng cho tài liệu, nên không thể nhầm với nguồn thật; cột `license_or_permission` trong `sources.csv` ghi `sample-data-for-lab`. Khi thay bằng nguồn công khai thật, giữ nguyên cấu trúc front matter và chạy lại hai lệnh ở đầu báo cáo; mọi bảng số bên dưới sẽ tự cập nhật.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | enum | `student`, `faculty`, `all` | Bắt buộc theo L3A. Tách hạn mức mượn sách của sinh viên khỏi của giảng viên, hai đoạn văn gần như đồng nghĩa với nhau. |
| `department` | string | `academic-affairs`, `library`, `finance`, `student-affairs`, `it-services` | Thu hẹp theo đơn vị ban hành; tránh lẫn "hạn nộp" học phí với "hạn" đăng ký học phần. |
| `category` | string | `registration`, `borrowing`, `scholarship`, `tuition`, `assessment`, `housing`, `support`, `facilities` | Lọc theo loại thủ tục khi câu hỏi nêu rõ thủ tục. |
| `language` | enum | `vi` | Chuẩn bị cho corpus song ngữ về sau; hiện toàn bộ là `vi`. |
| `source_url`, `retrieved_at`, `document_version` | string, date | `https://…`, `2026-09-20`, `2026.1` | Truy vết và kiểm tra độ mới. Không dùng để lọc nhưng agent in kèm khi trả lời. |
| `doc_id`, `chunk_index` | string, int | `phuc-khao-diem`, `2` | `doc_id` để `delete_document` xoá trọn tài liệu; `chunk_index` để chỉ đúng chunk đã nuôi câu trả lời. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

`ChunkingStrategyComparator().compare(text, chunk_size=300)` trên 3 tài liệu của corpus:

| Tài liệu | Chiến lược | Số chunk | Độ dài TB | Ngắn nhất | Dài nhất | Giữ được ngữ cảnh không? |
|---|---|---|---|---|---|---|
| muon-tai-lieu-sinh-vien (919 ký tự) | `fixed_size` | 4 | 252,2 | 109 | 300 | Không, cắt giữa câu, mất đơn vị của con số |
| | `by_sentences` | 3 | 304,3 | 190 | 366 | Có, nhưng gộp hai mục khác nhau vào một chunk |
| | `recursive` | 5 | 182,2 | 129 | 224 | Có, tách đúng theo mục |
| hoc-bong-khuyen-khich (1 080 ký tự) | `fixed_size` | 4 | 292,5 | 270 | 300 | Không |
| | `by_sentences` | 4 | 268,2 | 73 | 559 | Một phần, chênh lệch độ dài rất lớn |
| | `recursive` | 5 | 214,4 | 134 | 269 | Có |
| dieu-chinh-hoc-phan (929 ký tự) | `fixed_size` | 4 | 254,8 | 119 | 300 | Không |
| | `by_sentences` | 3 | 308,0 | 198 | 499 | Một phần |
| | `recursive` | 5 | 184,2 | 39 | 289 | Phần lớn có, còn vài chunk rất ngắn |

Nhận xét baseline: `fixed_size` đều kích thước nhưng phá vỡ câu và tách con số khỏi đơn vị của nó. `by_sentences` mạch lạc nhưng độ dài dao động từ 73 đến 559 ký tự, không kiểm soát được. `recursive` cân bằng nhất trên văn bản Markdown nhờ ưu tiên tách theo `\n\n`.

### Chiến lược của từng thành viên

**Thành viên 1 — Bùi Đức Vinh (2A202602801)**
- **Loại chiến lược:** custom — `HeadingChunker`, chia theo tiêu đề và mục Markdown, mục dài hơn 600 ký tự thì cắt tiếp bằng `RecursiveChunker`. Đây là chiến lược đáp ứng yêu cầu L3A "ít nhất một thành viên chia theo heading hoặc section".
- **Mô tả và lý do chọn:** Quy định học vụ được viết theo điều và mục, và mỗi câu hỏi benchmark gần như luôn ứng với đúng một mục. Giữ dòng tiêu đề bên trong chunk để embedding nhận được nhãn chủ đề của đoạn, ví dụ mục "Hạn mức và thời hạn mượn" tự nói lên nó đang bàn về hạn mức.
- **Kết quả:** 7/10, sau khi sửa lỗi ở mục 2.4 thì lên 8/10.
- **Code snippet:** đầy đủ trong `scripts/run_benchmark.py`.

```python
class HeadingChunker:
    HEADING = re.compile(r"^(#{1,6} .*)$", re.MULTILINE)

    def __init__(self, max_chars: int = 600) -> None:
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        parts = self.HEADING.split(text)          # [mở đầu, h1, thân1, h2, thân2, ...]
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
            chunks.extend([section] if len(section) <= self.max_chars
                          else self._fallback.chunk(section))
        return [c for c in chunks if c.strip()]
```

**Thành viên 2 — Đỗ Phúc Hưng (2A202602762)**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=2)`, chia theo ranh giới câu, mỗi chunk hai câu.
- **Mô tả và lý do chọn:** Quy định thường gói trọn một quy tắc trong một hoặc hai câu, ví dụ "Sinh viên được mượn tối đa 5 cuốn tài liệu cùng lúc, thời hạn mượn là 14 ngày cho mỗi cuốn". Chunk hai câu đủ để giữ trọn quy tắc kèm ngoại lệ đi liền sau, mà không kéo theo mục không liên quan.
- **Kết quả:** 8/10, cao nhất trong ba chiến lược cơ bản.

**Thành viên 3 — Đinh Công Tú (2A202602479)**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=300)`, tách theo thứ tự ưu tiên `\n\n`, `\n`, `. `, ` `.
- **Mô tả và lý do chọn:** Không giả định tài liệu có heading, nên vẫn chạy được khi nhóm bổ sung nguồn crawl về mất cấu trúc tiêu đề. Dùng làm đối chứng cho hai chiến lược phụ thuộc cấu trúc ở trên.
- **Kết quả:** 7/10.

**Thành viên 4 — Bùi Đức Thông (2A202602931)**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=300, overlap=30)`, cửa sổ trượt kích thước cố định — đường cơ sở của cả nhóm.
- **Mô tả và lý do chọn:** Đây là chiến lược duy nhất đã có sẵn trong `src/chunking.py`, nên nhóm giữ nó làm mốc "không làm gì thêm". Nếu ba chiến lược còn lại không vượt được mốc này thì công sức thiết kế là vô ích. Overlap 30 ký tự, tức 10% kích thước chunk, để một câu bị cắt ở ranh giới vẫn xuất hiện trọn vẹn trong ít nhất một chunk.
- **Kết quả:** 7/10, và đây là con số quan trọng nhất của mục này: **chiến lược tốt nhất của nhóm chỉ hơn đường cơ sở đúng 1 điểm.**

### So Sánh Giữa Các Thành Viên

Cùng corpus, cùng 5 câu hỏi, cùng `top_k=3`, embedder `paraphrase-multilingual-MiniLM-L12-v2`. Chấm theo `docs/SCORING.md`.

| Thành viên | Chiến lược | Số chunk | Độ dài TB | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng /10 |
|---|---|---|---|---|---|---|---|---|---|
| Bùi Đức Thông (đường cơ sở) | `FixedSizeChunker(300, 30)` | 38 | 267 | 2 | 1 | 1 | 1 | 2 | **7** |
| Đỗ Phúc Hưng | `SentenceChunker(2)` | 47 | 196 | 2 | 1 | 2 | 1 | 2 | **8** |
| Đinh Công Tú | `RecursiveChunker(300)` | 46 | 201 | 2 | 1 | 1 | 1 | 2 | **7** |
| Bùi Đức Vinh | `HeadingChunker(600)` | 39 | 236 | 2 | 1 | 1 | 1 | 2 | **7** |
| Bùi Đức Vinh | `HeadingChunkerV2(600, 180)` sau cải tiến | 30 | 307 | 2 | 1 | 2 | 1 | 2 | **8** |

| Thành viên | Điểm mạnh | Điểm yếu |
|---|---|---|
| Đỗ Phúc Hưng — sentence | Chunk nhỏ và thuần một ý nên điểm cosine tách bạch; thắng Q3 vì tách được mục điều kiện xét ra khỏi đoạn mở đầu | Sinh nhiều chunk nhất (47), độ dài dao động mạnh; câu hỏi cần hai ý liền nhau dễ bị cắt đôi |
| Đinh Công Tú — recursive | Không phụ thuộc tài liệu có heading, an toàn với nguồn crawl mất cấu trúc | Sinh chunk vụn, có chunk chỉ 39 ký tự, làm loãng top-3 |
| Bùi Đức Vinh — heading | Ít chunk hơn hẳn sentence và recursive (39 so với 47 và 46), mỗi chunk là một mục quy định trọn vẹn nên dễ trích dẫn nguồn | Bản gốc sinh chunk chỉ chứa dòng tiêu đề, chunk này thắng cosine nhưng không chứa con số nào |
| Bùi Đức Thông — fixed | Độ dài chunk bị chặn cứng ở 300 ký tự nên chi phí embedding dự đoán được trước; không phụ thuộc bất kỳ đặc điểm cấu trúc nào của văn bản | Cắt giữa câu nên tách con số khỏi đơn vị của nó; ở Q2 chunk vàng rơi xuống tận top-3, thấp nhất trong bốn chiến lược cùng với recursive |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Khác biệt thật sự nhỏ hơn nhóm dự đoán: bốn chiến lược chỉ chênh nhau 1 điểm trên 10, và cả bốn đều đưa đúng tài liệu vàng lên top-1 ở 4 trên 5 câu. Điều này nói rằng với corpus sạch và có cấu trúc, **chọn embedder quan trọng hơn chọn cách chunk** — xem mục 2.3.
>
> Trong phạm vi đó, `SentenceChunker(2)` và `HeadingChunkerV2` cùng dẫn đầu với 8/10, nhưng vì hai lý do khác nhau. Sentence thắng nhờ chunk nhỏ, thuần một ý nên con số không bị pha loãng. Heading V2 thắng nhờ chunk trùng khít với đơn vị soạn thảo của văn bản, và nó còn rẻ hơn hẳn: 30 chunk so với 47, tức giảm 36% chi phí embedding và lưu trữ cho cùng số điểm. Với corpus quy định thật sẽ lớn hơn nhiều, nhóm chọn **heading V2** làm chiến lược chính và giữ sentence làm phương án đối chứng.

### 2.3. Ảnh hưởng của embedder, lớn hơn ảnh hưởng của chunking

Cùng corpus, cùng 5 câu hỏi, chỉ đổi mô hình nhúng:

| Embedder | fixed | sentence | recursive | heading |
|---|---|---|---|---|
| `_mock_embed` (băm MD5, mặc định của lab) | 2 | 3 | 1 | 2 |
| `all-MiniLM-L6-v2` (mô hình tiếng Anh) | 7 | 8 | 8 | 8 |
| `paraphrase-multilingual-MiniLM-L12-v2` (đa ngữ) | 7 | 8 | 7 | 7 |

Đây là kết quả đáng chú ý nhất của nhóm. Đổi chiến lược chunking dịch chuyển điểm 1 đơn vị; đổi từ embedder giả lập sang embedder thật dịch chuyển điểm **5 đến 7 đơn vị**. Mock embedder chỉ băm chuỗi thành vector nên xếp hạng gần như ngẫu nhiên, mọi so sánh chiến lược chạy trên nó đều vô nghĩa.

Bất ngờ thứ hai: mô hình đa ngữ **không thắng** mô hình tiếng Anh trên corpus tiếng Việt này (7-8 so với 7-8, recursive còn thua 1 điểm). Lý do nhóm suy đoán là corpus dùng nhiều số và thuật ngữ học vụ lặp lại, nên phần lớn tín hiệu nằm ở từ khoá chứ không ở ngữ nghĩa sâu. Nhóm vẫn chọn mô hình đa ngữ làm mặc định vì nó ổn định hơn khi câu hỏi diễn đạt xa với văn bản gốc.

### 2.4. Cải tiến đã kiểm chứng: gộp mục quá ngắn

**Chẩn đoán.** Ở Q3, `HeadingChunker` gốc đưa chunk `hoc-bong-khuyen-khich#0` lên top-1 với điểm 0,832, bỏ xa chunk `#1` chứa đáp án thật ở 0,637. Chunk `#0` chỉ gồm dòng tiêu đề và một câu dẫn nhập, nên nó "thuần chủ đề" và thắng cosine, nhưng không chứa ngưỡng 3,2 hay 80 nào cả. Agent vì thế trả lời chung chung.

**Cách sửa.** `HeadingChunkerV2` gộp mọi mục ngắn hơn 180 ký tự vào mục kế tiếp, để dòng tiêu đề luôn đi kèm nội dung có dữ kiện.

**Kết quả đo được** (`scripts/ablation.py`, thí nghiệm B):

| Biến thể | Số chunk | Độ dài TB | Q1 | Q2 | Q3 | Q4 | Q5 | Tổng /10 |
|---|---|---|---|---|---|---|---|---|
| `HeadingChunker(600)` — `--strategy heading` | 39 | 236 | 2 | 1 | 1 | 1 | 2 | 7 |
| `HeadingChunkerV2(600, 180)` — `--strategy heading2` | 30 | 307 | 2 | 1 | **2** | 1 | 2 | **8** |

Sửa đúng lỗi đã chẩn đoán, và đồng thời giảm 23% số chunk.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

Bộ câu hỏi nằm trong hằng số `BENCHMARK` của `scripts/run_benchmark.py` để mọi thành viên chạy đúng cùng một bộ.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên được mượn tối đa bao nhiêu cuốn tài liệu và trong bao lâu? *(cần lọc `audience=student`)* | Tối đa 5 cuốn cùng lúc, thời hạn 14 ngày mỗi cuốn. | `muon-tai-lieu-sinh-vien`, mục Hạn mức và thời hạn mượn |
| 2 | Nộp đơn phúc khảo điểm trong thời hạn bao lâu và lệ phí bao nhiêu? | Trong 7 ngày làm việc kể từ ngày công bố điểm; lệ phí 50.000 đồng mỗi học phần. | `phuc-khao-diem`, hai mục Thời hạn nộp đơn và Lệ phí |
| 3 | Điều kiện để được xét học bổng khuyến khích học tập là gì? | Điểm trung bình học kỳ từ 3,2; rèn luyện từ 80; tối thiểu 14 tín chỉ; không bị kỷ luật. | `hoc-bong-khuyen-khich`, mục Điều kiện xét |
| 4 | Rút học phần sau thời hạn điều chỉnh thì bảng điểm ghi gì? | Ghi ký hiệu W, không tính vào điểm trung bình tích lũy. | `dieu-chinh-hoc-phan`, mục Rút học phần sau thời hạn điều chỉnh |
| 5 | Thư viện mở cửa mấy giờ vào thứ Bảy? | Từ 8 giờ đến 17 giờ. | `gio-mo-cua-thu-vien`, mục Giờ mở cửa |

Bộ câu hỏi đa dạng có chủ đích: câu 1 nhập nhằng theo đối tượng, câu 2 có hai phần nằm ở hai mục khác nhau, câu 3 hỏi danh sách điều kiện, câu 4 hỏi hệ quả của một hành động, câu 5 hỏi một dữ kiện đơn lẻ.

### Tổng hợp chất lượng truy xuất của nhóm

Chiến lược tốt nhất của nhóm là `HeadingChunkerV2`, đạt **8/10**.

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Chunk vàng trong top-3? | Điểm | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---|---------|
| 1 | Hạn mức mượn tài liệu | Mọi chiến lược đều 2/2 | Có, top-1 với điểm 0,821 | 2 | Xem mục lọc metadata bên dưới: không lọc thì tài liệu giảng viên đứng ngay sau |
| 2 | Thời hạn và lệ phí phúc khảo | Không chiến lược nào đạt 2 | Có, top-1 với điểm 0,510 | 1 | Câu hỏi hai phần; mục Lệ phí thắng ở 0,510, mục Thời hạn theo sau ở 0,457 |
| 3 | Điều kiện học bổng | sentence và heading V2 | Có, top-1 với điểm 0,792 | 2 | Heading gốc chỉ được 1 vì chunk tiêu đề che mất chunk điều kiện |
| 4 | Ký hiệu W khi rút học phần | Không chiến lược nào đạt 2 | Có, top-1 với điểm 0,641 | 1 | Chunk mở đầu thắng chunk chứa ký hiệu W vốn đứng ngay sau ở 0,584 |
| 5 | Giờ mở cửa thứ Bảy | Mọi chiến lược đều 2/2 | Có, top-1 với điểm 0,878 | 2 | Điểm cao nhất toàn bộ benchmark |

**Tổng: 8/10.** Cả 5 trên 5 câu đều có chunk vàng trong top-3, và 5 trên 5 có chunk vàng ở top-1. Hai điểm bị trừ đều không phải do truy xuất sai tài liệu, mà do **chunk ở top-1 không chứa đủ dữ kiện để trả lời**.

### Lọc bằng metadata có giúp ích không?

Nhóm đo trực tiếp bằng `scripts/ablation.py`, thí nghiệm A, trên Q1 với chiến lược `heading`:

| Cấu hình | Điểm | Top-1 | Top-2 |
|---|---|---|---|
| Không lọc | 2/2 | `muon-tai-lieu-sinh-vien#1` — 0,789 | `muon-tai-lieu-giang-vien#1` — 0,766 |
| Lọc `audience=student` | 2/2 | `muon-tai-lieu-sinh-vien#1` — 0,789 | `muon-tai-lieu-sinh-vien#0` — 0,705 |

**Câu trả lời trung thực: trên corpus này bộ lọc không làm tăng điểm.** Cả hai cấu hình đều 2/2. Nhưng nó thu hẹp khoảng cách an toàn một cách đáng kể: khi không lọc, tài liệu dành cho giảng viên đứng ngay vị trí thứ hai với điểm chỉ thấp hơn 0,023. Hai đoạn văn này gần như đồng nghĩa với nhau, chỉ khác con số 5 và 15, 14 ngày và 60 ngày. Chênh lệch 0,023 là quá mỏng: chỉ cần đổi cách diễn đạt câu hỏi hoặc đổi embedder là thứ tự có thể đảo, và khi đó agent sẽ trả lời sinh viên rằng họ được mượn 15 cuốn trong 60 ngày. **Bộ lọc ở đây là bảo hiểm chống trả lời sai, không phải công cụ tăng điểm.**

**Đánh đổi độ thu hồi, đo được bằng số.** Nhóm thử áp bộ lọc `audience=student` cho Q5, câu hỏi có đáp án nằm trong tài liệu `audience=all`:

| Cấu hình lọc cho Q5 | Điểm | Top-1 |
|---|---|---|
| Không lọc | 2/2 | `gio-mo-cua-thu-vien#1` |
| `audience=student`, quá chặt | **0/2** | `muon-tai-lieu-sinh-vien#2`, hoàn toàn lạc đề |
| `audience in [student, all]` | 2/2 | `gio-mo-cua-thu-vien#1` |

Lọc quá chặt làm điểm rơi từ 2 xuống 0 vì tài liệu chứa đáp án bị loại khỏi tập ứng viên trước cả khi xếp hạng. Cách dùng đúng là lọc theo tập giá trị `["student", "all"]`, tức là "dành riêng cho tôi, hoặc dành cho tất cả mọi người". Hàm `search_with_filter` trong `src/store.py` đã nhận giá trị dạng danh sách nên hỗ trợ sẵn cách này.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích hay nhất nhóm sẽ trình bày:**

> 1. **Chọn embedder quan trọng hơn chọn cách chunk.** Bốn chiến lược chunking chỉ chênh nhau 1 điểm trên 10, trong khi đổi từ embedder giả lập sang embedder thật thay đổi 5 đến 7 điểm. Mọi so sánh chiến lược chạy trên mock embedder đều là so sánh nhiễu với nhiễu.
> 2. **Chunk "thuần chủ đề" là một cái bẫy.** Chunk chỉ chứa dòng tiêu đề đạt điểm cosine cao nhất tài liệu vì nó không bị pha loãng bởi chi tiết, nhưng chính vì không có chi tiết nào nên nó vô dụng để trả lời. Gộp mục ngắn vào mục kế tiếp sửa được lỗi này và còn giảm 23% số chunk.
> 3. **Bộ lọc metadata là bảo hiểm, không phải bộ tăng điểm.** Nó không đổi điểm ở câu 1, nhưng nó loại bỏ một tài liệu gần như đồng nghĩa chỉ kém 0,023 điểm. Ngược lại, lọc quá chặt kéo điểm câu 5 từ 2 xuống 0. Đúng cách là lọc theo tập `["student", "all"]`.

**Phân tích lỗi (Bài tập 3.5).**

Trường hợp lỗi rõ nhất là **Q4**, câu duy nhất không chiến lược nào đạt 2 điểm.

- **Hiện tượng:** truy xuất trả về đúng tài liệu `dieu-chinh-hoc-phan`, nhưng chunk ở top-1 là đoạn mở đầu, điểm 0,641, nói về thời hạn điều chỉnh kéo dài hai tuần. Chunk chứa đáp án thật, ký hiệu W, nằm ở top-2 với 0,584.
- **Nguyên nhân:** câu hỏi chứa cụm "sau thời hạn điều chỉnh", và cụm này xuất hiện nguyên văn trong đoạn mở đầu. Embedding khớp theo bối cảnh từ ngữ, trong khi thứ người hỏi cần lại là hệ quả được nêu ở mục sau. Đây không phải lỗi chunking mà là **lệch giữa từ ngữ của câu hỏi và vị trí của đáp án**.
- **Q2 lỗi theo kiểu khác:** câu hỏi có hai phần, thời hạn và lệ phí, nằm ở hai mục riêng biệt. Không một chunk đơn lẻ nào chứa đủ cả hai, nên mọi chiến lược đều tối đa 1 điểm. Đây là giới hạn của việc lấy top-1 làm ngữ cảnh duy nhất.
- **Đề xuất cải thiện:**
  1. Cho agent dùng cả `top_k=3` chunk làm ngữ cảnh thay vì chỉ trích dẫn chunk đầu. Với Q2, chunk 1 và chunk chứa thời hạn cùng nằm trong top-3 nên câu trả lời sẽ đủ ý. Prompt trong `src/agent.py` đã đánh số nhiều khối ngữ cảnh, chỉ cần LLM thật thay cho hàm trích xuất offline hiện tại.
  2. Thêm bước xếp hạng lại theo từ khoá của câu hỏi, ưu tiên chunk chứa con số hoặc ký hiệu khi câu hỏi mang tính tra cứu dữ kiện.
  3. Với tài liệu quy định, thêm câu tóm tắt mỗi mục vào đầu chunk lúc nạp, để chunk vừa mang nhãn chủ đề vừa mang dữ kiện.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus và cùng một bộ câu hỏi, bốn chiến lược chunking của bốn thành viên cho kết quả chênh nhau rất ít, và mọi thất bại còn lại đều không nằm ở chỗ nhóm đã tối ưu. Nhóm mất nhiều công so sánh cách cắt văn bản, trong khi hai nguồn sai số lớn hơn nhiều là chất lượng embedder và cách agent sử dụng ngữ cảnh. Bài học là đo trước, tối ưu sau: nếu nhóm chạy bảng so sánh embedder ngay từ đầu thì đã biết nên đầu tư công sức vào đâu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu?**
> Thứ nhất, tách tài liệu theo đối tượng ngay từ lúc thu thập thay vì để một trang gộp nhiều đối tượng, vì đây là thứ làm cho bộ lọc có giá trị thật. Thứ hai, viết câu hỏi đánh giá trước rồi mới soát lại corpus, để phát hiện sớm những câu có đáp án nằm rải ở nhiều mục như Q2. Thứ ba, chốt embedder trước khi so sánh chiến lược chunking, vì thứ tự ngược lại khiến nhóm suýt kết luận sai từ bảng điểm chạy trên mock embedder.

**Kịch bản demo 5 phút (nhóm chạy trực tiếp trên máy).**

Chuẩn bị trước: `pip install -r requirements-local.txt` và chạy thử một lần để mô hình nhúng đã nằm sẵn trong cache, tránh tải model giữa buổi trình bày.

| Phút | Người trình bày | Nội dung | Lệnh chạy trực tiếp | Điều cần chỉ ra trên màn hình |
|---|---|---|---|---|
| 0:00–0:45 | Bùi Đức Thông | Corpus và lý do chọn chủ đề | `cat data/university/sources.csv` | 10 tài liệu, mỗi dòng có `source_url`, `retrieved_at`, `document_version`; nói rõ đây là dữ liệu mẫu trên `example.edu` |
| 0:45–1:30 | Đỗ Phúc Hưng | Vì sao `audience` là metadata có ích | `head -20 data/university/muon-tai-lieu-sinh-vien.md data/university/muon-tai-lieu-giang-vien.md` | Hai tài liệu gần như đồng nghĩa, chỉ khác 5 cuốn/14 ngày và 15 cuốn/60 ngày |
| 1:30–3:00 | Đinh Công Tú | Bảng so sánh 4 chiến lược chunking | `EMBEDDING_PROVIDER=local python scripts/run_benchmark.py --compare` | Bốn chiến lược chỉ chênh nhau 1 điểm; `heading2` đạt 8/10 với 30 chunk, ít hơn `sentence` 17 chunk cho cùng số điểm |
| 3:00–4:15 | Bùi Đức Vinh | Hai thí nghiệm đối chứng | `EMBEDDING_PROVIDER=local python scripts/ablation.py` | Thí nghiệm A: không lọc thì tài liệu giảng viên đứng thứ hai, chỉ kém 0,023. Thí nghiệm B: gộp mục ngắn đưa Q3 từ 1 lên 2 và giảm 23% số chunk |
| 4:15–5:00 | Bùi Đức Vinh | Ba bài học và câu hỏi mở cho lớp | không cần chạy lệnh | Ba gạch đầu dòng ở đầu mục 4; đặt câu hỏi cho nhóm khác: corpus của các bạn có cặp tài liệu nào chỉ khác nhau ở đối tượng không? |

**Phương án dự phòng nếu máy không chạy được embedder thật:** chạy `python scripts/run_benchmark.py --compare` với embedder giả lập, chiếu bảng điểm 1–3/10, rồi đối chiếu với bảng ở mục 2.3. Bản thân sự chênh lệch đó chính là phát hiện số 1 của nhóm, nên phương án dự phòng vẫn trình bày được đúng thông điệp.

**Ai trả lời câu hỏi nào khi lớp chất vấn.** Nguyên tắc: người sở hữu phần việc trả lời phần việc đó, nhóm trưởng chỉ đỡ những câu không rơi vào ai.

| Chủ đề câu hỏi | Người trả lời chính |
|---|---|
| Nguồn dữ liệu, giấy phép, vì sao dùng dữ liệu mẫu | Bùi Đức Thông |
| Thiết kế metadata, bộ lọc `audience`, đánh đổi độ thu hồi | Đỗ Phúc Hưng |
| Cách soạn 5 câu benchmark, cách chấm 2/1/0, `gold_keywords` | Đinh Công Tú |
| Mã nguồn `src/`, `HeadingChunkerV2`, so sánh embedder | Bùi Đức Vinh |

**Câu hỏi nhóm dự kiến bị hỏi, và câu trả lời đã chuẩn bị:**

| Câu hỏi có thể bị hỏi | Trả lời |
|---|---|
| Vì sao chỉ 5 câu benchmark, có quá ít để kết luận không? *(Đinh Công Tú)* | Có, 5 câu là mức tối thiểu theo yêu cầu lab. Nhóm không kết luận chiến lược nào thắng tuyệt đối, chỉ kết luận rằng khoảng cách giữa các chiến lược nhỏ hơn khoảng cách giữa các embedder, và kết luận này đứng vững vì khoảng cách đó là 5–7 điểm chứ không phải 1 điểm. |
| Vì sao không dùng ChromaDB để xếp hạng? *(Bùi Đức Vinh)* | `EmbeddingStore` vẫn mirror sang ChromaDB khi thư viện có mặt, nhưng việc xếp hạng làm tại chỗ bằng tích vô hướng để kết quả tái lập được y hệt trên mọi máy, kể cả máy không cài Chroma. |
| Bộ lọc metadata không tăng điểm thì giữ làm gì? *(Đỗ Phúc Hưng)* | Vì nó chống lỗi chứ không tăng điểm. Không lọc thì tài liệu giảng viên đứng thứ hai với khoảng cách 0,023; chỉ cần đổi cách diễn đạt câu hỏi là thứ tự có thể đảo và agent sẽ trả lời sinh viên rằng họ được mượn 15 cuốn. |
| Nếu thay corpus mẫu bằng quy định thật thì bảng số có còn đúng không? *(Bùi Đức Thông)* | Không đảm bảo, và nhóm nói rõ điều đó. Hai lệnh ở đầu báo cáo sẽ sinh lại toàn bộ bảng số; cấu trúc front matter và bộ câu hỏi giữ nguyên, chỉ cần cập nhật `gold` và `gold_keywords` cho khớp văn bản mới. |

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 8 / 10 — đủ 10 tài liệu, metadata đầy đủ và có 3 giá trị `audience`, nhưng là dữ liệu mẫu tự soạn chứ chưa phải nguồn công khai thật |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 — 4 chiến lược, có chiến lược riêng theo heading, có chẩn đoán lỗi và cải tiến đã kiểm chứng bằng số |
| Chất lượng truy xuất (Retrieval Quality) | 8 / 10 — 5/5 câu có chunk vàng ở top-1, 2 câu bị trừ vì chunk thiếu dữ kiện |
| Thuyết trình (Demo) | 4 / 5 (tự đánh giá trước buổi trình bày) — đã có kịch bản 5 phút, lệnh chạy trực tiếp và phương án dự phòng; trừ 1 điểm vì chưa chạy thử trước lớp |
| **Tổng phần nhóm** | **34 / 40** |

> Điểm Demo ở trên là dự kiến. Sau buổi trình bày, nhóm cập nhật lại con số này cùng một dòng ghi nhận phản hồi của lớp và của giảng viên.
