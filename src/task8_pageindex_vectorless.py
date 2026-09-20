"""PageIndex adapter for the retrieval endpoints exposed by pageindex==0.2.8.

Search existing PageIndex documents configured in pageindex_doc_ids.json.
HTTP errors propagate to Task 9's fallback boundary.
See docs/STEP_BY_STEP.md, section 7, for configuration and limitations.
"""

import hashlib
import json
import math
import os
import time
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv

from .contracts import validate_document, validate_search_results

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
CACHE_PATH = ROOT / "pageindex_doc_ids.json"
BASE_URL = "https://api.pageindex.ai"
REQUEST_TIMEOUT = float(os.getenv("PAGEINDEX_REQUEST_TIMEOUT", "20"))
SEARCH_TIMEOUT = float(os.getenv("PAGEINDEX_SEARCH_TIMEOUT", "60"))
POLL_INTERVAL = float(os.getenv("PAGEINDEX_POLL_INTERVAL", "1"))


class PageIndexError(RuntimeError):
    """Configuration, service status or response contract error."""


def _require_key():
    if not PAGEINDEX_API_KEY.strip():
        raise PageIndexError("PageIndex requires PAGEINDEX_API_KEY")


def _deadline(seconds):
    if not math.isfinite(seconds) or seconds <= 0:
        raise PageIndexError("PageIndex timeout must be positive and finite")
    return time.monotonic() + seconds


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("PageIndex operation timed out")
    return remaining


def _request(method, path, deadline, **kwargs):
    _require_key()
    if not math.isfinite(REQUEST_TIMEOUT) or REQUEST_TIMEOUT <= 0:
        raise PageIndexError("Invalid PageIndex request timeout")
    # Requests bounds connect/read inactivity; the deadline also bounds polling.
    timeout = min(REQUEST_TIMEOUT, _remaining(deadline))
    try:
        with requests.request(method, BASE_URL + path, headers={"api_key": PAGEINDEX_API_KEY},
                              timeout=timeout, **kwargs) as response:
            if not 200 <= response.status_code < 300:
                raise PageIndexError(f"PageIndex HTTP {response.status_code}")
            data = response.json()
    except requests.Timeout:
        raise TimeoutError("PageIndex HTTP request timed out") from None
    except (requests.RequestException, ValueError):
        # Do not expose provider response bodies, credentials or request headers.
        raise PageIndexError("Invalid or unavailable PageIndex response") from None
    _remaining(deadline)
    if not isinstance(data, dict):
        raise PageIndexError("PageIndex response must be an object")
    return data


def _identifier(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PageIndexError(f"Missing PageIndex {key}")
    return value


def _wait(path, deadline, *, ready=False):
    while True:
        data = _request("GET", path, deadline)
        status = data.get("status")
        if status in {"failed", "error", "cancelled"}:
            raise PageIndexError("PageIndex job failed")
        if status == "completed" and (not ready or data.get("retrieval_ready") is True):
            return data
        if status not in {"queued", "pending", "processing", "completed"}:
            raise PageIndexError("Unknown PageIndex job status")
        if not math.isfinite(POLL_INTERVAL) or POLL_INTERVAL <= 0:
            raise PageIndexError("Invalid PageIndex polling interval")
        time.sleep(min(POLL_INTERVAL, _remaining(deadline)))


def _load_documents():
    """Read configured IDs and source metadata for documents already on PageIndex."""
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8-sig"))
        entries = data["documents"]
        if not isinstance(entries, list) or not entries:
            raise ValueError("documents must be a non-empty list")
        seen = set()
        for entry in entries:
            doc_id = _identifier(entry, "doc_id")
            if doc_id in seen:
                raise ValueError("duplicate document ID")
            seen.add(doc_id)
            validate_document({"id": doc_id, "content": "metadata validation",
                               "metadata": entry["metadata"]})
        return entries
    except (OSError, ValueError, KeyError, TypeError, AttributeError, PageIndexError):
        raise PageIndexError("Configure existing document IDs and metadata in pageindex_doc_ids.json") from None


def _parse_nodes(response, entry):
    """Parse legacy retrieval's nested relevant_contents, not generated answers."""
    if not isinstance(response, dict):
        raise PageIndexError("Retrieval response must be an object")
    nodes = response.get("retrieved_nodes")
    if not isinstance(nodes, list):
        raise PageIndexError("Missing retrieved_nodes array")
    results = []
    seen = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("relevant_contents"), list):
            raise PageIndexError("Invalid retrieved node")
        for part in node["relevant_contents"]:
            if not isinstance(part, dict):
                raise PageIndexError("Invalid relevant content")
            text, page = part.get("relevant_content"), part.get("page_index")
            if (not isinstance(text, str) or not text.strip() or isinstance(page, bool)
                    or not isinstance(page, int) or page < 1):
                raise PageIndexError("Invalid content or page_index")
            text = text.strip()
            digest = hashlib.sha256(text.encode()).hexdigest()[:20]
            item_id = f"pageindex::{entry['doc_id']}::page-{page}::{digest}"
            if item_id in seen:
                continue
            seen.add(item_id)
            results.append({"id": item_id, "content": text, "score": 0.0,
                            "metadata": {**entry["metadata"], "chunk_index": page - 1,
                                         "page_index": page},
                            "retrieval_method": "pageindex"})
    return results


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Search configured existing documents within one shared polling deadline.

    The provider has no calibrated score: interleave per-document rankings and
    assign reciprocal output rank (not confidence, and not another RRF pass).
    """
    if not query.strip() or top_k <= 0:
        return []
    _require_key()
    entries = _load_documents()
    deadline = _deadline(SEARCH_TIMEOUT)
    rankings = []
    for entry in entries:
        doc_id = quote(entry["doc_id"], safe="")
        _wait(f"/doc/{doc_id}/?type=tree", deadline, ready=True)
        response = _request("POST", "/retrieval/", deadline,
                            json={"doc_id": entry["doc_id"], "query": query, "thinking": False})
        retrieval_id = quote(_identifier(response, "retrieval_id"), safe="")
        response = _wait(f"/retrieval/{retrieval_id}/", deadline)
        rankings.append(_parse_nodes(response, entry))
    results, seen = [], set()
    for rank in range(max(map(len, rankings), default=0)):
        for ranking in rankings:
            if rank < len(ranking) and ranking[rank]["id"] not in seen:
                item = ranking[rank].copy()
                seen.add(item["id"])
                item["score"] = 1.0 / (len(results) + 1)
                results.append(item)
                if len(results) == top_k:
                    validate_search_results(results, top_k=top_k, expected_method="pageindex")
                    return results
    validate_search_results(results, top_k=top_k, expected_method="pageindex")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search existing PageIndex documents")
    parser.add_argument("query")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(pageindex_search(args.query, args.top_k), ensure_ascii=False, indent=2))
