# Corpus K4-L3A — Dịch vụ và quy định đại học

10 tài liệu, chủ đề dịch vụ và quy định đại học, dùng cho benchmark Giai đoạn 2 của Lab 7.

> **Đây là dữ liệu mẫu do nhóm soạn để lab chạy được đầu-cuối, không phải quy định của một trường có thật.**
> Mọi `source_url` dùng tên miền `example.edu` (tên miền IANA dành riêng cho tài liệu) nên không thể nhầm với nguồn thật.
> Khi thay bằng nguồn công khai thật, giữ nguyên cấu trúc front matter và cập nhật `sources.csv`; xem `docs/DATA_COLLECTION.md`.

## Phân bố metadata

| audience | Số tài liệu | Tài liệu |
|---|---|---|
| `student` | 7 | course-registration, dieu-chinh-hoc-phan, hoc-phi-va-han-nop, hoc-bong-khuyen-khich, phuc-khao-diem, muon-tai-lieu-sinh-vien, ky-tuc-xa |
| `faculty` | 1 | muon-tai-lieu-giang-vien |
| `all` | 2 | gio-mo-cua-thu-vien, ho-tro-tai-khoan-cong-nghe |

| department | Số tài liệu |
|---|---|
| `academic-affairs` | 3 |
| `library` | 3 |
| `student-affairs` | 2 |
| `finance` | 1 |
| `it-services` | 1 |

Cặp `muon-tai-lieu-sinh-vien` và `muon-tai-lieu-giang-vien` cố ý mô tả **cùng một dịch vụ với hạn mức khác nhau** theo đối tượng. Đây là cặp tài liệu làm cho `metadata_filter={"audience": ...}` có việc thật để lọc.
