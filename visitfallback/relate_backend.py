"""Actual Relate graph used as the source for Gate 0 runtime decisions.

No synthetic fixture fallback: if import/open/query fails, verification fails.
"""
from pathlib import Path


def connect_new(path):
    try:
        import relate
    except ImportError as e:
        raise RuntimeError('relate-db not installed. Install requirements.txt; cannot claim Relate PASS.') from e
    store=Path(path)
    if store.exists():
        raise FileExistsError(f'Refusing to overwrite existing Relate store: {store}')
    store.parent.mkdir(parents=True,exist_ok=True)
    return relate.connect(str(store))


def _run(conn,q,**params):
    return conn.execute(q,params)


def seed(conn, fixture):
    prefix=fixture['id']+':'
    vid=fixture['id']
    _run(conn,'CREATE (v:Visit {id:$id,label:$label})',id=vid,label=fixture['title'])
    capabilities=set()
    for n in fixture['needs']:
        capabilities.add(n['capability'])
    for p in fixture['people']:
        capabilities.update(p['capabilities'])
    for c in sorted(capabilities):
        _run(conn,'CREATE (c:Capability {id:$id})',id=prefix+c)
    for n in fixture['needs']:
        _run(conn,'CREATE (n:Need {id:$id,slot:$slot,seq:$seq,start:$start,end:$end,origin:$origin,destination:$destination})',
             id=prefix+n['id'],slot=n['slot'],seq=n['seq'],start=n['start'],end=n['end'],origin=n['origin'],destination=n['destination'])
        _run(conn,'MATCH (v:Visit {id:$v}),(n:Need {id:$n}) CREATE (v)-[:NEEDS]->(n)',v=vid,n=prefix+n['id'])
        _run(conn,'MATCH (n:Need {id:$n}),(c:Capability {id:$c}) CREATE (n)-[:REQUIRES]->(c)',
             n=prefix+n['id'],c=prefix+n['capability'])
    for p in fixture['people']:
        pid=prefix+p['id']
        _run(conn,'CREATE (p:Person {id:$id,name:$name,cancelled:$cancelled})',
             id=pid,name=p['name'],cancelled=p.get('cancelled',False))
        _run(conn,'MATCH (v:Visit {id:$v}),(p:Person {id:$p}) CREATE (v)-[:HAS_HELPER]->(p)',v=vid,p=pid)
        for cap in p['capabilities']:
            _run(conn,'MATCH (p:Person {id:$p}),(c:Capability {id:$c}) CREATE (p)-[:CAN_DO]->(c)',p=pid,c=prefix+cap)
        for i,(s,e) in enumerate(p['availability']):
            wid=f'{pid}:window:{i}'
            _run(conn,'CREATE (w:Window {id:$id,start:$start,end:$end})',id=wid,start=s,end=e)
            _run(conn,'MATCH (p:Person {id:$p}),(w:Window {id:$w}) CREATE (p)-[:AVAILABLE_DURING]->(w)',p=pid,w=wid)
        for i,(s,e) in enumerate(p.get('busy',[])):
            bid=f'{pid}:busy:{i}'
            _run(conn,'CREATE (b:Busy {id:$id,start:$start,end:$end})',id=bid,start=s,end=e)
            _run(conn,'MATCH (p:Person {id:$p}),(b:Busy {id:$b}) CREATE (p)-[:BUSY_DURING]->(b)',p=pid,b=bid)
    for o in fixture['offers']:
        oid=prefix+o['id']
        _run(conn,'CREATE (o:Offer {id:$id,state:$state})',id=oid,state=o['state'])
        _run(conn,'MATCH (p:Person {id:$p}),(o:Offer {id:$o}) CREATE (p)-[:MADE_OFFER]->(o)',p=prefix+o['person'],o=oid)
        _run(conn,'MATCH (o:Offer {id:$o}),(n:Need {id:$n}) CREATE (o)-[:FOR_NEED]->(n)',o=oid,n=prefix+o['need'])


def _records(conn,q,**params):
    return [dict(row) for row in conn.execute(q,params)]


def read_model(conn,visit_id):
    p={'v':visit_id}
    v=_records(conn,'MATCH (v:Visit {id:$v}) RETURN v.id AS id,v.label AS label',**p)
    if len(v)!=1: raise ValueError('Expected exactly one visit in Relate')
    needs=_records(conn,'''MATCH (v:Visit {id:$v})-[:NEEDS]->(n:Need)-[:REQUIRES]->(c:Capability)
    RETURN n.id AS id,n.slot AS slot,n.seq AS seq,n.start AS start,n.end AS end,n.origin AS origin,
    n.destination AS destination,c.id AS required ORDER BY seq''',**p)
    people=_records(conn,'''MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)
    RETURN p.id AS id,p.name AS name,p.cancelled AS cancelled ORDER BY id''',**p)
    abilities=_records(conn,'''MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:CAN_DO]->(c:Capability)
    RETURN p.id AS person,c.id AS capability''',**p)
    windows=_records(conn,'''MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:AVAILABLE_DURING]->(w:Window)
    RETURN p.id AS person,w.start AS start,w.end AS end,w.id AS id''',**p)
    busy=_records(conn,'''MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:BUSY_DURING]->(b:Busy)
    RETURN p.id AS person,b.start AS start,b.end AS end,b.id AS id''',**p)
    offers=_records(conn,'''MATCH (v:Visit {id:$v})-[:NEEDS]->(n:Need)<-[:FOR_NEED]-(o:Offer)<-[:MADE_OFFER]-(p:Person)
    RETURN o.id AS id,o.state AS state,n.id AS need,p.id AS person''',**p)
    # Graph identifiers are scenario-prefixed. Preserve them internally and make
    # abilities cross-reference exact prefixed IDs; no alternate fixture reads.
    return {'visit':v[0],'tasks':needs,'people':people,'abilities':abilities,
            'windows':windows,'busy':busy,'offers':offers}


def mutate_offer(conn, visit_id, offer_local_id, new_state):
    if new_state not in ('confirmed','proposed','withdrawn'):
        raise ValueError('Invalid offer state')
    target=visit_id+':'+offer_local_id
    r=_records(conn,'MATCH (o:Offer {id:$id}) SET o.state=$state RETURN o.id AS id,o.state AS state',id=target,state=new_state)
    if len(r)!=1: raise ValueError(f'Missing offer {target}')
    return r[0]


def mutate_busy_window(conn, visit_id, person_local_id, index, start, end):
    """Change an existing, graph-linked external commitment via Cypher.

    Do not create or delete nodes while changing demo phases. If the linked
    Busy record is absent, fail instead of trusting the fixture.
    """
    if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= 1440:
        raise ValueError('Invalid synthetic busy interval')
    target=f'{visit_id}:{person_local_id}:busy:{index}'
    rows=_records(conn,
        'MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:BUSY_DURING]->(b:Busy {id:$id}) '
        'SET b.start=$start, b.end=$end RETURN b.id AS id,b.start AS start,b.end AS end',
        v=visit_id,id=target,start=start,end=end)
    if len(rows)!=1:
        raise ValueError(f'Expected exactly one attached Busy node: {target}')
    return rows[0]
