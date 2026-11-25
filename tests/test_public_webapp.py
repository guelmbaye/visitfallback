"""Regression tests for the optional public-facing, browser-isolated adapter."""
import http.client
import importlib.util
import json
import tempfile
import unittest
from http.server import HTTPServer
from pathlib import Path
from threading import Thread
from visitfallback.public_webapp import Handler, Sessions

class FakeDemo:
    def __init__(self, path, data):
        self.path = Path(path)
        self.path.write_text('fake store', encoding='utf-8')
        self.phase = 'A'
        self.closed = False
    def snapshot(self):
        return {'phase':self.phase,'data_kind':'SYNTHETIC_ONLY', 'covered': self.phase in 'AD'}
    def apply(self, phase):
        self.phase = phase
        return self.snapshot()
    def close(self):
        self.closed = True

class TestSessions(unittest.TestCase):
    def test_independent_stores_and_expiry(self):
        with tempfile.TemporaryDirectory() as d:
            now = [10.0]
            s = Sessions(d,'unused',max_sessions=2,idle_seconds=20,factory=FakeDemo,clock=lambda:now[0])
            try:
                ta,a=s.new(); tb,b=s.new()
                self.assertNotEqual(ta,tb)
                self.assertNotEqual(a.path,b.path)
                a.demo.apply('E')
                self.assertEqual(b.demo.snapshot()['phase'],'A')
                with self.assertRaises(RuntimeError): s.new()
                now[0]=31.0
                self.assertIsNone(s.find(ta))
                self.assertFalse(a.path.exists())
                self.assertFalse(b.path.exists())
                s.new()
            finally:
                s.close()

    def test_invalid_cookie_cannot_access_session(self):
        with tempfile.TemporaryDirectory() as d:
            s=Sessions(d,'unused',factory=FakeDemo)
            try:
                t,e=s.new()
                self.assertIsNone(s.find('../unsafe'))
                self.assertIsNone(s.find('invalid_token'))
                self.assertIs(s.find(t),e)
            finally:s.close()

class TestHttp(unittest.TestCase):
    def test_two_browser_sessions_do_not_interfere(self):
        with tempfile.TemporaryDirectory() as d:
            s=Sessions(d,'unused',factory=FakeDemo)
            class H(Handler):
                sessions=s
                allowed_origin='https://visitfallback.e-ntsi.com'
                def log_message(self,*args):pass
            srv=HTTPServer(('127.0.0.1',0),H)
            th=Thread(target=srv.serve_forever,daemon=True)
            th.start()
            try:
                def req(path,method='GET',body=None,cookie=None,origin=None):
                    c=http.client.HTTPConnection('127.0.0.1',srv.server_port,timeout=5)
                    hdr={}
                    if cookie:hdr['Cookie']=cookie
                    if origin:hdr['Origin']=origin
                    if body is not None:hdr['Content-Type']='application/json'
                    c.request(method,path,body=body,headers=hdr)
                    r=c.getresponse();data=json.loads(r.read().decode())
                    x=(r.status,r.getheader('Set-Cookie'),data)
                    c.close();return x
                _,ca,a=req('/api/state');_,cb,b=req('/api/state')
                ca=ca.split(';',1)[0];cb=cb.split(';',1)[0]
                self.assertNotEqual(ca,cb)
                self.assertEqual(a['phase'],'A');self.assertEqual(b['phase'],'A')
                status,_,changed=req('/api/phase','POST',b'{"phase":"E"}',ca,
                         origin='https://visitfallback.e-ntsi.com')
                self.assertEqual(status,200)
                self.assertEqual(changed['phase'],'E')
                self.assertEqual(req('/api/state',cookie=cb)[2]['phase'],'A')
                self.assertEqual(req('/api/state',cookie=ca)[2]['phase'],'E')
                self.assertEqual(req('/visitfallback/engine.py')[0],404)
                self.assertEqual(req('/data/scenarios.json')[0],404)
                self.assertEqual(req('/data/demo.rl')[0],404)
                self.assertEqual(req('/.git/config')[0],404)
                self.assertEqual(req('/api/phase','POST',b'{"phase":"D"}',cb,
                             origin='https://attacker.example')[0],403)
                self.assertEqual(req('/api/phase','POST',b'{"phase":"D"}')[0],409)
            finally:
                srv.shutdown();srv.server_close();th.join(timeout=4);s.close()

if __name__=='__main__':unittest.main()

@unittest.skipUnless(importlib.util.find_spec('relate') is not None, 'Relate required for real isolated stores')
class TestRealRelateSessions(unittest.TestCase):
    def test_real_graphs_independent(self):
        from visitfallback.demo_service import CareDemo
        with tempfile.TemporaryDirectory() as d:
            s = Sessions(d, 'data/scenarios.json', factory=CareDemo)
            try:
                _,a=s.new(); _,b=s.new()
                self.assertTrue(a.demo.snapshot()['covered'])
                self.assertFalse(a.demo.apply('E')['covered'])
                self.assertTrue(b.demo.snapshot()['covered'])
                self.assertEqual(b.demo.snapshot()['phase'], 'A')
                self.assertTrue(a.demo.apply('D')['covered'])
            finally:s.close()
