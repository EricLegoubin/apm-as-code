# APM as Code

Le portefeuille applicatif décrit en YAML, contrôlé en CI, publié en site statique.

- **Une application = un répertoire** sous `catalog/applications/`, maintenu par la tribe propriétaire.
- **La CI contrôle la cohérence** : 32 règles tracées (`docs/02-prd.md` §3) — identification, appartenance des composants, interfaces, séquences de versions, planning vs dépendances.
- **La PR porte la revue humaine** : checklist des contrôles non automatisés, `CODEOWNERS` par application.
- **Le build publie** un site de consultation et `catalog.json` pour les outils tiers (ServiceNow…).

## Démarrer

```bash
make install
make check          # tests + validation du catalogue
make site           # puis ouvrir site/index.html
```

## Déclarer une application

```
catalog/applications/app-mon-appli/
  application.yaml    obligatoire — fiche : identité, capacités, propriétaire/mainteneur/exploitant
  composition.yaml    composants internes, solutions externes
  interfaces.yaml     interfaces exposées / consommées
  releases.yaml       séquences de versions des composants et de l'application, dépendances
  planning.yaml       dates de mise à disposition
```

Commencer par `application.yaml`, compléter le reste progressivement. L'exemple `app-espace-client` montre tous les fichiers. Chaque YAML référence son schéma : VS Code (extension YAML) propose complétion et validation.

```yaml
# releases.yaml — une version d'application fixe ses composants et ses dépendances
application:
  - version: "2026.12"
    components: {cmp-ec-bff: 5.1.0, cmp-ec-mobile: 8.4.0}
    requires:
      - application: app-paiement-carte
        version: ">=4.2"
```

Si `app-paiement-carte` 4.2 est planifiée après la date de `app-espace-client` 2026.12, la CI échoue (`PLN-004`).

## Documentation

| | |
|---|---|
| [Constitution](docs/00-constitution.md) | Principes non négociables |
| [Brief](docs/01-brief.md) | Problème, utilisateurs, objectifs |
| [PRD](docs/02-prd.md) | Exigences et catalogue des règles |
| [Architecture](docs/03-architecture.md) | Modèle, composants, ADR |
| [Stories](docs/04-stories.md) | Epics, stories, backlog |
| [CLAUDE.md](CLAUDE.md) | Méthode de développement avec Claude Code |
