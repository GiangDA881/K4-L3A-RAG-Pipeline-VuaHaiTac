# RAG evaluation results

## Run information

| Field | Value |
| --- | --- |
| Evaluation date | 2026-09-20 |
| Framework and version | Custom LLM judge in `scripts/evaluate_ab.py`; 16 cases/config |
| Evaluator model | Same configured xKiro model used as judge |
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

Scores below come from the completed 16-case run. Each score is the mean of per-case 0..1 LLM-judge scores.

| Metric | Config A | Config B | Delta B-A |
| --- | ---: | ---: | ---: |
| Faithfulness | 0.955000 | 0.946250 | -0.008750 |
| Answer relevance | 0.738125 | 0.652500 | -0.085625 |
| Context recall | 0.621250 | 0.574375 | -0.046875 |
| Context precision | 0.580625 | 0.472500 | -0.108125 |
| **Average** | **0.723750** | **0.661406** | **-0.062344** |

## A/B comparison

- Cấu hình tốt hơn: Dense-only trong lần chạy này.
- Evidence: Dense-only cao hơn hybrid ở cả 4 metrics; average 0.723750 so với 0.661406, delta -0.062344.
- Trade-off latency/cost: Dense-only cần một lượt vector search; hybrid thêm BM25 và RRF nhưng lần chạy này không bù được phần giảm relevance, recall và precision.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | Những nhóm hoạt động nào được Vietnam Tourism gợi ý cho du khách? | Hybrid | 0.95 | 0.10 | 0.10 | 0.20 | retrieval | RRF đưa context kém bao phủ danh sách category của article_04 lên top-k. |
| 2 | Du khách cần chuẩn bị những tiện ích thực tế nào trước chuyến đi Việt Nam? | Hybrid | 0.85 | 0.10 | 0.20 | 0.20 | retrieval | Context bị phân tán giữa currency, taxi và SIM nên không bao phủ đủ ý hỏi. |
| 3 | Hội An thuộc câu hỏi về địa điểm, lịch trình hay ẩm thực? | Hybrid | 1.00 | 0.30 | 0.00 | 0.15 | retrieval/generation | Câu hỏi đa nguồn; RRF không lấy được context Food cần cho cao lầu. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| ---: | --- | --- | --- | --- |
| 1 | Ưu tiên dense-only hoặc điều chỉnh RRF candidate pool/top-k. | Hybrid thấp hơn dense ở context precision 0.108125 và relevance 0.085625. | Giữ context liên quan hơn cho corpus hiện tại. | Chạy lại `python scripts/evaluate_ab.py` sau mỗi thay đổi. |
| 2 | Thêm query expansion hoặc reranker cho câu hỏi đa nguồn. | Case 12 có hybrid context recall 0.00 và precision 0.15. | Tăng khả năng lấy đồng thời địa điểm, lịch trình và ẩm thực. | Theo dõi riêng 6 ambiguous cases trong raw JSON. |
| 3 | Calibrate `SCORE_THRESHOLD` bằng query đúng chủ đề và ngoài chủ đề. | Threshold hiện là cấu hình mặc định `0.3`. | Giảm fallback sai và safe refusal không cần thiết. | Ghi dense score, fallback rate và kết quả từng query. |

## Reproduction

```powershell
python -m src.task4_chunking_indexing
python -m pytest tests/test_contracts.py -q
python -m pytest tests/test_acceptance.py -q
python scripts/evaluate_ab.py
streamlit run app.py
```

`scripts/evaluate_ab.py` chạy cùng 16 câu hỏi cho Config A (`use_reranking=False`) và Config B (`use_reranking=True`), rồi lưu answer/context/source và điểm từng case vào `group_project/evaluation/ab_scores.json`.

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| --- | --- | ---: | ---: | --- |
| Dense-only versus hybrid + RRF | Dense-only average 0.723750 | -0.062344 for hybrid | Hybrid adds BM25/RRF overhead | Dense-only is the current baseline winner; test tuning before removing hybrid permanently. |
