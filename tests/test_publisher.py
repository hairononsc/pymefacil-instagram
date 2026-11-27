"""Prueba de punta a punta del publicador contra el servidor falso:  python3 tests/test_publisher.py"""
import json, os, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import fake_graph

ROOT = Path(__file__).resolve().parent.parent
srv = fake_graph.start(); port = srv.server_address[1]
tmp = Path(tempfile.mkdtemp())
cal = json.loads((ROOT / "calendar.json").read_text(encoding="utf-8"))
cal["posts"] = cal["posts"][:3]  # la prueba usa las 3 piezas originales; las nuevas no cambian el escenario
for p in cal["posts"]:
    p["status"] = "approved"; p["publish_at"] = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()  # vencidas hace 1 h
cal["posts"][0]["publish_at"] = "2099-01-01T12:00:00-04:00"                 # futura: no debe salir
cal["posts"][1]["publish_at"] = "2020-01-01T12:00:00-04:00"                 # muy atrasada: se omite
(tmp / "cal.json").write_text(json.dumps(cal))
env = dict(os.environ, IG_USER_ID="17841400000000000", IG_ACCESS_TOKEN="TOKEN_PRUEBA",
           MEDIA_BASE_URL=f"http://127.0.0.1:{port}", GRAPH_BASE_URL=f"http://127.0.0.1:{port}",
           CALENDAR_FILE=str(tmp / "cal.json"), STATE_FILE=str(tmp / "state.json"))
run = lambda *a: subprocess.run([sys.executable, str(ROOT / "publisher/publish.py"), *a], env=env, capture_output=True, text=True)
def check(cond, msg):
    print(("OK   " if cond else "FALLA"), msg)
    if not cond: sys.exit(1)

r = run("--verify"); check("@pymefacil.test" in r.stdout, "verify conecta con la cuenta")
r = run("--dry-run"); check(r.returncode == 0 and "2026-11-24-stock-bajo" in r.stdout, "dry-run valida las 3 piezas")
r = run(); st = json.loads((tmp / "state.json").read_text())
check(list(st["published"]) == ["2026-11-24-stock-bajo"], "publica solo la vencida a tiempo (no la futura ni la atrasada)")
check(sum(1 for m, e, _ in fake_graph.LOG if m == "POST" and e == "media") == 1, "imagen simple = 1 contenedor")
fake_graph.LOG.clear()
r = run("--post", "2026-11-19-nuevo-inicio", "--force")
posts = [x for x in fake_graph.LOG if x[0] == "POST"]
check(sum(1 for _, e, _ in posts if e == "media") == 7, "carrusel = 6 hijos + 1 padre")
parent = [b for _, e, b in posts if e == "media" and b.get("media_type") == "CAROUSEL"][0]
check(len(parent["children"].split(",")) == 6 and "Estrenamos Inicio nuevo" in parent["caption"], "el padre trae 6 hijos y el texto")
check(any("alt_text" in b for _, e, b in posts if e == "media"), "envía alt_text")
r = run(); check("Nada que publicar" in r.stdout, "segunda corrida no duplica")
# fallo transitorio al publicar: el segundo intento reutiliza el contenedor
cal["posts"][1]["publish_at"] = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(); (tmp / "cal.json").write_text(json.dumps(cal))
st = json.loads((tmp / "state.json").read_text()); st["published"].pop("2026-11-21-facturas-vencidas", None)
(tmp / "state.json").write_text(json.dumps(st))
fake_graph.FAIL_PUBLISH_ONCE["on"] = True; fake_graph.LOG.clear()
r = run("--post", "2026-11-21-facturas-vencidas", "--force")
check(r.returncode == 1 and "pending" in (tmp / "state.json").read_text() and json.loads((tmp / "state.json").read_text())["pending"], "si publicar falla, guarda el contenedor pendiente")
n_before = sum(1 for m, e, _ in fake_graph.LOG if m == "POST" and e == "media")
r = run("--post", "2026-11-21-facturas-vencidas", "--force")
n_after = sum(1 for m, e, _ in fake_graph.LOG if m == "POST" and e == "media")
check(r.returncode == 0 and n_after == n_before, "reintento reutiliza el contenedor (no vuelve a subir la imagen)")
env["IG_ACCESS_TOKEN"] = "MAL"; r = run("--verify"); check("token venció" in r.stderr or r.returncode != 0, "token malo da error claro")
print("\nTodo bien.")
