from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

import pytest
import yaml

from apm.loader import load_yaml
from apm.model import Catalog
from apm.rules import run

ROOT = Path(__file__).resolve().parents[1]
TODAY = dt.date(2026, 11, 2)


class Repo:
    """Copie du catalogue d'exemple, modifiable fichier par fichier."""

    def __init__(self, tmp: Path):
        self.root = tmp / "catalog"
        shutil.copytree(ROOT / "catalog", self.root)

    def path(self, rel: str) -> Path:
        return self.root / rel

    def edit(self, rel: str, fn) -> None:
        data, _ = load_yaml(self.path(rel))
        fn(data)
        self.path(rel).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def findings(self):
        return run(Catalog.load(self.root, TODAY))

    def rules(self) -> set[str]:
        return {f.rule for f in self.findings()}


@pytest.fixture
def repo(tmp_path) -> Repo:
    return Repo(tmp_path)
