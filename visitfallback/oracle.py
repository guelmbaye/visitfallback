"""Independent exhaustive reference check on raw fixture input.

DO NOT import the production engine. Enumerates whole assignments and checks
all obligations from scratch; designed for small synthetic fixtures only.
"""
import itertools


def reference(fixture):
    needs=sorted(fixture['needs'],key=lambda n:n['seq'])
    persons={p['id']:p for p in fixture['people']}
    pending=[]
    for need in needs:
        options=[]
        for offer in fixture['offers']:
            if offer['need']!=need['id'] or offer['state']!='confirmed':
                continue
            person=persons[offer['person']]
            if person.get('cancelled',False):
                continue
            if need['capability'] not in person['capabilities']:
                continue
            available=False
            for w in person['availability']:
                if w[0]<=need['start'] and need['end']<=w[1]:
                    available=True
            if not available:
                continue
            if any(need['start']<busy[1] and busy[0]<need['end'] for busy in person.get('busy',[])):
                continue
            options.append(person['id'])
        pending.append(options)
    if not all(pending):
        return False
    for ix in range(len(needs)-1):
        if needs[ix]['end']>needs[ix+1]['start'] or needs[ix]['destination']!=needs[ix+1]['origin']:
            return False
    for picks in itertools.product(*pending):
        ok=True
        for i in range(len(needs)):
            for j in range(i+1,len(needs)):
                if picks[i]==picks[j] and needs[i]['start']<needs[j]['end'] and needs[j]['start']<needs[i]['end']:
                    ok=False
        if ok:
            return True
    return False


def naive_any_confirmed(fixture):
    return any(o['state']=='confirmed' for o in fixture['offers'])


def naive_per_need_confirmed(fixture):
    return all(any(o['need']==n['id'] and o['state']=='confirmed' for o in fixture['offers']) for n in fixture['needs'])
