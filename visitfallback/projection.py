"""Test-only, fixture-to-edge projection; mirrors the graph structure.
Not used as fallback in Relate integration. Gate 0 always labels backend.
"""

def fixture_projection(f):
    cap=[]; win=[]; busy=[]
    for p in f['people']:
        for c in p['capabilities']:cap.append({'person':p['id'],'capability':c})
        for i,(start,end) in enumerate(p['availability']):
            win.append({'person':p['id'],'start':start,'end':end,'id':f"{p['id']}-W{i}"})
        for i,(start,end) in enumerate(p.get('busy',[])):
            busy.append({'person':p['id'],'start':start,'end':end,'id':f"{p['id']}-B{i}"})
    return {'visit':{'id':f['id'],'label':f['title']},
            'tasks':[{'id':n['id'],'slot':n['slot'],'seq':n['seq'],'start':n['start'],'end':n['end'],
                      'origin':n['origin'],'destination':n['destination'],'required':n['capability']} for n in f['needs']],
            'people':[{'id':p['id'],'name':p['name'],'cancelled':p.get('cancelled',False)} for p in f['people']],
            'offers':[dict(o) for o in f['offers']], 'abilities':cap,'windows':win,'busy':busy}
