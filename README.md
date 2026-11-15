# cap2032-data

Données des candidatures à l'élection présidentielle 2027 utilisées par l'application **Cap 2032** (Nicolas Sayde et Yannick Meneceur).

## Fichiers

| Fichier | Rôle |
|---|---|
| `cands.json` | Candidatures dont le programme est publié et leurs positions sur les 27 questions de Cap 2032, chacune avec sa source datée |
| `cands.json.sig` | Signature Ed25519 de `cands.json` (en base64). L'application refuse tout fichier dont la signature ne correspond pas |
| `manifest.json` | Numéro de version, date, empreinte SHA-256 et signature : l'application le lit d'abord et ne télécharge `cands.json` que s'il a changé |
| `CHANGELOG.md` | Journal public des mises à jour et des retours en arrière |

Clé publique de vérification (Ed25519, base64) : `mvRsiv6ok/UceE4N6jLKiYQnkP5f3J1wtfN0f90IYBo=`

## Sources et licence

- Positions des candidats : [2027 et moi](https://2027etmoi.fr) ([données sur data.gouv.fr](https://www.data.gouv.fr/organizations/2027etmoi/)), sous Licence Ouverte 2.0, converties vers les questions de Cap 2032.
- Quand la question de 2027 et moi est seulement proche de celle de Cap 2032, la position compte pour moitié (« atténué »).
- Certaines positions sont codées par Cap 2032 à partir d'une mesure précise du programme : la source est indiquée pour chacune (« codage Cap 2032 »).
- Une question sans source reste non renseignée : rien n'est deviné.

## Mise à jour

Les mises à jour sont préparées automatiquement à partir des sources ouvertes, contrôlées (structure, sources présentes), signées puis publiées. Un vérificateur reçoit un résumé de chaque changement et peut revenir à la version précédente. Les changements importants (candidat retiré, nombreuses positions modifiées, source manquante) attendent sa validation avant publication.

Aucune donnée d'utilisateur n'est stockée ici : l'application ne fait que lire ces fichiers.
