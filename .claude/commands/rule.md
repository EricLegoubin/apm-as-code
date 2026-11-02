---
description: Ajouter une règle de contrôle de bout en bout (PRD → test → code)
argument-hint: <description de la règle>
---

Règle demandée : $ARGUMENTS

1. Lis `docs/00-constitution.md` et le catalogue des règles (§3 de `docs/02-prd.md`).
2. Vérifie qu'aucune règle existante ne couvre déjà le besoin. Si oui, arrête-toi et propose d'ajuster celle-ci.
3. Choisis la famille (`STR`, `ID`, `REF`, `CMP`, `ITF`, `REL`, `PLN`) et le prochain numéro libre. Propose sévérité et formulation, puis **attends ma validation**.
4. Ajoute la ligne au catalogue du PRD (et la sémantique détaillée si la règle n'est pas évidente).
5. Écris dans `tests/test_rules.py` un test qui mute le catalogue d'exemple pour violer la règle et attend son ID. Lance-le : il doit échouer.
6. Implémente la règle dans `src/apm/rules/<famille>.py` avec `@rule`. Message : ce qui est faux + quoi faire.
7. `make check` doit être vert (catalogue d'exemple sans erreur, traçabilité OK).
8. Mets à jour `docs/04-stories.md` et résume le changement en trois lignes.
