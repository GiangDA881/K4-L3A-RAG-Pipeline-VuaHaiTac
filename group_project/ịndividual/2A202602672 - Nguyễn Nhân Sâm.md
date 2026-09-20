# Individual contribution report

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
| Contract/UI integration support | Rà soát contract cho generation result, citation source ID và lịch sử sources trong UI theo yêu cầu tích hợp. | `src/contracts.py`, `src/task10_generation.py`, `app.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Quyết định:** Dùng RRF để gộp thứ hạng, nhưng dùng dense cosine score cho fallback.  
   **Lý do/evidence:** Cosine score và BM25/RRF score thuộc các thang đo khác nhau; contract tests kiểm tra RRF chỉ chạy một lần và fallback dựa trên dense score.  
   **Trade-off:** RRF không cần hiệu chỉnh hai thang điểm, nhưng có thể đưa context kém liên quan vào top-k nếu candidate pool lớn hoặc query đa nguồn.

2. **Quyết định:** Đánh giá dense-only và hybrid + RRF trên cùng 16 cases.  
   **Lý do/evidence:** `scripts/evaluate_ab.py` chạy cùng question, expected answer, prompt, generator và top-k; raw kết quả được lưu trong `ab_scores.json`.  
   **Trade-off:** Dùng cùng LLM làm generator và judge giúp tái lập đơn giản, nhưng có thể tạo bias; kết quả cần được xem là LLM-judge evaluation, chưa phải benchmark độc lập bằng evaluator khác.

## Kiểm thử và kết quả

- Test hoặc query tôi đã dùng: `pytest tests/test_contracts.py -q`; `python scripts/evaluate_ab.py` trên 16 cases (5 keyword, 5 semantic, 6 ambiguous).
- Kết quả trước/sau nếu có: contract `15 passed`. Dense-only average `0.723750`; hybrid + RRF average `0.661406`; delta `-0.062344`. Dense-only cao hơn hybrid ở cả bốn metric trong lần chạy này.
- Lỗi đã phát hiện và cách xử lý: `golden_dataset.json` rỗng và `RESULT.md` còn placeholder; đã bổ sung dataset, báo cáo và script tái lập.

## Điều còn hạn chế

- Một hạn chế cụ thể của phần tôi làm: RRF hiện giảm điểm so với dense-only trên corpus này, đặc biệt context precision giảm `0.108125`; PageIndex chưa có bằng chứng runtime và cần API key nếu muốn demo fallback thật.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: thử candidate pool, query expansion hoặc reranker, rồi chạy RAGAS / evaluator độc lập và calibrate threshold bằng query in-domain/out-of-domain.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Nhân Sâm
