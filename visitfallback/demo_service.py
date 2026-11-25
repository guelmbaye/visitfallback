"""One-visit Relate-backed handoff demonstration with a separate exhaustive oracle.

No healthcare advice, real identities, authentication, or actual confirmations.
The only source of *runtime* relationships is the Relate graph.
"""
import copy
from pathlib import Path
from .gate0 import load
from .relate_backend import connect_new, seed, read_model, mutate_offer, mutate_busy_window
from .engine import explain
from .oracle import reference, naive_per_need_confirmed

# Celine has a separate fictional commitment in this SAME graph. At baseline
# it starts at noon (outside her 10:45-11:30 return). In phase E, the
# commitment moves to 11:00-11:15 and overlaps the return she confirmed.
# Times are minutes since midnight, 24h clock.
BUSY_NORMAL = (720, 750)
BUSY_CONFLICT = (660, 675)
BUSY_PERSON = 'CEL'

PHASES = {
    "A": {"name":"Original covered", "label":"Sofia covers all three needs", "expect": True,
          "states": {"SOUT":"confirmed", "SESC":"confirmed", "SRET":"confirmed", "OOUT":"proposed", "LESC":"proposed", "CRET":"proposed"}},
    "B": {"name":"Caregiver cancels", "label":"Sofia withdraws; alternatives are only proposed", "expect": False,
          "states": {"SOUT":"withdrawn", "SESC":"withdrawn", "SRET":"withdrawn", "OOUT":"proposed", "LESC":"proposed", "CRET":"proposed"}},
    "C": {"name":"Partial rescue", "label":"Omar and Lina confirm; the return remains unconfirmed", "expect": False,
          "states": {"SOUT":"withdrawn", "SESC":"withdrawn", "SRET":"withdrawn", "OOUT":"confirmed", "LESC":"confirmed", "CRET":"proposed"}},
    "D": {"name":"Complete rescue", "label":"Celine also confirms the return; the chain is complete", "expect": True,
          "states": {"SOUT":"withdrawn", "SESC":"withdrawn", "SRET":"withdrawn", "OOUT":"confirmed", "LESC":"confirmed", "CRET":"confirmed"}},
    "E": {"name":"All confirmed, still impossible",
          "label":"All three helpers confirm, but Celine is double-booked during the return",
          "expect": False,
          "states": {"SOUT":"withdrawn", "SESC":"withdrawn", "SRET":"withdrawn", "OOUT":"confirmed", "LESC":"confirmed", "CRET":"confirmed"}},
}

CYPHER = {
 "update": "MATCH (o:Offer {id: $id}) SET o.state = $state RETURN o.id, o.state",
 "read": "MATCH (v:Visit {id:$v})-[:NEEDS]->(n:Need)<-[:FOR_NEED]-(o:Offer)<-[:MADE_OFFER]-(p:Person) RETURN o.id, o.state, n.id, p.id",
 "abilities": "MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:CAN_DO]->(c:Capability) RETURN p.id, c.id",
 "windows": "MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:AVAILABLE_DURING]->(w:Window) RETURN p.id, w.start, w.end",
 "busy": "MATCH (v:Visit {id:$v})-[:HAS_HELPER]->(p:Person)-[:BUSY_DURING]->(b:Busy) RETURN p.id, b.start, b.end",
}

class CareDemo:
    def __init__(self, store, data="data/scenarios.json"):
        self.fixture = next(f for f in load(data) if f["id"] == "original_covered")
        self.fixture = copy.deepcopy(self.fixture)
        celine = next(p for p in self.fixture['people'] if p['id']==BUSY_PERSON)
        if celine.get('busy'):
            raise ValueError('Unexpected preexisting Celine commitment in source fixture')
        celine['busy'] = [list(BUSY_NORMAL)]
        self.conn = connect_new(store)
        try:
            seed(self.conn, self.fixture)
            self.phase = "A"
            self._validate(self.phase)
        except BaseException:
            self.conn.close()
            raise

    def close(self):
        self.conn.close()

    def _validate(self, phase):
        model=read_model(self.conn, self.fixture["id"])
        outcome=explain(model)
        shadow=copy.deepcopy(self.fixture)
        wanted=PHASES[phase]["states"]
        for o in shadow["offers"]:
            o["state"] = wanted[o["id"]]
        expected_busy = BUSY_CONFLICT if phase == 'E' else BUSY_NORMAL
        next(p for p in shadow['people'] if p['id']==BUSY_PERSON)['busy'] = [list(expected_busy)]
        actual_busy=[(b['start'],b['end']) for b in model['busy']
                     if b['id'] == f'{self.fixture["id"]}:{BUSY_PERSON}:busy:0'
                     and b['person'] == f'{self.fixture["id"]}:{BUSY_PERSON}']
        if actual_busy != [expected_busy]:
            raise AssertionError(f'Relate busy edge or window mismatch: {actual_busy} != {[expected_busy]}')
        oracle=reference(shadow)
        states={o["id"].split(":")[-1]:o["state"] for o in model["offers"]}
        if states != wanted:
            raise AssertionError(f"Graph offer states diverge from requested phase: {states} != {wanted}")
        if outcome["covered"] != oracle or oracle != PHASES[phase]["expect"]:
            raise AssertionError("Relate, oracle, and scenario contract disagree")
        return model,outcome,oracle,shadow

    def apply(self,phase):
        if phase not in PHASES: raise ValueError("Invalid phase")
        prior=self.phase
        before=read_model(self.conn,self.fixture['id'])
        old={o['id'].split(':')[-1]:o['state'] for o in before['offers']}
        busy_id=f'{self.fixture["id"]}:{BUSY_PERSON}:busy:0'
        old_busy=[(b['start'],b['end']) for b in before['busy'] if b['id']==busy_id]
        if len(old_busy)!=1: raise AssertionError('Missing unique Relate busy commitment')
        try:
            for oid,new_state in PHASES[phase]['states'].items():
                if old[oid]!=new_state:
                    mutate_offer(self.conn,self.fixture['id'],oid,new_state)
            new_busy=BUSY_CONFLICT if phase=='E' else BUSY_NORMAL
            if old_busy[0]!=new_busy:
                mutate_busy_window(self.conn,self.fixture['id'],BUSY_PERSON,0,*new_busy)
            self._validate(phase)
            self.phase=phase
        except Exception:
            # Defensive restore for a partially changed graph on a failed mutation.
            for oid,old_state in old.items():
                mutate_offer(self.conn,self.fixture['id'],oid,old_state)
            mutate_busy_window(self.conn,self.fixture['id'],BUSY_PERSON,0,*old_busy[0])
            self.phase=prior
            raise
        return self.snapshot()

    def snapshot(self):
        model,outcome,oracle,shadow=self._validate(self.phase)
        needs=[]
        confirmed_needs=sum(any(o['need']==n['id'] and o['state']=='confirmed' for o in model['offers']) for n in model['tasks'])
        blocked={r['need'] for r in outcome['uncovered_reasons'] if r['reason']=='no_eligible_confirmed_helper'}
        for need in model['tasks']:
            offers=[o for o in model['offers'] if o['need']==need['id']]
            person_names={p['id']:p['name'] for p in model['people']}
            offers_view=[{'person': person_names[o['person']], 'state':o['state'],
                          'id':o['id'].split(':')[-1]} for o in sorted(offers,key=lambda x:x['id'])]
            slot=need['slot']
            individually_eligible = slot not in blocked
            candidate_names=[person_names[o['person']] for o in offers if o['state']=='confirmed']
            display_person=outcome['assignments'].get(slot) or (candidate_names[0] if candidate_names else None)
            conflicts=[]
            for offer in offers:
                if offer['state']!='confirmed': continue
                for b in model['busy']:
                    if b['person']==offer['person'] and need['start']<b['end'] and b['start']<need['end']:
                        conflicts.append({'person':person_names[offer['person']], 'start':b['start'],'end':b['end']})
            needs.append({'id':need['id'], 'slot':slot, 'start':need['start'],'end':need['end'],
                          'origin':need['origin'],'destination':need['destination'],
                          'required':need['required'].split(':')[-1],
                          'assigned':outcome['assignments'].get(slot),
                          'individually_eligible':individually_eligible,
                          'candidate_name':display_person,
                          'offers':offers_view, 'conflicts':conflicts,
                          'reasons':[r for r in outcome['uncovered_reasons'] if r['need']==slot]})
        return {
          'data_kind':'SYNTHETIC_ONLY',
          'phase':self.phase,'name':PHASES[self.phase]['name'],
          'label':PHASES[self.phase]['label'],
          'covered':outcome['covered'],
          'covered_count':outcome['eligible_needs'],
          'confirmed_count':confirmed_needs,
          'need_count':outcome['total_needs'],
          'assignments':outcome['assignments'],
          'uncovered_reasons':outcome['uncovered_reasons'],
          'needs':needs,
          'people':[{'name':p['name'], 'cancelled':p['cancelled'],
                     'abilities':sorted(a['capability'].split(':')[-1] for a in model['abilities'] if a['person']==p['id'])}
                    for p in model['people']],
          'proof':{'same_outcome':outcome['covered']==oracle,
                   'independent_oracle':oracle,
                   'busy_window_verified':True,
                   'expected':PHASES[self.phase]['expect'],
                   'naive_per_need_confirmed':naive_per_need_confirmed(shadow),
                   'relate_read':True,
                   'store_mode':'single_file',
                   'graph_counts':outcome['graph_counts'],
                   'claim':outcome['claim']},
          'cypher':CYPHER,
        }
