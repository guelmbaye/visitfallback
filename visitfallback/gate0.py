"""Gate 0 report. Always labels whether actual Relate executed."""
import argparse,copy,json
from pathlib import Path
from .engine import explain
from .projection import fixture_projection
from .oracle import reference,naive_any_confirmed,naive_per_need_confirmed


def load(path):
    d=json.loads(Path(path).read_text(encoding='utf8'))
    if d.get('data_kind')!='SYNTHETIC_ONLY':
        raise ValueError('Refuse non-synthetic data')
    return d['scenarios']


def compare_scenarios(fixtures,reader):
    reports=[]
    for f in fixtures:
        model=reader(f)
        got=explain(model)
        want=reference(f)
        match=(got['covered']==want==f['expected_covered'])
        reports.append({'scenario':f['id'],'purpose':f['purpose'],
           'coverage_from_model':got['covered'],'oracle_coverage':want,
           'expected':f['expected_covered'],'parity':match,
           'naive_any_confirmed':naive_any_confirmed(f),
           'naive_per_need_confirmed':naive_per_need_confirmed(f),
           'details':got})
    return reports


def run_local(fixtures):
    return compare_scenarios(fixtures,fixture_projection)


def run_relate(fixtures,store):
    from .relate_backend import connect_new,seed,read_model,mutate_offer
    conn=connect_new(store)
    try:
        for f in fixtures:seed(conn,f)
        results=compare_scenarios(fixtures,lambda f: read_model(conn,f['id']))
        scenario=next(f for f in fixtures if f['id']=='rescue_complete')
        def verify(want):
            model=read_model(conn,scenario['id'])
            outcome=explain(model)['covered']
            return outcome==want
        a=verify(True)
        mutate_offer(conn,'rescue_complete','CRET','proposed')
        b=verify(False)
        mutate_offer(conn,'rescue_complete','CRET','confirmed')
        a2=verify(True)
        return results,{'A_confirmed':a,'B_withdrawn':b,'A_restored':a2,'restored':a and b and a2}
    finally:
        conn.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--backend',choices=['offline','relate','both'],default='offline')
    p.add_argument('--data',default='data/scenarios.json')
    p.add_argument('--store',default='build/visitfallback-gate0.rl')
    p.add_argument('--report',default='build/gate0-report.json')
    args=p.parse_args()
    f=load(args.data)
    results={'data_kind':'SYNTHETIC_ONLY','scenario_count':len(f),
        'interpretation':'No clinical advice, actual caregiver confirmation or service efficacy claims.'}
    if args.backend in ('offline','both'):
        r=run_local(f);results['offline']={'scenarios':r,'passed':all(x['parity'] for x in r),
            'false_covered':sum(x['coverage_from_model'] and not x['oracle_coverage'] for x in r),
            'status':'SIMULATED_PROJECTION_ONLY_NOT_RELATE'}
    if args.backend in ('relate','both'):
        r,m=run_relate(f,args.store)
        results['relate']={'scenarios':r,'passed':all(x['parity'] for x in r),
           'false_covered':sum(x['coverage_from_model'] and not x['oracle_coverage'] for x in r),
           'mutation':m,'store':args.store,'status':'ACTUAL_RELATE_EXECUTED'}
        if 'offline' in results:
            results['same_outcome']=all(
                a['coverage_from_model']==b['coverage_from_model']
                and a['details']['eligible_needs']==b['details']['eligible_needs']
                and a['details']['assignments']==b['details']['assignments']
                and [(z['need'],z['reason']) for z in a['details']['uncovered_reasons']]
                    ==[(z['need'],z['reason']) for z in b['details']['uncovered_reasons']]
                for a,b in zip(results['offline']['scenarios'],r)
            )
    ok=all(results[key]['passed'] for key in ('offline','relate') if key in results)
    if 'relate' in results:ok=ok and results['relate']['mutation']['restored'] and results.get('same_outcome',True)
    results['gate0_status']='PASS_FULL_RELATE' if ok and 'relate' in results else ('PASS_OFFLINE_ONLY' if ok else 'FAIL')
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'gate0_status':results['gate0_status'],'count':len(f),
                      'false_covered_offline':results.get('offline',{}).get('false_covered'),
                      'relate_pass':results.get('relate',{}).get('passed'),
                      'mutation':results.get('relate',{}).get('mutation'),
                      'report':str(path)},indent=2))
    if not ok:raise SystemExit(1)

if __name__=='__main__': main()
