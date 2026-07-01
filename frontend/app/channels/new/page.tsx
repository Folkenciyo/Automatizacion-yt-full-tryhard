"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const NICHES = [
  { id: 1, label: "Ruido blanco para bebés", generator_key: "white_noise" },
];

export default function NewChannelPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [nicheId, setNicheId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/channels", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ niche_id: nicheId, display_name: name.trim() }),
      });
      if (!res.ok) throw new Error("Error al crear el canal");
      const channel = await res.json();
      router.push(`/channels/${channel.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      setLoading(false);
    }
  }

  return (
    <div className="p-8">
      <h1 className="mb-6 text-2xl font-semibold">Nuevo canal</h1>
      <form onSubmit={handleSubmit} className="flex max-w-md flex-col gap-5">
        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">Nombre del canal</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ej: Ruido Blanco Bebés"
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white placeholder-zinc-600 focus:border-zinc-500 focus:outline-none"
            required
          />
        </div>
        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">Nicho</label>
          <select
            value={nicheId}
            onChange={(e) => setNicheId(Number(e.target.value))}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
          >
            {NICHES.map((n) => (
              <option key={n.id} value={n.id}>
                {n.label}
              </option>
            ))}
          </select>
        </div>
        {error && <p className="text-sm text-red-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200 disabled:opacity-50"
        >
          {loading ? "Creando..." : "Crear canal"}
        </button>
      </form>
    </div>
  );
}
