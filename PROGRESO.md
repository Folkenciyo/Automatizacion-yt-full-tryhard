# AutomatizaciónYT — Progreso y Hoja de Ruta

## Estado actual (29-Jun-2026) — actualizado fin de sesión noche

### ✅ Fase 0 — Setup base
- Monorepo con backend / frontend / worker
- Docker Compose con postgres, redis, backend, worker, frontend
- Modelo de datos multi-canal / multi-nicho desde el día 1

### ✅ Fase 1 — Motor de research
- YouTube Data API v3 integrada
- Ingesta de canales competidores por nicho
- Cálculo de patrones de título (n-gramas)
- Endpoints `/research/*`

### ✅ Fase 2 — Pipeline de generación (CLI)
- Interfaz `NicheGenerator` (plugin por nicho)
- Plugin `white_noise`: audio sintético (numpy/scipy), visual gradiente (ffmpeg lavfi), miniatura (Pillow)
- CLI de render end-to-end verificado

### ✅ Fase 3 — Metadata + Publish multi-canal
- Generador de metadata desde banco de patrones con fallback estático
- OAuth 2.0 por canal (Google Cloud, credenciales en volumen compartido)
- Cola de jobs Redis → worker consume render + publish
- Worker real: renderiza, actualiza DB, sube a YouTube, miniatura opcional
- Video publicado y verificado en YouTube

### ✅ Fase 4 — Dashboard
- Layout con sidebar de navegación
- Página de inicio con overview de canales y stats
- Lista de canales + crear canal desde UI
- Detalle de canal: proyectos, progreso YPP (Tier 1 / completo), estado OAuth
- Formulario nuevo video: 19 topics (incluyendo mixes), 5 estilos visuales, selector de duración custom (preset + min:seg)
- Página de proyecto: barra de progreso con pasos reales via SSE, polling automático, publicar en YouTube
- Previsualización de video (`<video controls>`) + miniatura antes de publicar
- Eliminación de proyectos con modal de confirmación (borra disco + DB)
- Botón re-renderizar en proyectos fallidos
- API routes Next.js como proxy al backend (preview con Range, thumbnail, delete, SSE progress)

---

## ⬜ Fase 5 — Plugin canciones infantiles (pendiente)
- Melodías de dominio público (Twinkle Twinkle, etc.)
- TTS open-source local (Piper TTS)
- Animación 2D procedural simple
- Registro como nicho `canciones_infantiles` en la plataforma

---

## Mejoras planificadas (backlog priorizado)

### Alta prioridad

#### Miniaturas de calidad
- [x] Fondo: frame extraído del mid-point del video con overlay semi-transparente degradado
- [x] Tipografía: Liberation Sans Bold (apt `fonts-liberation`) con fallback al font por defecto
- [x] Icono de ondas de sonido dibujado con Pillow arcs (esquina superior izquierda)
- [x] Sombra en texto para legibilidad sobre cualquier fondo
- [ ] Gradiente de marca por canal (requiere columna `brand_color` en tabla `channels` + migración)

#### Más sonidos blancos / ruido de color
- [x] `brown_noise` — ruido marrón (1/f², integración + low-pass 280 Hz)
- [x] `pink_noise` — ruido rosa (1/f, suma de bandas de octava con peso decreciente)
- [x] `fan` — ventilador (bandpass 180-5500 Hz + modulación de frecuencia de pala a 12 Hz)
- [x] `womb` — sonido de útero (bandpass 25-380 Hz + envelope de latido a 60 BPM)
- [x] `heartbeat` — latido LUB-DUB a 60 BPM con decay exponencial (30 s loop perfecto)
- [x] `shower` — ducha (bandpass 1200-18000 Hz)
- [x] `thunderstorm` — lluvia + 2-4 truenos de baja frecuencia con decay
- [x] `fireplace` — chimenea (bandpass 80-3500 Hz + 40-90 crepitaciones aleatorias)
- [x] `deep_sleep` — NUEVO: 60% ruido marrón + 40% ruido rosa + low-pass 4 kHz

#### Variedad y customización de audio
- [ ] Parámetro `intensity` (suave / normal / intenso) que ajusta la amplitud del filtro
- [ ] Parámetro `fade_in_seconds` y `fade_out_seconds` configurables
- [x] Mezcla de dos topics con balance configurable — formato `topic1+topic2:0.7` en el campo topic
- [ ] BPM de intensidad variable (el envelope oscila más rápido o más lento)

### Media prioridad

#### Animaciones variadas en vez de solo gradiente
- [x] `plasma` — plasma psicodélico con 3 ondas sinusoidales independientes (ffmpeg geq, 60 s loop)
- [x] `waves` — ondas de agua horizontales en paleta azul-verde (ffmpeg geq, 60 s loop)
- [x] `aurora` — aurora boreal con bandas verdes y deriva horizontal lenta (ffmpeg geq, 60 s loop)
- [x] `ai` — video IA vía fal.ai (WAN v2.1), 1 clip ~5 s por topic + concat loop; fallback a gradient si no hay FAL_KEY
- [x] Campo `visual_style` en `RenderRequest`, dispatcher en `generate_visual()`, selector en frontend
- [ ] `particles` — partículas flotantes (pendiente Python frames)
- [ ] `stars` — campo de estrellas con parpadeo (pendiente)
- [ ] `mandala` — patrón geométrico rotatorio (pendiente)
- **Nota:** clips geq se generan a 60 s y se concatenan (sin re-encode) hasta la duración final vía `ffmpeg -f concat`

#### Videos en bucle explícito (loop seamless)
- [x] Clips procedurales (plasma/waves/aurora) generados en 60 s y concatenados sin re-encode via `ffmpeg -f concat -c copy`
- [x] Clips IA concatenados igual tras re-encode a resolución target
- [ ] Verificación automática de calidad de loop: comparar primer y último frame con SSIM > 0.95
- [ ] Para gradiente: el loop ya es seamless en audio; el visual podría mejorar con crossfade de frames

#### Creación en lote (batch)
- [ ] Endpoint `POST /channels/{id}/batch` con lista de variantes `[{topic, duration, seed}]`
- [ ] Worker procesa la cola secuencialmente para no saturar CPU
- [ ] Dashboard muestra cola con posición y ETA

### Baja prioridad / futuro

#### Previsualización antes de publicar
- [x] Player `<video controls>` en la página del proyecto cuando status = review/scheduled/published
- [x] Endpoint `GET /video-projects/{id}/preview` con soporte Range requests (seeking)
- [x] Miniatura al lado del player (`GET /video-projects/{id}/thumbnail`)
- [ ] Botón "Publicar en YouTube" bloqueado hasta ver el preview (actualmente siempre activo)

#### Eliminación de proyectos
- [x] Botón "Eliminar" en la página del proyecto con modal de confirmación
- [x] Endpoint `DELETE /video-projects/{id}`: borra archivos del disco + fila DB
- [x] Redirect al canal tras eliminar
- [ ] Si ya publicado en YouTube: opción de borrar también del canal (YouTube API `videos.delete`)

#### Progreso de render real
- [x] Worker publica progreso en Redis (`render:progress:{id}`) con pct y step por etapa
- [x] Progreso ffmpeg real via `subprocess.Popen` + lectura stderr en `_run_ffmpeg_encode`
- [x] Endpoint SSE `GET /video-projects/{id}/progress` en backend
- [x] Frontend suscribe via `EventSource`, muestra paso actual ("Generando visual...", etc.)
- [x] Botón "Crear nuevo proyecto" en proyectos fallidos

#### Calendario de publicación
- [ ] Campo `scheduled_at` en `VideoProject` ya existe en el modelo
- [ ] Endpoint para programar publicación (`PATCH /video-projects/{id}/schedule`)
- [ ] Worker cron (cada hora) que busca proyectos en `scheduled` con `scheduled_at <= now()` y los publica
- [ ] Vista calendario en el dashboard (semana/mes) con drag & drop de slots

#### Métricas YPP reales
- [ ] Endpoint YouTube Analytics API para obtener subs + horas reales por canal
- [ ] Guardar en tabla `channel_metrics` (ya modelada) cada día via cron
- [ ] Barras de progreso YPP con datos reales en vez de 0/0

#### Gestión de errores en el dashboard
- [ ] Botón "reintentar render" para proyectos en estado `failed`
- [ ] Log de error visible en la página del proyecto

#### Optimización de almacenamiento
- [ ] Borrar archivos intermedios (audio_loop.wav, visual.mp4) tras publicar, conservar solo output.mp4 + thumbnail
- [ ] Opción de comprimir video a H.265 para reducir tamaño a la mitad manteniendo calidad

#### Multi-idioma
- [ ] Títulos / descripciones en inglés para alcanzar mercado angloparlante (mayor RPM)
- [ ] Parámetro `lang` en `VideoProjectCreate` → el generador de metadata produce en ese idioma

#### Segundo canal — Canciones infantiles (Fase 5)
- [ ] Plugin `kids_songs` con Piper TTS + melodías dominio público
- [ ] Animación 2D procedural (personaje geométrico simple)
- [ ] Nicho registrado como `canciones_infantiles` con `made_for_kids_default=true`

---

## Notas técnicas importantes

- **Ruta de trabajo local**: `C:\Projects\automatizacion-yt\` (sin tildes — Docker no acepta la ruta original con `ó`)
- **Ruta original del proyecto**: `C:\Users\folkencillo\Desktop\Automatizacion-YT\contenido\Automatización YT\` (solo para referencia, no usar con Docker)
- **Credenciales OAuth**: volumen Docker `credentials` montado en `/app/credentials` en backend y worker
- **Thumbnails personalizadas en YouTube**: requieren verificación de teléfono del canal (canal nuevo sin verificar → se omite sin error)
- **Cuota YouTube Data API**: 10.000 unidades/día por proyecto GCP; subir 1 video = ~1.600 unidades (~6 uploads/día)
- **Canal activo**: `pinkatanki@gmail.com`, channel ID guardado en DB como canal 1
- **Límite de duración sin verificar**: YouTube permite máximo 15 min en canales no verificados → default UI = 14:59 (899 s). Verificar en youtube.com/verify para subir videos más largos.
- **`uv lock` ejecutado**: `fal-client v1.0.0` ya está en el lock file del worker
- **FAL_KEY**: añadir al `.env` para activar `visual_style: "ai"` (fal.ai WAN v2.1)
