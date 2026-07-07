"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BRAND,
  COMPANY_LEGAL,
  COMPANY_SHORT,
  COPYRIGHT_NOTICE,
  PRODUCT,
  TAGLINE,
} from "@/lib/branding";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/trips", label: "Trips" },
  { href: "/fleet", label: "Fleet" },
  { href: "/maintenance", label: "Maintenance" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-road-border bg-black/20 px-5 py-8">
      <div className="mb-10">
        <p className="text-xs uppercase tracking-[0.35em] text-road-amber">{COMPANY_SHORT}</p>
        <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-road-muted">
          {COMPANY_LEGAL}
        </p>
        <h1 className="mt-4 font-display text-3xl text-white">{PRODUCT}</h1>
        <p className="mt-1 text-sm text-road-amber/90">by {BRAND}</p>
        <p className="mt-2 text-sm text-road-muted">{TAGLINE}</p>
      </div>

      <nav className="space-y-2">
        {links.map((link) => {
          const active = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`block rounded-lg px-4 py-3 text-sm transition ${
                active
                  ? "bg-road-amber/15 font-semibold text-road-amber"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto space-y-3">
        <div className="rounded-xl border border-road-border bg-road-panel p-4 text-xs text-road-muted">
          API: {process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"}
        </div>
        <p className="px-1 text-[10px] leading-relaxed text-road-muted/80">{COPYRIGHT_NOTICE}</p>
      </div>
    </aside>
  );
}