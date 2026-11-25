import importlib.util,tempfile,unittest
from pathlib import Path
from visitfallback.gate0 import load,run_relate
from visitfallback.engine import explain

@unittest.skipUnless(importlib.util.find_spec('relate'),'Requires real relate-db; never emulate it')
class RelateGate0Test(unittest.TestCase):
 def test_all_eleven_scenarios_and_mutation_cycle(self):
  with tempfile.TemporaryDirectory() as d:
   r,m=run_relate(load('data/scenarios.json'),str(Path(d)/'fresh.rl'))
   self.assertEqual(len(r),11)
   self.assertTrue(all(x['parity'] for x in r),[(x['scenario'],x['parity']) for x in r])
   self.assertTrue(m['restored'],m)
 def test_deleting_cypher_capability_edge_changes_decision(self):
  from visitfallback.relate_backend import connect_new,seed,read_model
  f=next(f for f in load('data/scenarios.json') if f['id']=='rescue_complete')
  with tempfile.TemporaryDirectory() as d:
   c=connect_new(str(Path(d)/'mutation.rl'))
   try:
    seed(c,f)
    self.assertTrue(explain(read_model(c,'rescue_complete'))['covered'])
    c.execute('''MATCH (p:Person {id:$p})-[r:CAN_DO]->(c:Capability {id:$cap}) DELETE r''',
              {'p':'rescue_complete:CEL','cap':'rescue_complete:DRIVE'})
    self.assertFalse(explain(read_model(c,'rescue_complete'))['covered'])
   finally:c.close()
