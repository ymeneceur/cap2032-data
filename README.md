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

Chaque nuit, l'Action « Mise à jour des candidatures » (`.github/workflows/update.yml`) :

1. récupère les données ouvertes de [2027 et moi](https://github.com/2027etmoi/2027etmoi) ;
2. les convertit vers les questions de Cap 2032 (`scripts/build_cands.py`) : candidatures dont le programme est publié, avec au moins 5 positions ;
3. contrôle les changements (`scripts/publish.py`) ;
4. publie la nouvelle version signée, l'archive dans `history/` et l'ajoute au journal ;
5. ouvre un ticket (issue) qui résume les changements : le vérificateur le reçoit par e-mail.

**Garde-fous.** La mise à jour attend la validation du vérificateur (dossier `pending/`) si une candidature disparaît, si plus de 5 positions changent, si une position s'inverse, ou si une source manque.

**Interventions du vérificateur** (Actions > Mise à jour des candidatures > Run workflow) :
- `approve` publie la mise à jour en attente ;
- `rollback` + numéro de version rétablit une version archivée (republiée sous un nouveau numéro).

La clé privée de signature est un secret du dépôt (`CAP_SIGNING_KEY`) : elle n'apparaît jamais dans les fichiers.

Aucune donnée d'utilisateur n'est stockée ici : l'application ne fait que lire ces fichiers.
