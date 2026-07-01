"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import type { VideoProject } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  idea: "bg-zinc-800 text-zinc-300",
  rendering: "bg-yellow-900/60 text-yellow-300",
  review: "bg-purple-900/60 text-purple-300",
  scheduled: "bg-cyan-900/60 text-cyan-300",
  published: "bg-green-900/60 text-green-300",
  failed: "bg-red-900/60 text-red-400",
};

function estimateTotalSeconds(project: VideoProject): number {
  if (project.title?.includes("10 Hora")) return 18000;
  if (project.title?.includes("5 Hora")) return 9000;
  if (project.title?.includes("2 Hora")) return 3600;
  if (project.title?.includes("1 Hora")) return 1800;
  return 60;
}

function useElapsed(sinceIso: string | null) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!sinceIso) return;
    const update = () => setElapsed(Math.floor((Date.now() - new Date(sinceIso).getTime()) / 1000));
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, [sinceIso]);
  return elapsed;
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function DeleteModal({ onConfirm, onCancel, loading }: { onConfirm: () => void; onCancel: () => void; loading: boolean }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="w-full max-w-sm rounded-xl border border-zinc-700 bg-zinc-900 p-6">
        <h2 className="mb-2 text-base font-semibold">¿Eliminar este proyecto?</h2>
        <p className="mb-6 text-sm text-zinc-400">
          Se borrarán el video, la miniatura y todos los archivos generados. Esta acción no se puede deshacer.
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="rounded px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="rounded bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
          >
            {loading ? "Eliminando..." : "Sí, eliminar"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function VideoProjectPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<VideoProject | null>(null);
  const [renderStartedAt, setRenderStartedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [realProgress, setRealProgress] = useState<{ pct: number; step: string } | null>(null);
  const elapsed = useElapsed(renderStartedAt);

  const fetchProject = useCallback(async () => {
    const res = await fetch(`/api/video-projects/${id}`);
    if (!res.ok) return;
    const data: VideoProject = await res.json();
    setProject(data);
    if (data.status === "rendering" && !renderStartedAt) {
      setRenderStartedAt(data.updated_at);
    }
  }, [id, renderStartedAt]);

  useEffect(() => { fetchProject(); }, [fetchProject]);

  useEffect(() => {
    if (!project) return;
    if (!["rendering", "scheduled"].includes(project.status)) return;
    const t = setInterval(fetchProject, 5000);
    return () => clearInterval(t);
  }, [project, fetchProject]);

  useEffect(() => {
    if (project?.status !== "rendering") return;
    const es = new EventSource(`/api/video-projects/${id}/progress`);
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data) as { pct: number; step: string };
        setRealProgress(data);
        if (data.step === "done" || data.step === "failed") {
          es.close();
          fetchProject();
        }
      } catch { /* ignore */ }
    };
    es.onerror = () => es.close();
    return () => es.close();
  }, [project?.status, id, fetchProject]);

  async function handlePublish() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/video-projects/${id}/publish`, { method: "POST" });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? "Error al publicar");
      }
      await fetchProject();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await fetch(`/api/video-projects/${id}`, { method: "DELETE" });
      router.push(`/channels/${project?.channel_id}`);
    } catch {
      setDeleting(false);
      setShowDeleteModal(false);
    }
  }

  if (!project) return <div className="p-8 text-zinc-500">Cargando...</div>;

  const estimatedTotal = estimateTotalSeconds(project);
  const progressPct = realProgress?.pct
    ?? (project.status === "rendering" ? Math.min(Math.round((elapsed / estimatedTotal) * 100), 10) : 100);

  const STEP_LABELS: Record<string, string> = {
    starting: "Iniciando...", audio: "Generando audio...", visual: "Generando visual...",
    mux: "Mezclando audio y video...", thumbnail: "Creando miniatura...",
    done: "Completado", failed: "Error",
  };

  const hasMedia = ["review", "scheduled", "published"].includes(project.status);

  return (
    <>
      {showDeleteModal && (
        <DeleteModal
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteModal(false)}
          loading={deleting}
        />
      )}

      <div className="p-8">
        <div className="mb-2 flex gap-2 text-xs text-zinc-500">
          <Link href={`/channels/${project.channel_id}`} className="hover:text-zinc-300">
            Canal {project.channel_id}
          </Link>
          <span>/</span>
          <span>Proyecto #{project.id}</span>
        </div>

        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold">{project.title ?? "Sin título"}</h1>
            <p className="mt-1 text-xs text-zinc-500">
              Creado {new Date(project.created_at).toLocaleString("es-ES")}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`rounded-full px-3 py-1 text-xs font-medium ${STATUS_STYLE[project.status] ?? "bg-zinc-800 text-zinc-400"}`}>
              {project.status}
            </span>
            <button
              onClick={() => setShowDeleteModal(true)}
              className="rounded p-1.5 text-zinc-600 hover:bg-zinc-800 hover:text-red-400"
              title="Eliminar proyecto"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Video + miniatura */}
        {hasMedia && (
          <div className="mb-6 flex gap-4">
            <div className="flex-1 overflow-hidden rounded-lg border border-zinc-800 bg-black">
              <video
                controls
                className="w-full"
                src={`/api/video-projects/${id}/preview`}
                preload="metadata"
              />
            </div>
            <div className="w-48 flex-shrink-0">
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-zinc-500">Miniatura</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`/api/video-projects/${id}/thumbnail`}
                alt="Miniatura del video"
                className="w-full rounded-lg border border-zinc-800 object-cover"
              />
            </div>
          </div>
        )}

        <div className="mb-6 flex flex-col gap-3">
          {project.status === "rendering" && (
            <div className="rounded-lg border border-yellow-800/50 bg-yellow-900/20 p-5">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-medium text-yellow-300">
                {realProgress ? (STEP_LABELS[realProgress.step] ?? "Procesando...") : "Renderizando..."}
              </p>
                <p className="text-xs text-yellow-500">{formatTime(elapsed)} transcurrido</p>
              </div>
              <div className="relative mb-2 h-2 overflow-hidden rounded-full bg-yellow-900/50">
                <div
                  className="h-full rounded-full bg-yellow-400 transition-all duration-1000"
                  style={{ width: `${progressPct}%` }}
                />
                <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-yellow-300/20 to-transparent" />
              </div>
              <div className="flex justify-between text-xs text-yellow-600">
                <span>{progressPct}%</span>
                <span>~{formatTime(Math.max(0, estimatedTotal - elapsed))} restante (estimado)</span>
              </div>
              <p className="mt-3 text-xs text-yellow-600">
                La página se actualiza automáticamente cada 5 segundos.
              </p>
            </div>
          )}

          {project.status === "review" && (
            <div className="rounded-lg border border-purple-800/50 bg-purple-900/20 p-5">
              <p className="mb-3 text-sm font-medium text-purple-300">
                Video listo — revisa el video y la miniatura antes de publicar.
              </p>
              {error && <p className="mb-3 text-sm text-red-400">{error}</p>}
              <button
                onClick={handlePublish}
                disabled={loading}
                className="rounded bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200 disabled:opacity-50"
              >
                {loading ? "Publicando..." : "Publicar en YouTube"}
              </button>
            </div>
          )}

          {project.status === "scheduled" && (
            <div className="rounded-lg border border-cyan-800/50 bg-cyan-900/20 p-5">
              <div className="mb-2 flex items-center gap-2">
                <div className="h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
                <p className="text-sm text-cyan-300">Subiendo a YouTube...</p>
              </div>
              <p className="text-xs text-cyan-600">Esto puede tardar unos minutos según el tamaño del archivo.</p>
            </div>
          )}

          {project.status === "published" && project.youtube_video_id && (
            <div className="rounded-lg border border-green-800/50 bg-green-900/20 p-5">
              <p className="mb-2 text-sm font-medium text-green-300">Publicado en YouTube.</p>
              <a
                href={`https://www.youtube.com/watch?v=${project.youtube_video_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-green-400 underline hover:text-green-300"
              >
                Ver en YouTube →
              </a>
            </div>
          )}

          {project.status === "failed" && (
            <div className="rounded-lg border border-red-800/50 bg-red-900/20 p-5">
              <p className="mb-3 text-sm text-red-400">El render falló.</p>
              <Link
                href={`/channels/${project.channel_id}/new-video`}
                className="rounded bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-600"
              >
                Crear nuevo proyecto
              </Link>
            </div>
          )}
        </div>

        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-5">
          <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">Metadata</h2>
          <p className="mb-2 font-medium">{project.title}</p>
          <p className="whitespace-pre-line text-xs text-zinc-400">{project.description}</p>
          {project.hashtags && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {project.hashtags.split(",").map((tag) => (
                <span key={tag.trim()} className="rounded-full bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
                  #{tag.trim()}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
