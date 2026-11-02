from __future__ import annotations

from ..findings import rule
from ..versions import parse_constraint, parse_version, satisfies


@rule("REL-001", "error", "Séquence de versions sur un composant de l'application")
def sequence_component(cat):
    for app in cat.apps.values():
        own = {c["id"] for c in app.components}
        for cmp_id, seq in app.component_sequences.items():
            if cmp_id not in own:
                yield seq, f"séquence de versions pour « {cmp_id} », qui n'est pas un composant de {app.id}"


def _check_sequence(seq, label):
    previous = None
    seen = set()
    for item in seq:
        v = parse_version(item["version"])
        if v is None:
            yield item, f"{label} : « {item['version']} » n'est pas une version valide (ex. 3.2.0, 2026.10)"
            continue
        if v in seen:
            yield item, f"{label} : version « {item['version']} » en double"
        elif previous is not None and v <= previous:
            yield item, f"{label} : « {item['version']} » doit être supérieure à la version qui la précède"
        seen.add(v)
        previous = v if previous is None or v > previous else previous


@rule("REL-002", "error", "Versions valides, uniques, strictement croissantes")
def sequences_ordered(cat):
    for app in cat.apps.values():
        for cmp_id, seq in app.component_sequences.items():
            yield from _check_sequence(seq, cmp_id)
        yield from _check_sequence(app.app_releases, app.id)


@rule("REL-003", "error", "Version d'application composée de versions de composants déclarées")
def release_composition(cat):
    for app in cat.apps.values():
        own = {c["id"] for c in app.components}
        for rel in app.app_releases:
            for cmp_id, version in rel["components"].items():
                if cmp_id not in own:
                    yield rel, f"{app.id} {rel['version']} : « {cmp_id} » n'est pas un composant de {app.id}"
                elif version not in {r["version"] for r in app.component_sequences.get(cmp_id, [])}:
                    yield rel, (f"{app.id} {rel['version']} : version {version} de « {cmp_id} » absente de sa "
                                f"séquence (releases.yaml › components › {cmp_id})")


def _requirements(cat):
    """Toutes les dépendances déclarées : (app, type, cible, contrainte, ancrage)."""
    for app in cat.apps.values():
        for rel in app.app_releases:
            for r in rel.get("requires", []):
                yield app, "application", r["application"], r["version"], r
        for seq in app.component_sequences.values():
            for cr in seq:
                for r in cr.get("requires", []):
                    yield app, "component", r["component"], r["version"], r


@rule("REL-004", "error", "Cible de dépendance existante, distincte, contrainte valide")
def requirement_target(cat):
    for app, kind, target, constraint, anchor in _requirements(cat):
        if kind == "application" and target == app.id:
            yield anchor, f"{app.id} ne peut pas dépendre d'elle-même"
        elif kind == "application" and target not in cat.apps:
            yield anchor, f"application « {target} » inconnue"
        elif kind == "component" and cat.component_app(target) is None:
            yield anchor, f"composant « {target} » déclaré par aucune application"
        elif parse_constraint(constraint) is None:
            yield anchor, f"contrainte « {constraint} » invalide (ex. >=1.4, >=1.4,<2, ~=3.2)"


@rule("REL-005", "error", "Contrainte satisfaite par au moins une version de la cible")
def requirement_satisfiable(cat):
    for app, kind, target, constraint, anchor in _requirements(cat):
        spec = parse_constraint(constraint)
        versions = cat.target_versions(kind, target)
        if spec is None or not versions or (kind == "application" and target == app.id):
            continue
        if not any(satisfies(spec, v) for v in versions):
            yield anchor, (f"aucune version de « {target} » ne satisfait « {constraint} » "
                           f"(connues : {', '.join(versions)})")


def _target_app(cat, kind, target):
    return target if kind == "application" else cat.component_app(target)


@rule("REL-006", "warning", "Dépendance de version adossée à une interface consommée")
def requirement_has_interface(cat):
    for app, kind, target, _, anchor in _requirements(cat):
        target_app = _target_app(cat, kind, target)
        if target_app and target_app != app.id and target_app in cat.apps \
                and target_app not in cat.interface_dependencies(app.id):
            yield anchor, (f"{app.id} dépend d'une version de {target_app} sans consommer aucune de ses "
                           f"interfaces : déclarer l'interface dans interfaces.yaml ou retirer la dépendance")


@rule("REL-007", "warning", "Pas de cycle de dépendances de version entre applications")
def requirement_cycles(cat):
    graph: dict[str, set[str]] = {a: set() for a in cat.apps}
    anchors: dict[str, object] = {}
    for app, kind, target, _, anchor in _requirements(cat):
        t = _target_app(cat, kind, target)
        if t and t != app.id and t in graph:
            graph[app.id].add(t)
            anchors.setdefault(app.id, anchor)
    for scc in _strongly_connected(graph):
        if len(scc) > 1:
            first = min(scc)
            yield anchors[first], ("cycle de dépendances de livraison entre " + ", ".join(sorted(scc))
                                   + " : ces applications ne peuvent pas être livrées indépendamment")


def _strongly_connected(graph: dict[str, set[str]]) -> list[set[str]]:
    """Tarjan itératif."""
    index, low, on_stack, stack, out, counter = {}, {}, set(), [], [], [0]
    for root in sorted(graph):
        if root in index:
            continue
        work = [(root, iter(sorted(graph[root])))]
        index[root] = low[root] = counter[0]; counter[0] += 1
        stack.append(root); on_stack.add(root)
        while work:
            node, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = low[nxt] = counter[0]; counter[0] += 1
                    stack.append(nxt); on_stack.add(nxt)
                    work.append((nxt, iter(sorted(graph[nxt]))))
                elif nxt in on_stack:
                    low[node] = min(low[node], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                comp = set()
                while True:
                    w = stack.pop(); on_stack.discard(w); comp.add(w)
                    if w == node:
                        break
                out.append(comp)
    return out
