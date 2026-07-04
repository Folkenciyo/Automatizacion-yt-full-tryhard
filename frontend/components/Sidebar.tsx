"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/channels", label: "Canales" },
  { href: "/studio", label: "Studio" },
  { href: "/studio/library", label: "↳ Biblioteca" },
  { href: "/studio/audio", label: "↳ Audio" },
];

export default function Sidebar() {
  const pathname = usePathname();
  if (pathname === "/login") return null;

  return (
    <aside className="flex w-52 shrink-0 flex-col border-r border-zinc-800 bg-zinc-900 px-4 py-6">
      <p className="mb-8 text-xs font-semibold uppercase tracking-widest text-zinc-500">
        AutoYT
      </p>
      <nav className="flex flex-col gap-1">
        {NAV.map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            className="rounded-md px-3 py-2 text-sm text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white"
          >
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
