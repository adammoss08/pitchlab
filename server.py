#!/usr/bin/env python3.15
"""Static PitchLab app and on-demand MIDI instrument samples."""

from __future__ import annotations

import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from audio import SoundFontRenderer


ROOT = Path(__file__).resolve().parent
AUDIO_PATH = re.compile(r'^/audio/(0|4|24|48|73|80)/(\d{1,3})\.wav$')


class Handler(BaseHTTPRequestHandler):
    renderer: SoundFontRenderer

    def send_bytes(self, body: bytes, content_type: str, cache: str = 'no-store'):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', cache)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; media-src 'self'; connect-src 'self'; img-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/healthz':
            self.send_bytes(b'ok\n', 'text/plain; charset=utf-8')
        elif path == '/':
            self.send_bytes((ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif path == '/app.js':
            self.send_bytes((ROOT / 'app.js').read_bytes(), 'text/javascript; charset=utf-8')
        elif match := AUDIO_PATH.fullmatch(path):
            try:
                body = self.renderer.render(int(match[1]), int(match[2]))
            except ValueError:
                self.send_error(404)
                return
            self.send_bytes(body, 'audio/wav', 'public, max-age=86400, immutable')
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        print('%s - %s' % (self.address_string(), format % args), flush=True)


def main():
    import sys
    if sys.version_info < (3, 15):
        raise SystemExit('PitchLab requires Python 3.15 or newer')
    Handler.renderer = SoundFontRenderer()
    port = int(os.environ.get('PORT', '8080'))
    server = ThreadingHTTPServer(('0.0.0.0', port), Handler)
    print(f'PitchLab listening on port {port}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
