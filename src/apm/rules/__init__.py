"""Règles sémantiques. Chaque module enregistre ses règles via @rule à l'import."""
from __future__ import annotations

from ..findings import RULES, Finding
from ..model import Catalog
from . import composition, identity, interfaces, planning, references, releases  # noqa: F401  (enregistrement)


def run(catalog: Catalog) -> list[Finding]:
    findings = list(catalog.load_findings)
    for r in RULES.values():
        if r.check is None:
            continue
        for anchor, message in r.check(catalog):
            file, line, app = catalog.locate(anchor)
            findings.append(Finding(file, line, r.id, message, r.severity, app))
    return sorted(findings)
