# Architecture — APM as Code

## 1. Vue d'ensemble

```
 tribe ──PR──▶ dépôt Git (catalog/*.yaml)
                 │
                 ├─ CI sur PR : apm validate --format github   → annotations, statut bloquant
                 │                + revue CODEOWNERS + checklist  → contrôles manuels
                 │
                 └─ CI sur main : apm build → site/ (HTML statique) + site/catalog.json
                                              │                       │
                                         Pages / bucket         adaptateur ServiceNow (hors dépôt)
```

## 2. Organisation du dépôt

```
catalog/
  referentials/
    organisation.yaml      unités : tribes, équipes, éditeurs
    capabilities.yaml      carte des capacités (arbre via parent)
    solutions.yaml         solutions externes
  applications/<app-id>/
    application.yaml       fiche                 (obligatoire)
    composition.yaml       composants, solutions (optionnel)
    interfaces.yaml        exposées, consommées  (optionnel)
    releases.yaml          séquences de versions (optionnel)
    planning.yaml          dates de mise à disposition (optionnel)
schemas/                   un JSON Schema par type de fichier
src/apm/                   loader, modèle, règles, site, CLI
tests/                     un test par règle + traçabilité
```

Les fichiers optionnels permettent une adoption progressive : une tribe commence par la fiche, ajoute ensuite composition et interfaces, puis versions et planning.

## 3. Modèle de données

```
OrgUnit ◀─owner/maintainer/operator── Application ──capabilities──▶ Capability
                                         │  1
                                         │ *
                                      Component ──provides──▶ Interface ◀──consumes── Component (autre app)
                                         │
Application ──solutions──▶ Solution      │ *
Application ── ApplicationRelease 1..* ──embarque──▶ ComponentRelease
ApplicationRelease ──requires──▶ Application (contrainte de version)
ComponentRelease   ──requires──▶ Component   (contrainte de version)
ApplicationRelease ──planning──▶ date, statut
```

Préfixes d'identifiants imposés par schéma : `app-`, `cmp-`, `itf-`, `org-`, `cap-`, `sol-`. Une référence est donc typée par sa forme et un identifiant ne peut pas être confondu d'un type à l'autre.

## 4. Composants logiciels

| Module | Rôle |
|---|---|
| `apm.loader` | Lecture YAML sans float ni timestamp implicites, rejet des clés dupliquées, table des numéros de ligne par nœud |
| `apm.model` | Chargement du dépôt en `Catalog` indexé (applications, composants, interfaces…) et calculs dérivés (consommateurs, disponibilités) |
| `apm.versions` | Comparaison de versions et contraintes (PEP 440 via `packaging`) |
| `apm.rules` | Registre `@rule(id, sévérité, titre)` ; un module par famille (`structure`, `identity`, `references`, `composition`, `interfaces`, `releases`, `planning`) |
| `apm.report` | Formats `text`, `github`, `json` |
| `apm.site` | Génération Jinja2, Mermaid côté client, export `catalog.json` |
| `apm.cli` | `apm validate`, `apm build` |

Une règle est une fonction `Catalog → Iterable[Finding]`. Elle ne lit pas de fichier, ne modifie pas le modèle et ne dépend pas d'une autre règle. Les règles structurelles (`STR-*`) s'exécutent au chargement ; si un fichier est invalide, il est exclu du modèle et les règles sémantiques s'exécutent sur le reste.

## 5. Décisions (ADR courts)

**ADR-001 — Un répertoire par application, un fichier par préoccupation.** Permet `CODEOWNERS` par application et des PR petites. Rejeté : un fichier unique par application (conflits, fichiers longs) ; un fichier par type d'objet (propriété diluée).

**ADR-002 — L'interface est déclarée par le fournisseur, la consommation par le consommateur.** Chaque tribe déclare ce qu'elle maîtrise ; la CI vérifie la jonction. « Entrant / sortant » est dérivé à l'affichage. Rejeté : déclaration de flux point à point par un tiers (personne n'en est propriétaire).

**ADR-003 — Versions et contraintes PEP 440.** Couvre SemVer (`3.2.0`) et calendaire (`2026.10`) avec une seule bibliothèque standard. Rejeté : SemVer strict (exclut le calendaire).

**ADR-004 — Date de disponibilité d'un composant = première version d'application planifiée qui l'embarque.** Un composant n'est pas livré seul en production ; c'est l'application qui porte le planning. Évite un second planning à maintenir.

**ADR-005 — Pas de framework de site.** Jinja2 + CSS + Mermaid suffisent ; un générateur (MkDocs, Hugo) imposerait un passage par Markdown sans gain.

**ADR-006 — Export JSON neutre.** Le modèle ServiceNow du groupe est une cible parmi d'autres ; l'adaptateur lit `catalog.json` et porte la correspondance d'attributs. Le modèle du dépôt reste piloté par les usages des tribes.

## 6. Extension

Ajouter un attribut : schéma → usage (règle, page ou export) → exemple → test. Ajouter une règle : voir `.claude/commands/rule.md`.
