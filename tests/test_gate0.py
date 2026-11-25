import copy,unittest
from visitfallback.gate0 import load,run_local
from visitfallback.engine import explain
from visitfallback.oracle import reference,naive_per_need_confirmed
from visitfallback.projection import fixture_projection

class GateZeroTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.f=load('data/scenarios.json');cls.by={f['id']:f for f in cls.f}
 def test_scenarios_are_synthetic(self):
  self.assertEqual(len(self.f),11)
 def test_oracle_expected_cases(self):
  self.assertTrue(all(reference(f)==f['expected_covered'] for f in self.f))
 def test_projection_oracle_parity(self):
  self.assertTrue(all(r['parity'] for r in run_local(self.f)))
 def test_zero_false_covered(self):
  self.assertEqual(sum(explain(fixture_projection(f))['covered'] and not reference(f) for f in self.f),0)
 def test_original_covered(self):
  self.assertTrue(explain(fixture_projection(self.by['original_covered']))['covered'])
 def test_cancelled_uncovered(self):
  self.assertFalse(explain(fixture_projection(self.by['cancelled']))['covered'])
 def test_two_of_three_not_covered(self):
  r=explain(fixture_projection(self.by['partial_trip']))
  self.assertEqual(r['eligible_needs'],2)
  self.assertFalse(r['covered'])
  self.assertIn('return',[x['need'] for x in r['uncovered_reasons']])
 def test_rescue_confirmed(self):
  r=explain(fixture_projection(self.by['rescue_complete']))
  self.assertTrue(r['covered'])
  self.assertEqual(r['assignments'],{'outbound':'Omar','escort':'Lina','return':'Celine'})
 def test_unconfirmed_never_counts(self):
  r=explain(fixture_projection(self.by['unconfirmed_return']))
  self.assertFalse(r['covered']);self.assertEqual(r['eligible_needs'],2)
 def test_busy_driver_rejected(self):
  r=explain(fixture_projection(self.by['busy_driver']))
  self.assertFalse(r['covered'])
  self.assertTrue(any(o['reason']=='conflicting_commitment' for x in r['uncovered_reasons'] for o in x.get('offers',[])))
 def test_missing_capability_rejected(self):
  r=explain(fixture_projection(self.by['capability_missing']))
  self.assertFalse(r['covered'])
  self.assertTrue(any(o['reason']=='missing_capability' for x in r['uncovered_reasons'] for o in x.get('offers',[])))
 def test_late_handoff_rejected(self):
  r=explain(fixture_projection(self.by['late_handoff']))
  self.assertFalse(r['covered']);self.assertTrue(any('temporal_overlap' in x['reason'] for x in r['uncovered_reasons']))
 def test_wrong_location_handoff_rejected(self):
  r=explain(fixture_projection(self.by['wrong_handoff_location']))
  self.assertFalse(r['covered']);self.assertTrue(any('location_mismatch' in x['reason'] for x in r['uncovered_reasons']))
 def test_helper_cancelled(self):
  self.assertFalse(explain(fixture_projection(self.by['helper_cancelled']))['covered'])
 def test_availability_short(self):
  self.assertFalse(explain(fixture_projection(self.by['availability_short']))['covered'])
 def test_naive_baseline_false_positive_exists(self):
  self.assertTrue(naive_per_need_confirmed(self.by['busy_driver']))
  self.assertFalse(reference(self.by['busy_driver']))
 def test_independent_oracle_does_not_share_engine(self):
  import inspect,visitfallback.oracle as oracle
  self.assertNotIn('from .engine',inspect.getsource(oracle))
 def test_fixture_mutation_is_detected_by_reference(self):
  f=copy.deepcopy(self.by['rescue_complete'])
  for o in f['offers']:
   if o['id']=='CRET':o['state']='proposed'
  self.assertFalse(reference(f))
  self.assertFalse(explain(fixture_projection(f))['covered'])
 def test_missing_complete_coverage_does_not_claim_medical_outcome(self):
  self.assertIn('No actual caregiver acceptance',explain(fixture_projection(self.by['rescue_complete']))['claim'])
