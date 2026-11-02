from __future__ import annotations

from ..findings import rule


@rule("CMP-001", "error", "Un composant appartient à une seule application")
def single_owner(cat):
    for app in cat.apps.values():
        for c in app.components:
            owners = cat.component_owners[c["id"]]
            if len(owners) > 1:
                others = sorted(set(owners) - {app.id}) or [app.id + " (deux fois)"]
                yield c, f"composant « {c['id']} » aussi déclaré par {', '.join(others)} : un seul propriétaire"


@rule("CMP-002", "warning", "Application en build ou run avec au moins un composant")
def has_components(cat):
    for app in cat.apps.values():
        if app.application["lifecycle"] in ("build", "run") and not app.components:
            yield app.application, "application en build/run sans composant : compléter composition.yaml"
