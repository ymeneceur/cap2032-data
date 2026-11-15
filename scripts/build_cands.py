"""Construit cands.json pour Cap 2032 à partir des données ouvertes de 2027 et moi.

Usage : python scripts/build_cands.py CHEMIN/2027etmoi/data SORTIE.json

Règle de sélection : candidature dont le programme est publié (en tout ou en partie, selon 2027 et moi)
et qui a au moins 5 positions sur les questions de Cap 2032.
Les problèmes rencontrés (mesure citée introuvable, etc.) sont écrits dans SORTIE.issues.json.
"""
import json,re,os,sys,datetime as dt
E,OUT=sys.argv[1],sys.argv[2]
Q=json.load(open(f'{E}/questions.json',encoding='utf-8'));POS=Q['positions'];QT={x['id']:x['texte'] for x in Q['questions']}
CAND=json.load(open(f'{E}/candidats.json',encoding='utf-8'))
INFO={c['id']:c for c in CAND['candidats']}
S={'pour':2,'plutot_pour':1,'nuance':0,'plutot_contre':-1,'contre':-2}
# Nos questions (numéro 1-27) -> question 2027etmoi, sens, coefficient (0,5 = question proche mais pas identique)
MAP={1:('q05',1,1),2:('q01',1,1),4:('q03',1,1),7:('q18',1,1),8:('q17',1,1),9:('q35',-1,1),10:('q14',1,.5),11:('q29',1,1),12:('q11',1,1),15:('q15',1,1),17:('q19',1,1),18:('q20',1,1),20:('q33',1,1),25:('q34',1,1)}
# Codage complémentaire à partir des mesures sourcées (motif cherché dans le texte de la mesure)
EXTRA={
 3:{'lisnard':(2,r"200 milliards d'euros d'économies"),'philippe':(1,r'déficit public')},
 5:{'melenchon':(2,r'Renationalisation de la SNCF'),'roussel':(2,r'TotalEnergies et Engie nationalisés'),'philippot':(2,r'Renationalisation des autoroutes'),'branco':(2,r'nationalisation de la distribution'),'maurel':(2,r"Reprise par l'État de l'infrastructure autoroutière"),'ruffin':(1,r'nationalisations possibles')},
 6:{'glucksmann':(2,r'Grand emprunt européen'),'tondelier':(1,r'haut conseil militaire intégré'),'philippe':(1,r'union européenne des marchés de capitaux'),'dupont-aignan':(-2,r"Sortie de l'Union européenne"),'maurel':(-1,r'rabais sur la contribution')},
 13:{'ruffin':(2,r'réduction de moitié du trafic aérien'),'tondelier':(1,r"hausse du prix des billets d'avion")},
 14:{'philippe':(1,r'zéro surtransposition'),'lisnard':(1,r'Fin des surtranspositions'),'retailleau':(2,r'Réautorisation de certains néonicotinoïdes'),'tondelier':(-2,r'Sortie progressive des pesticides')},
 19:{'maurel':(2,r'Hausse annuelle d.au moins 4 %')},
 21:{'maurel':(1,r"Inscription de l'audiovisuel public dans la Constitution")}}
# Mesures qui répondent plus directement à nos questions que la question proche de 2027etmoi : elles remplacent le codage
OVR={'tondelier':{6:(2,r'haut conseil militaire intégré'),10:(2,r'Régularisation des travailleurs sans papiers'),5:(1,r"régies publiques de l'eau")}}
MIN_POS=5
issues=[]
out=[]
for f in sorted(os.listdir(f'{E}/programmes')):
    if not f.endswith('.json'):continue
    cid=f[:-5]
    prog=json.load(open(f'{E}/programmes/{f}',encoding='utf-8'))
    if prog.get('programme',{}).get('etat') not in ('complet','partiel'):continue
    info=INFO.get(cid,{})
    pos={}
    for n,(qq,sens,coef) in MAP.items():
        p=POS.get(cid,{}).get(qq)
        if p and p['position'] in S:
            pos[n]={'v':S[p['position']]*sens*coef,'r':p['resume'],'s':p['source'],'via':f"2027etmoi : « {QT[qq]} »"+(' (question proche)' if coef<1 else '')+(' (sens inversé)' if sens<0 else '')}
    def coded(n,v,rx):
        m=next((m for m in prog.get('mesures',[]) if re.search(rx,m['texte'])),None)
        if not m:
            issues.append(f"{cid} : mesure introuvable pour le codage Cap 2032 de la question {n} (motif « {rx} »)");return None
        return {'v':v,'r':m['texte'],'s':m['source'],'via':'mesure du programme (codage Cap 2032)'}
    for n,d in EXTRA.items():
        if cid in d and n not in pos:
            c=coded(n,*d[cid])
            if c:pos[n]=c
    for n,(v,rx) in OVR.get(cid,{}).items():
        c=coded(n,v,rx)
        if c:pos[n]=c
    if len(pos)<MIN_POS:continue
    out.append({'id':cid,'nom':info.get('nom',cid),'parti':info.get('parti',''),'statut':info.get('statut',''),'statut_detail':info.get('statut_detail',''),
      'prog':{'titre':prog['programme'].get('titre'),'url':prog['programme'].get('url'),'etat':prog['programme'].get('etat'),'maj':prog.get('mise_a_jour')},
      'pos':{str(k):v for k,v in sorted(pos.items())}})
ALL=[{'id':c['id'],'nom':c['nom'],'parti':c.get('parti',''),'statut':c['statut'],'detail':c.get('statut_detail',''),'s':c.get('source')} for c in CAND['candidats'] if c['statut'] in('declare','pressenti')]
now=dt.datetime.now(dt.timezone.utc)
res={'version':int(now.strftime('%Y%m%d%H')),'generated':now.replace(microsecond=0).isoformat(),'maj':Q['mise_a_jour'],'maj_candidats':CAND['mise_a_jour'],'maj_donnees':json.load(open(f'{E}/meta.json'))['donnees'],'cands':out,'all':ALL}
json.dump(res,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(issues,open(OUT+'.issues.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(len(out),'candidatures retenues ;',len(issues),'problème(s)')
