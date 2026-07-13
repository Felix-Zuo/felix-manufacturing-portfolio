"use client";

import { ShieldCheck } from "lucide-react";
import { usePathname } from "next/navigation";

import { navigation } from "@/data/navigation";
import { profile } from "@/data/profile";

export function SiteFooter() {
  const pathname = usePathname();

  if (pathname === "/") return null;

  return (
    <footer className="site-footer border-t hairline bg-[#04060c]">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-[1.3fr_0.7fr_1fr]">
        <div>
          <p className="font-semibold text-slate-100">Felix Zuo</p>
          <p className="mono-label mt-2 text-slate-500">{profile.headline}</p>
          <p className="mt-5 max-w-sm text-sm leading-6 text-slate-400">
            Manufacturing project coordination and process improvement, backed by public
            synthetic-data tooling evidence.
          </p>
        </div>
        <nav aria-label="Footer">
          <p className="mono-label text-slate-500">Site</p>
          <ul className="mt-4 space-y-2.5">
            {navigation.map((item) => (
              <li key={item.href}>
                <a className="text-sm text-slate-400 transition-colors hover:text-slate-100" href={`/${item.href}`}>
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div>
          <p className="mono-label text-slate-500">Contact</p>
          <ul className="mt-4 space-y-2.5 text-sm">
            <li>
              <a className="text-slate-400 transition-colors hover:text-slate-100" href={`mailto:${profile.email}`}>
                {profile.email}
              </a>
            </li>
            <li>
              <a
                className="text-slate-400 transition-colors hover:text-slate-100"
                href={profile.github}
                rel="noreferrer"
                target="_blank"
              >
                github.com/Felix-Zuo
              </a>
            </li>
          </ul>
          <p className="mono-label mt-6 flex items-center gap-2 text-emerald-400/80">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            Synthetic data only
          </p>
        </div>
      </div>
      <div className="border-t hairline">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-5">
          <p className="text-xs text-slate-600">© {new Date().getFullYear()} Felix Zuo. All public demos use sanitized or synthetic data.</p>
          <p className="mono-label text-slate-600">Next.js · Vercel-ready</p>
        </div>
      </div>
    </footer>
  );
}
