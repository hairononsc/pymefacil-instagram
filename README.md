# PymeFácil · Instagram automático

Paquete para preparar y publicar contenido en el Instagram de PymeFácil. Estrategia, perfil y calendario: `docs/perfil-y-estrategia.md`.

```
calendar.json            cola de publicaciones (texto, imágenes, fecha, estado)
state.json               lo ya publicado (lo crea el publicador)
media/                   imágenes JPEG listas (carrusel, posts, portadas de destacados)
build/build_media.py     genera las imágenes con la marca (Chrome headless + Inter)
publisher/publish.py     publica en Instagram vía Graph API
tests/                   prueba de punta a punta con un servidor Meta simulado
.github/workflows/       publicación automática cada hora (GitHub Actions)
```

## Uso diario

```bash
python3 publisher/publish.py --dry-run     # valida calendar.json y muestra qué saldría
python3 publisher/publish.py --verify      # comprueba token y cuenta
python3 publisher/publish.py               # publica lo que ya toque (máx. 1 por corrida)
python3 publisher/publish.py --post ID --force   # publica una pieza ahora
python3 build/build_media.py [filtro]      # regenera imágenes
python3 tests/test_publisher.py            # prueba el flujo sin tocar Instagram
```

Nada se publica hasta que cambies `"status": "draft"` a `"approved"` en `calendar.json`. Una pieza atrasada más de 48 h se omite para no subir contenido viejo por accidente.

## Configuración (una sola vez)

1. **Cuenta:** Instagram Profesional (Business o Creator) vinculada a una Página de Facebook. Ya cumplido según nos dijiste.
2. **App de Meta:** en developers.facebook.com crea una app, añade el producto de Instagram y solicita los permisos `instagram_basic`, `instagram_content_publish`, `pages_show_list` y `pages_read_engagement`. Mientras la app esté en modo desarrollo y tú seas administrador de la app, puedes publicar en tu propia cuenta sin pasar la revisión de Meta.
3. **Token:** para probar sirve el Explorador de la Graph API (el token de usuario dura poco, se puede cambiar por uno de larga duración). Para producción conviene un token de usuario del sistema creado en el Business Manager y con la cuenta asignada. Revisa en la documentación de Meta el flujo vigente, porque cambia con frecuencia.
4. **ID de Instagram:** con el token, `GET /me/accounts` lista tus Páginas; luego `GET /{id-de-la-pagina}?fields=instagram_business_account` devuelve el `IG_USER_ID`.
5. **Imágenes públicas:** Instagram descarga cada imagen desde una URL pública (`MEDIA_BASE_URL` + `media/archivo.jpg`). Opciones: repositorio público de GitHub (`https://raw.githubusercontent.com/OWNER/REPO/main`), GitHub Pages, o un bucket público de Supabase Storage.
6. **Variables:** copia `.env.example` a `.env` para correr en local, o crea los secretos `IG_USER_ID`, `IG_ACCESS_TOKEN` y `MEDIA_BASE_URL` en GitHub (Settings → Secrets and variables → Actions). Con eso el flujo `.github/workflows/instagram.yml` publica solo.
7. Corre `--verify`; si responde `Conectado como @...`, cambia la primera pieza a `approved`.

## Notas técnicas

- Solo JPEG, hasta 8 MB por imagen; carruseles de 2 a 10 imágenes; texto de hasta 2,200 caracteres y 30 hashtags. El publicador lo valida antes de llamar a Meta.
- El token viaja en el encabezado `Authorization`, no en la URL, para que no aparezca en registros.
- Si Meta falla justo al publicar, el publicador guarda el contenedor en `state.json` y el siguiente intento lo reutiliza en vez de volver a subir las imágenes. Un mismo contenedor no puede publicarse dos veces, así que no hay duplicados.
- La versión de la Graph API es `GRAPH_VERSION` (por defecto `v25.0`). Meta retira versiones cada cierto tiempo: súbela cuando haga falta.
- Las láminas con montos dicen "Datos de ejemplo"; si pones cifras reales de un cliente, pide su permiso.
