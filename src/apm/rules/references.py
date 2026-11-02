from __future__ import annotations

from ..findings import rule


@rule("REF-001", "error", "Unités d'organisation référencées existantes")
def org_refs(cat):
    for app in cat.apps.values():
        org = app.application["organisation"]
        for role in ("owner", "maintainer", "operator"):
            if org[role] not in cat.units:
                yield org, f"{role} : unité « {org[role]} » inconnue dans referentials/organisation.yaml"


@rule("REF-002", "error", "Capacités référencées existantes")
def capability_refs(cat):
    for app in cat.apps.values():
        for cap in app.application["capabilities"]:
            if cap not in cat.capabilities:
                yield app.application, f"capacité « {cap} » inconnue dans referentials/capabilities.yaml"


@rule("REF-003", "error", "Solutions référencées existantes")
def solution_refs(cat):
    for app in cat.apps.values():
        for s in (app.composition or {}).get("solutions", []):
            if s["solution"] not in cat.solutions:
                yield s, f"solution « {s['solution']} » inconnue dans referentials/solutions.yaml"


@rule("REF-004", "error", "Parents des référentiels existants et sans cycle")
def parents(cat):
    for index, label in ((cat.units, "unité"), (cat.capabilities, "capacité")):
        for item in index.values():
            parent = item.get("parent")
            if parent is None:
                continue
            if parent not in index:
                yield item, f"{label} « {item['id']} » : parent « {parent} » inconnu"
                continue
            seen, cur = {item["id"]}, parent
            while cur is not None and cur in index:
                if cur in seen:
                    yield item, f"{label} « {item['id']} » : cycle dans la hiérarchie des parents"
                    break
                seen.add(cur)
                cur = index[cur].get("parent")


@rule("REF-005", "warning", "Rattachement à une capacité feuille")
def leaf_capabilities(cat):
    parents_ = {c.get("parent") for c in cat.capabilities.values()}
    for app in cat.apps.values():
        for cap in app.application["capabilities"]:
            if cap in cat.capabilities and cap in parents_:
                yield app.application, (f"« {cap} » a des sous-capacités : rattacher l'application à la "
                                        f"sous-capacité qu'elle réalise")
