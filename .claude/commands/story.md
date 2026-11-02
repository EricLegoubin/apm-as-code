---
description: Implémenter une story prête de docs/04-stories.md
argument-hint: <ID de story, ex. S2.8>
---

Story : $ARGUMENTS

1. Lis la constitution, la story et les exigences qu'elle référence (PRD, architecture).
2. Si la story est `draft` ou si un critère d'acceptation n'est pas testable, arrête-toi : propose les critères manquants et la mise à jour du PRD, puis attends ma validation.
3. Liste les fichiers à modifier et le plan de tests. Attends ma validation si le schéma ou le modèle changent (fais relire par l'agent `model-guardian`).
4. Tests d'abord, puis implémentation, par petits incréments ; `make check` après chacun.
5. Mets à jour le catalogue d'exemple si le modèle change, régénère le site et vérifie visuellement les pages touchées.
6. Passe la story à `done`. Résume : ce qui a changé, ce qui reste hors périmètre.
