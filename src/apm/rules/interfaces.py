from __future__ import annotations

from ..findings import rule


def _own(cat, app, cmp_id):
    return cat.component_app(cmp_id) == app.id and any(c["id"] == cmp_id for c in app.components)


@rule("ITF-001", "error", "Interface exposée portée par un composant de l'application")
def provider_component(cat):
    for app in cat.apps.values():
        for itf in app.provides:
            if not _own(cat, app, itf["component"]):
                yield itf, f"« {itf['id']} » : le composant « {itf['component']} » n'appartient pas à {app.id}"


@rule("ITF-002", "error", "Interface consommée existante")
def consumed_exists(cat):
    for app in cat.apps.values():
        for c in app.consumes:
            if "interface" in c and c["interface"] not in cat.interfaces:
                yield c, f"interface « {c['interface']} » exposée par aucune application"


@rule("ITF-003", "error", "Composant consommateur appartenant à l'application")
def consumer_component(cat):
    for app in cat.apps.values():
        for c in app.consumes:
            if not _own(cat, app, c["component"]):
                yield c, f"le composant consommateur « {c['component']} » n'appartient pas à {app.id}"


@rule("ITF-004", "warning", "Pas de consommation de sa propre interface")
def self_consumption(cat):
    for app in cat.apps.values():
        for c in app.consumes:
            provider = cat.interfaces.get(c.get("interface"))
            if provider and provider[0] == app.id:
                yield c, f"« {c['interface']} » est exposée par {app.id} elle-même : échange interne, à retirer"


@rule("ITF-005", "info", "Interface exposée avec au moins un consommateur")
def unused_interface(cat):
    for app in cat.apps.values():
        for itf in app.provides:
            if not cat.consumers.get(itf["id"]) and not itf.get("external_consumers"):
                yield itf, f"« {itf['id']} » n'a aucun consommateur déclaré"
