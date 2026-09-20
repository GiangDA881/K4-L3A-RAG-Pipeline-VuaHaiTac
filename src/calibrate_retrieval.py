"""Run two real retrieval probes in a separate index; save reproducible evidence."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import task4_chunking_indexing as indexing
from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=indexing.EMBEDDING_MODEL)
    parser.add_argument("--output", type=Path, default=Path("reports/retrieval_calibration.json"))
    args = parser.parse_args()
    indexing.EMBEDDING_MODEL = args.model
    indexing._sentence_transformer.cache_clear()
    model_tag = hashlib.sha256(args.model.encode()).hexdigest()[:12]
    indexing.CHROMA_DIR = indexing.CHROMA_DIR / "calibration" / model_tag
    documents = indexing.load_documents()
    chunks = indexing.chunk_documents(documents)
    indexing.index_to_vectorstore(indexing.embed_chunks(chunks))
    probes = []
    for domain, query in [
        ("in_domain", "Điều kiện kinh doanh dịch vụ lữ hành quốc tế tại Việt Nam là gì?"),
        ("out_of_domain", "Làm thế nào để huấn luyện mạng nơ-ron tích chập phân loại ảnh mèo và chó?"),
    ]:
        dense = semantic_search(query, top_k=10)
        sparse = lexical_search(query, top_k=10)
        fused = rerank_rrf([dense, sparse], top_k=5)
        probes.append({"domain": domain, "query": query,
                       "best_dense_score": max((r["score"] for r in dense), default=0.0),
                       "dense": dense, "hybrid": fused})
    inside, outside = [probe["best_dense_score"] for probe in probes]
    threshold = round((inside + outside) / 2, 4) if inside > outside else None
    output = {
        "date": datetime.now(timezone.utc).isoformat(),
        "embedding_model": args.model,
        "embedding_dimension": len(indexing.embed_texts(["dimension probe"])[0]),
        "documents": len(documents), "chunks": len(chunks),
        "corpus_sha256": hashlib.sha256(json.dumps(documents, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
        "chunk_size": indexing.CHUNK_SIZE, "chunk_overlap": indexing.CHUNK_OVERLAP,
        "top_k": 5, "rrf_k": 60, "suggested_threshold": threshold,
        "limitation": "Two probes only; threshold applies only to this model and corpus. No live PageIndex call.",
        "probes": probes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in output.items() if k != "probes"}, ensure_ascii=True))
    for probe in probes:
        print(probe["domain"], probe["best_dense_score"])


if __name__ == "__main__":
    main()
