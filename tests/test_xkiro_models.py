import pytest

from src.llm_client import (
    DEFAULT_FREE_MODEL,
    DEFAULT_XKIRO_BASE_URL,
    openai_compatible_client,
)
from src.xkiro_models import default_free_model, load_free_model_snapshot


def test_free_model_snapshot_includes_qwen_omni_flash():
    snapshot = load_free_model_snapshot()
    ids = {item["id"] for item in snapshot["models"]}
    assert snapshot["default_model"] == "qwen/qwen3.8-omni-flash:free"
    assert DEFAULT_FREE_MODEL in ids
    assert snapshot["source"] == "https://api.xkiro.com/v1/models"
    assert all(":free" in item["id"] or item["owned_by"] for item in snapshot["models"])
    assert default_free_model() == DEFAULT_FREE_MODEL


def test_xkiro_base_url_has_v1_suffix():
    assert DEFAULT_XKIRO_BASE_URL.endswith("/v1")


def test_xkiro_client_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xkiro")
    monkeypatch.delenv("XKIRO_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="XKIRO_API_KEY"):
        openai_compatible_client()
