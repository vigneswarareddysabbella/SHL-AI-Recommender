import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "shl_catalog.json"


@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    with CATALOG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_by_name(name: str) -> dict[str, Any] | None:
    normalized = name.strip().lower()
    for item in load_catalog():
        if item["name"].lower() == normalized:
            return item
    for item in load_catalog():
        plain = item["name"].lower().replace("(new)", "").strip()
        if normalized in item["name"].lower() or normalized in plain:
            return item
    return None
