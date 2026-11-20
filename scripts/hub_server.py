"""Read-only portfolio hub, serving only curated public assets."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from os.path import relpath
from urllib.parse import unquote, urlsplit
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import local_services as services
from urllib.request import urlopen
ROOT = Path(__file__).resolve().parents[1]

class Hub(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):
        pass

    def guess_type(self, path):
        if str(path).endswith('.md'):
            return 'text/plain; charset=utf-8'
        return super().guess_type(path)

    def do_GET(self):
        port = self.server.server_address[1]
        if self.headers.get('Host') not in [f'127.0.0.1:{port}', f'localhost:{port}']:
            return self.send_error(403)
        # Always send current bytes, even when an old tab supplies conditional headers.
        for header in ['If-Modified-Since', 'If-None-Match']:
            if header in self.headers: del self.headers[header]
        path = unquote(urlsplit(self.path).path)
        if path in ('/api/instance','/api/status','/api/services'):
            if path=='/api/instance':
                record={'portfolio':services.INSTANCE}
            else:
                record={key:services.active_port(key) for key in services.INDEX}
                if path=='/api/status':record={key:bool(port) for key,port in record.items()}
            body=json.dumps(record).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            if self.command != 'HEAD': self.wfile.write(body)
            return
        target = (ROOT / path.lstrip('/')).resolve()
        try:
            relative = target.relative_to(ROOT)
        except ValueError:
            return self.send_error(404)
        special = path == '/' or relative.as_posix() in ['index.html', 'local.html', 'README.md','vrfitai/README.md','hsi-sr-lab/README.md','manufacturing-platform/README.md','firewatch/README.md','signal-lab/README.md']
        curated = (bool(relative.parts) and relative.parts[0] in ['projects', 'assets', 'preview', 'docs']
                   and target.suffix.lower() in ['.html', '.css', '.js', '.svg', '.png', '.jpg', '.webp', '.md', '.json', '.docx', '.pdf', '.txt', '.csv', '.mp4'])
        research = (len(relative.parts) > 2 and relative.parts[:2] == ('hsi-sr-lab', 'thesis-final')
                    and target.suffix.lower() in ['.py', '.m', '.json', '.png', '.md', '.pdf', '.csv'])
        archive_file = relative.as_posix() in {
            'signal-lab/original/Virtual_Oscilloscope.vi',
            'hsi-sr-lab/thesis-final/source/LICENSE',
        }
        cases = (len(relative.parts)>2 and relative.parts[:2]==('case-studies','medical')
                 and target.suffix.lower() in ['.html','.js','.css','.svg','.png','.jpg','.jpeg','.md','.json','.zip','.txt'])
        thesis_tables = (len(relative.parts) == 3 and relative.parts[:2] == ('hsi-sr-lab','evidence')
                         and target.suffix.lower() == '.csv')
        if not (special or curated or research or cases or archive_file or thesis_tables) or (target.is_dir() and path != '/'):
            return self.send_error(404)
        if path == '/' or target.suffix == '.html':
            file = ROOT / 'index.html' if path == '/' else target
            if not file.is_file():
                return self.send_error(404)
            asset = relpath(ROOT / 'assets/local-apps.js', file.parent)
            body = file.read_bytes().replace(b'<html ', b'<html data-local-hub ', 1)
            source = f'<script defer src="{asset}"></script>'.encode()
            body = body.replace(b'</head>', source + b'</head>', 1)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
            return
        if self.command == 'HEAD':
            response = super().send_head()
            if response: response.close()
        else:
            super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            file=ROOT/'projects/404.html'
            if file.is_file():
                body=file.read_bytes();self.send_response(404);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers()
                if self.command!='HEAD':self.wfile.write(body)
                return
        super().send_error(code,message,explain)

    def do_HEAD(self):
        self.do_GET()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, max-age=0')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

if __name__ == '__main__':
    port=int(sys.argv[1]) if len(sys.argv)>1 else 8790
    server = ThreadingHTTPServer(('127.0.0.1', port), Hub)
    print(f'Portfolio http://127.0.0.1:{port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
