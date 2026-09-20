# TEAMMATES

Nhóm **VuaHaiTac** — repo `K4-L3A-RAG-Pipeline-VuaHaiTac`

Báo cáo cá nhân đặt tên `MSV - Ho Va Ten.md`, nộp trong `group_project/ịndividual/`.

- Giang đã nộp: [2A202602446 - Nguyễn Xuân Trường Giang.md](group_project/ịndividual/2A202602446%20-%20Nguyễn%20Xuân%20Trường%20Giang.md)
- Hoàn đã nộp: [2A202602954 - Phan Trọng Hoàn.md](group_project/ịndividual/2A202602954%20-%20Phan%20Trọng%20Hoàn.md)
- Sâm đã nộp: [2A202602672 - Nguyễn Nhân Sâm.md](group_project/ịndividual/2A202602672%20-%20Nguyễn%20Nhân%20Sâm.md)

| Họ và tên | Mã học viên | Vai trò | Nhánh | Phần việc |
| --- | --- | --- | --- | --- |
| Nguyễn Xuân Trường Giang | `2A202602446` | Nhóm trưởng — Generation, LLM, UI | `giang/generation-ui` | Task 10 generation có citation; cấu hình LLM (xKiro); `app.py` Streamlit; điều phối repo, `.env.example`, demo |
| Phan Trọng Hoàn | `2A202602954` | Data & Indexing | `hoan/data-index` | Task 1 thu thập tài liệu chính sách; Task 2 crawl tin; Task 3 chuẩn hoá Markdown; Task 4 chunk, embedding, ChromaDB |
| Nguyễn Nhân Sâm | `2A202602672` | Retrieval & Evaluation | `sam/retrieval-eval` | Task 5 dense search; Task 6 BM25; Task 7 RRF; Task 8 PageIndex fallback; Task 9 retrieval pipeline; golden dataset và `group_project/evaluation/RESULT.md` |

## File / module phụ trách

| Thành viên | File chính |
| --- | --- |
| Nguyễn Xuân Trường Giang | `src/task10_generation.py`, `app.py` |
| Phan Trọng Hoàn | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py`, `src/task4_chunking_indexing.py`, `data/` |
| Nguyễn Nhân Sâm | `src/task5_semantic_search.py`, `src/task6_lexical_search.py`, `src/task7_reranking.py`, `src/task8_pageindex_vectorless.py`, `src/task9_retrieval_pipeline.py`, `group_project/evaluation/` |

Cả nhóm cùng giữ `src/contracts.py`, `tests/` và README chạy được. Mỗi người commit trên nhánh của mình rồi mở PR vào `main`.
