"""Offline contract + actual Relate integration when the package is present."""
import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from visitfallback.demo_service import PHASES,CareDemo,BUSY_CONFLICT,BUSY_NORMAL
from visitfallback.gate0 import load
from visitfallback.projection import fixture_projection
from visitfallback.engine import explain
from visitfallback.oracle import reference

FIX=next(f for f in load('data/scenarios.json') if f['id']=='original_covered')

class PhaseContractTest(unittest.TestCase):
    def test_all_expected_states_present(self):
        expected={o['id'] for o in FIX['offers']}
        for key, phase in PHASES.items():
            self.assertEqual(set(phase['states']),expected)
            self.assertIn(key,'ABCDE')
    def test_oracle_outcomes_per_phase(self):
        for key,phase in PHASES.items():
            f=copy.deepcopy(FIX)
            for o in f['offers']:
                o['state']=phase['states'][o['id']]
            next(p for p in f['people'] if p['id']=='CEL')['busy']=[list(BUSY_CONFLICT if key=='E' else BUSY_NORMAL)]
            self.assertEqual(reference(f),phase['expect'],key)
            self.assertEqual(explain(fixture_projection(f))['covered'],phase['expect'],key)
    def test_only_return_confirmation_needed_in_c_to_d(self):
        diff=[x for x in PHASES['C']['states'] if PHASES['C']['states'][x]!=PHASES['D']['states'][x]]
        self.assertEqual(diff,['CRET'])
        self.assertEqual(PHASES['C']['states']['CRET'],'proposed')
        self.assertEqual(PHASES['D']['states']['CRET'],'confirmed')
    def test_all_confirmed_but_double_booked_e(self):
        f=copy.deepcopy(FIX)
        for o in f['offers']:
            o['state']=PHASES['E']['states'][o['id']]
        next(p for p in f['people'] if p['id']=='CEL')['busy']=[list(BUSY_CONFLICT)]
        from visitfallback.oracle import naive_per_need_confirmed
        self.assertTrue(naive_per_need_confirmed(f))
        self.assertFalse(reference(f))
        out=explain(fixture_projection(f))
        self.assertFalse(out['covered'])
        self.assertEqual(out['eligible_needs'],2)
        self.assertIn('conflicting_commitment',str(out['uncovered_reasons']))

    def test_e_is_same_offer_states_as_d(self):
        self.assertEqual(PHASES['D']['states'],PHASES['E']['states'])
        self.assertTrue(PHASES['D']['expect'])
        self.assertFalse(PHASES['E']['expect'])

    def test_no_true_coverage_with_partial_confirmation(self):
        self.assertFalse(PHASES['B']['expect'])
        self.assertFalse(PHASES['C']['expect'])
    def test_ui_file_contains_no_external_libraries(self):
        src=Path('web/index.html').read_text()
        self.assertNotIn('https://',' '.join(src.split('<script')))  # no externally hosted scripts
        self.assertIn('SYNTHETIC DATA',src)
        self.assertIn('Not medical advice',src)
    def test_handler_restricted_to_localhost(self):
        src=Path('visitfallback/webapp.py').read_text()
        self.assertIn("args.host!='127.0.0.1'",src)
    def test_not_a_real_confirmation_claim(self):
        src=Path('web/index.html').read_text()
        self.assertIn('It does not send messages to real helpers',src)

@unittest.skipUnless(importlib.util.find_spec('relate') is not None,'relate-db not installed; needs local Windows Relate')
class RealRelateUiTest(unittest.TestCase):
    def test_one_store_five_relate_mutations_with_oracle(self):
        with tempfile.TemporaryDirectory() as d:
            demo=CareDemo(str(Path(d)/'visitfallback-demo.rl'))
            try:
                self.assertEqual(demo.snapshot()['phase'],'A')
                for phase in 'BCDEDA':
                    s=demo.apply(phase)
                    self.assertEqual(s['covered'], PHASES[phase]['expect'])
                    self.assertTrue(s['proof']['same_outcome'])
                    self.assertTrue(s['proof']['relate_read'])
                self.assertEqual(demo.snapshot()['covered'],True)
            finally: demo.close()
    def test_e_real_relate_and_oracle_reject_confirmed_double_booking(self):
        with tempfile.TemporaryDirectory() as d:
            demo=CareDemo(str(Path(d)/'visitfallback-demo.rl'))
            try:
                good=demo.apply('D')
                bad=demo.apply('E')
                restored=demo.apply('D')
                self.assertTrue(good['covered'])
                self.assertEqual(good['confirmed_count'],3)
                self.assertFalse(bad['covered'])
                self.assertEqual(bad['confirmed_count'],3)
                self.assertEqual(bad['covered_count'],2)
                self.assertTrue(bad['proof']['naive_per_need_confirmed'])
                self.assertTrue(bad['proof']['same_outcome'])
                self.assertEqual(bad['needs'][2]['conflicts'][0]['person'],'Celine')
                self.assertIn('conflicting_commitment',str(bad['uncovered_reasons']))
                self.assertTrue(restored['covered'])
                self.assertFalse(restored['needs'][2]['conflicts'])
            finally: demo.close()

    def test_external_busy_graph_mutation_cannot_be_ignored(self):
        from visitfallback.relate_backend import mutate_busy_window
        with tempfile.TemporaryDirectory() as d:
            demo=CareDemo(str(Path(d)/'visitfallback-demo.rl'))
            try:
                demo.apply('D')
                mutate_busy_window(demo.conn,demo.fixture['id'],'CEL',0,*BUSY_CONFLICT)
                with self.assertRaises(AssertionError):
                    demo.snapshot()
                mutate_busy_window(demo.conn,demo.fixture['id'],'CEL',0,*BUSY_NORMAL)
                self.assertTrue(demo.snapshot()['covered'])
            finally: demo.close()

    def test_missing_return_and_restoring_changes_real_graph_decision(self):
        with tempfile.TemporaryDirectory() as d:
            demo=CareDemo(str(Path(d)/'visitfallback-demo.rl'))
            try:
                a=demo.apply('D')
                b=demo.apply('C')
                c=demo.apply('D')
                self.assertTrue(a['covered'])
                self.assertFalse(b['covered'])
                self.assertTrue(c['covered'])
                self.assertEqual({o['person']:o['state'] for o in b['needs'][2]['offers']}['Celine'],'proposed')
            finally:demo.close()

class LocalHttpContractTest(unittest.TestCase):
    def test_api_roundtrip_and_no_code_exposure(self):
        from http.server import HTTPServer
        from http.client import HTTPConnection
        from threading import Thread
        from visitfallback.webapp import Handler
        class FakeDemo:
            current='A'
            def snapshot(self): return {'phase':self.current,'covered':self.current in ('A','D')}
            def apply(self,p):
                if p not in PHASES:raise ValueError('invalid phase')
                self.current=p
                return self.snapshot()
        Handler.demo=FakeDemo()
        class QuietHandler(Handler):
            def log_message(self,*args): pass
        s=HTTPServer(('127.0.0.1',0),QuietHandler)
        t=Thread(target=s.serve_forever,daemon=True);t.start()
        try:
            c=HTTPConnection('127.0.0.1',s.server_port,timeout=2)
            c.request('GET','/api/state');r=c.getresponse()
            self.assertEqual(r.status,200)
            self.assertTrue(json.loads(r.read())['covered'])
            c.request('POST','/api/phase',body=b'{"phase":"C"}',headers={'Content-Type':'application/json'})
            r=c.getresponse()
            self.assertEqual(r.status,200)
            self.assertFalse(json.loads(r.read())['covered'])
            c.request('GET','/visitfallback/demo_service.py');r=c.getresponse()
            self.assertEqual(r.status,404);r.read()
            c.close()
        finally:
            s.shutdown();s.server_close();t.join(timeout=2)
