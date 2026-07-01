"use client";

import { useEffect, useRef, useState } from "react";

type AudioAsset = {
  id: number;
  title: string;
  source: string;
  duration_seconds: number | null;
  created_at: string;
};

export default function AudioPage() {
  const [assets, setAssets] = useState<AudioAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchAssets = async () => {
    const res = await fetch("/api/audio-assets");
    if (res.ok) setAssets(await res.json());
    setLoading(false);
  };

  useEffect(() => { fetchAssets(); }, []);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fileRef.current?.files?.[0] || !title) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("title", title);
    fd.append("file", fileRef.current.files[0]);
    await fetch("/api/audio-assets", { method: "POST", body: fd });
    setTitle("");
    if (fileRef.current) fileRef.current.value = "";
    await fetchAssets();
    setUploading(false);
  };

  const deleteAsset = async (id: number) => {
    if (!confirm("¿Eliminar este audio?")) return;
    await fetch(`/api/audio-assets/${id}`, { method: "DELETE" });
    await fetchAssets();
  };

  const fmtDuration = (s: number | null) => {
    if (!s) return "—";
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, "0")}`;
  };

  return (
    <div className="p-8">
      <h1 className="mb-2 text-2xl font-bold">Biblioteca de Audio</h1>
      <p className="mb-6 text-zinc-400">Importa canciones de Suno o cualquier MP3/WAV</p>

      <form onSubmit={handleUpload} className="mb-8 flex gap-3 items-end">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-400">Título</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="El Patito Pepe"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-zinc-400">Archivo (MP3 / WAV)</label>
          <input
            ref={fileRef}
            type="file"
            accept=".mp3,.wav,.m4a,.ogg"
            className="text-sm text-zinc-300"
            required
          />
        </div>
        <button
          type="submit"
          disabled={uploading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
        >
          {uploading ? "Subiendo..." : "Subir"}
        </button>
      </form>

      {loading ? (
        <div className="text-zinc-400">Cargando...</div>
      ) : assets.length === 0 ? (
        <div className="rounded-xl border border-dashed border-zinc-700 p-12 text-center text-zinc-500">
          No hay audios. Importa una canción de Suno para empezar.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {assets.map((a) => (
            <div key={a.id} className="flex items-center gap-4 rounded-xl border border-zinc-700 bg-zinc-900 p-4">
              <div className="text-2xl">🎵</div>
              <div className="flex-1">
                <p className="font-medium">{a.title}</p>
                <p className="text-xs text-zinc-500">{a.source} · {fmtDuration(a.duration_seconds)}</p>
              </div>
              <button
                onClick={() => deleteAsset(a.id)}
                className="rounded bg-red-900/40 px-3 py-1 text-xs text-red-400 hover:bg-red-900/70"
              >
                Eliminar
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
