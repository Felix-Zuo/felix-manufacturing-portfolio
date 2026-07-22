"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useSyncExternalStore } from "react";
import { Mail, Menu, X } from "lucide-react";

import { navigation } from "@/data/navigation";
import { profile } from "@/data/profile";

type Locale = "en" | "zh";

const LOCALE_STORAGE_KEY = "felix-portfolio-locale";
const LOCALE_CHANGE_EVENT = "felix-portfolio-locale-change";

const NAV_LABELS: Readonly<Record<string, Readonly<Record<Locale, string>>>> = {
  "#impact": { en: "Impact", zh: "成果" },
  "#project-map": { en: "Project Map", zh: "项目地图" },
  "#case-studies": { en: "Case Studies", zh: "案例研究" },
  "#portfolio-lab": { en: "Portfolio Lab", zh: "作品实验室" },
  "#methodology": { en: "Methodology", zh: "方法论" },
  "#about": { en: "About", zh: "关于" },
  "#contact": { en: "Contact", zh: "联系" },
};

const UI_COPY = {
  en: {
    brandMeta: "MFG · OPS · IMPROVEMENT",
    closeMenu: "Close menu",
    email: "Email",
    emailFelix: "Email Felix",
    mobileNavigation: "Mobile navigation",
    openMenu: "Open menu",
    primaryNavigation: "Primary navigation",
  },
  zh: {
    brandMeta: "制造 · 运营 · 改善",
    closeMenu: "关闭菜单",
    email: "发邮件",
    emailFelix: "给 Felix 发邮件",
    mobileNavigation: "移动端导航",
    openMenu: "打开菜单",
    primaryNavigation: "主导航",
  },
} as const;

function getLocaleSnapshot(): Locale {
  return window.localStorage.getItem(LOCALE_STORAGE_KEY) === "zh" ? "zh" : "en";
}

function getServerLocaleSnapshot(): Locale {
  return "en";
}

function subscribeToLocale(onStoreChange: () => void) {
  const handleChange = () => onStoreChange();
  window.addEventListener("storage", handleChange);
  window.addEventListener(LOCALE_CHANGE_EVENT, handleChange);

  return () => {
    window.removeEventListener("storage", handleChange);
    window.removeEventListener(LOCALE_CHANGE_EVENT, handleChange);
  };
}

export function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const locale = useSyncExternalStore(
    subscribeToLocale,
    getLocaleSnapshot,
    getServerLocaleSnapshot,
  );
  const copy = UI_COPY[locale];
  const immersive = pathname === "/";

  return (
    <header className={`${immersive ? "site-nav-immersive" : ""} site-nav fixed inset-x-0 top-0 z-40 border-b hairline bg-[#05080f]/85 backdrop-blur-md`}>
      <nav
        aria-label={copy.primaryNavigation}
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5"
      >
        <Link className="flex items-baseline gap-3" href="/" onClick={() => setOpen(false)}>
          <span className="font-semibold text-slate-100">Felix Zuo</span>
          <span className="mono-label hidden text-slate-500 sm:inline">{copy.brandMeta}</span>
        </Link>

        <div className="hidden items-center gap-7 lg:flex">
          {navigation.map((item) => (
            <a className="text-sm text-slate-400 transition-colors hover:text-slate-100" href={`/${item.href}`} key={item.href}>
              {NAV_LABELS[item.href]?.[locale] ?? item.label}
            </a>
          ))}
          <a
            className="inline-flex items-center gap-2 rounded-md bg-amber-400 px-3.5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
            href={`mailto:${profile.email}`}
          >
            <Mail className="h-4 w-4" aria-hidden="true" />
            {copy.email}
          </a>
        </div>

        <button
          aria-expanded={open}
          aria-label={open ? copy.closeMenu : copy.openMenu}
          className="rounded-md border hairline p-2 text-slate-300 lg:hidden"
          onClick={() => setOpen((v) => !v)}
          type="button"
        >
          {open ? <X className="h-5 w-5" aria-hidden="true" /> : <Menu className="h-5 w-5" aria-hidden="true" />}
        </button>
      </nav>

      {open && (
        <div
          aria-label={copy.mobileNavigation}
          className="border-t hairline bg-[#05080f]/95 px-5 pb-6 pt-3 lg:hidden"
        >
          <div className="flex flex-col gap-1">
            {navigation.map((item) => (
              <a
                className="rounded-md px-2 py-2.5 text-sm text-slate-300 transition-colors hover:bg-slate-800/50 hover:text-white"
                href={`/${item.href}`}
                key={item.href}
                onClick={() => setOpen(false)}
              >
                {NAV_LABELS[item.href]?.[locale] ?? item.label}
              </a>
            ))}
            <a
              className="mt-3 inline-flex w-fit items-center gap-2 rounded-md bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-950"
              href={`mailto:${profile.email}`}
              onClick={() => setOpen(false)}
            >
              <Mail className="h-4 w-4" aria-hidden="true" />
              {copy.emailFelix}
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
