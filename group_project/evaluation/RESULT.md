# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-20 |
| Framework and version | pytest contract/acceptance checks; API-backed RAGAS run pending |
| Evaluator model | Chưa chạy evaluator LLM |
| Generator model | xKiro `qwen/qwen3.8-omni-flash:free` (configured) |
| Embedding model | `BAAI/bge-m3` (configured) |
| Corpus version/commit | Working tree; commit hash chưa được cung cấp |
| Golden dataset size | 16 cases: 5 keyword, 5 semantic, 6 ambiguous |
| `top_k` | 5 |
| Fallback threshold and calibration | `0.3`; cần calibrate bằng query in-domain/out-of-domain |

## Configurations

- **Config A — dense-only:** dense semantic retrieval, `top_k=5`, cùng corpus và prompt.
- **Config B — hybrid + RRF:** dense + BM25, RRF `k=60`, `top_k=5`, cùng corpus và prompt.

Hai cấu hình dùng cùng golden dataset, generator, evaluator, prompt và `top_k`; chỉ thay retrieval strategy.

## Overall scores

Chưa có API-backed generation run trong phiên này, vì vậy không ghi số giả. Bảng dưới thể hiện trạng thái đo hiện tại.

| Metric | Config A | Config B | Delta B-A |
| --- | ---: | ---: | ---: |
| Faithfulness | N/A | N/A | N/A |
| Answer relevance | N/A | N/A | N/A |
| Context recall | N/A | N/A | N/A |
| Context precision | N/A | N/A | N/A |
| **Average** | N/A | N/A | N/A |

## A/B comparison

- Cấu hình tốt hơn: Chưa kết luận trước khi chạy cùng 15 cases.
- Evidence: Contract tests đã pass 15/15; acceptance data/report checks được thiết kế để xác nhận artifact trước khi đo LLM.
- Trade-off latency/cost: Dense-only cần một lượt vector search; hybrid thêm BM25 và RRF nên có thêm CPU/latency nhưng phù hợp truy vấn tên riêng và từ khóa pháp lý.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Quy định e-visa 90 ngày trong hai trang visa có mâu thuẫn nhau không? | Chưa đo | N/A | N/A | N/A | N/A | retrieval | Hai nguồn gần nghĩa; cần kiểm tra deduplication và citation map giữa article_01/article_02. |
| 2 | Nếu hỏi về mức ký quỹ kinh doanh lữ hành, nên dùng nguồn nào? | Chưa đo | N/A | N/A | N/A | N/A | retrieval | Query pháp lý có thể bị lẫn với bài hướng dẫn nếu BM25 không giữ được tên nghị định. |
| 3 | Tôi cần một câu trả lời vừa có món ăn vừa có hoạt động. | Chưa đo | N/A | N/A | N/A | N/A | generation/prompt | Câu hỏi nhiều ý cần citation riêng cho article_04 và article_05, tránh trộn evidence. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Chạy A/B evaluator trên đủ 15 cases sau khi có API key. | Bảng metric hiện chưa có số đo thật. | Có faithfulness, relevance, recall, precision có thể báo cáo. | Chạy cùng generator/prompt/top_k cho dense-only và hybrid. |
| 2 | Calibrate `SCORE_THRESHOLD` bằng query đúng chủ đề và ngoài chủ đề. | Threshold hiện là cấu hình mặc định `0.3`. | Giảm fallback sai và safe refusal không cần thiết. | Ghi dense score, fallback rate và kết quả từng query. |
| 3 | Kiểm tra citation theo `Source ID` cho câu hỏi đa nguồn. | Ba case ambiguous cố ý kiểm tra nhầm nguồn. | Tăng context precision và khả năng audit câu trả lời. | Đối chiếu citation trong answer với `sources` trả về. |

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m src.task4_chunking_indexing
.\.venv\Scripts\python.exe -m pytest tests/test_contracts.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_acceptance.py -q
streamlit run app.py
```

Khi có API key, chạy cùng 15 câu hỏi cho Config A (`retrieve(..., use_reranking=False)`) và Config B (`retrieve(..., use_reranking=True)`), lưu answer/context/source rồi tính bốn metric bằng cùng evaluator model.

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Chưa thực hiện | N/A | N/A | N/A | Cần hoàn tất baseline A/B trước khi kết luận bonus. |
