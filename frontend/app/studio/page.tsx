"use client";

import Link from "next/link";

export default function StudioPage() {
  return (
    <div className="p-8">
      <h1 className="mb-2 text-2xl font-bold">Studio</h1>
      <p className="mb-8 text-zinc-400">Crea canciones infantiles con video IA + audio</p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Link
          href="/studio/storyboard/new"
          className="flex flex-col gap-2 rounded-xl border border-zinc-700 bg-zinc-900 p-6 hover:border-indigo-500 transition-colors"
        >
          <span className="text-2xl">✏️</span>
          <span className="font-semibold">Nuevo Storyboard</span>
          <span className="text-sm text-zinc-400">Escribe la historia, divídela en escenas y genera los clips</span>
        </Link>

        <Link
          href="/studio/library"
          className="flex flex-col gap-2 rounded-xl border border-zinc-700 bg-zinc-900 p-6 hover:border-indigo-500 transition-colors"
        >
          <span className="text-2xl">🎬</span>
          <span className="font-semibold">Biblioteca de Clips</span>
          <span className="text-sm text-zinc-400">Todos los clips IA generados, listos para usar</span>
        </Link>

        <Link
          href="/studio/audio"
          className="flex flex-col gap-2 rounded-xl border border-zinc-700 bg-zinc-900 p-6 hover:border-indigo-500 transition-colors"
        >
          <span className="text-2xl">🎵</span>
          <span className="font-semibold">Biblioteca de Audio</span>
          <span className="text-sm text-zinc-400">Importa canciones de Suno o genera con MusicGen</span>
        </Link>
      </div>
    </div>
  );
}
