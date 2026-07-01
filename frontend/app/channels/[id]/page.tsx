import Link from "next/link";
import { getChannel, getChannelProjects, getNiches, getOAuthStatus } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  idea: "bg-zinc-800 text-zinc-300",
  rendering: "bg-yellow-900/60 text-yellow-300",
  review: "bg-purple-900/60 text-purple-300",
  scheduled: "bg-cyan-900/60 text-cyan-300",
  published: "bg-green-900/60 text-green-300",
  failed: "bg-red-900/60 text-red-400",
};

const YPP_TIER1 = { subs: 500, hours: 3000 };
const YPP_FULL = { subs: 1000, hours: 4000 };

export default async function ChannelPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const channelId = Number(id);

  const [channel, projects, niches, oauth] = await Promise.all([
    getChannel(channelId),
    getChannelProjects(channelId),
    getNiches(),
    getOAuthStatus(channelId),
  ]);

  if (!channel) return <div className="p-8 text-zinc-400">Canal no encontrado.</div>;

  const niche = (niches ?? []).find((n) => n.id === channel.niche_id);
  const published = (projects ?? []).filter((p) => p.status === "published").length;

  return (
    <div className="p-8">
      <div className="mb-2 flex items-center gap-2 text-xs text-zinc-500">
        <Link href="/channels" className="hover:text-zinc-300">Canales</Link>
        <span>/</span>
        <span>{channel.display_name}</span>
      </div>

      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{channel.display_name}</h1>
          <p className="mt-1 text-sm text-zinc-500">{niche?.name ?? `nicho ${channel.niche_id}`}</p>
        </div>
        <div className="flex gap-2">
          {!oauth?.connected && (
            <a
              href={`http://localhost:8000/channels/${channelId}/oauth/start`}
              className="rounded border border-yellow-700 px-3 py-1.5 text-xs text-yellow-400 hover:bg-yellow-900/30 transition-colors"
            >
              Conectar YouTube
            </a>
          )}
          {oauth?.connected && (
            <span className="rounded border border-green-800 px-3 py-1.5 text-xs text-green-400">
              YouTube conectado
            </span>
          )}
          <Link
            href={`/channels/${channelId}/new-video`}
            className="rounded bg-white px-3 py-1.5 text-xs font-medium text-black hover:bg-zinc-200 transition-colors"
          >
            + Nuevo video
          </Link>
        </div>
      </div>

      {/* YPP Progress */}
      <div className="mb-8 grid grid-cols-2 gap-4">
        {[
          { label: "Tier 1 YPP", subs: YPP_TIER1.subs, hours: YPP_TIER1.hours },
          { label: "YPP completo", subs: YPP_FULL.subs, hours: YPP_FULL.hours },
        ].map(({ label, subs, hours }) => (
          <div key={label} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <p className="mb-3 text-xs font-medium text-zinc-400">{label}</p>
            <div className="mb-2">
              <div className="mb-1 flex justify-between text-xs text-zinc-500">
                <span>Suscriptores</span><span>0 / {subs}</span>
              </div>
              <div className="h-1.5 rounded-full bg-zinc-800">
                <div className="h-1.5 rounded-full bg-zinc-500" style={{ width: "0%" }} />
              </div>
            </div>
            <div>
              <div className="mb-1 flex justify-between text-xs text-zinc-500">
                <span>Horas vistas</span><span>0 / {hours}h</span>
              </div>
              <div className="h-1.5 rounded-full bg-zinc-800">
                <div className="h-1.5 rounded-full bg-zinc-500" style={{ width: "0%" }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Stats row */}
      <div className="mb-6 flex gap-4">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3">
          <p className="text-xs text-zinc-500">Videos publicados</p>
          <p className="text-2xl font-semibold">{published}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3">
          <p className="text-xs text-zinc-500">Total proyectos</p>
          <p className="text-2xl font-semibold">{(projects ?? []).length}</p>
        </div>
      </div>

      {/* Video projects */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-400">Proyectos de video</h2>
      </div>

      {projects && projects.length > 0 ? (
        <div className="flex flex-col gap-2">
          {[...projects].reverse().map((p) => (
            <Link
              key={p.id}
              href={`/video-projects/${p.id}`}
              className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-3 hover:border-zinc-600 transition-colors"
            >
              <div>
                <p className="text-sm font-medium">{p.title ?? "Sin título"}</p>
                <p className="mt-0.5 text-xs text-zinc-500">
                  {new Date(p.created_at).toLocaleDateString("es-ES")}
                  {p.youtube_video_id && ` · YT: ${p.youtube_video_id}`}
                </p>
              </div>
              <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[p.status] ?? "bg-zinc-800 text-zinc-400"}`}>
                {p.status}
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-dashed border-zinc-700 p-10 text-center">
          <p className="text-zinc-500">Sin proyectos todavía.</p>
          <Link
            href={`/channels/${channelId}/new-video`}
            className="mt-3 inline-block rounded bg-white px-4 py-2 text-sm font-medium text-black hover:bg-zinc-200 transition-colors"
          >
            Crear primer video
          </Link>
        </div>
      )}
    </div>
  );
}
