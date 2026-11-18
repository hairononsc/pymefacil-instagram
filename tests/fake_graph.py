"""Servidor falso de la Graph API para probar el publicador sin tocar Instagram.
Sirve también /media/* como si fuera el hosting público, y descarga cada image_url como haría Meta."""
import json, sys, threading, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer as HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG, POLLS, COUNT = [], {}, [0]
FAIL_PUBLISH_ONCE = {"on": False}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b)))
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path.startswith("/media/"):
            f = ROOT / urllib.parse.unquote(u.path[1:])
            if not f.exists(): return self._send(404, {})
            d = f.read_bytes(); self.send_response(200); self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); return self.wfile.write(d)
        if self.headers.get("Authorization") != "Bearer TOKEN_PRUEBA":
            return self._send(401, {"error": {"code": 190, "message": "token inválido"}})
        parts = u.path.strip("/").split("/")  # v25.0/<id>
        oid = parts[1]; LOG.append(("GET", oid, q))
        if "status_code" in q.get("fields", [""])[0]:
            POLLS[oid] = POLLS.get(oid, 0) + 1
            return self._send(200, {"status_code": "IN_PROGRESS" if POLLS[oid] < 2 else "FINISHED"})
        if "permalink" in q.get("fields", [""])[0]:
            return self._send(200, {"permalink": f"https://www.instagram.com/p/{oid}/"})
        return self._send(200, {"username": "pymefacil.test", "name": "PymeFácil", "id": oid})
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); body = urllib.parse.parse_qs(self.rfile.read(n).decode())
        body = {k: v[0] for k, v in body.items()}
        if self.headers.get("Authorization") != "Bearer TOKEN_PRUEBA":
            return self._send(401, {"error": {"code": 190, "message": "token inválido"}})
        parts = self.path.strip("/").split("/"); ig, ep = parts[1], parts[2]
        LOG.append(("POST", ep, body))
        if ep == "media":
            if "image_url" in body:  # Meta descarga la imagen: debe ser pública y JPEG
                try:
                    r = urllib.request.urlopen(body["image_url"]); assert r.headers["Content-Type"] == "image/jpeg"
                except Exception as e:
                    return self._send(400, {"error": {"code": 9004, "message": f"no se pudo descargar {body['image_url']}: {e}"}})
            COUNT[0] += 1; return self._send(200, {"id": f"C{COUNT[0]}"})
        if ep == "media_publish":
            if FAIL_PUBLISH_ONCE["on"]:
                FAIL_PUBLISH_ONCE["on"] = False
                return self._send(500, {"error": {"code": 2, "message": "fallo transitorio simulado"}})
            return self._send(200, {"id": "M_" + body["creation_id"]})
        self._send(404, {})

def start(port=0):
    s = HTTPServer(("127.0.0.1", port), H); threading.Thread(target=s.serve_forever, daemon=True).start(); return s
