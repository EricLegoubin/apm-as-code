# Constitution — APM as Code

Principes non négociables. Toute spec, story ou PR qui en contredit un est rejetée ou amende d'abord ce document (par PR dédiée, revue par l'équipe d'architecture).

1. **Le YAML dans Git est la seule source de vérité.** Le site HTML et l'export JSON sont des produits dérivés, régénérés à chaque build, jamais modifiés à la main.
2. **Une règle = un identifiant, une spec, un test, une implémentation.** Pas de contrôle sans les quatre. L'identifiant (`REF-001`…) est le même dans le PRD, le code, le test et le message d'erreur. Le test `test_traceability.py` le vérifie.
3. **Les tribes possèdent leurs fiches, l'architecture possède le modèle.** `CODEOWNERS` donne à chaque tribe la main sur ses répertoires d'application ; `schemas/`, `src/` et `docs/` sont relus par l'équipe d'architecture.
4. **Modèle minimal, étendu par l'usage.** Un attribut n'entre dans le schéma que s'il sert un contrôle, une page ou un export identifié. Pas d'attribut « pour plus tard ».
5. **Automatiser d'abord, relire ensuite.** Ce qui est vérifiable par la machine l'est en CI. Le reste figure dans la checklist de PR. Un contrôle manuel qui revient trois fois devient une story d'automatisation.
6. **Déterministe.** Même entrée, même sortie. La date de référence des contrôles de planning est injectable (`--today`).
7. **Sobre.** Python + PyYAML, jsonschema, Jinja2, packaging. Aucun service à opérer : un dépôt, une CI, un site statique.
8. **Indépendant des outils du groupe.** L'export est un JSON neutre ; le chargement vers ServiceNow (ou tout autre outil) est un adaptateur séparé qui ne contraint pas le modèle.
