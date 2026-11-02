# Brief produit — APM as Code

## Problème

La connaissance du portefeuille applicatif est dispersée (wiki, tableurs, CMDB groupe, mémoire des équipes). Elle est incomplète, rarement à jour, et ne dit rien des dépendances de livraison. Conséquences : périmètres d'application ambigus, composants sans propriétaire, impacts découverts en recette, plannings incompatibles entre tribes.

## Proposition

Décrire le portefeuille en YAML dans un dépôt Git, au plus près des équipes qui le font vivre. La CI contrôle la cohérence ; la PR porte la revue humaine ; le build publie un site de consultation et un export pour les outils tiers.

## Utilisateurs

| Rôle | Besoin principal |
|---|---|
| Product owner / lead dev de tribe | Déclarer et maintenir ses applications sans outil supplémentaire |
| Architecte | Voir les dépendances, faire respecter les règles, faire évoluer le modèle |
| Exploitation | Savoir qui exploite quoi et ce qui arrive en production |
| Pilotage (RTE, PMO) | Vérifier que le plan de livraison respecte les dépendances |

## Objectifs opérationnels (critères de réussite)

| # | Objectif | Mesure |
|---|---|---|
| O1 | Chaque application est identifiée, on sait ce qu'elle fait, son rattachement est sans ambiguïté | 100 % des applications avec fiche valide (propriétaire, mainteneur, exploitant, capacités) |
| O2 | Chaque composant appartient à une et une seule application | 0 erreur `CMP-001` sur `main` |
| O3 | Les dépendances entre applications sont connues | Graphe publié ; 0 erreur `ITF-*` |
| O4 | Les dépendances entre versions de composants et d'applications sont connues | 0 erreur `REL-*` |
| O5 | Le plan de réalisation est cohérent avec les dépendances | 0 erreur `PLN-*` |

## Hors périmètre (v1)

CMDB d'infrastructure, coûts, évaluation TIME / obsolescence, workflow d'approbation hors PR, saisie par formulaire, synchronisation bidirectionnelle avec ServiceNow.
