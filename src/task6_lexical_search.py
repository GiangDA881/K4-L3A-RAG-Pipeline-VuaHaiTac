"""
Task 6 — Lexical search bằng BM25.

Dùng cùng corpus chunks với Task 5. BM25 phù hợp với từ khóa chính xác, mã tài
liệu và tên riêng. Output phải theo SearchResult và sort score giảm dần.
"""

from __future__ import annotations

import re

import numpy as np
from rank_bm25 import BM25Plus

from .contracts import validate_search_results


CORPUS: list[dict] = []
_TOKEN_RE = re.compile(r"[0-9A-Za-zÀ-ỹ]+", re.UNICODE)

_bm25_index: BM25Plus | None = None
_bm25_corpus_ids: tuple[str, ...] | None = None


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens; giữ số hiệu văn bản như 09/2017 sau khi tách."""
    return _TOKEN_RE.findall(text.lower())


def build_bm25_index(corpus: list[dict]) -> BM25Plus:
    """Tạo BM25+ index từ cùng corpus chunks của Task 4.

    BM25+ tránh IDF=0 trên corpus nhỏ (Okapi cho N=2, df=1 ra score 0).
    """
    tokenized = [tokenize(item["content"]) or [""] for item in corpus]
    return BM25Plus(tokenized)


def _active_corpus() -> list[dict]:
    global CORPUS
    if CORPUS:
        return CORPUS
    from .task4_chunking_indexing import chunk_documents, load_documents

    CORPUS = chunk_documents(load_documents())
    return CORPUS


def _bm25_for(corpus: list[dict]) -> BM25Plus:
    global _bm25_index, _bm25_corpus_ids
    ids = tuple(item["id"] for item in corpus)
    if _bm25_index is None or _bm25_corpus_ids != ids:
        _bm25_index = build_bm25_index(corpus)
        _bm25_corpus_ids = ids
    return _bm25_index


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Trả về BM25 SearchResult theo score giảm dần."""
    if top_k <= 0:
        return []
    corpus = _active_corpus()
    if not corpus:
        return []

    bm25 = _bm25_for(corpus)
    tokens = tokenize(query)
    if not tokens:
        return []

    scores = bm25.get_scores(tokens)
    ranked = np.argsort(scores)[::-1]
    results: list[dict] = []
    seen: set[str] = set()
    for index in ranked:
        score = float(scores[index])
        if score <= 0:
            continue
        item = corpus[int(index)]
        item_id = item["id"]
        if item_id in seen:
            continue
        seen.add(item_id)
        results.append(
            {
                "id": item_id,
                "content": item["content"],
                "score": score,
                "metadata": item["metadata"],
                "retrieval_method": "bm25",
            }
        )
        if len(results) >= top_k:
            break

    results.sort(key=lambda item: (-item["score"], item["id"]))
    output = results[:top_k]
    validate_search_results(output, top_k=top_k, expected_method="bm25")
    return output


if __name__ == "__main__":
    for result in lexical_search("Luật Du lịch 09/2017/QH14 ký quỹ lữ hành", top_k=3):
        print(f"{result['score']:.3f} {result['id']} {result['metadata']['title']}")
