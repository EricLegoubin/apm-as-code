"""Génération du site statique (FR-20, FR-21) et de l'export JSON (FR-22)."""
from __future__ import annotations

import datetime as dt
import json
import shutil
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from ..findings import RULES, Finding
from ..model import App, Catalog
from ..report import counts
from ..versions import parse_constraint, satisfies

LIFECYCLE = {"planned": "Envisagée", "build": "En construction", "run": "En service",
             "retiring": "En retrait", "retired": "Retirée"}
STATUS = {"planned": "Prévue", "confirmed": "Confirmée", "delivered": "Livrée", "cancelled": "Annulée"}
ROLES = {"owner": "Propriétaire", "maintainer": "Mainteneur", "operator": "Exploitant"}
NAV = [("index.html", "Applications"), ("capabilities.html", "Capacités"), ("organisation.html", "Organisation"),
       ("solutions.html", "Solutions"), ("dependencies.html", "Dépendances"), ("roadmap.html", "Feuille de route"),
       ("quality.html", "Contrôles")]


def mid(text: str) -> str:
    """Identifiant Mermaid sûr."""
    return text.replace("-", "_").replace(".", "_")


def mlabel(text: str) -> str:
    return '"' + str(text).replace('"', "#quot;") + '"'


class View:
    def __init__(self, cat: Catalog, findings: list[Finding]):
        self.cat = cat
        self.findings = findings
        self.by_app: dict[str, list[Finding]] = defaultdict(list)
        for f in findings:
            if f.app:
                self.by_app[f.app].append(f)

    # ----- noms -----
    def unit(self, uid):
        return self.cat.units.get(uid, {"id": uid, "name": uid})

    def cap(self, cid):
        return self.cat.capabilities.get(cid, {"id": cid, "name": cid})

    def cap_path(self, cid):
        path, cur, seen = [], cid, set()
        while cur and cur in self.cat.capabilities and cur not in seen:
            seen.add(cur)
            path.insert(0, self.cat.capabilities[cur]["name"])
            cur = self.cat.capabilities[cur].get("parent")
        return " › ".join(path) or cid

    def app_name(self, aid):
        return self.cat.apps[aid].name if aid in self.cat.apps else aid

    # ----- dépendances -----
    def edges(self) -> dict[tuple[str, str], list[str]]:
        """(consommateur, fournisseur) → noms d'interfaces."""
        out: dict[tuple[str, str], list[str]] = defaultdict(list)
        for itf_id, consumers in self.cat.consumers.items():
            provider = self.cat.interfaces.get(itf_id)
            if not provider:
                continue
            for consumer, _ in consumers:
                if consumer != provider[0]:
                    out[(consumer, provider[0])].append(provider[1]["name"])
        return dict(sorted(out.items()))

    def used_by(self, aid) -> list[str]:
        return sorted({c for (c, p) in self.edges() if p == aid})

    def mermaid_graph(self, focus: str | None = None) -> str:
        lines = ["flowchart LR"]
        edges = self.edges()
        nodes = set(self.cat.apps) if focus is None else {focus} | {x for e in edges for x in e if focus in e}
        for aid in sorted(nodes):
            lines.append(f"  {mid(aid)}[{mlabel(self.app_name(aid))}]")
            link = f"{aid}.html" if focus else f"apps/{aid}.html"
            lines.append(f'  click {mid(aid)} "{link}"')
        for (c, p), names in edges.items():
            if c in nodes and p in nodes:
                lines.append(f"  {mid(c)} -->|{mlabel(', '.join(sorted(set(names))))}| {mid(p)}")
        if focus:
            lines.append(f"  style {mid(focus)} stroke-width:3px")
        return "\n".join(lines)

    # ----- versions -----
    def requirement_status(self, kind, target, constraint, date: dt.date | None):
        spec = parse_constraint(constraint)
        versions = self.cat.target_versions(kind, target) if spec else []
        ok_versions = [v for v in versions if satisfies(spec, v)]
        dates = [self.cat.availability[(kind, target, v)] for v in ok_versions
                 if (kind, target, v) in self.cat.availability]
        earliest = min(dates) if dates else None
        if not ok_versions:
            state = "ko"
        elif earliest is None:
            state = "unplanned"
        elif date is not None and earliest > date:
            state = "late"
        else:
            state = "ok"
        owner = target if kind == "application" else self.cat.component_app(target)
        return {"kind": kind, "target": target, "owner": owner, "constraint": constraint,
                "earliest": earliest, "state": state}

    def releases(self, app: App) -> list[dict]:
        plan = {p["version"]: p for p in app.planned}
        rows = []
        for rel in app.app_releases:
            p = plan.get(rel["version"])
            d = dt.date.fromisoformat(p["date"]) if p and p["status"] != "cancelled" else None
            reqs = [self.requirement_status(k, t, c, d)
                    for k, t, c, _ in self.cat.version_requirements(app.id, rel)]
            rows.append({"release": rel, "plan": p, "date": d, "requires": reqs,
                         "issue": any(r["state"] != "ok" for r in reqs)})
        return rows

    def current_release(self, app: App):
        delivered = [r for r in self.releases(app) if r["plan"] and r["plan"]["status"] == "delivered"]
        return delivered[-1]["release"] if delivered else None

    # ----- feuille de route -----
    def roadmap(self) -> list[dict]:
        rows = []
        for app in self.cat.apps.values():
            for r in self.releases(app):
                if r["plan"]:
                    rows.append({"app": app, **r})
        return sorted(rows, key=lambda r: (r["plan"]["date"], r["app"].id))

    def gantt(self) -> str:
        lines = ["gantt", "  dateFormat YYYY-MM-DD", "  axisFormat %b %Y"]
        by_app = defaultdict(list)
        for r in self.roadmap():
            by_app[r["app"].id].append(r)
        for i, (aid, rows) in enumerate(sorted(by_app.items())):
            lines.append(f"  section {self.app_name(aid)}")
            for j, r in enumerate(rows):
                st = r["plan"]["status"]
                tags = ["milestone"] + (["done"] if st == "delivered" else []) + (["crit"] if r["issue"] else []) \
                    + (["active"] if st == "confirmed" else [])
                lines.append(f"  {r['release']['version']} : {', '.join(tags)}, m{i}_{j}, {r['plan']['date']}, 0d")
        return "\n".join(lines)

    # ----- arbres -----
    def tree(self, index: dict[str, dict]) -> list[dict]:
        children = defaultdict(list)
        for item in index.values():
            children[item.get("parent")].append(item)

        def node(item, depth=0):
            kids = sorted(children.get(item["id"], []), key=lambda x: x["name"])
            return {"item": item, "children": [node(k, depth + 1) for k in kids]}
        return [node(i) for i in sorted(children[None], key=lambda x: x["name"])]

    def apps_by_capability(self) -> dict[str, list[App]]:
        out = defaultdict(list)
        for app in self.cat.apps.values():
            for c in app.application["capabilities"]:
                out[c].append(app)
        return out

    def apps_by_unit(self) -> dict[str, dict[str, list[App]]]:
        out: dict[str, dict[str, list[App]]] = defaultdict(lambda: defaultdict(list))
        for app in self.cat.apps.values():
            for role, uid in app.application["organisation"].items():
                out[uid][role].append(app)
        return out

    def apps_by_solution(self) -> dict[str, list[tuple[App, str]]]:
        out = defaultdict(list)
        for app in self.cat.apps.values():
            for s in (app.composition or {}).get("solutions", []):
                out[s["solution"]].append((app, s["usage"]))
        return out


def export(view: View) -> dict:
    cat = view.cat
    apps = []
    for app in cat.apps.values():
        a = app.application
        apps.append({
            **{k: a.get(k) for k in ("id", "name", "aliases", "external_refs", "summary", "description",
                                     "lifecycle", "links")},
            "capabilities": [{"id": c, "name": view.cap(c)["name"], "path": view.cap_path(c)} for c in a["capabilities"]],
            "organisation": {r: {"id": u, "name": view.unit(u)["name"]} for r, u in a["organisation"].items()},
            "components": app.components,
            "solutions": [{**s, "name": cat.solutions.get(s["solution"], {}).get("name")}
                          for s in (app.composition or {}).get("solutions", [])],
            "provides": [{**i, "consumers": [c for c, _ in cat.consumers.get(i["id"], [])]} for i in app.provides],
            "consumes": [{**c, "provider": (cat.interfaces.get(c.get("interface")) or [None])[0]} for c in app.consumes],
            "depends_on": sorted(cat.interface_dependencies(app.id)),
            "used_by": view.used_by(app.id),
            "releases": app.releases or {},
            "planning": app.planned,
        })
    c = counts(view.findings)
    return {"generated_for": cat.today.isoformat(), "applications": apps,
            "referentials": cat.referentials,
            "quality": {"errors": c["error"], "warnings": c["warning"], "infos": c["info"],
                        "findings": [f.as_dict() for f in view.findings]}}


def build(cat: Catalog, findings: list[Finding], output: str | Path) -> None:
    out = Path(output)
    if out.exists():
        shutil.rmtree(out)
    (out / "apps").mkdir(parents=True)
    shutil.copy(Path(__file__).parent / "static" / "style.css", out / "style.css")

    env = Environment(loader=PackageLoader("apm", "site/templates"), autoescape=select_autoescape(),
                      trim_blocks=True, lstrip_blocks=True)
    view = View(cat, findings)
    c = counts(findings)
    env.globals.update(v=view, cat=cat, NAV=NAV, LIFECYCLE=LIFECYCLE, STATUS=STATUS, ROLES=ROLES,
                       RULES=RULES, counts=c, today=cat.today, mid=mid)

    def render(template, path, root="", **ctx):
        html = env.get_template(template).render(root=root, page=path, **ctx)
        (out / path).write_text(html, encoding="utf-8")

    for tpl in ("index", "capabilities", "organisation", "solutions", "dependencies", "roadmap", "quality"):
        render(f"{tpl}.html", f"{tpl}.html")
    for app in cat.apps.values():
        render("app.html", f"apps/{app.id}.html", root="../", app=app)
    (out / "catalog.json").write_text(json.dumps(export(view), ensure_ascii=False, indent=2, default=str),
                                      encoding="utf-8")
