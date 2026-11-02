"""Constats et registre des règles (constitution §2)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

SEVERITIES = ("error", "warning", "info")


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    title: str
    check: Callable | None = None  # None : règle appliquée au chargement (STR-*)


@dataclass(order=True)
class Finding:
    file: str
    line: int
    rule: str
    message: str = field(compare=False)
    severity: str = field(compare=False, default="error")
    app: str | None = field(compare=False, default=None)

    def as_dict(self) -> dict:
        return {"rule": self.rule, "severity": self.severity, "file": self.file,
                "line": self.line or None, "app": self.app, "message": self.message}


RULES: dict[str, Rule] = {}


def declare(rule_id: str, severity: str, title: str, check: Callable | None = None) -> Rule:
    assert severity in SEVERITIES, severity
    assert rule_id not in RULES, f"règle {rule_id} déclarée deux fois"
    RULES[rule_id] = Rule(rule_id, severity, title, check)
    return RULES[rule_id]


def rule(rule_id: str, severity: str, title: str):
    """Décorateur : la fonction reçoit un Catalog et produit des (règle, objet|lieu, message)."""
    def wrap(fn: Callable[..., Iterable]) -> Callable:
        declare(rule_id, severity, title, fn)
        return fn
    return wrap
