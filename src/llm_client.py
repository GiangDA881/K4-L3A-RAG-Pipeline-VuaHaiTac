"""OpenAI-compatible LLM client, defaulting to xKiro free models."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEFAULT_XKIRO_BASE_URL = "https://api.xkiro.com/v1"
DEFAULT_FREE_MODEL = "qwen/qwen3.8-omni-flash:free"
SAFE_REFUSAL = "Tôi không thể xác minh thông tin này từ nguồn hiện có."


def llm_provider() -> str:
    return (os.getenv("LLM_PROVIDER") or "xkiro").strip().lower()


def llm_model() -> str:
    return (os.getenv("LLM_MODEL") or DEFAULT_FREE_MODEL).strip()


def xkiro_api_key() -> str:
    return (os.getenv("XKIRO_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()


def xkiro_base_url() -> str:
    return (
        os.getenv("XKIRO_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_XKIRO_BASE_URL
    ).strip()


def openai_compatible_client() -> OpenAI:
    """Client for xKiro or any OpenAI-compatible gateway."""
    provider = llm_provider()
    if provider in {"xkiro", "openai"}:
        if provider == "xkiro":
            api_key = xkiro_api_key()
            base_url = xkiro_base_url()
        else:
            api_key = (os.getenv("OPENAI_API_KEY") or os.getenv("XKIRO_API_KEY") or "").strip()
            base_url = (os.getenv("OPENAI_BASE_URL") or "").strip() or None
        if not api_key:
            raise RuntimeError(
                "Thiếu API key. Điền XKIRO_API_KEY (hoặc OPENAI_API_KEY) trong .env. "
                "Tạo key tại https://xkiro.com/dashboard"
            )
        kwargs: dict = {
            "api_key": api_key,
            "timeout": 120.0,
            "max_retries": 2,
        }
        if provider == "xkiro" or base_url:
            kwargs["base_url"] = base_url or DEFAULT_XKIRO_BASE_URL
        return OpenAI(**kwargs)
    raise ValueError(f"Unsupported OpenAI-compatible provider: {provider}")


def chat_completion(system_prompt: str, user_message: str, *, model: str | None = None) -> str:
    """Call the configured chat model and return plain text."""
    provider = llm_provider()
    if provider in {"xkiro", "openai"}:
        client = openai_compatible_client()
        response = client.chat.completions.create(
            model=model or llm_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            top_p=0.9,
        )
        content = response.choices[0].message.content
        if not content or not str(content).strip():
            return SAFE_REFUSAL
        return str(content).strip()

    if provider == "gemini":
        from google import genai

        api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("Thiếu GEMINI_API_KEY trong .env")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model or llm_model(),
            contents=f"{system_prompt}\n\n{user_message}",
        )
        text = getattr(response, "text", None)
        if not text or not str(text).strip():
            return SAFE_REFUSAL
        return str(text).strip()

    if provider == "anthropic":
        import anthropic

        api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError("Thiếu ANTHROPIC_API_KEY trong .env")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model or llm_model(),
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=0.3,
            top_p=0.9,
        )
        text_parts = [
            block.text
            for block in response.content
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        if not text_parts:
            return SAFE_REFUSAL
        return "\n".join(text_parts).strip()

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


if __name__ == "__main__":
    print(f"provider={llm_provider()}")
    print(f"model={llm_model()}")
    print(f"base_url={xkiro_base_url()}")
    if llm_provider() == "xkiro" and not xkiro_api_key():
        print("Thiếu XKIRO_API_KEY — chưa gọi chat. Điền key rồi chạy lại: python -m src.llm_client")
    else:
        print(chat_completion("Reply with exactly: ok", "ping"))
