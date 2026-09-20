# RAG evaluation results

## Indexing configuration

Giá trị dùng cho corpus Du lịch Việt Nam (ghi lại để lần evaluation sau dùng cùng cấu hình):

| Field | Value |
| --- | --- |
| `CHUNKING_METHOD` | recursive |
| `CHUNK_SIZE` | 500 |
| `CHUNK_OVERLAP` | 50 |
| Embedding | `BAAI/bge-m3` (1024-d, cosine, `embed_texts()` dùng chung Task 4 và 5) |
| Lexical | BM25+ trên cùng chunk corpus |
| Indexed chunks | 709 từ 9 documents |

500/50 giữ đủ một điều luật hoặc đoạn tin, overlap tránh mất câu ở biên. BM25+ thay Okapi vì corpus nhỏ làm IDF của Okapi về 0.

## Run information

### Retrieval phase: RRF and fallback (2026-09-20)

- RRF dùng `k=60`, rank bắt đầu từ 1; ID xuất hiện ở rank 2 của dense và rank 1 của BM25 nhận `1/62 + 1/61 = 0.03252247488101534`. Item được copy trước khi đổi score/method. ID trùng trong cùng một ranked list bị báo lỗi để sửa upstream.
- Task 9 fuse đúng một lần ở đường hybrid; quyết định fallback lấy `max(score)` từ dense gốc. Điều kiện là `< score_threshold`, nên score bằng threshold vẫn giữ hybrid. `use_reranking=False` giữ baseline dense-only.
- Fallback rỗng, timeout, exception hoặc dữ liệu sai contract đều giữ kết quả retrieval hiện có. Khi cả hai retriever không có evidence và fallback lỗi, trả `[]` cho tầng generation xử lý.
- PageIndex chưa được bật vì môi trường không có `PAGEINDEX_API_KEY`. Upload/cache/timeout/parsing API thật của Task 8 vẫn chưa triển khai; test provider lỗi dùng mock, không phải kiểm chứng dịch vụ thật.
- `python -m src.task7_reranking`: chunk `b` đứng đầu với score `0.03252247488101534`.
- `.venv\Scripts\python.exe -m pytest tests/test_contracts.py tests/test_retrieval_pipeline.py -q`: **27 passed**. Bổ sung hai helper `reorder_for_llm` và `format_context` của Task 10 để contract test hiện có chạy được; generation end-to-end vẫn ngoài phạm vi pha này.

#### Threshold calibration

Chroma chính ban đầu có 0 chunks; BGE-M3 chưa được tải. Thử nghiệm dùng model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và index riêng trong `chroma_db/calibration/`, không thay cấu hình BGE-M3 hay index chính.

Hai query hiệu chỉnh:

1. Trong domain: “Điều kiện kinh doanh dịch vụ lữ hành quốc tế tại Việt Nam là gì?”
2. Ngoài domain: “Làm thế nào để huấn luyện mạng nơ-ron tích chập phân loại ảnh mèo và chó?”

Chạy lại: `python -m src.calibrate_retrieval --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Nếu dùng cache của workspace, đặt `HF_HOME` tới `.cache/huggingface` trước khi chạy. Script lưu model, dimension, hash corpus, hai dense ranked lists và kết quả RRF trong `reports/retrieval_calibration.json`.

`SCORE_THRESHOLD=0.3` trong Task 9 hiện là giá trị mặc định chưa hiệu chỉnh cho BGE-M3. Threshold từ MiniLM phải truyền qua tham số `score_threshold` khi dùng đúng model/index thử nghiệm; không áp dụng tự động sang BGE-M3. Hai query chỉ là sanity check ban đầu, chưa đủ để tối ưu ngưỡng cho mọi query hay mọi corpus.

Kết quả đo thật: **9 documents, 709 chunks**, recursive 500/50, MiniLM 384 chiều, cosine; dense/BM25 lấy 10 candidates, RRF `k=60`, trả `top_k=5`.

| Query | Best dense cosine | So với threshold `0.4967` | Nhánh quyết định |
| --- | ---: | --- | --- |
| Điều kiện kinh doanh dịch vụ lữ hành quốc tế tại Việt Nam là gì? | 0.8157963753 | Cao hơn | Giữ hybrid |
| Làm thế nào để huấn luyện mạng nơ-ron tích chập phân loại ảnh mèo và chó? | 0.1776284575 | Thấp hơn | Thử PageIndex; giữ hybrid nếu provider chưa cấu hình/lỗi |

**Chọn ngưỡng thử nghiệm `0.4967`**, làm tròn trung điểm hai cosine score `(0.8157963753 + 0.1776284575) / 2`. Query trong domain tìm được chunk về phạm vi kinh doanh lữ hành quốc tế trong Luật Du lịch; query ngoài domain có top dense là một đoạn bảng xe trong Nghị định 168, không chứa evidence về mạng nơ-ron. Đây chỉ là lựa chọn ban đầu cho cấu hình MiniLM/corpus trên, không phải ngưỡng đã được tối ưu hoặc dùng chung cho BGE-M3. Query ngoài domain vẫn có thể nhận hybrid chunks khi fallback không khả dụng; có kết quả retrieval không đồng nghĩa đủ evidence để trả lời. Cần tầng generation kiểm tra evidence và safe refusal.

Đã gọi `retrieve(..., score_threshold=0.4967)` thật với cùng model/index cho cả hai query: mỗi query trả 5 hybrid results; query ngoài domain ghi log `PageIndex fallback failed (RuntimeError); keeping retrieval results` do thiếu API key và pipeline không dừng. Kết quả lưu ở `pipeline_results` trong JSON evidence.

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | TODO  |
| Framework and version              | TODO  |
| Evaluator model                    | TODO  |
| Generator model                    | TODO  |
| Embedding model                    | TODO  |
| Corpus version/commit              | TODO  |
| Golden dataset size                | TODO  |
| `top_k`                            | TODO  |
| Fallback threshold and calibration | MiniLM thử nghiệm: `0.4967`; BGE-M3 mặc định `0.3` chưa hiệu chỉnh; xem phần trên |

## Configurations

- **Config A — dense-only:** TODO
- **Config B — hybrid + RRF:** TODO

Hai config phải dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |     TODO |     TODO |      TODO |
| Answer relevance  |     TODO |     TODO |      TODO |
| Context recall    |     TODO |     TODO |      TODO |
| Context precision |     TODO |     TODO |      TODO |
| **Average**       |     TODO |     TODO |      TODO |

## A/B comparison

- Cấu hình tốt hơn: TODO
- Evidence: TODO
- Trade-off về latency/cost: TODO

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | TODO     | TODO   |         TODO |      TODO |   TODO |      TODO | retrieval/generation/data | TODO       |
|   2 | TODO     | TODO   |         TODO |      TODO |   TODO |      TODO | retrieval/generation/data | TODO       |
|   3 | TODO     | TODO   |         TODO |      TODO |   TODO |      TODO | retrieval/generation/data | TODO       |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | TODO   | TODO                           | TODO            | TODO          |
|        2 | TODO   | TODO                           | TODO            | TODO          |
|        3 | TODO   | TODO                           | TODO            | TODO          |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| TODO       | TODO     |         TODO |               TODO | TODO       |
