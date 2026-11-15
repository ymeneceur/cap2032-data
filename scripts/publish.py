"""Publie, met en attente, approuve ou annule une mise à jour des candidatures de Cap 2032.

  python scripts/publish.py --mode update   --new /tmp/new.json
  python scripts/publish.py --mode approve
  python scripts/publish.py --mode rollback --version 2026111501

La clé privée Ed25519 (PEM) est lue dans la variable d'environnement CAP_SIGNING_KEY.
Écrit le résumé destiné au vérificateur dans /tmp/summary.md et, pour GitHub Actions,
les sorties status (none, published, held, approved, rolledback) et title.
"""
import argparse, base64, datetime as dt, hashlib, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = os.environ.get('GITHUB_REPOSITORY', 'ymeneceur/cap2032-data')
ACTIONS = f'https://github.com/{REPO}/actions/workflows/update.yml'
SITE = 'https://ymeneceur.github.io/cap2032-data/'
SUMMARY = Path('/tmp/summary.md')
# Garde-fous : au-delà, la mise à jour attend le vérificateur
MAX_CHANGES = 5
VL = {2: 'tout à fait d’accord', 1: 'plutôt d’accord', 0: 'partagé', -1: 'plutôt pas d’accord', -2: 'pas du tout d’accord'}


def lab(v):
    if v is None:
        return 'non renseigné'
    r = max(-2, min(2, round(v)))
    return VL[r] + (' (atténué)' if abs(v) != abs(r) else '')


def out(**kw):
    p = os.environ.get('GITHUB_OUTPUT')
    for k, v in kw.items():
        print(f'{k}={v}')
        if p:
            with open(p, 'a', encoding='utf-8') as f:
                f.write(f'{k}={v}\n')


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def core(o):
    c = {k: v for k, v in o.items() if k not in ('version', 'generated')}
    c['cands'] = sorted(c.get('cands', []), key=lambda x: x['id'])
    return c


def new_version(cur):
    v = int(dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H'))
    return max(v, int(cur.get('version', 0)) + 1)


def diff(cur, new, issues):
    A = {c['id']: c for c in cur['cands']}
    B = {c['id']: c for c in new['cands']}
    added = [B[k] for k in B if k not in A]
    removed = [A[k] for k in A if k not in B]
    changes, notes, problems = [], [], list(issues)
    for k in B:
        if k not in A:
            continue
        a, b = A[k], B[k]
        if a.get('statut') != b.get('statut'):
            notes.append(f"{b['nom']} : statut « {a.get('statut')} » → « {b.get('statut')} »")
        if a.get('prog', {}).get('etat') != b.get('prog', {}).get('etat'):
            notes.append(f"{b['nom']} : programme {a['prog'].get('etat')} → {b['prog'].get('etat')}")
        for q in sorted(set(a['pos']) | set(b['pos']), key=int):
            pa, pb = a['pos'].get(q), b['pos'].get(q)
            va, vb = (pa or {}).get('v'), (pb or {}).get('v')
            if va == vb and (pa or {}).get('s') == (pb or {}).get('s'):
                continue
            src = (pb or {}).get('s') or {}
            changes.append({'nom': b['nom'], 'q': q, 'old': va, 'new': vb, 'src': src,
                            'inv': va is not None and vb is not None and va * vb < 0 and abs(va - vb) >= 3})
    for c in new['cands']:
        for q, p in c['pos'].items():
            s = p.get('s') or {}
            if not s.get('url') or not s.get('date'):
                problems.append(f"{c['nom']}, question {q} : source sans lien ou sans date")
    oldall = {x['id'] for x in cur.get('all', [])}
    newall = [x for x in new.get('all', []) if x['id'] not in oldall]
    return added, removed, changes, notes, problems, newall


def reasons_to_hold(removed, changes, problems):
    r = []
    if removed:
        r.append('candidature(s) retirée(s) des données : ' + ', '.join(c['nom'] for c in removed))
    if len(changes) > MAX_CHANGES:
        r.append(f'{len(changes)} positions modifiées (plus de {MAX_CHANGES})')
    inv = [c for c in changes if c['inv']]
    if inv:
        r.append('position inversée : ' + ', '.join(f"{c['nom']} (question {c['q']})" for c in inv))
    if problems:
        r.append(f'{len(problems)} problème(s) de source ou de codage')
    return r


def summary_md(title, cur, new, d, hold, version):
    added, removed, changes, notes, problems, newall = d
    L = [f'# {title}', '']
    if hold:
        L += ['**La mise à jour attend ta validation** : elle n’est pas encore dans l’application.', '', 'Motifs :']
        L += [f'- {r}' for r in hold] + ['']
        L += ['**Pour la publier** : ouvre ' + ACTIONS + ', touche « Run workflow », choisis `approve`, puis « Run workflow ».',
              '**Pour la rejeter** : ne fais rien ; la prochaine vérification repartira des données publiées.', '']
    else:
        L += [f'Version **{version}** publiée sur {SITE} : les téléphones la recevront à leur prochaine vérification (au plus 24 h).', '',
              f"**En cas de problème** : ouvre {ACTIONS}, touche « Run workflow », choisis `rollback` et indique la version `{cur.get('version')}` pour revenir à l’état précédent.", '']
    L += [f"Données 2027 et moi du {new.get('maj_donnees', '?')} · {len(new['cands'])} candidatures retenues (programme publié et au moins 5 positions).", '']
    if added:
        L += ['## Nouvelles candidatures sur la carte', '']
        for c in added:
            L.append(f"- **{c['nom']}** ({c['parti']}), {len(c['pos'])} positions. Codage Cap 2032 complémentaire à prévoir si besoin. Programme : {c['prog'].get('url')}")
        L.append('')
    if removed:
        L += ['## Candidatures retirées', ''] + [f"- {c['nom']}" for c in removed] + ['']
    if notes:
        L += ['## Statuts et programmes', ''] + [f'- {n}' for n in notes] + ['']
    if changes:
        L += ['## Positions modifiées', '']
        for c in changes:
            s = c['src']
            L.append(f"- {c['nom']}, question {c['q']} : {lab(c['old'])} → **{lab(c['new'])}**"
                     + (' ⚠️ inversion' if c['inv'] else '')
                     + (f" — source : [{s.get('titre', 'lien')}]({s.get('url')}) ({s.get('date', '?')})" if s.get('url') else ''))
        L.append('')
    if newall:
        L += ['## Candidatures annoncées sans programme publié (non affichées sur la carte)', '']
        L += [f"- {x['nom']} ({x.get('parti', '')}), {x['statut']}" for x in newall] + ['']
    if problems:
        L += ['## Problèmes détectés', ''] + [f'- {p}' for p in problems] + ['']
    L += ['---', 'Message automatique du dépôt cap2032-data. Sources : 2027 et moi (Licence Ouverte 2.0).']
    return '\n'.join(L)


def sign_and_write(data, note):
    from cryptography.hazmat.primitives import serialization
    pem = os.environ.get('CAP_SIGNING_KEY', '').strip()
    if not pem:
        sys.exit('CAP_SIGNING_KEY manquant : impossible de signer.')
    key = serialization.load_pem_private_key(pem.encode(), None)
    raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
    sig = base64.b64encode(key.sign(raw)).decode()
    (ROOT / 'cands.json').write_bytes(raw)
    (ROOT / 'cands.json.sig').write_text(sig)
    (ROOT / 'history').mkdir(exist_ok=True)
    (ROOT / 'history' / f"{data['version']}.json").write_bytes(raw)
    man = {'version': data['version'], 'generated': data['generated'], 'file': 'cands.json',
           'sha256': hashlib.sha256(raw).hexdigest(), 'sig': sig, 'bytes': len(raw), 'candidats': len(data['cands'])}
    (ROOT / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding='utf-8')
    log = ROOT / 'CHANGELOG.md'
    old = log.read_text(encoding='utf-8') if log.exists() else '# Journal des mises à jour\n'
    head, _, rest = old.partition('\n')
    day = dt.datetime.now(dt.timezone.utc).strftime('%d/%m/%Y')
    log.write_text(f"{head}\n\n## {data['version']} ({day})\n{note}\n{rest}", encoding='utf-8')


def stamp(data, cur):
    data = dict(data)
    data['version'] = new_version(cur)
    data['generated'] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='update', choices=['update', 'approve', 'rollback'])
    ap.add_argument('--new', default='/tmp/new.json')
    ap.add_argument('--version', default='')
    a = ap.parse_args()
    cur = load(ROOT / 'cands.json')
    pending = ROOT / 'pending' / 'cands.json'

    if a.mode == 'rollback':
        src = ROOT / 'history' / f'{a.version.strip()}.json'
        if not src.exists():
            sys.exit(f'Version {a.version} introuvable dans history/.')
        data = stamp(load(src), cur)
        d = diff(cur, data, [])
        sign_and_write(data, f'- Retour à la version {a.version} (demandé par le vérificateur).')
        title = f'↩️ Retour à la version {a.version} (publiée sous le n° {data["version"]})'
        SUMMARY.write_text(summary_md(title, cur, data, d, [], data['version']), encoding='utf-8')
        return out(status='rolledback', title=title)

    if a.mode == 'approve':
        if not pending.exists():
            SUMMARY.write_text('Aucune mise à jour en attente.', encoding='utf-8')
            return out(status='none', title='Aucune mise à jour en attente')
        data = stamp(load(pending), cur)
        d = diff(cur, data, [])
        sign_and_write(data, '- Mise à jour validée par le vérificateur.')
        for f in (ROOT / 'pending').iterdir():
            f.unlink()
        (ROOT / 'pending').rmdir()
        title = f'✅ Mise à jour validée et publiée (version {data["version"]})'
        SUMMARY.write_text(summary_md(title, cur, data, d, [], data['version']), encoding='utf-8')
        return out(status='approved', title=title)

    new = load(a.new)
    issues = load(a.new + '.issues.json') if Path(a.new + '.issues.json').exists() else []
    if core(new) == core(cur) and not issues:
        SUMMARY.write_text('Aucun changement dans les données ouvertes.', encoding='utf-8')
        return out(status='none', title='Aucun changement')
    if pending.exists() and core(load(pending)) == core(new):
        SUMMARY.write_text('Mise à jour déjà en attente de validation.', encoding='utf-8')
        return out(status='none', title='Déjà en attente')
    d = diff(cur, new, issues)
    added, removed, changes, notes, problems, newall = d
    if not (added or removed or changes or notes or problems):
        # seules les dates de mise à jour des sources ont bougé : on publie sans déranger personne
        data = stamp(new, cur)
        sign_and_write(data, '- Dates de mise à jour des sources actualisées.')
        SUMMARY.write_text('Mise à jour technique (dates des sources).', encoding='utf-8')
        return out(status='quiet', title=f'Mise à jour technique (version {data["version"]})')
    hold = reasons_to_hold(removed, changes, problems)
    if hold:
        (ROOT / 'pending').mkdir(exist_ok=True)
        pending.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding='utf-8')
        title = '⏸ Mise à jour des candidatures en attente de validation'
        SUMMARY.write_text(summary_md(title, cur, new, d, hold, None), encoding='utf-8')
        (ROOT / 'pending' / 'summary.md').write_text(SUMMARY.read_text(encoding='utf-8'), encoding='utf-8')
        return out(status='held', title=title)
    data = stamp(new, cur)
    bits = []
    if added: bits.append(f'{len(added)} nouvelle(s) candidature(s)')
    if changes: bits.append(f'{len(changes)} position(s) modifiée(s)')
    if notes: bits.append(f'{len(notes)} changement(s) de statut ou de programme')
    sign_and_write(data, '- ' + ', '.join(bits) + '.')
    title = f'🗳 Candidatures mises à jour (version {data["version"]}) : ' + ', '.join(bits)
    SUMMARY.write_text(summary_md(title, cur, data, d, [], data['version']), encoding='utf-8')
    out(status='published', title=title)


if __name__ == '__main__':
    main()
