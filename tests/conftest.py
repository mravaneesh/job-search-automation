from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    def _load(name: str):
        path = FIXTURES / name
        if name.endswith(".json"):
            return json.loads(path.read_text())
        return path.read_text()

    return _load
