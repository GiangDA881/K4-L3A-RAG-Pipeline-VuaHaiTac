"""List xKiro chat models, with a local snapshot of the free catalog."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

from .llm_client import DEFAULT_FREE_MODEL, DEFAULT_XKIRO_BASE_URL


SNAPSHOT_PATH = Path(__file__).with_name("xkiro_free_models.json")
MODELS_URL = f"{DEFAULT_XKIRO_BASE_URL}/models"


def load_free_model_snapshot() -> dict:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def fetch_models(access_tier: str | None = "free") -> list[dict]:
    with urlopen(MODELS_URL, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    models = payload.get("data") or []
    if access_tier:
        models = [item for item in models if item.get("access_tier") == access_tier]
    return models


def default_free_model() -> str:
    snapshot = load_free_model_snapshot()
    return snapshot.get("default_model") or DEFAULT_FREE_MODEL


if __name__ == "__main__":
    snapshot = load_free_model_snapshot()
    print(f"Default: {snapshot['default_model']}")
    print(f"Snapshot ({len(snapshot['models'])} free models):")
    for item in snapshot["models"]:
        print(f"  {item['id']}")
    print()
    try:
        live = fetch_models("free")
    except OSError as exc:
        print(f"Live catalog unavailable: {exc}")
    else:
        print(f"Live catalog ({len(live)} free models):")
        for item in live:
            marker = " *" if item.get("id") == snapshot["default_model"] else ""
            print(f"  {item.get('id')}{marker}")
