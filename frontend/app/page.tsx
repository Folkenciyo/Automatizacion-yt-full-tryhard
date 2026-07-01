import Link from "next/link";
import { getChannels, getHealth, getNiches } from "@/lib/api";

export default async function Home() {
  const [health, channels, niches] = await Promise.all([getHealth(), getChannels(), getNiches()]);
  const nicheMap = Object.fromEntries((niches ?? []).map((n) => [n.id, n]));

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Panel de control</h1>
          <p className="mt-1 text-sm text-zinc-400">Plataforma multi-canal de YouTube automatizado</p>
        </div>
        <span
          className={`flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${
            health ? "bg-green-900/50 text-green-400" : "bg-red-900/50 text-red-400"
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${health ? "bg-green-400" : "bg-red-400"}`} />
          {health ? "Backend conectado" : "Backend sin conexión"}
        </span>
      </div>

      <div className="mb-8 grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">Canales activos</p>
          <p className="mt-1 text-3xl font-semibold">
            {(channels ?? []).filter((c) => c.status === "active").length}
          </p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">Nichos</p>
          <p className="mt-1 text-3xl font-semibold">{(niches ?? []).length}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
          <p className="text-xs text-zinc-500">Acceso rápido</p>
          <Link
            href="/channels/new"
            className="mt-2 inline-block rounded bg-white px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-zinc-200"
          >
            + Nuevo canal
          </Link>
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-400">Canales</h2>
        <Link href="/channels" className="text-xs text-zinc-500 hover:text-zinc-300">
          Ver todos →
        </Link>
      </div>

      {channels && channels.length > 0 ? (
        <div className="flex flex-col gap-3">
          {channels.map((ch) => {
            const niche = nicheMap[ch.niche_id];
            return (
              <Link
                key={ch.id}
                href={`/channels/${ch.id}`}
                className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-5 py-4 transition-colors hover:border-zinc-600"
              >
                <div>
                  <p className="font-medium">{ch.display_name}</p>
                  <p className="mt-0.5 text-xs text-zinc-500">{niche?.name ?? `nicho ${ch.niche_id}`}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs ${
                      ch.status === "active" ? "bg-green-900/50 text-green-400" : "bg-zinc-800 text-zinc-400"
                    }`}
                  >
                    {ch.status}
                  </span>
                  <span className="text-zinc-600">→</span>
                </div>
              </Link>
            );
          })}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-zinc-700 p-10 text-center">
          <p className="text-zinc-400">Sin canales todavía.</p>
          <Link
            href="/channels/new"
            className="mt-3 inline-block rounded bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200"
          >
            Crear el primer canal
          </Link>
        </div>
      )}
    </div>
  );
}
