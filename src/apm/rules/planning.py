from __future__ import annotations

import datetime as dt

from ..findings import rule
from ..versions import parse_constraint, parse_version, satisfies


def _active(app):
    return [p for p in app.planned if p["status"] != "cancelled"]


@rule("PLN-001", "error", "Version planifiée existante dans la séquence")
def planned_exists(cat):
    for app in cat.apps.values():
        known = {r["version"] for r in app.app_releases}
        for p in app.planned:
            if p["version"] not in known:
                yield p, f"version « {p['version']} » absente de releases.yaml › application"


@rule("PLN-002", "error", "Dates dans l'ordre de la séquence")
def dates_ordered(cat):
    for app in cat.apps.values():
        order = {r["version"]: i for i, r in enumerate(app.app_releases)}
        entries = sorted((order[p["version"]], p) for p in _active(app) if p["version"] in order)
        latest = None
        for _, p in entries:
            d = dt.date.fromisoformat(p["date"])
            if latest and d < latest[0]:
                yield p, (f"{app.id} {p['version']} le {p['date']} : antérieure à {latest[1]} "
                          f"({latest[0].isoformat()}) qui la précède dans la séquence")
            if latest is None or d > latest[0]:
                latest = (d, p["version"])


def _dependency_checks(cat):
    """Pour chaque version planifiée : (entrée de planning, app, version, cible, contrainte, dispo la plus tôt)."""
    for app in cat.apps.values():
        releases = {r["version"]: r for r in app.app_releases}
        for p in _active(app):
            rel = releases.get(p["version"])
            if rel is None:
                continue
            d = dt.date.fromisoformat(p["date"])
            for kind, target, constraint, _ in cat.version_requirements(app.id, rel):
                spec = parse_constraint(constraint)
                if spec is None or not any(satisfies(spec, v) for v in cat.target_versions(kind, target)):
                    continue  # REL-004 / REL-005
                dates = [cat.availability[(kind, target, v)] for v in cat.target_versions(kind, target)
                         if satisfies(spec, v) and (kind, target, v) in cat.availability]
                yield p, app, d, target, constraint, min(dates) if dates else None


@rule("PLN-003", "error", "Dépendance satisfaite par une version planifiée")
def dependency_planned(cat):
    for p, app, d, target, constraint, earliest in _dependency_checks(cat):
        if earliest is None:
            yield p, (f"{app.id} {p['version']} requiert {target} {constraint}, qui n'est pas planifiée : "
                      f"planifier la version de {target} ou retirer la dépendance")


@rule("PLN-004", "error", "Dépendance disponible au plus tard à la date de livraison")
def dependency_on_time(cat):
    for p, app, d, target, constraint, earliest in _dependency_checks(cat):
        if earliest is not None and earliest > d:
            yield p, (f"{app.id} {p['version']} le {d.isoformat()} requiert {target} {constraint}, "
                      f"disponible au plus tôt le {earliest.isoformat()} : décaler l'une des deux dates")


@rule("PLN-005", "warning", "Statut cohérent avec la date")
def status_vs_date(cat):
    for app in cat.apps.values():
        for p in app.planned:
            d = dt.date.fromisoformat(p["date"])
            if p["status"] == "delivered" and d > cat.today:
                yield p, f"{app.id} {p['version']} marquée delivered avec une date future ({p['date']})"
            elif p["status"] in ("planned", "confirmed") and d < cat.today:
                yield p, (f"{app.id} {p['version']} prévue le {p['date']}, date passée : "
                          f"passer en delivered, ou replanifier")


@rule("PLN-006", "info", "Version d'application planifiée")
def release_planned(cat):
    for app in cat.apps.values():
        planned = {p["version"] for p in app.planned}
        for rel in app.app_releases:
            if rel["version"] not in planned:
                yield rel, f"{app.id} {rel['version']} n'a pas de date de mise à disposition"
