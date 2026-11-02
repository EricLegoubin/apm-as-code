# PRD — APM as Code

Référence : [brief](01-brief.md), [constitution](00-constitution.md). Les exigences sont identifiées (`FR-xx`, `NFR-xx`, règles `XXX-nnn`) et tracées dans les [stories](04-stories.md).

## 1. Exigences fonctionnelles

### Description du portefeuille

- **FR-01 Référentiels partagés.** Le dépôt décrit les unités d'organisation (tribes, équipes, éditeurs), la carte des capacités fonctionnelles (hiérarchique) et le catalogue des solutions externes (produits, SaaS, middleware).
- **FR-02 Fiche d'application.** Identifiant, dénomination, alias, références externes (ServiceNow…), description courte, description longue, capacités, cycle de vie, propriétaire / mainteneur / exploitant.
- **FR-03 Composition.** Composants internes (propres à l'application) et solutions externes utilisées (référence au catalogue + usage).
- **FR-04 Interfaces.** L'application fournisseur déclare les interfaces qu'elle expose (portées par un de ses composants). L'application consommatrice déclare les interfaces qu'elle consomme (par un de ses composants) ou ses échanges avec des tiers externes.
- **FR-05 Séquences de versions.** Pour chaque composant, une séquence ordonnée de versions et leurs dépendances vers d'autres composants. Pour l'application, une séquence ordonnée de versions qui fixe la version de chaque composant embarqué et ses dépendances vers d'autres applications.
- **FR-06 Planning.** Date de mise à disposition en production et statut (`planned`, `confirmed`, `delivered`, `cancelled`) de chaque version d'application.

### Contrôle

- **FR-10 Validation en CI.** `apm validate` exécute toutes les règles du §3 et sort en échec s'il existe au moins une erreur (ou un avertissement avec `--strict`).
- **FR-11 Localisation.** Chaque constat indique règle, sévérité, fichier, ligne quand elle est connue, message actionnable.
- **FR-12 Formats de sortie.** `text` (humain), `github` (annotations de PR), `json` (outillage).
- **FR-13 Contrôles manuels.** Le modèle de PR liste les vérifications non automatisées ; `CODEOWNERS` impose la relecture par la tribe propriétaire.

### Consultation et export

- **FR-20 Site statique.** `apm build` génère : accueil (indicateurs + liste filtrable), fiche par application, capacités, organisation, solutions, dépendances (graphe + matrice), feuille de route, rapport de contrôle.
- **FR-21 Fiche d'application consolidée.** Elle montre aussi l'information dérivée : consommateurs de ses interfaces, applications dont elle dépend et qui dépendent d'elle, dates de disponibilité des dépendances, constats la concernant.
- **FR-22 Export JSON.** `catalog.json` normalisé (relations résolues), base des adaptateurs vers d'autres outils.

## 2. Exigences non fonctionnelles

- **NFR-01** Validation + build d'un portefeuille de 300 applications en moins de 30 s sur un runner CI standard.
- **NFR-02** Site consultable sans serveur applicatif (fichiers statiques). Le graphe utilise Mermaid ; les tableaux restent lisibles sans JavaScript.
- **NFR-03** Fichiers éditables dans un IDE avec complétion : chaque YAML référence son JSON Schema (`# yaml-language-server: $schema=…`).
- **NFR-04** Le YAML est lu sans conversion implicite des nombres décimaux ni des dates (`2026.10` reste une chaîne). Les clés dupliquées sont une erreur.
- **NFR-05** Sortie déterministe (ordre de tri stable, date de référence injectable).

## 3. Catalogue des règles

Sévérités : `error` bloque la CI ; `warning` bloque avec `--strict` ; `info` est affiché sur le site uniquement.

| ID | Sévérité | Règle | Objectif |
|---|---|---|---|
| STR-001 | error | Le fichier est un YAML valide, sans clé dupliquée | — |
| STR-002 | error | Le fichier respecte son JSON Schema | O1 |
| STR-003 | error | Un répertoire d'application contient `application.yaml` | O1 |
| STR-004 | warning | Fichier inattendu dans un répertoire d'application | — |
| ID-001 | error | L'identifiant de l'application est égal au nom de son répertoire | O1 |
| ID-002 | error | Les identifiants sont uniques (application, interface, unité, capacité, solution) | O1 |
| ID-003 | warning | Un alias ou une dénomination d'application n'entre pas en collision avec celle d'une autre application | O1 |
| REF-001 | error | Propriétaire, mainteneur, exploitant référencent une unité d'organisation existante | O1 |
| REF-002 | error | Les capacités référencées existent | O1 |
| REF-003 | error | Les solutions référencées existent | O1 |
| REF-004 | error | Les parents des référentiels existent et ne forment pas de cycle | O1 |
| REF-005 | warning | Une application est rattachée à une capacité feuille (sans sous-capacité) | O1 |
| CMP-001 | error | Un composant appartient à une et une seule application | O2 |
| CMP-002 | warning | Une application en `build` ou `run` déclare au moins un composant | O2 |
| ITF-001 | error | Le composant qui porte une interface exposée appartient à l'application | O3 |
| ITF-002 | error | Une interface consommée existe | O3 |
| ITF-003 | error | Le composant consommateur appartient à l'application | O3 |
| ITF-004 | warning | Une application ne consomme pas sa propre interface | O3 |
| ITF-005 | info | Une interface exposée a au moins un consommateur | O3 |
| REL-001 | error | Une séquence de versions de composant porte sur un composant de l'application | O4 |
| REL-002 | error | Dans une séquence, les versions sont valides, uniques et strictement croissantes | O4 |
| REL-003 | error | Une version d'application référence des composants de l'application, dans des versions déclarées dans leur séquence | O4 |
| REL-004 | error | La cible d'une dépendance de version existe, n'est pas l'application elle-même, et la contrainte est valide | O4 |
| REL-005 | error | Au moins une version de la cible satisfait la contrainte | O4 |
| REL-006 | warning | Une dépendance de version vers une autre application s'appuie sur une interface consommée de cette application | O3, O4 |
| REL-007 | warning | Les dépendances de version entre applications ne forment pas de cycle | O4 |
| PLN-001 | error | Une version planifiée existe dans la séquence de l'application | O5 |
| PLN-002 | error | Les dates de mise à disposition suivent l'ordre de la séquence | O5 |
| PLN-003 | error | Chaque dépendance d'une version planifiée est satisfaite par une version planifiée de la cible | O5 |
| PLN-004 | error | La dépendance est disponible au plus tard à la date de la version qui la requiert | O5 |
| PLN-005 | warning | Le statut est cohérent avec la date (`delivered` pas dans le futur, `planned`/`confirmed` pas dans le passé) | O5 |
| PLN-006 | info | Chaque version d'application est planifiée | O5 |

### Sémantique des dépendances de version (REL-005, PLN-003, PLN-004)

- Une contrainte suit la syntaxe PEP 440 (`>=1.4`, `>=1.4,<2`, `~=3.2`) ; une version nue vaut `==`.
- La **date de disponibilité d'une version d'application** est sa date planifiée (hors `cancelled`).
- La **date de disponibilité d'une version de composant** est la date de la première version d'application planifiée qui l'embarque.
- Une dépendance est satisfaite à la date *d* s'il existe une version de la cible qui satisfait la contrainte et qui est disponible à une date ≤ *d*.
- Les dépendances déclarées sur une version de composant s'appliquent à chaque version d'application qui embarque cette version de composant.

## 4. Contrôles manuels en PR

Repris dans `.github/pull_request_template.md` :

1. La description courte est compréhensible par quelqu'un hors de la tribe.
2. Les capacités rattachées décrivent ce que fait l'application, pas ce qu'elle pourrait faire.
3. Propriétaire, mainteneur et exploitant ont été confirmés par les intéressés.
4. Aucune interface réelle n'est omise (comparer avec les flux connus, la passerelle d'API, les topics).
5. Les dates de planning sont celles des engagements de PI, pas des souhaits.
