#!/usr/bin/env python3
"""Publicador de Instagram para PymeFácil (Instagram Graph API, cuentas Profesionales).

Lee calendar.json, sube las publicaciones 'approved' cuya hora ya llegó y anota lo publicado en state.json.
Pensado para correr cada hora (GitHub Actions, cron o una tarea programada).

Variables de entorno:
  IG_USER_ID        ID de la cuenta de Instagram Profesional (no es el @usuario)
  IG_ACCESS_TOKEN   Token con permisos instagram_basic e instagram_content_publish
  MEDIA_BASE_URL    URL pública donde viven las imágenes (la API las descarga desde ahí), p. ej. https://cdn.ejemplo.com
  GRAPH_VERSION     Opcional. Por defecto v25.0
  GRAPH_BASE_URL    Opcional. Por defecto https://graph.facebook.com (solo se cambia en pruebas)

Uso:
  python3 publisher/publish.py --verify            # comprueba el token y la cuenta
  python3 publisher/publish.py --dry-run           # valida y muestra qué se publicaría
  python3 publisher/publish.py                     # publica lo que toque (máx. 1 por corrida)
  python3 publisher/publish.py --post ID --force   # publica una pieza concreta ahora (debe estar 'approved')
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parent.parent
CALENDAR = Path(os.environ.get("CALENDAR_FILE", ROOT / "calendar.json"))
STATE = Path(os.environ.get("STATE_FILE", ROOT / "state.json"))

CAPTION_MAX = 2200      # límite de Instagram
HASHTAGS_MAX = 30       # límite de Instagram
IMAGE_MAX_BYTES = 8 * 1024 * 1024
CAROUSEL_MIN, CAROUSEL_MAX = 2, 10
CONTAINER_TTL = timedelta(hours=20)  # los contenedores de Meta expiran a las 24 h
TRANSIENT_CODES = {1, 2, 4, 17, 32, 341, 613}  # errores de Meta que valen la pena reintentar


class PublishError(RuntimeError):
    pass


# ----------------------------------------------------------------------------- config / archivos
def env(name: str, default: str | None = None, required: bool = False) -> str:
    v = os.environ.get(name, default)
    if required and not v:
        raise PublishError(f"Falta la variable de entorno {name}")
    return v or ""


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def media_url(rel: str) -> str:
    base = env("MEDIA_BASE_URL", required=True).rstrip("/")
    return f"{base}/{quote(rel.lstrip('/'))}"


# ----------------------------------------------------------------------------- validación
def validate(post: dict) -> list[str]:
    errs: list[str] = []
    pid = post.get("id", "?")
    kind = post.get("type")
    media = post.get("media") or []
    caption = post.get("caption", "")
    if kind not in ("image", "carousel"):
        errs.append(f"{pid}: type debe ser 'image' o 'carousel'")
    if kind == "image" and len(media) != 1:
        errs.append(f"{pid}: una imagen necesita exactamente 1 archivo en media")
    if kind == "carousel" and not (CAROUSEL_MIN <= len(media) <= CAROUSEL_MAX):
        errs.append(f"{pid}: un carrusel necesita entre {CAROUSEL_MIN} y {CAROUSEL_MAX} imágenes")
    if len(caption) > CAPTION_MAX:
        errs.append(f"{pid}: el texto tiene {len(caption)} caracteres (máx. {CAPTION_MAX})")
    if caption.count("#") > HASHTAGS_MAX:
        errs.append(f"{pid}: más de {HASHTAGS_MAX} hashtags")
    try:
        datetime.fromisoformat(post["publish_at"])
        if datetime.fromisoformat(post["publish_at"]).tzinfo is None:
            errs.append(f"{pid}: publish_at necesita zona horaria (p. ej. -04:00)")
    except (KeyError, ValueError):
        errs.append(f"{pid}: publish_at inválido (usa 2026-11-19T12:00:00-04:00)")
    alt = post.get("alt_text")
    if isinstance(alt, list) and kind == "carousel" and len(alt) != len(media):
        errs.append(f"{pid}: alt_text debe tener una entrada por imagen")
    for rel in media:
        f = ROOT / rel
        if not f.exists():
            errs.append(f"{pid}: no existe {rel}")
            continue
        if f.stat().st_size > IMAGE_MAX_BYTES:
            errs.append(f"{pid}: {rel} pesa más de 8 MB")
        if f.suffix.lower() not in (".jpg", ".jpeg"):
            errs.append(f"{pid}: {rel} debe ser JPEG (la API de Instagram no acepta otros formatos)")
        else:
            with f.open("rb") as fh:
                if fh.read(3) != b"\xff\xd8\xff":
                    errs.append(f"{pid}: {rel} no es un JPEG válido")
    return errs


def due_posts(posts: list[dict], state: dict, now: datetime, late_hours: float) -> list[dict]:
    out = []
    for p in posts:
        if p.get("status") != "approved" or p["id"] in state["published"]:
            continue
        when = datetime.fromisoformat(p["publish_at"])
        if when > now:
            continue
        if now - when > timedelta(hours=late_hours):
            print(f"[omitida] {p['id']}: pasó hace más de {late_hours:g} h. Cambia publish_at o usa --post {p['id']} --force")
            continue
        out.append(p)
    return sorted(out, key=lambda p: p["publish_at"])


# ----------------------------------------------------------------------------- API de Meta
class Graph:
    def __init__(self, user_id: str, token: str, version: str, base: str):
        self.user_id = user_id
        self.base = f"{base.rstrip('/')}/{version}"
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"  # fuera de la URL para que no salga en logs

    def call(self, method: str, path: str, retries: int = 3, **params):
        url = f"{self.base}/{path.lstrip('/')}"
        for attempt in range(1, retries + 1):
            try:
                r = self.s.request(method, url, data=params if method == "POST" else None,
                                   params=params if method == "GET" else None, timeout=60)
            except requests.RequestException as e:
                if attempt == retries:
                    raise PublishError(f"Sin conexión con Meta: {e}") from e
                time.sleep(2 ** attempt)
                continue
            try:
                body = r.json()
            except ValueError:
                body = {}
            err = body.get("error")
            if r.ok and not err:
                return body
            code = (err or {}).get("code")
            msg = (err or {}).get("message", r.text[:200])
            if (r.status_code >= 500 or code in TRANSIENT_CODES) and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            hint = ""
            if code == 190:
                hint = " (el token venció o fue revocado: genera uno nuevo)"
            elif code in (10, 200):
                hint = " (falta un permiso: revisa instagram_content_publish y que la cuenta sea Profesional)"
            elif code == 9007:
                hint = " (Meta aún procesa la imagen: reintenta en unos minutos)"
            raise PublishError(f"Meta respondió {r.status_code} / código {code}: {msg}{hint}")
        raise PublishError("Reintentos agotados")

    def account(self) -> dict:
        return self.call("GET", self.user_id, fields="username,name")

    def container(self, **params) -> str:
        return self.call("POST", f"{self.user_id}/media", **params)["id"]

    def wait_finished(self, cid: str, timeout: int = 180) -> None:
        t0 = time.time()
        while True:
            st = self.call("GET", cid, fields="status_code,status")
            code = st.get("status_code")
            if code == "FINISHED":
                return
            if code in ("ERROR", "EXPIRED"):
                raise PublishError(f"El contenedor {cid} quedó en {code}: {st.get('status', '')}")
            if time.time() - t0 > timeout:
                raise PublishError(f"El contenedor {cid} no terminó en {timeout}s (estado {code})")
            time.sleep(3)

    def publish(self, cid: str) -> str:
        return self.call("POST", f"{self.user_id}/media_publish", retries=1, creation_id=cid)["id"]

    def permalink(self, media_id: str) -> str:
        try:
            return self.call("GET", media_id, fields="permalink").get("permalink", "")
        except PublishError:
            return ""


def build_container(g: Graph, post: dict) -> str:
    alt = post.get("alt_text")
    if post["type"] == "image":
        params = {"image_url": media_url(post["media"][0]), "caption": post["caption"]}
        if isinstance(alt, str) and alt:
            params["alt_text"] = alt
        cid = g.container(**params)
    else:
        kids = []
        for i, rel in enumerate(post["media"]):
            params = {"image_url": media_url(rel), "is_carousel_item": "true"}
            if isinstance(alt, list) and alt[i]:
                params["alt_text"] = alt[i]
            kid = g.container(**params)
            g.wait_finished(kid)
            kids.append(kid)
        cid = g.container(media_type="CAROUSEL", children=",".join(kids), caption=post["caption"])
    g.wait_finished(cid)
    return cid


def publish_post(g: Graph, post: dict, state: dict) -> None:
    pid = post["id"]
    now = datetime.now(timezone.utc)
    pending = state["pending"].get(pid)
    cid = None
    if pending and now - datetime.fromisoformat(pending["created"]) < CONTAINER_TTL:
        cid = pending["creation_id"]
        print(f"[{pid}] reutilizo el contenedor {cid} de un intento anterior")
    if not cid:
        cid = build_container(g, post)
        state["pending"][pid] = {"creation_id": cid, "created": now.isoformat()}
        save_json(STATE, state)  # si algo falla al publicar, el próximo intento no vuelve a subir las imágenes
    media_id = g.publish(cid)
    state["published"][pid] = {"media_id": media_id, "permalink": g.permalink(media_id), "at": now.isoformat()}
    state["pending"].pop(pid, None)
    save_json(STATE, state)
    print(f"[{pid}] publicado -> {state['published'][pid]['permalink'] or media_id}")


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="valida y muestra, sin llamar a Meta")
    ap.add_argument("--verify", action="store_true", help="comprueba token y cuenta")
    ap.add_argument("--post", help="id de una publicación concreta")
    ap.add_argument("--force", action="store_true", help="con --post: publica aunque no sea su hora")
    ap.add_argument("--max", type=int, default=1, help="máximo de publicaciones por corrida (por defecto 1)")
    ap.add_argument("--late-hours", type=float, default=48, help="no publica piezas con más retraso que esto")
    a = ap.parse_args()

    cal = load_json(CALENDAR, {"posts": []})
    state = load_json(STATE, {})
    state.setdefault("published", {})
    state.setdefault("pending", {})
    posts = cal["posts"]

    ids = [p["id"] for p in posts]
    if len(ids) != len(set(ids)):
        print("Hay ids repetidos en calendar.json", file=sys.stderr)
        return 1

    problems = [e for p in posts if p.get("status") == "approved" or a.post == p["id"] for e in validate(p)]
    if problems:
        print("Problemas en calendar.json:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc)
    if a.post:
        match = [p for p in posts if p["id"] == a.post]
        if not match:
            print(f"No existe la publicación {a.post}", file=sys.stderr)
            return 1
        if match[0].get("status") != "approved":
            print(f"{a.post} no está 'approved'", file=sys.stderr)
            return 1
        if a.post in state["published"]:
            print(f"{a.post} ya se publicó")
            return 0
        queue = match if a.force else [p for p in due_posts(match, state, now, a.late_hours)]
    else:
        queue = due_posts(posts, state, now, a.late_hours)
    queue = queue[: a.max]

    if a.dry_run:
        for p in posts:
            errs = validate(p)
            flag = "OK " if not errs else "ERR"
            est = "publicada" if p["id"] in state["published"] else p.get("status")
            print(f"{flag} {p['id']:32} {p['type']:8} {p['publish_at']}  [{est}]")
            for e in errs:
                print("      " + e)
        print(f"\nSe publicaría ahora: {[p['id'] for p in queue] or 'nada'}")
        return 0

    g = Graph(env("IG_USER_ID", required=True), env("IG_ACCESS_TOKEN", required=True),
              env("GRAPH_VERSION", "v25.0"), env("GRAPH_BASE_URL", "https://graph.facebook.com"))
    if a.verify:
        acc = g.account()
        print(f"Conectado como @{acc.get('username')} ({acc.get('name', '')}) id={g.user_id}")
        return 0
    if not queue:
        print("Nada que publicar por ahora.")
        return 0

    failed = False
    for p in queue:
        try:
            publish_post(g, p, state)
        except PublishError as e:
            failed = True
            print(f"[{p['id']}] ERROR: {e}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
