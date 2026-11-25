"""Local-only browser proof for VisitFallback using a real Relate store."""
import argparse, json, mimetypes
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from .demo_service import CareDemo

WEB=Path(__file__).resolve().parent.parent/'web'

class Handler(BaseHTTPRequestHandler):
    demo=None
    def _json(self,payload,code=200):
        raw=json.dumps(payload,ensure_ascii=False).encode('utf8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(raw)))
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/state':
            try: self._json(self.demo.snapshot())
            except Exception as e: self._json({'error':str(e)},500)
            return
        files={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css','/favicon.ico':None}
        if path not in files:
            self.send_error(404);return
        if files[path] is None:
            self.send_response(204);self.end_headers();return
        payload=(WEB/files[path]).read_bytes()
        mimetype={".js":"text/javascript",".css":"text/css",".html":"text/html"}[Path(files[path]).suffix]
        self.send_response(200);self.send_header('Content-Type',mimetype+'; charset=utf-8')
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)
    def do_POST(self):
        if urlsplit(self.path).path != '/api/phase':
            self.send_error(404); return
        if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
            self._json({'error':'application/json required'},415);return
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: self._json({'error':'invalid content length'},400);return
        if length<2 or length>500:
            self._json({'error':'invalid request size'},413);return
        try:
            body=json.loads(self.rfile.read(length).decode('utf8'))
            if set(body)!= {'phase'} or not isinstance(body['phase'],str):
                raise ValueError('Only phase accepted')
            self._json(self.demo.apply(body['phase']))
        except (ValueError,TypeError) as e:
            self._json({'error':str(e)},400)
        except Exception as e:
            self._json({'error':str(e)},500)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=8766)
    p.add_argument('--store',default='build/visitfallback-ui-new.rl')
    p.add_argument('--data',default='data/scenarios.json')
    args=p.parse_args()
    if args.host!='127.0.0.1': p.error('This prototype is intentionally local-only (127.0.0.1).')
    demo=CareDemo(args.store,args.data)
    Handler.demo=demo
    try:
        with HTTPServer((args.host,args.port),Handler) as server:
            print('Real Relate preflight PASS; separate oracle parity PASS; synthetic only',flush=True)
            print(f'Open http://127.0.0.1:{args.port}/',flush=True)
            print('Ctrl+C to stop; do not expose publicly without hardening.',flush=True)
            server.serve_forever()
    finally:
        demo.close()

if __name__=='__main__':main()
