# CLAUDE.md — APM as Code

Portefeuille applicatif décrit en YAML, contrôlé en CI, publié en site statique. Lire `docs/00-constitution.md` avant toute modification.

## Commandes

```bash
make install     # pip install -e .[dev]
make check       # tests + validation du catalogue d'exemple (doit être vert avant tout commit)
make site        # génère site/ (ouvrir site/index.html)
apm validate catalog --format text|github|json [--strict] [--today AAAA-MM-JJ]
apm build catalog -o site [--today AAAA-MM-JJ]
```

## Méthode (spec d'abord)

Les artefacts de planification sont dans `docs/` et font foi : brief → PRD (exigences et **catalogue des règles**) → architecture (modèle, ADR) → stories.

Pour toute évolution :

1. **Spécifier.** Modifier le PRD (exigence ou règle avec ID) et, si le modèle change, l'architecture (+ ADR si décision structurante). Créer ou mettre à jour la story dans `docs/04-stories.md` avec des critères Étant donné / Quand / Alors.
2. **Tester.** Écrire le test qui échoue (`tests/test_rules.py` : catalogue d'exemple muté pour violer la règle).
3. **Implémenter.** Le plus petit changement qui fait passer le test. Le message d'erreur dit quoi corriger.
4. **Vérifier.** `make check`. Le test de traçabilité échoue si une règle existe dans le code sans être dans le PRD et sans test, ou l'inverse.
5. **Livrer.** Story passée à `done`, catalogue d'exemple mis à jour si le modèle a changé.

Ne jamais : ajouter un attribut de schéma sans usage (constitution §4), éditer `site/`, introduire une dépendance Python sans ADR.

## Conventions

- Code et identifiants en anglais, documentation et messages utilisateur en français.
- Règle = fonction décorée `@rule("FAM-nnn", severity, "titre")` dans `src/apm/rules/<famille>.py`, pure (`Catalog → Iterable[Finding]`).
- Identifiants préfixés : `app-`, `cmp-`, `itf-`, `org-`, `cap-`, `sol-`.
- Les dates sont des chaînes ISO `AAAA-MM-JJ` ; les versions sont des chaînes PEP 440.

## Commandes et agents Claude Code

- `/rule <description>` : ajoute une règle de bout en bout (PRD → test → code).
- `/story <ID>` : implémente une story `ready` de `docs/04-stories.md`.
- Agent `model-guardian` : relit toute modification de `schemas/` ou du modèle au regard de la constitution.
- Agent `qa` : relit une PR (couverture des critères d'acceptation, messages, non-régression du site).
