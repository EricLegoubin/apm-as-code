from __future__ import annotations

from collections import defaultdict

from ..findings import rule


@rule("ID-001", "error", "Identifiant d'application = nom du répertoire")
def app_id_matches_dir(cat):
    for app in cat.apps.values():
        if app.application["id"] != app.id:
            yield app.application, (f"l'identifiant « {app.application['id']} » doit être égal au nom du "
                                    f"répertoire « {app.id} » (renommer l'un ou l'autre)")


@rule("ID-002", "error", "Unicité des identifiants")
def unique_ids(cat):
    lists = [(cat.referentials["organisation"].get("units", []), "unité"),
             (cat.referentials["capabilities"].get("capabilities", []), "capacité"),
             (cat.referentials["solutions"].get("solutions", []), "solution")]
    for items, label in lists:
        seen = set()
        for item in items:
            if item["id"] in seen:
                yield item, f"{label} « {item['id']} » déclarée plusieurs fois"
            seen.add(item["id"])
    seen_itf: dict[str, str] = {}
    for app in cat.apps.values():
        for itf in app.provides:
            if itf["id"] in seen_itf:
                yield itf, f"interface « {itf['id']} » déjà déclarée par {seen_itf[itf['id']]}"
            else:
                seen_itf[itf["id"]] = app.id


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())


@rule("ID-003", "warning", "Pas de collision de dénomination ou d'alias entre applications")
def name_collisions(cat):
    names: dict[str, list[str]] = defaultdict(list)
    for app in cat.apps.values():
        for n in {_norm(app.application["name"]), *(_norm(a) for a in app.application.get("aliases", []))}:
            names[n].append(app.id)
    for app in cat.apps.values():
        for n in {_norm(app.application["name"]), *(_norm(a) for a in app.application.get("aliases", []))}:
            others = [a for a in names[n] if a != app.id]
            if others:
                yield app.application, f"« {n} » désigne aussi {', '.join(others)} : lever l'ambiguïté"
