"""Evaluate dense-only and hybrid retrieval on the golden dataset."""

from __future__ import annotations

import json
import re
from pathlib import Path

from src.llm_client import chat_completion

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
OUTPUT = ROOT / "group_project" / "evaluation" / "ab_scores.json"

JUDGE_SYSTEM = """You are a strict RAG evaluator. Return only a JSON object with these four numeric keys,
each between 0 and 1: faithfulness, answer_relevance, context_recall, context_precision.
faithfulness measures support by retrieved context; answer_relevance measures directness;
context_recall measures coverage of expected context; context_precision measures relevance of retrieved context."""


def parse_scores(text: str) -> dict[str, float]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Evaluator returned non-JSON: {text[:200]}")
    raw = json.loads(match.group(0))
    keys = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
    return {key: max(0.0, min(1.0, float(raw[key]))) for key in keys}


def judge(case: dict, result: dict) -> dict[str, float]:
    context = "\n\n".join(
        f"[{source.get('id')}] {source.get('content', '')}"
        for source in result.get("sources", [])
    ) or "(no context retrieved)"
    prompt = f"""Question: {case['question']}
Expected answer: {case['expected_answer']}
Expected context: {case['expected_context']}
Generated answer: {result['answer']}
Retrieved context:\n{context}"""
    return parse_scores(chat_completion(JUDGE_SYSTEM, prompt))


def run_config(cases: list[dict], use_reranking: bool) -> list[dict]:
    import src.task10_generation as generation
    from src.task9_retrieval_pipeline import retrieve as pipeline_retrieve

    original = generation.retrieve
    generation.retrieve = lambda query, top_k: pipeline_retrieve(
        query, top_k=top_k, use_reranking=use_reranking
    )
    rows = []
    try:
        for number, case in enumerate(cases, 1):
            result = generation.generate_with_citation(case["question"], top_k=5)
            scores = judge(case, result)
            rows.append({"number": number, "question": case["question"], "result": result, "scores": scores})
            print(f"{'hybrid' if use_reranking else 'dense'} {number}/{len(cases)} {scores}")
    finally:
        generation.retrieve = original
    return rows


def average(rows: list[dict]) -> dict[str, float]:
    keys = ("faithfulness", "answer_relevance", "context_recall", "context_precision")
    return {key: sum(row["scores"][key] for row in rows) / len(rows) for key in keys}


def main() -> None:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    dense_rows = run_config(cases, use_reranking=False)
    hybrid_rows = run_config(cases, use_reranking=True)
    dense = average(dense_rows)
    hybrid = average(hybrid_rows)
    delta = {key: hybrid[key] - dense[key] for key in dense}
    payload = {
        "dataset_size": len(cases),
        "dense_only": dense,
        "hybrid_rrf": hybrid,
        "delta": delta,
        "rows": {"dense_only": dense_rows, "hybrid_rrf": hybrid_rows},
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"dense_only": dense, "hybrid_rrf": hybrid, "delta": delta}, ensure_ascii=False, indent=2))
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
