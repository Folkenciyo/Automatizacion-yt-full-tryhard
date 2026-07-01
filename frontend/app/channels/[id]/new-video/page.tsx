"use client";

import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

const TOPICS = [
  // --- Ruidos de color ---
  { value: "white_noise",  label: "Ruido Blanco Puro" },
  { value: "pink_noise",   label: "Ruido Rosa" },
  { value: "brown_noise",  label: "Ruido Marrón" },
  { value: "deep_sleep",   label: "Sueño Profundo (NUEVO)" },
  // --- Naturaleza ---
  { value: "rain",         label: "Lluvia" },
  { value: "ocean",        label: "Olas del Mar" },
  { value: "thunderstorm", label: "Tormenta con Lluvia" },
  { value: "garden_summer",label: "Jardín de Verano" },
  { value: "fireplace",    label: "Chimenea" },
  { value: "shower",       label: "Ducha" },
  // --- Bebé ---
  { value: "womb",         label: "Sonido de Útero" },
  { value: "heartbeat",    label: "Latido de Corazón" },
  // --- Ambiente ---
  { value: "fan",          label: "Ventilador" },
  // --- Mezclas ---
  { value: "rain+fireplace:0.6",    label: "Lluvia + Chimenea" },
  { value: "ocean+rain:0.5",        label: "Mar + Lluvia" },
  { value: "brown_noise+rain:0.5",  label: "Ruido Marrón + Lluvia" },
  { value: "heartbeat+womb:0.5",    label: "Latido + Útero" },
  { value: "deep_sleep+ocean:0.7",  label: "Sueño Profundo + Mar" },
  { value: "rain+thunderstorm:0.6", label: "Lluvia + Tormenta" },
];

const VISUAL_STYLES = [
  { value: "gradient", label: "Gradiente (rápido)" },
  { value: "plasma",   label: "Plasma psicodélico" },
  { value: "waves",    label: "Ondas de agua" },
  { value: "aurora",   label: "Aurora Boreal" },
  { value: "ai",       label: "Video IA en bucle (HuggingFace)" },
];

// YouTube limit: unverified channels → max 15 min. Keep longer options for when verified.
const DURATIONS = [
  { value: 899,   label: "14:59 min (canal sin verificar)" },
  { value: 60,    label: "1 minuto (prueba)" },
  { value: 3600,  label: "1 hora (requiere verificación)" },
  { value: 7200,  label: "2 horas (requiere verificación)" },
  { value: 18000, label: "5 horas (requiere verificación)" },
  { value: 36000, label: "10 horas (requiere verificación)" },
  { value: -1,    label: "Personalizado..." },
];

export default function NewVideoPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [topic, setTopic] = useState("rain");
  const [visualStyle, setVisualStyle] = useState("gradient");
  const [duration, setDuration] = useState(899);
  const [customMin, setCustomMin] = useState("14");
  const [customSec, setCustomSec] = useState("59");
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 1000));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCustom = duration === -1;
  const effectiveDuration = isCustom
    ? Math.max(1, (parseInt(customMin) || 0) * 60 + (parseInt(customSec) || 0))
    : duration;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      // 1. Crear proyecto
      const res = await fetch(`/api/channels/${id}/new-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, duration_seconds: effectiveDuration, seed, visual_style: visualStyle }),
      });
      if (!res.ok) throw new Error("Error al crear el proyecto");
      const project = await res.json();

      // 2. Encolar render inmediatamente
      await fetch(`/api/video-projects/${project.id}/render`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, duration_seconds: effectiveDuration, seed, visual_style: visualStyle }),
      });

      router.push(`/video-projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      setLoading(false);
    }
  }

  return (
    <div className="p-8">
      <div className="mb-2 flex gap-2 text-xs text-zinc-500">
        <span>Canales</span><span>/</span>
        <span>Canal {id}</span><span>/</span>
        <span>Nuevo video</span>
      </div>
      <h1 className="mb-6 text-2xl font-semibold">Nuevo video</h1>

      <form onSubmit={handleSubmit} className="flex max-w-md flex-col gap-5">
        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">Sonido</label>
          <select
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
          >
            {TOPICS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">Animación visual</label>
          <select
            value={visualStyle}
            onChange={(e) => setVisualStyle(e.target.value)}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
          >
            {VISUAL_STYLES.map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
          </select>
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">Duración</label>
          <select
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
          >
            {DURATIONS.map((d) => <option key={d.value} value={d.value}>{d.label}</option>)}
          </select>
          {isCustom && (
            <div className="mt-2 flex items-center gap-2">
              <input
                type="number"
                min={0}
                max={1440}
                value={customMin}
                onChange={(e) => setCustomMin(e.target.value)}
                className="w-24 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
                placeholder="min"
              />
              <span className="text-zinc-500">:</span>
              <input
                type="number"
                min={0}
                max={59}
                value={customSec}
                onChange={(e) => setCustomSec(e.target.value)}
                className="w-20 rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
                placeholder="seg"
              />
              <span className="text-xs text-zinc-500">
                = {effectiveDuration}s
              </span>
            </div>
          )}
        </div>

        <div>
          <label className="mb-1.5 block text-sm text-zinc-400">
            Semilla visual <span className="text-zinc-600">(determina colores y variación)</span>
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              className="w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:border-zinc-500 focus:outline-none"
            />
            <button
              type="button"
              onClick={() => setSeed(Math.floor(Math.random() * 9999))}
              className="rounded border border-zinc-700 px-3 py-2 text-xs text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors"
            >
              Aleatorio
            </button>
          </div>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200 disabled:opacity-50"
        >
          {loading ? "Creando y encolando render..." : "Crear y renderizar"}
        </button>
      </form>
    </div>
  );
}
