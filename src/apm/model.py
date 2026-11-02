"""Chargement du dépôt en Catalog indexé, et informations dérivées."""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .findings import RULES, Finding, declare
from .loader import YamlError, load_yaml

declare("STR-001", "error", "YAML valide, sans clé dupliquée")
declare("STR-002", "error", "Conformité au JSON Schema")
declare("STR-003", "error", "application.yaml présent")
declare("STR-004", "warning", "Fichier inattendu dans un répertoire d'application")

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"
APP_FILES = ("application", "composition", "interfaces", "releases", "planning")
REFERENTIALS = ("organisation", "capabilities", "solutions")


def _schemas() -> dict[str, Draft202012Validator]:
    return {
        p.name.removesuffix(".schema.json"): Draft202012Validator(
            json.loads(p.read_text(encoding="utf-8")), format_checker=FormatChecker())
        for p in sorted(SCHEMA_DIR.glob("*.schema.json"))
    }


@dataclass
class App:
    id: str
    dir: str
    application: dict | None = None
    composition: dict | None = None
    interfaces: dict | None = None
    releases: dict | None = None
    planning: dict | None = None

    @property
    def name(self) -> str:
        return (self.application or {}).get("name", self.id)

    @property
    def components(self) -> list[dict]:
        return (self.composition or {}).get("components", [])

    @property
    def provides(self) -> list[dict]:
        return (self.interfaces or {}).get("provides", [])

    @property
    def consumes(self) -> list[dict]:
        return (self.interfaces or {}).get("consumes", [])

    @property
    def component_sequences(self) -> dict[str, list[dict]]:
        return (self.releases or {}).get("components", {})

    @property
    def app_releases(self) -> list[dict]:
        return (self.releases or {}).get("application", [])

    @property
    def planned(self) -> list[dict]:
        return (self.planning or {}).get("releases", [])


@dataclass
class Catalog:
    root: Path
    today: dt.date
    apps: dict[str, App] = field(default_factory=dict)
    referentials: dict[str, dict] = field(default_factory=dict)
    load_findings: list[Finding] = field(default_factory=list)
    _where: dict[int, tuple[str, int, str | None]] = field(default_factory=dict, repr=False)

    # ---------- chargement ----------
    @classmethod
    def load(cls, root: Path | str, today: dt.date | None = None) -> "Catalog":
        cat = cls(Path(root), today or dt.date.today())
        validators = _schemas()
        for name in REFERENTIALS:
            data = cat._read(cat.root / "referentials" / f"{name}.yaml", name, validators, None, required=True)
            cat.referentials[name] = data or {}
        app_root = cat.root / "applications"
        for app_dir in sorted(p for p in app_root.iterdir() if p.is_dir()) if app_root.is_dir() else []:
            app = App(id=app_dir.name, dir=cat._rel(app_dir))
            for f in sorted(app_dir.iterdir()):
                if f.is_file() and f.suffix in (".yaml", ".yml") and f.stem in APP_FILES:
                    continue
                cat._add("STR-004", cat._rel(f), 0, app.id,
                         f"fichier inattendu ; attendus : {', '.join(n + '.yaml' for n in APP_FILES)}")
            app.application = cat._read(app_dir / "application.yaml", "application", validators, app.id, required=True)
            if app.application is None:
                continue  # fiche absente ou invalide : le reste de l'application n'est pas exploité
            for kind in APP_FILES[1:]:
                setattr(app, kind, cat._read(app_dir / f"{kind}.yaml", kind, validators, app.id))
            cat.apps[app.id] = app
        return cat

    def _rel(self, path: Path) -> str:
        # Séparateur « / » sur tous les OS : annotations CI, CODEOWNERS et site restent identiques.
        try:
            return path.relative_to(self.root.parent).as_posix()
        except ValueError:
            return path.as_posix()

    def _add(self, rule_id: str, file: str, line: int | None, app: str | None, message: str) -> None:
        self.load_findings.append(Finding(file, line or 0, rule_id, message, RULES[rule_id].severity, app))

    def _read(self, path: Path, kind: str, validators, app_id, required=False):
        rel = self._rel(path)
        if not path.exists():
            if required:
                rule = "STR-003" if kind == "application" else "STR-002"
                self._add(rule, rel, 0, app_id, f"fichier obligatoire absent : {path.name}")
            return None
        try:
            data, lines = load_yaml(path)
        except YamlError as exc:
            self._add("STR-001", rel, exc.line, app_id, f"YAML invalide : {exc}")
            return None
        data = {} if data is None else data
        errors = sorted(validators[kind].iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
        if errors:
            for err in errors:
                line = _line_for(data, list(err.absolute_path), lines)
                where = "/".join(map(str, err.absolute_path)) or "(racine)"
                self._add("STR-002", rel, line, app_id, f"{where} : {_schema_message(err)}")
            return None
        for obj_id, line in lines.items():
            self._where[obj_id] = (rel, line, app_id)
        self._where[id(data)] = (rel, lines.get(id(data), 1), app_id)
        return data

    def locate(self, anchor) -> tuple[str, int, str | None]:
        if isinstance(anchor, tuple):
            return anchor
        return self._where.get(id(anchor), ("?", 0, None))

    # ---------- index ----------
    @cached_property
    def units(self) -> dict[str, dict]:
        return {u["id"]: u for u in self.referentials["organisation"].get("units", [])}

    @cached_property
    def capabilities(self) -> dict[str, dict]:
        return {c["id"]: c for c in self.referentials["capabilities"].get("capabilities", [])}

    @cached_property
    def solutions(self) -> dict[str, dict]:
        return {s["id"]: s for s in self.referentials["solutions"].get("solutions", [])}

    @cached_property
    def component_owners(self) -> dict[str, list[str]]:
        """cmp-id → applications qui le déclarent (plus d'une = CMP-001)."""
        owners: dict[str, list[str]] = {}
        for app in self.apps.values():
            for c in app.components:
                owners.setdefault(c["id"], []).append(app.id)
        return owners

    def component_app(self, cmp_id: str) -> str | None:
        owners = self.component_owners.get(cmp_id)
        return owners[0] if owners else None

    @cached_property
    def interfaces(self) -> dict[str, tuple[str, dict]]:
        """itf-id → (application fournisseur, déclaration). Première déclaration retenue."""
        out: dict[str, tuple[str, dict]] = {}
        for app in self.apps.values():
            for itf in app.provides:
                out.setdefault(itf["id"], (app.id, itf))
        return out

    @cached_property
    def consumers(self) -> dict[str, list[tuple[str, dict]]]:
        """itf-id → [(application consommatrice, déclaration)]."""
        out: dict[str, list[tuple[str, dict]]] = {}
        for app in self.apps.values():
            for c in app.consumes:
                if "interface" in c:
                    out.setdefault(c["interface"], []).append((app.id, c))
        return out

    def interface_dependencies(self, app_id: str) -> set[str]:
        """Applications dont app_id consomme au moins une interface."""
        deps = set()
        for c in self.apps[app_id].consumes:
            provider = self.interfaces.get(c.get("interface"))
            if provider and provider[0] != app_id:
                deps.add(provider[0])
        return deps

    def version_requirements(self, app_id: str, release: dict) -> list[tuple[str, str, str, dict]]:
        """Dépendances effectives d'une version d'application :
        [(type 'application'|'component', cible, contrainte, objet d'ancrage)]."""
        app = self.apps[app_id]
        reqs = [("application", r["application"], r["version"], r) for r in release.get("requires", [])]
        for cmp_id, version in release.get("components", {}).items():
            for cr in app.component_sequences.get(cmp_id, []):
                if cr["version"] == version:
                    reqs += [("component", r["component"], r["version"], r) for r in cr.get("requires", [])]
        return reqs

    def target_versions(self, kind: str, target: str) -> list[str]:
        if kind == "application":
            app = self.apps.get(target)
            return [r["version"] for r in app.app_releases] if app else []
        owner = self.component_app(target)
        return [r["version"] for r in self.apps[owner].component_sequences.get(target, [])] if owner else []

    @cached_property
    def availability(self) -> dict[tuple[str, str, str], dt.date]:
        """(kind, cible, version) → première date de mise à disposition planifiée (hors cancelled). ADR-004."""
        out: dict[tuple[str, str, str], dt.date] = {}
        for app in self.apps.values():
            releases = {r["version"]: r for r in app.app_releases}
            for p in app.planned:
                if p["status"] == "cancelled":
                    continue
                d = dt.date.fromisoformat(p["date"])
                keys = [("application", app.id, p["version"])]
                rel = releases.get(p["version"])
                if rel:
                    keys += [("component", c, v) for c, v in rel.get("components", {}).items()]
                for k in keys:
                    if k not in out or d < out[k]:
                        out[k] = d
        return out


def _line_for(data, path: list, lines: dict[int, int]) -> int:
    node, line = data, lines.get(id(data), 1)
    for key in path:
        try:
            node = node[key]
        except (KeyError, IndexError, TypeError):
            break
        line = lines.get(id(node), line)
    return line


def _schema_message(err) -> str:
    if err.validator == "pattern":
        return f"« {err.instance} » ne respecte pas le format attendu ({err.validator_value})"
    if err.validator == "additionalProperties":
        return err.message.replace("Additional properties are not allowed", "propriété non prévue par le modèle")
    if err.validator == "required":
        return err.message.replace("is a required property", "est obligatoire")
    if err.validator == "enum":
        return f"« {err.instance} » n'est pas une valeur autorisée ({', '.join(map(str, err.validator_value))})"
    if err.validator == "oneOf":
        return "ne correspond à aucune forme attendue (interface interne ou échange externe)"
    return err.message
