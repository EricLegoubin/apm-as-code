# Epics et stories

Statuts : `done`, `ready` (spécifiée, prête à développer), `draft` (à affiner). Une story n'est `ready` que si ses critères d'acceptation sont testables et ses règles présentes dans le PRD.

## E1 — Modèle et schémas

| ID | Story | Exigences | Statut |
|---|---|---|---|
| S1.1 | En tant qu'architecte, je dispose des schémas des 8 types de fichiers pour que les tribes aient complétion et validation dans leur IDE | FR-01..06, NFR-03 | done |
| S1.2 | En tant que PO, je trouve un exemple complet de portefeuille pour m'en inspirer | FR-02..06 | done |

**Critères S1.1** — Étant donné un YAML conforme, quand il est validé contre son schéma, alors aucun constat. Étant donné un identifiant sans préfixe, alors `STR-002`.

## E2 — Contrôles

| ID | Story | Règles | Statut |
|---|---|---|---|
| S2.1 | Lecture sûre du YAML et localisation des constats | STR-001..004, NFR-04 | done |
| S2.2 | Identification sans ambiguïté | ID-001..003, REF-001..005 | done |
| S2.3 | Appartenance des composants | CMP-001..002 | done |
| S2.4 | Cohérence des interfaces | ITF-001..005 | done |
| S2.5 | Cohérence des séquences de versions | REL-001..007 | done |
| S2.6 | Cohérence du planning avec les dépendances | PLN-001..006 | done |
| S2.7 | Sorties `text`, `github`, `json` et code retour | FR-10..12 | done |

**Critère commun** — Étant donné le catalogue d'exemple, quand `apm validate` s'exécute, alors 0 erreur. Étant donné ce catalogue modifié pour violer la règle X, alors un constat X est émis sur le bon fichier. (Un test par règle dans `tests/test_rules.py`.)

**Critères S2.6** — Étant donné `app-a 2.0` le 2026-12-01 qui requiert `app-b >=3.0`, et `app-b 3.0` planifiée le 2026-12-15, alors `PLN-004` sur le planning de `app-a`. Si aucune version `>=3.0` de `app-b` n'est planifiée, alors `PLN-003`.

## E3 — Consultation

| ID | Story | Exigences | Statut |
|---|---|---|---|
| S3.1 | Accueil avec indicateurs et liste filtrable | FR-20 | done |
| S3.2 | Fiche d'application consolidée | FR-21 | done |
| S3.3 | Vues capacités, organisation, solutions | FR-20 | done |
| S3.4 | Graphe et matrice des dépendances | FR-20, NFR-02 | done |
| S3.5 | Feuille de route avec signalement des incohérences | FR-20 | done |
| S3.6 | Rapport de contrôle | FR-20 | done |

## E4 — Gouvernance et CI

| ID | Story | Exigences | Statut |
|---|---|---|---|
| S4.1 | Workflow CI : validation bloquante sur PR, build et publication sur `main` | FR-10, FR-13 | done |
| S4.2 | Modèle de PR et `CODEOWNERS` | FR-13 | done |

## E5 — Export

| ID | Story | Exigences | Statut |
|---|---|---|---|
| S5.1 | Export `catalog.json` avec relations résolues | FR-22 | done |
| S5.2 | Adaptateur de chargement ServiceNow (table de correspondance des ~30 attributs groupe) | ADR-006 | draft |

## Backlog (draft)

- **S2.8** Versionner les contrats d'interface (`provides: itf-x@2`) et contrôler la compatibilité consommateur/fournisseur.
- **S3.7** Vue « impact » : pour une version donnée, applications et versions à livrer avant / après.
- **S5.3** Export ArchiMate Open Exchange Format pour les outils de modélisation.
- **S4.3** Contrôler que `CODEOWNERS` couvre chaque répertoire d'application et correspond à son propriétaire.
- **S6.1** Amorçage du dépôt depuis un export ServiceNow (une fiche minimale par application).
- **S6.2** Indicateurs de complétude par tribe (part des fichiers optionnels renseignés).
