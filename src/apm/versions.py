"""Versions et contraintes PEP 440 (ADR-003)."""
from __future__ import annotations

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


def parse_version(text: str) -> Version | None:
    try:
        return Version(str(text))
    except InvalidVersion:
        return None


def parse_constraint(text: str) -> SpecifierSet | None:
    text = str(text).strip()
    if text[:1].isdigit():
        text = "==" + text
    try:
        return SpecifierSet(text)
    except InvalidSpecifier:
        return None


def satisfies(constraint: SpecifierSet, version: str) -> bool:
    parsed = parse_version(version)
    return parsed is not None and constraint.contains(parsed, prereleases=True)
