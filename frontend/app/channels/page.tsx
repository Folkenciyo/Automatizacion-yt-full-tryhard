import Link from "next/link";
import { getChannels, getNiches } from "@/lib/api";

export default async function ChannelsPage() {
  const [channels, niches] = await Promise.all([getChannels(), getNiches()]);
  const nicheMap = Object.fromEntries((niches ?? []).map((n) => [n.id, n]));

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Canales</h1>
        <Link
          href="/channels/new"
          className="rounded bg-white px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-zinc-200"
        >
          + Nuevo canal
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
                  <p className="mt-0.5 text-xs text-zinc-500">
                    {niche?.name ?? `nicho ${ch.niche_id}`} · creado{" "}
                    {new Date(ch.created_at).toLocaleDateString("es-ES")}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  {ch.oauth_credentials_ref ? (
                    <span className="text-xs text-green-400">YouTube conectado</span>
                  ) : (
                    <span className="text-xs text-zinc-500">Sin YouTube</span>
                  )}
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
        <div className="rounded-lg border border-dashed border-zinc-700 p-12 text-center">
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
