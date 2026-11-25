"""Rule engine over graph-projected relationships (not over stored fixture JSON)."""
from itertools import product


def overlaps(a,b):
    return a['start'] < b['end'] and b['start'] < a['end']


def explain(model):
    tasks = sorted(model['tasks'], key=lambda t:(t['seq'],t['id']))
    byid = {t['id']:t for t in tasks}
    people = {p['id']:p for p in model['people']}
    abilities = {p['id']:set() for p in model['people']}
    for edge in model['abilities']:
        abilities[edge['person']].add(edge['capability'])
    windows = {p['id']:[] for p in model['people']}
    for window in model['windows']:
        windows[window['person']].append(window)
    busies = {p['id']:[] for p in model['people']}
    for busy in model['busy']:
        busies[busy['person']].append(busy)
    accepts = {t['id']:[] for t in tasks}
    rejections = {t['id']:[] for t in tasks}
    for o in model['offers']:
        t = byid[o['need']]
        p = people[o['person']]
        reason = None
        if o['state']!='confirmed':
            reason = 'not_confirmed'
        elif p['cancelled']:
            reason = 'person_cancelled'
        elif t['required'] not in abilities[p['id']]:
            reason = 'missing_capability'
        elif not any(w['start']<=t['start'] and t['end']<=w['end'] for w in windows[p['id']]):
            reason = 'outside_availability'
        elif any(overlaps(t,b) for b in busies[p['id']]):
            reason = 'conflicting_commitment'
        if reason:
            rejections[t['id']].append({'person':p['name'],'reason':reason})
        else:
            accepts[t['id']].append(p['id'])
    for t in tasks:
        accepts[t['id']] = sorted(set(accepts[t['id']]))
    handoff_errors=[]
    for a,b in zip(tasks,tasks[1:]):
        if a['end']>b['start']:
            handoff_errors.append(f"temporal_overlap:{a['slot']}->{b['slot']}")
        if a['destination'] != b['origin']:
            handoff_errors.append(f"location_mismatch:{a['slot']}->{b['slot']}")
    def valid_assignment(selections):
        seen={}
        for t,p in zip(tasks,selections):
            for prior in seen.get(p,[]):
                if overlaps(t, prior):
                    return False
            seen.setdefault(p,[]).append(t)
        return True
    solution=None
    if not handoff_errors and all(accepts[t['id']] for t in tasks):
        for choices in product(*(accepts[t['id']] for t in tasks)):
            if valid_assignment(choices):
                solution={t['slot']:people[p]['name'] for t,p in zip(tasks,choices)}
                break
    individual_ok=sum(bool(accepts[t['id']]) for t in tasks)
    reasons=[{'need':t['slot'],'reason':'no_eligible_confirmed_helper',
              'offers':rejections[t['id']]} for t in tasks if not accepts[t['id']]]
    reasons += [{'need':'journey','reason':x} for x in handoff_errors]
    if solution is None and not reasons and len(tasks)>0:
        reasons.append({'need':'journey','reason':'helper_assignment_conflict'})
    return {
        'visit':model['visit']['id'],
        'covered':solution is not None,
        'assignments':solution or {},
        'eligible_needs':individual_ok,
        'total_needs':len(tasks),
        'uncovered_reasons':reasons,
        'graph_counts':{'needs':len(tasks),'offers':len(model['offers']),
                        'abilities':len(model['abilities'])},
        'claim':'Synthetic confirmation feasibility only. No actual caregiver acceptance, medical or transport outcome.'
    }
