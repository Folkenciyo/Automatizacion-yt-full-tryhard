"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

type Clip = {
  id: number;
  status: string;
  file_path: string | null;
};

type Prompt = {
  id: number;
  order: number;
  prompt_text: string;
  clip_id: number | null;
  clip: Clip | null;
};

type Storyboard = {
  id: number;
  title: string;
  story_text: string;
  status: string;
  prompts: Prompt[];
};

const STATUS_COLOR: Record<string, string> = {
  queued: "text-yellow-400",
  generating: "text-blue-400 animate-pulse",
  ready: "text-green-400",
  failed: "text-red-400",
};

export default function StoryboardDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [sb, setSb] = useState<Storyboard | null>(null);
  const [generating, setGenerating] = useState<number | null>(null);
  const [syncing, setSyncing] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftText, setDraftText] = useState("");

  const fetchSb = async () => {
    const res = await fetch(`/api/storyboards/${id}`);
    if (res.ok) setSb(await res.json());
  };

  useEffect(() => {
    fetchSb();
    const interval = setInterval(fetchSb, 8000);
    return () => clearInterval(interval);
  }, [id]);

  const generateClip = async (promptId: number) => {
    setGenerating(promptId);
    await fetch(`/api/storyboards/${id}/prompts/${promptId}/generate`, { method: "POST" });
    await fetchSb();
    setGenerating(null);
  };

  const generateAll = async () => {
    if (!sb) return;
    for (const p of sb.prompts) {
      if (!p.clip_id) {
        await generateClip(p.id);
        await new Promise((r) => setTimeout(r, 500));
      }
    }
  };

  const syncClip = async (clipId: number, promptId: number) => {
    setSyncing(promptId);
    await fetch(`/api/clips/${clipId}/sync`, { method: "POST" });
    await fetchSb();
    setSyncing(null);
  };

  const startEditing = (p: Prompt) => {
    setEditingId(p.id);
    setDraftText(p.prompt_text);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setDraftText("");
  };

  const saveAndRegenerate = async (promptId: number) => {
    await fetch(`/api/storyboards/${id}/prompts/${promptId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt_text: draftText }),
    });
    setEditingId(null);
    setDraftText("");
    await generateClip(promptId);
  };

  if (!sb) return <div className="p-8 text-zinc-400">Cargando...</div>;

  const readyCount = sb.prompts.filter((p) => p.clip?.status === "ready").length;

  return (
    <div className="p-8 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">{sb.title}</h1>
        <p className="text-sm text-zinc-400 mt-1">{sb.story_text}</p>
        <p className="text-xs text-zinc-500 mt-2">
          {readyCount}/{sb.prompts.length} escenas listas
        </p>
      </div>

      <div className="mb-4 flex gap-3">
        <button
          onClick={generateAll}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500"
        >
          Generar todas las escenas
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {sb.prompts.map((p) => (
          <div key={p.id} className="rounded-xl border border-zinc-700 bg-zinc-900 p-4 flex gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-zinc-800 text-sm font-bold text-zinc-400">
              {p.order + 1}
            </div>

            <div className="flex-1 min-w-0">
              {editingId === p.id ? (
                <div className="mb-3 flex flex-col gap-2">
                  <textarea
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    rows={3}
                    className="w-full rounded-md border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
                    autoFocus
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => saveAndRegenerate(p.id)}
                      disabled={generating === p.id || !draftText.trim()}
                      className="rounded bg-indigo-600 px-3 py-1 text-xs font-medium hover:bg-indigo-500 disabled:opacity-50"
                    >
                      {generating === p.id ? "Enviando a pokemon..." : "Guardar y regenerar"}
                    </button>
                    <button
                      onClick={cancelEditing}
                      className="rounded bg-zinc-700 px-3 py-1 text-xs hover:bg-zinc-600"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mb-3 flex items-start justify-between gap-3">
                  <p className="text-sm text-zinc-300">{p.prompt_text}</p>
                  <button
                    onClick={() => startEditing(p)}
                    className="shrink-0 text-xs text-zinc-500 hover:text-zinc-300 hover:underline"
                  >
                    Editar
                  </button>
                </div>
              )}

              {p.clip ? (
                <div className="flex items-start gap-4">
                  {p.clip.status === "ready" && p.clip.file_path ? (
                    <video
                      src={`/api/clips/${p.clip.id}/preview`}
                      className="h-24 w-40 rounded object-cover bg-zinc-800"
                      controls
                      muted
                      loop
                    />
                  ) : (
                    <div className="flex h-24 w-40 items-center justify-center rounded bg-zinc-800 text-xs text-zinc-500">
                      {p.clip.status === "generating" ? "Generando..." : p.clip.status}
                    </div>
                  )}
                  <div className="flex flex-col gap-2">
                    <span className={`text-xs font-medium ${STATUS_COLOR[p.clip.status]}`}>
                      {p.clip.status}
                    </span>
                    {p.clip.status !== "ready" && p.clip.status !== "failed" && (
                      <button
                        onClick={() => syncClip(p.clip!.id, p.id)}
                        disabled={syncing === p.id}
                        className="rounded bg-zinc-700 px-3 py-1 text-xs hover:bg-zinc-600 disabled:opacity-50"
                      >
                        {syncing === p.id ? "Sincronizando..." : "Sincronizar"}
                      </button>
                    )}
                    {(p.clip.status === "ready" || p.clip.status === "failed") && (
                      <button
                        onClick={() => generateClip(p.id)}
                        disabled={generating === p.id}
                        className="rounded bg-zinc-700 px-3 py-1 text-xs hover:bg-zinc-600 disabled:opacity-50"
                      >
                        {generating === p.id ? "Enviando a pokemon..." : "Regenerar"}
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => generateClip(p.id)}
                  disabled={generating === p.id}
                  className="rounded bg-indigo-600/30 border border-indigo-600/50 px-3 py-1 text-xs text-indigo-300 hover:bg-indigo-600/50 disabled:opacity-50"
                >
                  {generating === p.id ? "Enviando a pokemon..." : "Generar clip"}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
