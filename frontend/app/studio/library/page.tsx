"use client";

import { useEffect, useState } from "react";

type Clip = {
  id: number;
  prompt: string;
  status: "queued" | "generating" | "ready" | "failed";
  duration_seconds: number;
  created_at: string;
  storyboard_id: number | null;
  storyboard_title: string | null;
};

const STATUS_COLOR: Record<string, string> = {
  queued: "text-yellow-400",
  generating: "text-blue-400",
  ready: "text-green-400",
  failed: "text-red-400",
};

const STATUS_LABEL: Record<string, string> = {
  queued: "En cola",
  generating: "Generando...",
  ready: "Listo",
  failed: "Error",
};

export default function LibraryPage() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<number | null>(null);

  const fetchClips = async () => {
    const res = await fetch("/api/clips");
    if (res.ok) setClips(await res.json());
    setLoading(false);
  };

  useEffect(() => {
    fetchClips();
    const interval = setInterval(fetchClips, 10000);
    return () => clearInterval(interval);
  }, []);

  const syncClip = async (id: number) => {
    setSyncing(id);
    await fetch(`/api/clips/${id}/sync`, { method: "POST" });
    await fetchClips();
    setSyncing(null);
  };

  const deleteClip = async (id: number) => {
    if (!confirm("¿Eliminar este clip?")) return;
    await fetch(`/api/clips/${id}`, { method: "DELETE" });
    await fetchClips();
  };

  if (loading) return <div className="p-8 text-zinc-400">Cargando...</div>;

  const groups = new Map<string, { title: string; storyboardId: number | null; clips: Clip[] }>();
  for (const clip of clips) {
    const key = clip.storyboard_id != null ? String(clip.storyboard_id) : "none";
    if (!groups.has(key)) {
      groups.set(key, {
        title: clip.storyboard_title ?? "Sin storyboard",
        storyboardId: clip.storyboard_id,
        clips: [],
      });
    }
    groups.get(key)!.clips.push(clip);
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Biblioteca de Clips</h1>
          <p className="text-sm text-zinc-400">{clips.length} clips totales</p>
        </div>
        <a
          href="/studio/storyboard/new"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500"
        >
          + Nuevo Storyboard
        </a>
      </div>

      {clips.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-700 p-12 text-center text-zinc-500">
          No hay clips aún. Crea un storyboard para empezar.
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {[...groups.values()].map((group) => (
            <div key={group.title + group.storyboardId}>
              <div className="mb-3 flex items-center gap-2">
                {group.storyboardId != null ? (
                  <a
                    href={`/studio/storyboard/${group.storyboardId}`}
                    className="text-sm font-semibold text-zinc-200 hover:text-white hover:underline"
                  >
                    {group.title}
                  </a>
                ) : (
                  <span className="text-sm font-semibold text-zinc-500">{group.title}</span>
                )}
                <span className="text-xs text-zinc-600">{group.clips.length} clips</span>
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {group.clips.map((clip) => (
                  <div key={clip.id} className="rounded-xl border border-zinc-700 bg-zinc-900 overflow-hidden">
                    {clip.status === "ready" ? (
                      <video
                        src={`/api/clips/${clip.id}/preview`}
                        className="h-40 w-full object-cover bg-zinc-800"
                        controls
                        muted
                        loop
                      />
                    ) : (
                      <div className="flex h-40 items-center justify-center bg-zinc-800 text-zinc-500 text-sm">
                        {STATUS_LABEL[clip.status]}
                      </div>
                    )}
                    <div className="p-4">
                      <p className="text-sm text-zinc-300 line-clamp-2 mb-2">{clip.prompt}</p>
                      <div className="flex items-center justify-between">
                        <span className={`text-xs font-medium ${STATUS_COLOR[clip.status]}`}>
                          {STATUS_LABEL[clip.status]}
                        </span>
                        <span className="text-xs text-zinc-500">{clip.duration_seconds}s</span>
                      </div>
                      <div className="mt-3 flex gap-2">
                        {clip.status !== "ready" && clip.status !== "failed" && (
                          <button
                            onClick={() => syncClip(clip.id)}
                            disabled={syncing === clip.id}
                            className="flex-1 rounded bg-zinc-700 px-2 py-1 text-xs hover:bg-zinc-600 disabled:opacity-50"
                          >
                            {syncing === clip.id ? "Sincronizando..." : "Sincronizar"}
                          </button>
                        )}
                        <button
                          onClick={() => deleteClip(clip.id)}
                          className="rounded bg-red-900/40 px-2 py-1 text-xs text-red-400 hover:bg-red-900/70"
                        >
                          Eliminar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
