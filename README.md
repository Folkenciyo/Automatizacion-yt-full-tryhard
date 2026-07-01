# Automatización YT

Plataforma multi-canal para generar y publicar videos de YouTube de forma automatizada (ruido blanco / sonidos relax como primer nicho, canciones infantiles como segundo), con research de competencia y banco de títulos.

Ver el plan completo y las decisiones de arquitectura en [`docs/PLAN.md`](docs/PLAN.md).

## Estructura

```
backend/    FastAPI + SQLAlchemy + Alembic — API, modelo de datos, research de competencia
frontend/   Next.js (App Router) + Tailwind — dashboard
worker/     Pipeline de generación (audio + visual + render con ffmpeg), CLI de pruebas
```

## Arranque rápido (Docker — recomendado)

```bash
cp .env.example .env          # edita YOUTUBE_API_KEY si vas a usar el research
docker compose up -d --build
docker compose exec backend uv run alembic upgrade head   # aplica el esquema la primera vez
```

- Backend: http://localhost:8000 (`/health`, `/niches`, `/channels`, `/research/*`)
- Frontend: http://localhost:3000
- Postgres y Redis quedan solo en la red interna de Docker (no se exponen al host, para no chocar con otros proyectos locales).

Para desplegar en Dokploy: apunta la app de tipo "Docker Compose" a este repo (usa el `docker-compose.yml` de la raíz). Dokploy gestiona las labels de Traefik automáticamente — no hace falta tocarlas.

## Desarrollo local sin Docker (backend + frontend)

Requiere Postgres accesible (puedes levantar solo ese servicio con `docker compose up -d postgres` y mapear el puerto que prefieras).

```bash
# backend
cd backend
uv sync
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:<puerto>/automation_yt" uv run alembic upgrade head
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:<puerto>/automation_yt" uv run uvicorn app.main:app --reload

# frontend (en otra terminal)
cd frontend
npm install
BACKEND_URL=http://localhost:8000 npm run dev
```

## Probar el pipeline de generación (worker) sin pasar por el dashboard

Renderiza un video de prueba end-to-end (audio sintético + visual procedural + mux) en segundos, sin necesitar la plataforma ni credenciales de YouTube:

```bash
cd worker
uv sync
uv run python -m app.cli --topic rain --duration 60 --seed 1 --output-dir ./output
```

`--topic` acepta `rain`, `ocean`, `garden_summer`, `white_noise`. El resultado queda en `./output/output.mp4` + `thumbnail.png`.

> Nota de escalado: para videos largos de producción (1-10 horas) el tiempo de render y el tamaño de archivo crecen proporcionalmente — valida primero con duraciones cortas (como en el ejemplo) antes de lanzar un render de varias horas.

## Research de canales de referencia (requiere `YOUTUBE_API_KEY`)

1. Crea una clave de API en Google Cloud Console con la "YouTube Data API v3" habilitada (cuota gratis: 10.000 unidades/día).
2. Crea un nicho: `POST /niches` con `{"slug": "white_noise", "name": "...", "generator_key": "white_noise"}`.
3. Ingresa un canal de referencia: `POST /research/channels` con `{"niche_id": 1, "youtube_channel_id": "UCxxxxxxxx"}`.
4. Genera el banco de patrones de título: `POST /research/niches/{niche_id}/refresh-title-patterns`.

## Roadmap

Ver fases completas en [`docs/PLAN.md`](docs/PLAN.md). Resumen del estado actual:

- [x] Fase 0 — Setup base (monorepo, Docker, modelo de datos multi-canal/multi-nicho)
- [x] Fase 1 — Motor de research (YouTube Data API, patrones de título)
- [x] Fase 2 — Pipeline de generación (plugin "ruido blanco" + CLI de render)
- [ ] Fase 3 — Metadata avanzada + publish automático a YouTube (OAuth)
- [ ] Fase 4 — Dashboard completo (elegir idea, revisar, calendario, métricas)
- [ ] Fase 5 — Segundo canal (canciones infantiles) + loop de crecimiento
