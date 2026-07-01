"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type Channel = { id: number; display_name: string };

export default function NewStoryboardPage() {
  const router = useRouter();
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelId, setChannelId] = useState("");
  const [title, setTitle] = useState("");
  const [storyText, setStoryText] = useState("");
  const [prompts, setPrompts] = useState<string[]>([""]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/channels").then((r) => r.json()).then(setChannels);
  }, []);

  const autoSplit = () => {
    const lines = storyText
      .split(/\n|\.(?=\s)/)
      .map((l) => l.trim())
      .filter((l) => l.length > 10);
    if (lines.length > 0) setPrompts(lines);
  };

  const updatePrompt = (i: number, val: string) => {
    setPrompts((prev) => prev.map((p, idx) => (idx === i ? val : p)));
  };

  const addPrompt = () => setPrompts((prev) => [...prev, ""]);
  const removePrompt = (i: number) => setPrompts((prev) => prev.filter((_, idx) => idx !== i));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!channelId) return;
    setSaving(true);
    const res = await fetch("/api/storyboards", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel_id: parseInt(channelId),
        title,
        story_text: storyText,
        prompts: prompts
          .filter((p) => p.trim())
          .map((prompt_text, i) => ({ prompt_text, order: i })),
      }),
    });
    if (res.ok) {
      const sb = await res.json();
      router.push(`/studio/storyboard/${sb.id}`);
    }
    setSaving(false);
  };

  return (
    <div className="p-8 max-w-3xl">
      <h1 className="mb-2 text-2xl font-bold">Nuevo Storyboard</h1>
      <p className="mb-8 text-zinc-400">Escribe la historia de tu canción y divídela en escenas</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        <div className="grid grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-zinc-400">Canal</label>
            <select
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
              required
            >
              <option value="">Seleccionar canal...</option>
              {channels.map((c) => (
                <option key={c.id} value={c.id}>{c.display_name}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-zinc-400">Título de la canción</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="El Patito Pepe"
              className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
              required
            />
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-400">Historia / Descripción de la canción</label>
          <textarea
            value={storyText}
            onChange={(e) => setStoryText(e.target.value)}
            rows={5}
            placeholder="El patito Pepe vive en un estanque. Por las mañanas sale a nadar. Come pan que le tiran los niños. Por la noche vuelve a su nido."
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 resize-none"
          />
          <button
            type="button"
            onClick={autoSplit}
            className="self-end text-xs text-indigo-400 hover:text-indigo-300"
          >
            Auto-dividir en escenas ↓
          </button>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <label className="text-xs text-zinc-400">Prompts por escena (en inglés para mejor resultado)</label>
            <button
              type="button"
              onClick={addPrompt}
              className="text-xs text-indigo-400 hover:text-indigo-300"
            >
              + Añadir escena
            </button>
          </div>
          {prompts.map((p, i) => (
            <div key={i} className="flex gap-2 items-start">
              <span className="mt-2 text-xs text-zinc-500 w-5 shrink-0">{i + 1}</span>
              <textarea
                value={p}
                onChange={(e) => updatePrompt(i, e.target.value)}
                rows={2}
                placeholder={`cute cartoon duck swimming in a pond, sunny day, animation style`}
                className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 resize-none"
              />
              {prompts.length > 1 && (
                <button
                  type="button"
                  onClick={() => removePrompt(i)}
                  className="mt-2 text-zinc-500 hover:text-red-400 text-xs"
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        <button
          type="submit"
          disabled={saving}
          className="self-start rounded-lg bg-indigo-600 px-6 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
        >
          {saving ? "Guardando..." : "Crear Storyboard"}
        </button>
      </form>
    </div>
  );
}
