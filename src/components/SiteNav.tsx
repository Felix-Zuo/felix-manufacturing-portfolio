"use client";

import Link from "next/link";
import { useState } from "react";
import { Mail, Menu, X } from "lucide-react";

import { navigation } from "@/data/navigation";
import { profile } from "@/data/profile";

export function SiteNav() {
  const [open, setOpen] = useState(false);

  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b hairline bg-[#05080f]/85 backdrop-blur-md">
      <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
        <Link className="flex items-baseline gap-3" href="/" onClick={() => setOpen(false)}>
          <span className="font-semibold text-slate-100">Felix Zuo</span>
          <span className="mono-label hidden text-slate-500 sm:inline">MFG · OPS · IMPROVEMENT</span>
        </Link>

        <div className="hidden items-center gap-7 lg:flex">
          {navigation.map((item) => (
            <a className="text-sm text-slate-400 transition-colors hover:text-slate-100" href={`/${item.href}`} key={item.href}>
              {item.label}
            </a>
          ))}
          <a
            className="inline-flex items-center gap-2 rounded-md bg-amber-400 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
            href={`mailto:${profile.email}`}
          >
            <Mail className="h-4 w-4" aria-hidden="true" />
            Email
          </a>
        </div>

        <button
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          className="rounded-md border hairline p-2 text-slate-300 lg:hidden"
          onClick={() => setOpen((v) => !v)}
          type="button"
        >
          {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
        </button>
      </nav>

      {open && (
        <div className="border-t hairline bg-[#05080f]/95 px-5 pb-6 pt-3 lg:hidden">
          <div className="flex flex-col gap-1">
            {navigation.map((item) => (
              <a
                className="rounded-md px-2 py-2.5 text-sm text-slate-300 transition-colors hover:bg-slate-800/50 hover:text-white"
                href={`/${item.href}`}
                key={item.href}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            ))}
            <a
              className="mt-3 inline-flex w-fit items-center gap-2 rounded-md bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-950"
              href={`mailto:${profile.email}`}
              onClick={() => setOpen(false)}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              Email Felix
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
