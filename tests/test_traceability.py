"""Constitution §2 : une règle = un ID présent dans le PRD, le code et les tests."""
import re

from apm.findings import RULES
import apm.rules  # noqa: F401

from .conftest import ROOT
from .test_rules import CASES

ID = re.compile(r"^\| ([A-Z]{2,3}-\d{3}) \| (error|warning|info) \|", re.M)


def test_rules_are_specified_implemented_and_tested():
    prd = dict(ID.findall((ROOT / "docs" / "02-prd.md").read_text(encoding="utf-8")))
    assert set(prd) == set(RULES), "écart entre le catalogue du PRD et le registre du code"
    assert {k: v.severity for k, v in RULES.items()} == prd, "sévérité différente entre PRD et code"
    assert set(CASES) == set(RULES), "règle sans test (ou test sans règle)"
