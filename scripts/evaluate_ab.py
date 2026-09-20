"""Run a reproducible dense-only versus hybrid RAG evaluation.

The configured LLM acts as both generator and judge. The judge returns four
0..1 scores for every case; raw rows are saved for audit before aggregation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.llm_client import chat_completion


ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT_PATH = ROOT / "group_project" / "evaluation" / "ab_scores.json"
SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."

JUDGE_SYSTEM = """Bạn là evaluator RAG. Chấm độc lập bốn metric trong khoảng 0 đến 1.
faithfulness: câu trả lời có được hỗ trợ bởi context được lấy hay không.
answer_relevance: câu trả lời có trực tiếp trả lời câu hỏi hay không.
context_recall: context lấy được có bao phủ expected_context/ground truth hay không.
context_precision: phần lớn context lấy được có liên quan đến câu hỏi hay không.
Chỉ trả về JSON object với đúng bốn khóa trên, giá trị là số thực."""


def _parse_scores(text: str) -> dict[str, float]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Evaluator did not return JSON: {text[:300]}")
    raw = json.loads(match.group(0))
    keys = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
    return {key: max(0.0, min(1.0, float(raw[key]))) for key in keys}


def _judge(case: dict, result: dict) -> dict[str, float]:
    contexts = "\n\n".join(
        f"[{item.get('id')}] {item.get('content', '')}" for item in result.get("sources", [])
    ) or "(no context retrieved)"
    prompt = f"""Question: {case['question']}
Expected answer: {case['expected_answer']}
Expected context: {case['expected_context']}
Generated answer: {result['answer']}
Retrieved context:
{contexts}
"""
    return _parse_scores(chat_completion(JUDGE_SYSTEM, prompt))


def _run_config(cases: list[dict], *, use_reranking: bool) -> list[dict]:
    import src.task10_generation as generation
    from src.task9_retrieval_pipeline import retrieve as pipeline_retrieve

    original_retrieve = generation.retrieve
    generation.retrieve = lambda query, top_k: pipeline_retrieve(
        query, top_k=top_k, use_reranking=use_reranking
    )
    rows = []
    try:
        for index, case in enumerate(cases, 1):
            result = generation.generate_with_citation(case["question"], top_k=5)
            scores = _judge(case, result)
            rows.append({"index": index, "question": case["question"], "result": result, "scores": scores})
            print(f"{'hybrid' if use_reranking else 'dense'} {index}/{len(cases)}: {scores}")
    finally:
        generation.retrieve = original_retrieve
    return rows


def _average(rows: list[dict]) -> dict[str, float]:
    keys = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
    return {key: sum(row["scores"][key] for row in rows) / len(rows) for key in keys}


def main() -> None:
    cases = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    dense_rows = _run_config(cases, use_reranking=False)
    hybrid_rows = _run_config(cases, use_reranking=True)
    dense = _average(dense_rows)
    hybrid = _average(hybrid_rows)
    delta = {key: hybrid[key] - dense[key] for key in dense}
    payload = {"dataset_size": len(cases), "dense_only": dense, "hybrid_rrf": hybrid, "delta": delta, "rows": {"dense_only": dense_rows, "hybrid_rrf": hybrid_rows}}
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"dense_only": dense, "hybrid_rrf": hybrid, "delta": delta}, ensure_ascii=False, indent=2))
    print(f"Saved raw scores to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
