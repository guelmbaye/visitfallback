"""Public demo adapter: isolated synthetic Relate store for each browser session.

This is a small web-serving adapter; visitfallback.demo_service, engine,
relate_backend, oracle and the UI remain unchanged. Not a clinical product.
Run behind HTTPS nginx, on localhost only, with ONE Python process.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .demo_service import CareDemo

LOG = logging.getLogger('visitfallback.public')
WEB = Path(__file__).resolve().parent.parent / 'web'
_TOKEN = re.compile(r'^[A-Za-z0-9_-]{32,64}$')
_COOKIE = 'vf_demo'
_STATIC = {'/': 'index.html', '/index.html': 'index.html',
           '/app.js': 'app.js', '/styles.css': 'styles.css', '/favicon.ico': None}
_CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; font-src 'self'; "
        "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")


@dataclass
class Entry:
    demo: object
    path: Path
    last_seen: float


class Sessions:
    """One Relate .rl file and one CareDemo object per opaque browser cookie.

    Uses a single-thread HTTPServer: no overlapping writes inside a process.
    Keep one service worker, never multiple worker processes sharing a store.
    """
    def __init__(self, root, data, *, max_sessions=24, idle_seconds=1800,
                 factory=CareDemo, clock=time.monotonic):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.data = str(data)
        self.max_sessions = max_sessions
        self.idle_seconds = idle_seconds
        self.factory = factory
        self.clock = clock
        self.sessions: dict[str, Entry] = {}

    def _release(self, token):
        entry = self.sessions.pop(token, None)
        if entry:
            try:
                entry.demo.close()
            finally:
                try:
                    entry.path.unlink(missing_ok=True)
                except OSError:
                    LOG.exception('Could not remove expired Relate file')

    def reap(self):
        now = self.clock()
        for token, entry in list(self.sessions.items()):
            if now - entry.last_seen >= self.idle_seconds:
                self._release(token)

    def find(self, token):
        self.reap()
        if not token or not _TOKEN.fullmatch(token):
            return None
        entry = self.sessions.get(token)
        if entry:
            entry.last_seen = self.clock()
        return entry

    def new(self):
        self.reap()
        if len(self.sessions) >= self.max_sessions:
            raise RuntimeError('Public demo capacity temporarily reached')
        token = secrets.token_urlsafe(32)
        path = self.root / f'{token}.rl'
        demo = self.factory(str(path), self.data)
        entry = Entry(demo, path, self.clock())
        self.sessions[token] = entry
        return token, entry

    def close(self):
        for token in list(self.sessions):
            self._release(token)


def _cookie_token(header):
    if not header:
        return None
    try:
        cookie = SimpleCookie()
        cookie.load(header)
        item = cookie.get(_COOKIE)
        return item.value if item else None
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    sessions: Sessions | None = None
    allowed_origin: str | None = None
    secure_cookies: bool = True

    def _headers(self, status, mimetype, length, token=None):
        self.send_response(status)
        self.send_header('Content-Type', mimetype)
        self.send_header('Content-Length', str(length))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', _CSP)
        if token:
            secure = '; Secure' if self.secure_cookies else ''
            self.send_header('Set-Cookie',
                f'{_COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict{secure}')
        self.end_headers()

    def _reply(self, body, status=200, token=None):
        raw = json.dumps(body, ensure_ascii=False).encode('utf-8')
        self._headers(status, 'application/json; charset=utf-8', len(raw), token)
        self.wfile.write(raw)

    def _error(self, status, msg):
        self._reply({'error': msg}, status)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/state':
            token = _cookie_token(self.headers.get('Cookie'))
            entry = self.sessions.find(token)
            issued = None
            if not entry:
                try:
                    issued, entry = self.sessions.new()
                except RuntimeError:
                    self._error(503, 'Demo busy; retry later')
                    return
                except Exception:
                    LOG.exception('Could not create Relate session')
                    self._error(503, 'Demo temporarily unavailable')
                    return
            try:
                self._reply(entry.demo.snapshot(), token=issued)
            except Exception:
                LOG.exception('Failed Relate snapshot')
                self._error(500, 'Relate verification unavailable')
            return
        if path not in _STATIC:
            self._error(404, 'Not found')
            return
        if _STATIC[path] is None:
            self._headers(204, 'text/plain; charset=utf-8', 0)
            return
        p = WEB / _STATIC[path]
        try:
            raw = p.read_bytes()
        except OSError:
            self._error(500, 'Static asset unavailable')
            return
        kind = {'.html':'text/html', '.css':'text/css', '.js':'text/javascript'}[p.suffix]
        self._headers(200, f'{kind}; charset=utf-8', len(raw))
        self.wfile.write(raw)

    def do_POST(self):
        if urlsplit(self.path).path != '/api/phase':
            self._error(404, 'Not found')
            return
        origin = self.headers.get('Origin')
        if origin and origin != self.allowed_origin:
            self._error(403, 'Origin denied')
            return
        if self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':
            self._error(415, 'application/json required')
            return
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self._error(400, 'Invalid Content-Length')
            return
        if not 2 <= size <= 500:
            self._error(413, 'Invalid request size')
            return
        token = _cookie_token(self.headers.get('Cookie'))
        entry = self.sessions.find(token)
        if not entry:
            self._error(409, 'Demo session expired; refresh page')
            return
        try:
            payload = json.loads(self.rfile.read(size).decode('utf-8'))
            if not isinstance(payload, dict) or set(payload) != {'phase'}:
                raise ValueError('Only phase accepted')
            if not isinstance(payload['phase'], str) or len(payload['phase']) != 1 or payload['phase'] not in 'ABCDE':
                raise ValueError('Invalid phase')
            self._reply(entry.demo.apply(payload['phase']))
        except (ValueError, UnicodeDecodeError):
            self._error(400, 'Invalid phase request')
        except Exception:
            LOG.exception('Failed Relate mutation')
            self._error(500, 'Relate verification unavailable')


def main():
    parser = argparse.ArgumentParser(description='VisitFallback synthetic public demo (localhost reverse proxy only)')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--store-dir', default='/run/visitfallback/stores')
    parser.add_argument('--data', default='data/scenarios.json')
    parser.add_argument('--max-sessions', type=int, default=24)
    parser.add_argument('--idle-minutes', type=int, default=30)
    parser.add_argument('--origin', default='https://visitfallback.e-ntsi.com')
    parser.add_argument('--dev-http', action='store_true', help='LOCAL testing only: allow non-Secure session cookies over HTTP')
    args = parser.parse_args()
    if args.host != '127.0.0.1':
        parser.error('Public mode may only bind to 127.0.0.1 behind a reverse proxy')
    if args.max_sessions < 1 or args.max_sessions > 100:
        parser.error('max-sessions must be between 1 and 100')
    if args.idle_minutes < 1 or args.idle_minutes > 120:
        parser.error('idle-minutes must be between 1 and 120')
    if args.dev_http and args.origin != f'http://127.0.0.1:{args.port}':
        parser.error('--dev-http requires --origin http://127.0.0.1:<port>')
    logging.basicConfig(level=logging.INFO)
    sessions = Sessions(args.store_dir, args.data,
        max_sessions=args.max_sessions, idle_seconds=args.idle_minutes * 60)
    # Force a genuine Relate initialization and oracle preflight at startup.
    # Do not reuse this graph: the real visitor gets a fresh isolated store.
    try:
        token, check = sessions.new()
        check.demo.snapshot()
        sessions._release(token)
    except Exception:
        sessions.close()
        raise
    class PublicHandler(Handler):
        pass
    PublicHandler.sessions = sessions
    PublicHandler.allowed_origin = args.origin
    PublicHandler.secure_cookies = not args.dev_http
    try:
        with HTTPServer((args.host, args.port), PublicHandler) as srv:
            print('Relate preflight PASS; isolated synthetic browser sessions enabled', flush=True)
            print(f'Listening on http://{args.host}:{args.port} — HTTPS reverse proxy required', flush=True)
            srv.serve_forever()
    finally:
        sessions.close()

if __name__ == '__main__':
    main()
