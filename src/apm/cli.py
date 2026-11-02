"""apm validate | apm build"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from .model import Catalog
from .report import FORMATS, counts
from .rules import run


def _date(text: str) -> dt.date:
    return dt.date.fromisoformat(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="apm", description="Portefeuille applicatif as code")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="contrôle la cohérence du catalogue")
    v.add_argument("catalog", nargs="?", default="catalog")
    v.add_argument("--format", choices=FORMATS, default="text")
    v.add_argument("--strict", action="store_true", help="les alertes font échouer la validation")
    v.add_argument("--today", type=_date, help="date de référence AAAA-MM-JJ (défaut : aujourd'hui)")
    v.add_argument("--show-info", action="store_true", help="affiche aussi les constats de niveau info")

    b = sub.add_parser("build", help="génère le site statique et l'export JSON")
    b.add_argument("catalog", nargs="?", default="catalog")
    b.add_argument("-o", "--output", default="site")
    b.add_argument("--today", type=_date)

    args = parser.parse_args(argv)
    catalog = Catalog.load(args.catalog, args.today)
    findings = run(catalog)

    if args.command == "validate":
        shown = findings if args.show_info or args.format == "json" else [f for f in findings if f.severity != "info"]
        print(FORMATS[args.format](shown, findings))
        c = counts(findings)
        return 1 if c["error"] or (args.strict and c["warning"]) else 0

    from .site import build
    build(catalog, findings, args.output)
    c = counts(findings)
    print(f"Site généré dans {args.output}/ — {len(catalog.apps)} applications, "
          f"{c['error']} erreur(s), {c['warning']} alerte(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
