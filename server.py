#!/usr/bin/env python3
"""HTTP server with range request support (needed for video seeking in browsers)."""
import http.server, os, re, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000

class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404)
            return None

        size = os.fstat(f.fileno()).st_size
        ctype = self.guess_type(path)
        rng = self.headers.get('Range')

        if rng:
            m = re.match(r'bytes=(\d+)-(\d*)', rng)
            if not m:
                self.send_error(400, 'Bad Range')
                f.close()
                return None
            start = int(m.group(1))
            end   = int(m.group(2)) if m.group(2) else size - 1
            end   = min(end, size - 1)
            length = end - start + 1
            self.send_response(206)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
            self.send_header('Content-Length', str(length))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(65536, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)
            f.close()
            return None
        else:
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(size))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            return f

    def log_message(self, fmt, *args):
        pass  # silent

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    httpd = http.server.HTTPServer(('', PORT), RangeHandler)
    print(f'Serving on http://localhost:{PORT}')
    httpd.serve_forever()
