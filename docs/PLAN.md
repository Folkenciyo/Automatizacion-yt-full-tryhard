# Plan: Plataforma multi-canal de YouTube automatizado (ruido blanco + canciones infantiles, ampliable)

## Contexto

Proyecto nuevo desde cero. Objetivo: lanzar canales de YouTube generados y editados con herramientas gratuitas/open-source, monetizando lo antes posible. La plataforma debe gestionar **varios canales en paralelo, cada uno enfocado a un nicho distinto** (ruido blanco / sonidos relax como primer nicho, canciones infantiles como segundo), todos generados automáticamente pero con su propia lógica de contenido, research y metadata. Por eso el "nicho" se modela como entidad de primera clase desde la Fase 0, no como un añadido posterior — evita reescribir arquitectura cuando se sume el segundo canal.

Decisiones confirmadas con el usuario:
- Contenido inicial a producir primero: ruido blanco / sonidos relax (canciones infantiles es el segundo nicho, ya planificado en la arquitectura desde el día 1).
- Presupuesto: 100% gratuito / open-source (sin APIs de pago) — aplica a todos los nichos.
- Plataforma: app web, desplegable con Docker en Dokploy (stack flexible), multi-canal.
- Research de competencia: solo metadata pública vía YouTube Data API (títulos, descripciones, tags propios, vistas, cadencia, duración), segmentado por nicho. Sin scraping de video/audio de terceros.

## Riesgos clave a gestionar (afectan directamente "monetizar rápido")

1. **Política de "inauthentic content" de YouTube (vigente desde jul. 2025)**: penaliza contenido repetitivo/masivo sin valor añadido (plantillas idénticas, voces IA sin edición, clips reciclados). Mitigación: cada video debe variar (paleta visual generada con semilla distinta, mezcla de sonido única, intro de marca, descripción con valor real), no clonar un template 1:1.
2. **Umbrales YPP 2026**: Tier 1 (Super Thanks/Memberships) ya disponible con 500 subs + 3 videos + 3.000h vistas (90 días). Ad revenue completo (lo que de verdad monetiza) sigue requiriendo 1.000 subs + 4.000h de visionado (12 meses) o 10M vistas Shorts (90 días). Implicación: hay que diseñar para maximizar watch-time real (videos largos de 1-10h con buena retención), no solo subir volumen.
3. **COPPA / "Made for Kids"**: contenido de sueño para bebés es probable que YouTube lo clasifique como dirigido a niños (por temática), aunque el target real sean los padres. Si se marca como "made for kids": sin anuncios personalizados, sin comentarios, sin notificaciones — RPM más bajo de lo normal. Hay que autocertificar con honestidad por video (obligatorio legal, no es opcional evitarlo). Esto se planifica como expectativa de ingresos, no como bloqueante.
4. **YouTube Data API**: tags de videos de OTROS canales no son visibles vía API (Google los oculta desde hace años por privacidad) — el research de competencia se basa en títulos, descripciones, duración, vistas, cadencia de publicación y miniaturas, no en tags ajenos. Cuota gratis: 10.000 unidades/día **por proyecto de Google Cloud**, compartida entre todos los canales que autentiquen bajo ese proyecto; subir un video cuesta ~1.600 unidades (~6 uploads/día). Con un solo canal sobra. Al añadir más canales/nichos, si se sube a diario en varios a la vez, conviene repartir los canales en proyectos GCP distintos (cada uno con su propia cuota gratis de 10.000) en vez de pedir un aumento de cuota.
5. **Nicho "canciones infantiles" (segundo canal)**: requiere música y voz sin coste. Mitigación 100% gratis: melodías de dominio público (Twinkle Twinkle, Itsy Bitsy Spider, etc. — sin licencia que pagar, solo nueva grabación/arreglo propio) + TTS open-source local (Piper o Coqui TTS, sin API de pago) para voces, + animación 2D procedural simple (formas/personajes generados por código) en vez de animación con personajes con derechos de terceros.

## Arquitectura técnica

Monorepo con 3 piezas + compose en la raíz, todo dockerizado para desplegar en Dokploy (sin tocar labels de Traefik manualmente — los gestiona Dokploy):

```
/backend             FastAPI + Pydantic v2 + SQLAlchemy/Alembic (Postgres)
/frontend            Next.js App Router + Tailwind (dashboard)
/worker              Worker Python para render de audio/video con ffmpeg + CLI de pruebas
/docker-compose.yml  Orquestación de los 5 servicios (backend, frontend, worker, postgres, redis)
```

- **Postgres**: modelo multi-tenant interno — `niches`, `channels` (FK niche), `competitor_channels`/`competitor_videos` (FK niche), `title_templates` (FK niche), `video_projects` (FK channel), `channel_metrics` (FK channel).
- **Redis**: cola de jobs para el worker de render (evita bloquear la API con tareas de ffmpeg de minutos/horas). Pendiente de cablear en Fase 3+ (hoy el worker corre por CLI directo).
- Se omite MongoDB del stack por defecto: no hay datos no-estructurados que lo justifiquen todavía.

### Pipeline de contenido — arquitectura de plugin por nicho (Repository Pattern)

Interfaz común `NicheGenerator` (`worker/app/niches/base.py`) con 3 operaciones: `generate_audio()`, `generate_visual()`, `generate_metadata()`. El orquestador (`worker/app/render.py`) solo conoce la interfaz, no los detalles de cada nicho.

- **Plugin "ruido blanco / sonidos relax"** (`worker/app/niches/white_noise.py`, implementado): audio sintético con `numpy`/`scipy` (ruido filtrado por banda + envolvente de intensidad, loop sin costuras vía crossfade), visual procedural con `ffmpeg lavfi` (filtro `gradients`, semilla/colores variables por video).
- **Plugin "canciones infantiles"** (pendiente, Fase 5): melodías de dominio público + TTS open-source local + animación 2D procedural.
- **Render**: `ffmpeg` (`-stream_loop` sobre el audio + mux con el visual ya a duración completa), miniatura generada con `Pillow`.
- **Metadata**: por ahora plantilla estática por nicho/topic; se conectará al banco de patrones de título (Fase 3).
- **Publish**: pendiente (Fase 3) — YouTube Data API v3 (`videos.insert` + `thumbnails.set`), OAuth independiente por canal.

### Fases (roadmap)

**Fase 0 — Setup base** ✅: monorepo, docker-compose, FastAPI/Next.js, modelo de datos multi-canal/multi-nicho en Postgres (Alembic).

**Fase 1 — Motor de research** ✅: integración YouTube Data API (channels.list, playlistItems.list, videos.list), ingesta de canales de referencia por nicho, cálculo de patrones de título (n-gramas), endpoints `/research/*`.

**Fase 2 — Pipeline de generación (CLI)** ✅: interfaz `NicheGenerator`, plugin "ruido blanco", CLI (`worker/app/cli.py`) que renderiza un video de prueba end-to-end.

**Fase 3 — Metadata + Publish multi-canal** (pendiente): generador de título/descripción/hashtags desde el banco de patrones real, integración OAuth + subida a YouTube por canal, cola de publish (Redis) independiente por canal.

**Fase 4 — Dashboard completo** (pendiente): Next.js conectando todo — selector de canal/nicho, alta de canales desde la UI, elegir idea, revisar antes de publicar, calendario, métricas por canal (progreso hacia elegibilidad YPP).

**Fase 5 — Segundo canal + loop de crecimiento** (pendiente): plugin "canciones infantiles" para el segundo canal, refinamiento de plantillas con feedback de analytics, aplicar a YPP por canal en cuanto cumpla umbrales.

## Verificación de las fases entregadas

- Fase 0: `docker compose up` levanta backend (`/health` 200), frontend, Postgres con migraciones aplicadas — verificado.
- Fase 1: endpoints `/research/channels` (POST ingesta, GET listado), `/research/channels/{id}/videos`, `/research/niches/{id}/refresh-title-patterns` — verificado con datos simulados (n-gramas correctos); pendiente probar con una `YOUTUBE_API_KEY` real.
- Fase 2: `.mp4` reproducible (h264/aac), duración exacta al segundo objetivo, salto en el punto de loop del audio menor que el salto típico entre muestras (sin click audible), tamaño de archivo proporcional — verificado tanto en local como dentro del contenedor Docker del worker.
