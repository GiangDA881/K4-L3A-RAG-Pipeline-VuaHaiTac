"""
Task 10 — Generation có citation.

Hướng dẫn:
    1. Retrieve top-k chunks.
    2. Reorder để giảm lost-in-the-middle.
    3. Format context kèm title và source.
    4. Gọi provider được chọn trong .env.
    5. Trả answer, sources và retrieval_source.

Nếu context không đủ hoặc provider lỗi, trả safe refusal; không bịa thông tin.
"""

import os

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


load_dotenv()

TOP_K = 5
TOP_P = 0.9
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "xkiro")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen/qwen3.8-omni-flash:free")

SYSTEM_PROMPT = """Trả lời chỉ từ context được cung cấp.
Mỗi khẳng định phải có citation. Nếu thiếu evidence, hãy từ chối xác minh."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Đưa chunks quan trọng về đầu và cuối context."""
    if len(chunks) <= 2:
        return list(chunks)
    return chunks[::2] + chunks[1::2][::-1]


def format_context(chunks: list[dict]) -> str:
    """Tạo context có title và source label."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        parts.append(
            f"[Document {index} | Title: {metadata['title']} | "
            f"Source: {metadata['source']}]\n{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Gọi xKiro (OpenAI-compatible), OpenAI, Gemini hoặc Anthropic theo .env."""
    from .llm_client import chat_completion

    return chat_completion(system_prompt, user_message)


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Trả về GenerationResult."""
    # TODO: Implement end-to-end generation.
    #
    # chunks = retrieve(query, top_k=top_k)
    # if not chunks:
    #     return {
    #         "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
    #         "sources": [],
    #         "retrieval_source": "none",
    #     }
    # reordered = reorder_for_llm(chunks)
    # context = format_context(reordered)
    # user_message = f"Context:\n{context}\n\nQuestion: {query}"
    # answer = call_llm(SYSTEM_PROMPT, user_message)
    # return {
    #     "answer": answer,
    #     "sources": chunks,
    #     "retrieval_source": chunks[0]["retrieval_method"],
    # }
    raise NotImplementedError("Implement generate_with_citation")


if __name__ == "__main__":
    print(generate_with_citation("test query"))
