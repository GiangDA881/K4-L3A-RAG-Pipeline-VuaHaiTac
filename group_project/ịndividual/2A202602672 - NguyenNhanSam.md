# Báo cáo đóng góp cá nhân

## Thông tin

- Họ và tên: Nguyễn Nhân Sâm
- Mã học viên: 2A202602672
- Nhóm: VuaHaiTac
- Repository/branch: `K4-L3A-RAG-Pipeline-VuaHaiTac` / `sam/retrieval-eval`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Dense retrieval | Hoàn thiện truy vấn ChromaDB, chuyển cosine distance thành similarity và trả về `SearchResult` đúng schema. | `src/task5_semantic_search.py` | Done |
| BM25 retrieval | Xây dựng lexical search trên cùng corpus chunks, chuẩn hóa token và sắp xếp kết quả theo score. | `src/task6_lexical_search.py` | Done |
| RRF fusion | Gộp dense và BM25 theo công thức Reciprocal Rank Fusion, khử trùng ID và gắn method `hybrid`. | `src/task7_reranking.py` | Done |
| Retrieval pipeline | Điều phối dense, BM25, RRF và fallback theo dense cosine threshold; xử lý lỗi fallback để pipeline không crash. | `src/task9_retrieval_pipeline.py` | Done |
| PageIndex fallback | Giữ contract fallback và xử lý provider failure trong pipeline; tích hợp API PageIndex thật chưa được xác minh. | `src/task8_pageindex_vectorless.py`, `src/task9_retrieval_pipeline.py` | Partial |
| Golden dataset | Tạo 16 câu hỏi bám corpus du lịch: 5 keyword, 5 semantic và 6 ambiguous/multi-source. | `group_project/evaluation/golden_dataset.json` | Done |
| A/B evaluation | Viết script chạy dense-only và hybrid + RRF trên cùng dataset, cùng generator/evaluator; lưu điểm từng case và raw context. | `scripts/evaluate_ab.py`, `group_project/evaluation/ab_scores.json` | Done |
| Evaluation report | Tổng hợp 4 metrics, delta, worst performers, root cause và recommendations. | `group_project/evaluation/RESULT.md`, `reports/RESULT.md` | Done |
| Contract/UI integration support | Rà soát contract cho generation result, citation source ID và lịch sử sources trong UI theo yêu cầu tích hợp. | `src/contracts.py`, `src/task10_generation.py`, `app.py` | Shared |

## Quyết định kỹ thuật quan trọng

1. **Dùng RRF để gộp thứ hạng, nhưng dùng dense cosine score cho fallback.**  
   **Lý do/evidence:** cosine score và BM25/RRF score thuộc các thang đo khác nhau; contract tests kiểm tra RRF chỉ chạy một lần và fallback dựa trên dense score.  
   **Trade-off:** RRF không cần hiệu chỉnh hai thang điểm, nhưng có thể đưa context kém liên quan vào top-k nếu candidate pool lớn hoặc query đa nguồn.

2. **Đánh giá dense-only và hybrid + RRF trên cùng 16 cases.**  
   **Lý do/evidence:** `scripts/evaluate_ab.py` chạy cùng question, expected answer, prompt, generator và top-k; raw kết quả được lưu trong `ab_scores.json`.  
   **Trade-off:** dùng cùng LLM làm generator và judge giúp tái lập đơn giản, nhưng có thể tạo bias; kết quả cần được xem là LLM-judge evaluation, chưa phải benchmark độc lập bằng evaluator khác.

## Kiểm thử và kết quả

- Test đã dùng: `pytest tests/test_contracts.py -q`.
- Kết quả contract: `15 passed`.
- Golden dataset: 16 cases hợp lệ, gồm đủ 5 keyword, 5 semantic và 6 ambiguous.
- A/B evaluation trên 16 cases:
  - Dense-only average: `0.723750`.
  - Hybrid + RRF average: `0.661406`.
  - Delta hybrid so với dense-only: `-0.062344`.
  - Dense-only cao hơn hybrid ở faithfulness, answer relevance, context recall và context precision trong lần chạy này.
- Lỗi đã phát hiện và xử lý: `golden_dataset.json` rỗng và `RESULT.md` còn placeholder; đã bổ sung dataset, báo cáo và script tái lập.

## Điều còn hạn chế

- PageIndex là provider ngoài; phần upload/query thật chưa có bằng chứng runtime và cần API key nếu muốn demo fallback thật.
- RRF hiện giảm điểm so với dense-only trên corpus này, đặc biệt context precision giảm `0.108125`; cần thử candidate pool, query expansion hoặc reranker trước khi kết luận cấu hình cố định.
- Evaluator hiện là custom LLM judge dùng cùng model xKiro; nếu có thêm thời gian, nên chạy RAGAS hoặc evaluator model độc lập và calibrate threshold bằng query in-domain/out-of-domain.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc mình đã thực hiện và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Nhân Sâm
