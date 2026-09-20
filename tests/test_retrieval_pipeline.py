"""Offline regression tests for fusion and fallback boundaries."""

from copy import deepcopy

import pytest

from src.task7_reranking import rerank_rrf
from src import task9_retrieval_pipeline as pipeline


def item(item_id, score, method="dense"):
    return {
        "id": item_id, "content": "Evidence", "score": score,
        "retrieval_method": method,
        "metadata": {"source": "test.md", "title": "Test", "doc_type": "legal",
                     "url": None, "chunk_index": 0},
    }


def test_rrf_preserves_inputs_and_sums_rank_contributions():
    lists = [[item("a", .9), item("b", .8)],
             [item("b", 70, "bm25"), item("c", 50, "bm25")]]
    before = deepcopy(lists)
    fused = rerank_rrf(lists, top_k=3)
    assert lists == before
    assert [r["id"] for r in fused] == ["b", "a", "c"]
    assert fused[0]["score"] == pytest.approx(1 / 62 + 1 / 61)
    assert all(r["retrieval_method"] == "hybrid" for r in fused)
    assert all(r is not original for r in fused for ranking in lists for original in ranking)


def test_rrf_rejects_upstream_duplicates():
    with pytest.raises(ValueError, match="unique"):
        rerank_rrf([[item("a", .9), item("a", .8)]])


def test_rrf_limits_empty_and_ties():
    assert rerank_rrf([]) == []
    assert rerank_rrf([[item("a", .9)]], top_k=0) == []
    assert rerank_rrf([[item("a", .9)]], top_k=-1) == []
    assert rerank_rrf([[item("b", .9)], [item("a", 9)]], top_k=1)[0]["id"] == "a"
    assert rerank_rrf([[item("a", .9)]], k=0)[0]["score"] == 1
    with pytest.raises(ValueError):
        rerank_rrf([], k=-1)


@pytest.mark.parametrize("score,should_fallback", [(0.49, True), (0.5, False), (0.9, False)])
def test_real_fusion_uses_original_dense_threshold(monkeypatch, score, should_fallback):
    dense = [item("a", score)]
    calls = []
    monkeypatch.setattr(pipeline, "semantic_search", lambda query, top_k: dense)
    monkeypatch.setattr(pipeline, "lexical_search", lambda query, top_k: [item("a", 100, "bm25")])
    monkeypatch.setattr(pipeline, "pageindex_search", lambda query, top_k: calls.append(query) or [])
    output = pipeline.retrieve("query", score_threshold=.5)
    assert bool(calls) == should_fallback
    assert dense[0]["score"] == score
    assert output[0]["score"] == pytest.approx(2 / 61)


@pytest.mark.parametrize("failure", [TimeoutError, RuntimeError])
@pytest.mark.parametrize("has_evidence", [False, True])
def test_provider_failure_keeps_available_evidence(monkeypatch, failure, has_evidence):
    dense = [item("a", .1)] if has_evidence else []
    monkeypatch.setattr(pipeline, "semantic_search", lambda query, top_k: dense)
    monkeypatch.setattr(pipeline, "lexical_search", lambda query, top_k: [])
    def unavailable(query, top_k):
        raise failure("provider error")
    monkeypatch.setattr(pipeline, "pageindex_search", unavailable)
    assert pipeline.retrieve("query", score_threshold=.5) == rerank_rrf([dense, []])


def test_malformed_fallback_keeps_hybrid(monkeypatch):
    dense = [item("a", .1)]
    monkeypatch.setattr(pipeline, "semantic_search", lambda query, top_k: dense)
    monkeypatch.setattr(pipeline, "lexical_search", lambda query, top_k: [])
    monkeypatch.setattr(pipeline, "pageindex_search", lambda query, top_k: [{"invalid": True}])
    assert pipeline.retrieve("query") == rerank_rrf([dense, []])


def test_empty_request_does_not_call_providers(monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Providers must not run for empty requests")
    monkeypatch.setattr(pipeline, "semantic_search", unexpected)
    monkeypatch.setattr(pipeline, "lexical_search", unexpected)
    monkeypatch.setattr(pipeline, "pageindex_search", unexpected)
    assert pipeline.retrieve("  ") == []
    assert pipeline.retrieve("query", top_k=0) == []
    assert pipeline.retrieve("query", top_k=-1) == []
