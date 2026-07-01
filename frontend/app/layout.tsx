import type { Metadata } from "next";
import { Geist } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geist = Geist({ variable: "--font-geist", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AutomatizaciónYT",
  description: "Plataforma multi-canal de YouTube automatizado",
};

const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/channels", label: "Canales" },
  { href: "/studio", label: "Studio" },
  { href: "/studio/library", label: "↳ Biblioteca" },
  { href: "/studio/audio", label: "↳ Audio" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${geist.variable} h-full`}>
      <body className="flex h-full min-h-screen bg-zinc-950 text-zinc-100 antialiased">
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
        <main className="flex-1 overflow-auto">{children}</main>
      </body>
    </html>
  );
}
