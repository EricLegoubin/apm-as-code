"""Un cas par règle du catalogue (docs/02-prd.md §3) : le catalogue d'exemple est modifié pour violer la règle."""
from __future__ import annotations

import pytest

APP = "applications/app-kyc/application.yaml"
KYC_REL = "applications/app-kyc/releases.yaml"
KYC_PLN = "applications/app-kyc/planning.yaml"
EC_ITF = "applications/app-espace-client/interfaces.yaml"
EC_REL = "applications/app-espace-client/releases.yaml"


def ec_release(version):
    def get(d):
        return next(r for r in d["application"] if r["version"] == version)
    return get


def plan(version):
    def get(d):
        return next(p for p in d["releases"] if p["version"] == version)
    return get


CASES = {
    "STR-001": lambda r: r.path(APP).write_text(r.path(APP).read_text() + "\nname: doublon\n"),
    "STR-002": lambda r: r.edit(APP, lambda d: d.update(id="kyc")),
    "STR-003": lambda r: r.path(APP).unlink(),
    "STR-004": lambda r: r.path("applications/app-kyc/notes.txt").write_text("x"),
    "ID-001": lambda r: r.edit(APP, lambda d: d.update(id="app-kyc-bis")),
    "ID-002": lambda r: r.edit("referentials/organisation.yaml", lambda d: d["units"].append(dict(d["units"][0]))),
    "ID-003": lambda r: r.edit(APP, lambda d: d["aliases"].append("onboarding")),
    "REF-001": lambda r: r.edit(APP, lambda d: d["organisation"].update(owner="org-inconnue")),
    "REF-002": lambda r: r.edit(APP, lambda d: d.update(capabilities=["cap-inconnue"])),
    "REF-003": lambda r: r.edit("applications/app-kyc/composition.yaml",
                                lambda d: d["solutions"].append({"solution": "sol-inconnue", "usage": "x"})),
    "REF-004": lambda r: r.edit("referentials/capabilities.yaml",
                                lambda d: d["capabilities"][0].update(parent="cap-inconnue")),
    "REF-005": lambda r: r.edit(APP, lambda d: d.update(capabilities=["cap-relation-client"])),
    "CMP-001": lambda r: r.edit("applications/app-kyc/composition.yaml",
                                lambda d: d["components"].append({"id": "cmp-tc-api", "name": "x", "type": "backend"})),
    "CMP-002": lambda r: r.edit("applications/app-kyc/composition.yaml", lambda d: d.update(components=[])),
    "ITF-001": lambda r: r.edit("applications/app-kyc/interfaces.yaml",
                                lambda d: d["provides"][0].update(component="cmp-tc-api")),
    "ITF-002": lambda r: r.edit(EC_ITF, lambda d: d["consumes"][0].update(interface="itf-inconnue")),
    "ITF-003": lambda r: r.edit(EC_ITF, lambda d: d["consumes"][0].update(component="cmp-tc-api")),
    "ITF-004": lambda r: r.edit("applications/app-tenue-compte/interfaces.yaml", lambda d: d.update(
        consumes=[{"interface": "itf-compte-api", "component": "cmp-tc-batch"}])),
    "ITF-005": lambda r: None,  # présent dans l'exemple : itf-compte-evenements
    "REL-001": lambda r: r.edit(KYC_REL, lambda d: d["components"].update({"cmp-tc-api": [{"version": "1.0.0"}]})),
    "REL-002": lambda r: r.edit(KYC_REL, lambda d: d["application"].reverse()),
    "REL-003": lambda r: r.edit(KYC_REL, lambda d: d["application"][1]["components"].update(
        {"cmp-kyc-connecteur": "9.9.9"})),
    "REL-004": lambda r: r.edit(EC_REL, lambda d: ec_release("2026.12")(d)["requires"].append(
        {"application": "app-inconnue", "version": ">=1"})),
    "REL-005": lambda r: r.edit(EC_REL, lambda d: ec_release("2026.12")(d)["requires"][0].update(version=">=9")),
    "REL-006": lambda r: r.edit("applications/app-terminal-buraliste/releases.yaml", lambda d: d["application"][0]
                                .update(requires=[{"application": "app-kyc", "version": ">=1.8"}])),
    "REL-007": lambda r: r.edit("applications/app-tenue-compte/releases.yaml", lambda d: d["application"][2]
                                .update(requires=[{"application": "app-espace-client", "version": ">=2026.10"}])),
    "PLN-001": lambda r: r.edit(KYC_PLN, lambda d: d["releases"].append(
        {"version": "3.0", "date": "2027-03-01", "status": "planned"})),
    "PLN-002": lambda r: r.edit(KYC_PLN, lambda d: plan("2.0")(d).update(date="2026-01-01")),
    "PLN-003": lambda r: r.edit(KYC_PLN, lambda d: d["releases"].remove(plan("2.0")(d))),
    "PLN-004": lambda r: r.edit(KYC_PLN, lambda d: plan("2.0")(d).update(date="2026-11-30")),
    "PLN-005": lambda r: r.edit(KYC_PLN, lambda d: plan("2.0")(d).update(status="delivered")),
    "PLN-006": lambda r: None,  # présent dans l'exemple : app-ouverture-compte 7.2
}


@pytest.mark.parametrize("rule_id", sorted(CASES))
def test_rule_detects_violation(repo, rule_id):
    CASES[rule_id](repo)
    assert rule_id in repo.rules()


def test_example_catalog_has_no_error_nor_warning(repo):
    blocking = [f for f in repo.findings() if f.severity != "info"]
    assert blocking == [], "\n".join(f"{f.rule} {f.file}:{f.line} {f.message}" for f in blocking)


def test_finding_is_located_on_file_and_line(repo):
    CASES["REF-001"](repo)
    f = next(f for f in repo.findings() if f.rule == "REF-001")
    assert f.file.endswith("app-kyc/application.yaml") and f.line > 1 and f.app == "app-kyc"


def test_component_level_dependency_is_checked_against_planning(repo):
    """S2.6 : la dépendance cmp-ec-bff 5.1.0 → cmp-pc-cartes >=2.1 s'applique à la version qui embarque le BFF."""
    repo.edit(EC_REL, lambda d: ec_release("2026.12")(d).pop("requires"))
    repo.edit("applications/app-espace-client/planning.yaml", lambda d: plan("2026.12")(d).update(date="2026-11-25"))
    msgs = [f.message for f in repo.findings() if f.rule == "PLN-004"]
    assert any("cmp-pc-cartes" in m for m in msgs)


def test_cancelled_release_does_not_satisfy_dependency(repo):
    repo.edit(KYC_PLN, lambda d: plan("2.0")(d).update(status="cancelled"))
    assert "PLN-003" in repo.rules()
