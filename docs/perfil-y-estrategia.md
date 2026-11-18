# PymeFácil en Instagram — perfil, línea de contenido y calendario

_Preparado el 18 nov 2026. Basado en el sistema de diseño de PymeFácil y en el rediseño del Inicio._

## 1. Perfil nuevo

| Campo | Propuesta | Nota |
|---|---|---|
| Nombre (el que se busca) | **PymeFácil \| ERP para tu pyme** (28 caracteres) | Incluye la palabra que la gente busca. |
| Usuario | `@pymefacil.do` (o el que esté libre) | Verificar disponibilidad antes de cambiarlo; evita guiones bajos y números. |
| Categoría | Empresa de software (o "Software") | Se cambia en Editar perfil → Categoría. |
| Foto | Ícono de la app (`assets/icon/app_icon.png` del repositorio) sobre fondo blanco | No usar el logo sobre un color de módulo (regla del sistema de diseño). |
| Enlace | Página de PymeFácil o enlace a WhatsApp/registro | Un solo enlace claro. Pendiente: definir cuál. |
| Botón de contacto | WhatsApp o correo del negocio | Pendiente: definir canal. |

**Bio (139 de 150 caracteres):**

```
El ERP para tu pyme dominicana.
Vende, cobra, compra y controla tu dinero desde el celular.
Punto de venta · Facturas · Inventario · Cobros
```

Sin emojis y sin promesas que no podamos sostener (no dice "gratis" ni "en 5 minutos"). Cuando los planes estén definidos se puede añadir una línea con la invitación a probar.

**Destacados (portadas ya generadas en `media/destacado-*.jpg`):** Novedades · Cómo funciona · Punto de venta · Cobros · Inventario.

**Publicaciones fijadas (3):** 1) el carrusel del Inicio nuevo, 2) una presentación corta de qué es PymeFácil, 3) "Cómo empezar".

> Instagram no permite cambiar nombre, bio ni foto por API. Esos cambios se hacen desde la app, o puedo hacerlos contigo en el navegador cuando aprobemos los textos.

## 2. Línea visual (sale del sistema de diseño)

- **Colores:** azul `#2563EB` (único primario), verde `#15803D` para dinero/éxito, navy `#0F172A` para titulares, fondo en degradado muy suave `#F8FAFC → #DBEAFE`.
- **Tipografía:** Inter (titulares en ExtraBold, apoyo en Medium).
- **Formato:** 1080×1350 (4:5). Titular grande con una palabra clave en azul, una tarjeta de la interfaz abajo, "Datos de ejemplo" cuando hay montos inventados.
- **Una idea por pieza**, el monto o el dato importante primero (principio "primero el dinero" de la app).

## 3. Voz

Español dominicano con tuteo ("Vende", "Cobra", "Actualiza"), frases cortas, voz activa. Hablar como el dueño del negocio, no como contador: nada de jerga fiscal salvo en piezas dirigidas a quienes ya usan facturación fiscal. Sin emojis en los diseños (en textos, con moderación).

## 4. Pilares de contenido y ritmo

| Pilar | Peso | Ejemplos |
|---|---|---|
| Novedades del producto | 30 % | Inicio nuevo, mejoras, módulos |
| Tips para tu pyme | 30 % | Qué números mirar a diario, cómo cobrar a tiempo |
| Cómo se usa | 20 % | Primera venta, cierre de caja, cargar inventario |
| Negocios dominicanos | 10 % | Colmados, ferreterías, boutiques, salones |
| Comunidad | 10 % | Preguntas, encuestas en Stories |

**Ritmo sugerido:** 3 publicaciones por semana (martes, jueves, sábado) y 3–5 Stories. Hora: 12:00 (pico de mediodía en RD) y 19:00 como alternativa; ajustar con las estadísticas después de 3–4 semanas.

## 5. Calendario de las primeras 4 semanas

Horas en America/Santo_Domingo. Las 3 primeras piezas ya están diseñadas y cargadas en `calendar.json` (en estado `draft`).

| Fecha | Pieza | Pilar | Estado |
|---|---|---|---|
| Jue 19 nov, 12:00 | Carrusel: **Nuevo Inicio** (6 láminas) | Novedades | Listo |
| Sáb 21 nov, 11:00 | **Sabe quién te debe, sin buscar** (facturas vencidas) | Novedades / Cobros | Listo |
| Mar 24 nov, 12:00 | **Que no se te acabe lo que más vendes** (stock bajo) | Novedades / Inventario | Listo |
| Jue 26 nov | Cómo hacer tu primera venta (carrusel de pasos) | Cómo se usa | Por diseñar |
| Sáb 28 nov | Los 3 números que debes mirar cada día: vendido hoy, ticket promedio, por cobrar | Tips | Por diseñar |
| Mar 1 dic | Conoce a FacilBot, la mascota de PymeFácil | Comunidad | Por diseñar |
| Jue 3 dic | Cuadra tu caja al cerrar el día | Cómo se usa | Por diseñar (validar flujo) |
| Sáb 5 dic | Recordatorios de cobro por WhatsApp | Novedades | Por diseñar (validar que esté disponible) |
| Mar 8 dic | Tu pyme en PymeFácil: colmado, ferretería, boutique, salón | Negocios RD | Por diseñar |
| Jue 10 dic | Comisiones de vendedores sin hoja de cálculo | Novedades | Por diseñar (validar) |
| Sáb 12 dic | Facturación fiscal (e-CF) para quienes ya la usan | Tips | **Revisar con el equipo antes de publicar** (cumplimiento DGII) |
| Mar 15 dic | Planes y forma de cobro | Novedades | Cuando los planes estén cerrados |

Las piezas marcadas "validar" parten de módulos que aparecen en el diseño de la app; confirmar que estén disponibles para los clientes antes de anunciarlas.

## 6. Cómo funciona la automatización

1. Cada pieza vive en `calendar.json` con su imagen (`media/*.jpg`), texto, texto alternativo, fecha/hora y estado (`draft` → `approved`).
2. Un publicador (`publisher/publish.py`) corre cada hora, sube a Instagram las piezas `approved` cuya hora ya llegó y anota lo publicado en `state.json`, así nunca duplica.
3. Las imágenes tienen que estar en una URL pública, porque Instagram las descarga desde ahí.
4. Para agregar contenido nuevo: se diseña la pieza (`build/build_media.py`), se añade al calendario y se marca `approved`.

**Qué hace falta de tu lado (una sola vez):** crear la app en Meta for Developers, generar el token con permisos `instagram_basic` e `instagram_content_publish`, obtener el ID de la cuenta de Instagram y decidir dónde se alojan las imágenes. Los pasos están en el README del paquete.

**Límites a tener en cuenta:** la API solo acepta imágenes JPEG, máximo 8 MB; carruseles de 2 a 10 imágenes; textos de hasta 2,200 caracteres y 30 hashtags. Meta mantiene un tope diario de publicaciones por API, muy por encima de nuestro ritmo.
