# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Xuân Trường Giang
- Mã học viên: 2A202602446
- Nhóm: VuaHaiTac
- Repository/branch: `GiangDA881/K4-L3A-RAG-Pipeline-VuaHaiTac` (`main`; làm việc qua các PR #1–#4, #6–#7)

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| 1. Chuẩn bị repository | Đặt quy chuẩn tên repo `K4-L3A-RAG-Pipeline-VuaHaiTac` và báo cáo `MSV - Ho Va Ten.md`; cấu hình LLM xKiro (OpenAI-compatible, model free `qwen/qwen3.8-omni-flash:free`); `TEAMMATES.md`; cài `.venv`, Playwright Chromium, `.env` | `README.md`, `.env.example`, `src/llm_client.py`, `TEAMMATES.md` — PR #1, #2, #3 | Done |
| 2. Thu thập và chuẩn hóa corpus | Chốt đề tài Du lịch Việt Nam. Tải 3 PDF Công báo vào `data/landing/legal/`. Crawl 6 trang `vietnam.travel` (visa, e-visa, lịch trình, địa điểm, ẩm thực) vào `data/landing/news/`. Convert Markdown, giữ `Source` + `Landing` | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py`, `data/` — PR #4 | Done |
| 3. Tạo chunk, embedding, hai đường tìm kiếm | Recursive 500/50; embed chung `BAAI/bge-m3` qua `embed_texts()`; upsert Chroma 709 chunk, reindex không nhân bản; dense + BM25+ đúng SearchResult | `src/task4_chunking_indexing.py`, `src/task5_semantic_search.py`, `src/task6_lexical_search.py` — PR #6, #7 | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Corpus chính sách lấy PDF Công báo (Luật 09/2017/QH14, NĐ 168/2017, NĐ 94/2021); bài viết lấy `vietnam.travel`. Crawl4AI, fallback requests + MarkItDown nếu trang chặn.  
   **Lý do/evidence:** Nguồn công khai, có URL, ổn định lúc chấm. 3 test dữ liệu trong `tests/test_acceptance.py` pass.  
   **Trade-off:** Markdown tin còn nav của site; không dùng trang bị WAF.

2. **Quyết định:** Giữ recursive `CHUNK_SIZE=500`, `OVERLAP=50`; cùng `embed_texts()` cho corpus và query; BM25+ thay Okapi.  
   **Lý do/evidence:** 500 ký tự khớp một điều/đoạn; reindex vẫn 709 chunk. Query visa → dense ra e-visa; query “Luật Du lịch / ký quỹ” → BM25 ra luật và nghị định. Okapi cho IDF=0 khi N=2 (đúng case contract test).  
   **Trade-off:** Embedding chạy CPU (máy không GPU), lần index đầu chậm. Không gộp nhiều chiến thuật chunk vào một collection — so A/B bằng metric, không merge vector.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `python -m src.task1_collect_legal_docs` / `task2_crawl_news` / `task3_convert_markdown`; `python -m src.task4_chunking_indexing`; `python -m src.task5_semantic_search` và `python -m src.task6_lexical_search`; `pytest tests/test_acceptance.py::test_corpus_*`; `pytest tests/test_contracts.py -q`.
- Kết quả trước/sau nếu có: 709 chunks / 9 documents, chạy lại vẫn 709; 3 test dữ liệu acceptance passed; tại mốc 3 thì chunk / dense / BM25 pass (10 passed).
- Lỗi đã phát hiện và cách xử lý: các fail còn lại thuộc RRF/retrieve/generation nên để teammate phụ trách các module đó; Okapi IDF=0 khi N=2 nên chuyển BM25+.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: chunk tin tức còn boilerplate menu; chưa lọc main content.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: tách collection theo chiến thuật chunk của từng thành viên và chạy A/B 4 metric trên cùng golden set.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Xuân Trường Giang
