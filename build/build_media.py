#!/usr/bin/env python3
"""Genera las imágenes de Instagram de PymeFácil (JPEG, 1080x1350 y portadas de destacados 1080x1920).

Usa los tokens de la marca (azul #2563EB, verde #15803d, Inter) y renderiza HTML con Chrome headless.
Uso:  python3 build/build_media.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "media"
OUT.mkdir(exist_ok=True)

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:%(w)dpx;height:%(h)dpx;font-family:'Inter',sans-serif;color:#0f172a;
 background:linear-gradient(165deg,#f8fafc 0%%,#e8f0fe 55%%,#dbeafe 100%%);position:relative;overflow:hidden}
.top{position:absolute;top:64px;left:72px;right:72px;display:flex;justify-content:space-between;align-items:center}
.brand{font-size:44px;font-weight:800;color:#0f1f4d;letter-spacing:-1px}
.count{font-size:28px;color:#475569;font-weight:600}
.main{position:absolute;top:190px;left:72px;right:72px}
.eyebrow{display:inline-block;background:#dbeafe;color:#1e40af;font-weight:700;font-size:26px;letter-spacing:2px;
 padding:12px 26px;border-radius:999px;margin-bottom:36px}
h1{font-size:96px;line-height:1.02;font-weight:800;letter-spacing:-3.5px;color:#0f172a}
h1 em{font-style:normal;color:#2563eb}
.sub{font-size:40px;line-height:1.35;color:#475569;font-weight:500;margin-top:32px}
.card{background:#fff;border:2px solid #e2e8f0;border-radius:36px;box-shadow:0 14px 40px rgba(37,99,235,.10);padding:48px}
.label{font-size:30px;color:#475569;font-weight:600}
.amount{font-size:104px;font-weight:800;letter-spacing:-3px;color:#0f172a;margin-top:6px;font-variant-numeric:tabular-nums}
.chip-up{display:inline-flex;align-items:center;gap:10px;background:#dcfce7;color:#166534;font-weight:700;font-size:28px;
 padding:12px 24px;border-radius:999px}
.bars{display:flex;align-items:flex-end;gap:14px;height:170px;margin-top:36px}
.bars i{flex:1;background:#bbf7d0;border-radius:8px}
.bars i.hi{background:#15803d}
.stats{display:flex;gap:24px;margin-top:36px}
.stat{flex:1;background:#f1f5f9;border-radius:24px;padding:28px 32px}
.stat b{display:block;font-size:44px;font-weight:800;margin-top:6px;font-variant-numeric:tabular-nums}
.row{display:flex;align-items:center;gap:28px;padding:30px 0;border-top:2px solid #e2e8f0}
.row:first-of-type{border-top:0}
.ico{width:88px;height:88px;border-radius:24px;display:flex;align-items:center;justify-content:center;flex:none}
.ico.red{background:#fee2e2}.ico.amber{background:#fef3c7}.ico.blue{background:#dbeafe}.ico.green{background:#dcfce7}
.row .t{font-size:36px;font-weight:700}
.row .s{font-size:25px;color:#475569;margin-top:6px}
.row .r{margin-left:auto;font-size:36px;font-weight:800;color:#b91c1c;white-space:nowrap;font-variant-numeric:tabular-nums}
.row .r.amb{color:#92400e}
.btn{display:flex;align-items:center;justify-content:center;gap:24px;background:#15803d;color:#fff;font-size:54px;font-weight:800;
 border-radius:32px;height:170px;box-shadow:0 14px 30px rgba(21,128,61,.30)}
.chips{display:flex;flex-wrap:wrap;gap:22px}
.chip{background:#fff;border:3px solid #cbd5e1;color:#1d4ed8;font-weight:700;font-size:40px;padding:22px 40px;border-radius:999px}
.note{position:absolute;bottom:56px;left:72px;font-size:24px;color:#475569;font-weight:500}
.dots{position:absolute;bottom:60px;right:72px;display:flex;gap:12px}
.dots b{width:14px;height:14px;border-radius:50%%;background:#bfdbfe}
.dots b.on{background:#2563eb;width:40px;border-radius:999px}
.cta{display:inline-block;background:#2563eb;color:#fff;font-size:48px;font-weight:800;padding:34px 64px;border-radius:28px;margin-top:56px}
.cover{display:flex;align-items:center;justify-content:center;flex-direction:column;height:%(h)dpx;
 background:linear-gradient(160deg,#3b82f6 0%%,#1d4ed8 100%%)}
.cover .circle{width:420px;height:420px;border-radius:50%%;background:rgba(255,255,255,.16);display:flex;align-items:center;justify-content:center}
.cover p{color:#fff;font-size:76px;font-weight:800;margin-top:70px;letter-spacing:-1px}
"""

ICON = {
    "arrow": '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#166534" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M8 7h9v9"/></svg>',
    "alert": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#b91c1c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12v20l-3-2-3 2-3-2-3 2z"/><path d="M12 7v5M12 15.5v.5"/></svg>',
    "box": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/></svg>',
    "cart": '<svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4a1 1 0 0 0 1 .8h8.8a1 1 0 0 0 1-.8L20 7H6"/></svg>',
    "cash": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#15803d" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6 10v4M18 10v4"/></svg>',
    "ticket": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-3a2 2 0 0 0 0-4z"/><path d="M9 9h6M9 15h6"/></svg>',
    "scan": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8v8M10 8v8M14 8v8M17 8v8"/></svg>',
    "user": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    "truck": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 6h13v10H1zM14 10h4l3 3v3h-7z"/><circle cx="5.5" cy="18" r="1.8"/><circle cx="17.5" cy="18" r="1.8"/></svg>',
    "tag": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><circle cx="7" cy="7" r="1.5"/></svg>',
    "calendar": '<svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>',
}

COVER_ICONS = {
    "Novedades": '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>',
    "Cómo funciona": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "Punto de venta": '<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.7 12.4a1 1 0 0 0 1 .8h8.8a1 1 0 0 0 1-.8L20 7H6"/>',
    "Cobros": '<path d="M6 2h12v20l-3-2-3 2-3-2-3 2z"/><path d="M9 7h6M9 11h6M9 15h4"/>',
    "Inventario": '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
}


FONT = ("<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link href='https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=block' rel='stylesheet'>")


def page(body, w=1080, h=1350):
    return f"<!doctype html><html><head><meta charset='utf-8'>{FONT}<style>{CSS % {'w': w, 'h': h}}</style></head><body>{body}</body></html>"


def top(n=None, total=None):
    c = f"<div class='count'>{n}/{total}</div>" if n else ""
    return f"<div class='top'><div class='brand'>PymeFácil</div>{c}</div>"


def dots(n, total):
    return "<div class='dots'>" + "".join(f"<b class='{'on' if i == n else ''}'></b>" for i in range(1, total + 1)) + "</div>"


EXAMPLE = "<div class='note'>Datos de ejemplo</div>"

BARS = "".join(f"<i class='{'hi' if i == 4 else ''}' style='height:{v}%'></i>" for i, v in enumerate([30, 38, 52, 60, 100, 70, 58, 44, 50, 62, 56, 48]))


def card_ventas(compact=False):
    stats = '' if compact else "<div class='stats'><div class='stat'><div class='label'>Ventas</div><b>23</b></div><div class='stat'><div class='label'>Ticket promedio</div><b>RD$ 802.17</b></div></div>"
    return f"""<div class='card'>
      <div style='display:flex;justify-content:space-between;align-items:center'>
        <div class='label'>Vendido hoy</div><div class='chip-up'>{ICON['arrow']}12% vs. domingo pasado</div></div>
      <div class='amount'>RD$ 18,450.00</div>
      <div class='bars'>{BARS}</div>
      {stats}</div>"""


def card_atencion(extra=False):
    rows = f"""<div class='row'><div class='ico red'>{ICON['alert']}</div><div><div class='t'>4 facturas vencidas</div>
      <div class='s'>Más vieja: Ferretería Peña, 38 días</div></div><div class='r'>RD$ 12,300.00</div></div>
      <div class='row'><div class='ico amber'>{ICON['box']}</div><div><div class='t'>6 productos con stock bajo</div>
      <div class='s'>Aceite Crisol 1 L, Arroz La Garza 5 lb…</div></div><div class='r amb'>Revisar</div></div>"""
    return f"<div class='card' style='padding:20px 48px'>{rows}</div>"


SLIDES = {}

# ---------- Carrusel: Nuevo Inicio (6 láminas) ----------
T = 6
SLIDES["carrusel-inicio-01"] = page(f"""{top(1, T)}<div class='main' style='top:230px'>
  <span class='eyebrow'>NOVEDAD</span><h1>Tu negocio,<br><em>de un vistazo.</em></h1>
  <p class='sub'>Estrenamos un Inicio nuevo en PymeFácil.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:650px'>{card_ventas(True)}</div>{EXAMPLE}{dots(1, T)}""")

SLIDES["carrusel-inicio-02"] = page(f"""{top(2, T)}<div class='main'>
  <h1>Lo que vendiste hoy, <em>primero.</em></h1>
  <p class='sub'>Abres la app y ves cuánto llevas y cómo vas frente al mismo día de la semana pasada.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:580px'>{card_ventas()}</div>{EXAMPLE}{dots(2, T)}""")

SLIDES["carrusel-inicio-03"] = page(f"""{top(3, T)}<div class='main'>
  <h1>Lo que necesita tu <em>atención,</em> a la vista.</h1>
  <p class='sub'>Facturas vencidas y productos por agotarse, sin tener que buscarlos.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:760px'>{card_atencion()}</div>{EXAMPLE}{dots(3, T)}""")

SLIDES["carrusel-inicio-04"] = page(f"""{top(4, T)}<div class='main'>
  <h1>Nueva venta en <em>un toque.</em></h1>
  <p class='sub'>El botón que más usas, siempre a mano para vender rápido.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:790px'><div class='btn'>{ICON['cart']}Nueva venta</div></div>{dots(4, T)}""")

SLIDES["carrusel-inicio-05"] = page(f"""{top(5, T)}<div class='main'>
  <h1>Todo en una <em>sola app.</em></h1>
  <p class='sub'>Vende, cobra, compra y controla tu dinero.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:700px'><div class='chips'>
  {''.join(f"<span class='chip'>{c}</span>" for c in ['Punto de venta','Facturas','Cobros','Inventario','Compras','Clientes','Comisiones','Finanzas'])}
  </div></div>{dots(5, T)}""")

SLIDES["carrusel-inicio-06"] = page(f"""{top(6, T)}<div class='main' style='top:330px'>
  <h1>Actualiza y míralo <em>en tu pyme.</em></h1>
  <p class='sub'>Cuéntanos qué te parece el Inicio nuevo. Escríbenos por mensaje directo.</p>
  <div class='cta'>Link en la bio</div></div>{dots(6, T)}""")

# ---------- Publicaciones sueltas ----------
SLIDES["post-facturas-vencidas"] = page(f"""{top()}<div class='main'>
  <span class='eyebrow'>COBROS</span><h1>Sabe quién te debe, <em>sin buscar.</em></h1>
  <p class='sub'>Tus facturas vencidas aparecen en el Inicio: cuántas son, cuál es la más vieja y cuánto suman.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:860px'>{card_atencion()}</div>{EXAMPLE}""")

SLIDES["post-stock-bajo"] = page(f"""{top()}<div class='main'>
  <span class='eyebrow'>INVENTARIO</span><h1>Que no se te acabe <em>lo que más vendes.</em></h1>
  <p class='sub'>PymeFácil te avisa cuando un producto está por agotarse, antes de que pierdas la venta.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:900px'><div class='card' style='padding:20px 48px'>
  <div class='row'><div class='ico amber'>{ICON['box']}</div><div><div class='t'>6 productos con stock bajo</div>
  <div class='s'>Aceite Crisol 1 L, Arroz La Garza 5 lb…</div></div><div class='r amb'>Revisar</div></div></div></div>{EXAMPLE}""")


def rows_card(rows):
    """rows: lista de (icono, color, título, subtítulo, valor_derecha, clase_valor)."""
    html = "".join(
        f"<div class='row'><div class='ico {c}'>{ICON[i]}</div><div><div class='t'>{t}</div><div class='s'>{s}</div></div>"
        f"<div class='r {rc}' style='{'' if rc else 'color:#0f172a'}'>{r}</div></div>"
        for i, c, t, s, r, rc in rows)
    return f"<div class='card' style='padding:20px 48px'>{html}</div>"


def step(n):
    return f"<span class='eyebrow'>PASO {n} DE 4</span>"


# ---------- Carrusel: Tu primera venta (6 láminas) ----------
T = 6
SLIDES["carrusel-primera-venta-01"] = page(f"""{top(1, T)}<div class='main' style='top:230px'>
  <span class='eyebrow'>CÓMO SE USA</span><h1>Tu primera venta, <em>en 4 pasos.</em></h1>
  <p class='sub'>Desde que abres PymeFácil hasta que cobras. Desliza.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:820px'><div class='btn'>{ICON['cart']}Nueva venta</div></div>{dots(1, T)}""")

SLIDES["carrusel-primera-venta-02"] = page(f"""{top(2, T)}<div class='main'>
  {step(1)}<h1>Toca <em>Nueva venta.</em></h1>
  <p class='sub'>Está en el Inicio, siempre a mano. Es el botón verde.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:800px'><div class='btn'>{ICON['cart']}Nueva venta</div></div>{dots(2, T)}""")

SLIDES["carrusel-primera-venta-03"] = page(f"""{top(3, T)}<div class='main'>
  {step(2)}<h1>Toca o <em>escanea</em> los productos.</h1>
  <p class='sub'>Cada toque suma uno al carrito. Con lector de código o sin él.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:760px'>{rows_card([
      ('scan', 'blue', 'Arroz La Garza 5 lb', 'Escaneado', '× 2', ''),
      ('box', 'amber', 'Aceite Crisol 1 L', 'Tocado en la lista', '× 1', ''),
      ('tag', 'blue', 'Café Santo Domingo 1 lb', 'Tocado en la lista', '× 1', '')])}</div>{EXAMPLE}{dots(3, T)}""")

SLIDES["carrusel-primera-venta-04"] = page(f"""{top(4, T)}<div class='main'>
  {step(3)}<h1>¿Para <em>quién</em> es la venta?</h1>
  <p class='sub'>Déjala en Consumidor final o elige un cliente de tu lista.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:820px'><div class='card' style='display:flex;align-items:center;gap:28px'>
  <div class='ico blue'>{ICON['user']}</div><div class='t' style='font-size:40px;font-weight:700'>Consumidor final</div>
  <div style='margin-left:auto;font-size:38px;font-weight:700;color:#2563eb'>Elegir</div></div></div>{dots(4, T)}""")

SLIDES["carrusel-primera-venta-05"] = page(f"""{top(5, T)}<div class='main'>
  {step(4)}<h1><em>Cobra</em> y listo.</h1>
  <p class='sub'>Si te pagan justo en efectivo, toca Exacto y la venta queda hecha.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:760px'><div class='card'>
  <div style='display:flex;justify-content:space-between;align-items:baseline'><div class='label'>4 artículos</div>
  <div style='font-size:60px;font-weight:800;letter-spacing:-1.5px;font-variant-numeric:tabular-nums'>RD$ 1,135.00</div></div>
  <div style='display:flex;gap:24px;margin-top:40px'>
   <div style='flex:1;border:3px solid #15803d;border-radius:28px;display:flex;flex-direction:column;align-items:center;justify-content:center;height:150px;color:#15803d'>
    <b style='font-size:40px'>Exacto</b><span style='font-size:28px'>en efectivo</span></div>
   <div class='btn' style='flex:2;height:150px;font-size:50px'>COBRAR</div></div></div></div>{EXAMPLE}{dots(5, T)}""")

SLIDES["carrusel-primera-venta-06"] = page(f"""{top(6, T)}<div class='main' style='top:330px'>
  <h1>Guárdalo para <em>tu primera venta.</em></h1>
  <p class='sub'>¿Te trabaste en algún paso? Escríbenos por mensaje directo y te ayudamos.</p>
  <div class='cta'>Link en la bio</div></div>{dots(6, T)}""")

# ---------- Post: los 3 números de cada día ----------
SLIDES["post-tres-numeros"] = page(f"""{top()}<div class='main'>
  <span class='eyebrow'>TIPS PARA TU PYME</span><h1>Los 3 números que <em>debes mirar</em> cada día.</h1></div>
  <div style='position:absolute;left:72px;right:72px;top:625px'>{rows_card([
      ('cash', 'green', 'Vendido hoy', 'Cómo vas frente a la semana pasada', 'RD$ 18,450.00', ''),
      ('ticket', 'blue', 'Ticket promedio', 'Cuánto te compra cada cliente', 'RD$ 802.17', ''),
      ('alert', 'red', 'Facturas vencidas', 'El dinero que está en la calle', 'RD$ 12,300.00', '')])}
  <p class='sub' style='margin-top:32px;font-size:32px'>Los tres están en el Inicio de PymeFácil, apenas abres la app.</p></div>{EXAMPLE}""")

# ---------- Carrusel: Tu pyme en PymeFácil (6 láminas) ----------
T = 6
SLIDES["carrusel-tu-pyme-01"] = page(f"""{top(1, T)}<div class='main' style='top:260px'>
  <span class='eyebrow'>NEGOCIOS RD</span><h1>Hecha para <em>tu pyme.</em></h1>
  <p class='sub'>Colmado, ferretería, boutique o salón: así te ayuda PymeFácil. Desliza.</p></div>
  <div style='position:absolute;left:72px;right:72px;top:860px'><div class='chips'>
  {''.join(f"<span class='chip'>{c}</span>" for c in ['Colmado', 'Ferretería', 'Boutique', 'Salón'])}</div></div>{dots(1, T)}""")

SLIDES["carrusel-tu-pyme-02"] = page(f"""{top(2, T)}<div class='main'>
  <span class='eyebrow'>COLMADO</span><h1>Despacha rápido, <em>sin que falte nada.</em></h1></div>
  <div style='position:absolute;left:72px;right:72px;top:640px'>{rows_card([
      ('scan', 'blue', 'Venta en segundos', 'Toca o escanea y cobra', '', ''),
      ('box', 'amber', 'Aviso de stock bajo', 'Antes de quedarte sin arroz o aceite', '', ''),
      ('cash', 'green', 'Vendido hoy', 'Lo ves al abrir la app', '', '')])}</div>{dots(2, T)}""")

SLIDES["carrusel-tu-pyme-03"] = page(f"""{top(3, T)}<div class='main'>
  <span class='eyebrow'>FERRETERÍA</span><h1>Cobra a tiempo <em>a tus clientes.</em></h1></div>
  <div style='position:absolute;left:72px;right:72px;top:640px'>{rows_card([
      ('alert', 'red', 'Facturas vencidas', 'Quién te debe y desde cuándo', '', ''),
      ('truck', 'blue', 'Compras a suplidores', 'Lo que pediste y cuándo llega', '', ''),
      ('box', 'amber', 'Inventario al día', 'Cada venta descuenta del stock', '', '')])}</div>{dots(3, T)}""")

SLIDES["carrusel-tu-pyme-04"] = page(f"""{top(4, T)}<div class='main'>
  <span class='eyebrow'>BOUTIQUE</span><h1>Tu catálogo, <em>ordenado.</em></h1></div>
  <div style='position:absolute;left:72px;right:72px;top:640px'>{rows_card([
      ('tag', 'blue', 'Por categorías', 'Hombre, mujer, accesorios…', '', ''),
      ('scan', 'blue', 'Con lector de código', 'O tocando el producto', '', ''),
      ('box', 'amber', 'Cuántos te quedan', 'Lo ves en cada producto', '', '')])}</div>{dots(4, T)}""")

SLIDES["carrusel-tu-pyme-05"] = page(f"""{top(5, T)}<div class='main'>
  <span class='eyebrow'>SALÓN</span><h1>Tu agenda de citas, <em>en una vista.</em></h1></div>
  <div style='position:absolute;left:72px;right:72px;top:640px'>{rows_card([
      ('calendar', 'blue', 'Citas por día', 'Toda la semana a la vista', '', ''),
      ('user', 'blue', 'Por estilista', 'Cada quien con su columna', '', ''),
      ('ticket', 'blue', 'Paquetes de servicios', 'Ej.: manicure, sesión 7 de 10', '', '')])}</div>{dots(5, T)}""")

SLIDES["carrusel-tu-pyme-06"] = page(f"""{top(6, T)}<div class='main' style='top:330px'>
  <h1>¿Cuál es <em>tu negocio?</em></h1>
  <p class='sub'>Cuéntanos en los comentarios y te decimos cómo usarlo en tu pyme.</p>
  <div class='cta'>Link en la bio</div></div>{dots(6, T)}""")


def cover(label):
    svg = f"<svg width='230' height='230' viewBox='0 0 24 24' fill='none' stroke='#fff' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>{COVER_ICONS[label]}</svg>"
    return page(f"<div class='cover'><div class='circle'>{svg}</div><p>{label}</p></div>", 1080, 1920)


for name in COVER_ICONS:
    slug = name.lower().replace("ó", "o").replace(" ", "-")
    SLIDES[f"destacado-{slug}"] = (cover(name), 1920)


def chrome() -> str:
    """Ruta de Chrome: variable CHROME, o la habitual en Linux/Windows/macOS."""
    import os
    import shutil
    cands = [os.environ.get("CHROME"), shutil.which("google-chrome"), shutil.which("chrome"),
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in cands:
        if c and Path(c).exists():
            return c
    raise SystemExit("No encuentro Chrome: define la variable CHROME con su ruta")


def render(name, html, h=1350):
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "s.html"
        f.write_text(html, encoding="utf-8")
        png = Path(td) / "s.png"
        subprocess.run(
            [chrome(), "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1", "--virtual-time-budget=8000", f"--window-size=1080,{h}",
             f"--screenshot={png}", f.as_uri()],
            check=True, capture_output=True, timeout=90)
        im = Image.open(png).convert("RGB").crop((0, 0, 1080, h))
        out = OUT / f"{name}.jpg"
        im.save(out, "JPEG", quality=92, optimize=True)  # Instagram API: solo JPEG, máx. 8 MB
        print(f"{out.name}  {im.size}  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    only = sys.argv[1:]
    for name, spec in SLIDES.items():
        if only and not any(o in name for o in only):
            continue
        html, h = spec if isinstance(spec, tuple) else (spec, 1350)
        render(name, html, h)
