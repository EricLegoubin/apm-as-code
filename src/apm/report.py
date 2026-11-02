"""Formats de sortie des constats (FR-11, FR-12)."""
from __future__ import annotations

import json
from collections import Counter

from .findings import Finding

LABEL = {"error": "ERREUR", "warning": "ALERTE", "info": "INFO"}
GH = {"error": "error", "warning": "warning", "info": "notice"}


def counts(findings: list[Finding]) -> Counter:
    return Counter(f.severity for f in findings)


def as_text(findings: list[Finding], total: list[Finding] | None = None) -> str:
    lines = [f"{LABEL[f.severity]:<7}{f.rule:<9}{f.file}{':' + str(f.line) if f.line else ''}\n"
             f"{'':16}{f.message}" for f in findings]
    c = counts(total if total is not None else findings)
    lines.append(f"\n{c['error']} erreur(s), {c['warning']} alerte(s), {c['info']} info(s)")
    return "\n".join(lines)


def as_github(findings: list[Finding], total: list[Finding] | None = None) -> str:
    out = []
    for f in findings:
        loc = f"file={f.file}" + (f",line={f.line}" if f.line else "")
        msg = f.message.replace("%", "%25").replace("\n", "%0A")
        out.append(f"::{GH[f.severity]} {loc},title={f.rule}::{msg}")
    c = counts(total if total is not None else findings)
    out.append(f"{c['error']} erreur(s), {c['warning']} alerte(s), {c['info']} info(s)")
    return "\n".join(out)


def as_json(findings: list[Finding], total=None) -> str:
    return json.dumps([f.as_dict() for f in findings], ensure_ascii=False, indent=2)


FORMATS = {"text": as_text, "github": as_github, "json": as_json}
