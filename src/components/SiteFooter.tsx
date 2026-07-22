"use client";

import { ShieldCheck } from "lucide-react";
import { usePathname } from "next/navigation";
import { useSyncExternalStore } from "react";

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
    contact: "Contact",
    copyright: (year: number) =>
      `© ${year} Felix Zuo. All public demos use sanitized or synthetic data.`,
    description:
      "Manufacturing project coordination and process improvement, backed by public synthetic-data tooling evidence.",
    footerNavigation: "Footer navigation",
    headline: profile.headline,
    site: "Site",
    syntheticOnly: "Synthetic data only",
    technology: "Next.js · Vercel-ready",
  },
  zh: {
    contact: "联系方式",
    copyright: (year: number) =>
      `© ${year} Felix Zuo。所有公开演示均使用脱敏或合成数据。`,
    description:
      "聚焦制造项目协调与流程改善，以可公开验证的合成数据工具作为成果证据。",
    footerNavigation: "页脚导航",
    headline: "制造项目协调与数字化流程改善",
    site: "站点导航",
    syntheticOnly: "仅使用合成数据",
    technology: "Next.js · 可部署至 Vercel",
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

export function SiteFooter() {
  const pathname = usePathname();
  const locale = useSyncExternalStore(
    subscribeToLocale,
    getLocaleSnapshot,
    getServerLocaleSnapshot,
  );
  const copy = UI_COPY[locale];

  if (pathname === "/") return null;

  return (
    <footer className="site-footer border-t hairline bg-[#04060c]">
      <div className="mx-auto grid max-w-6xl gap-10 px-5 py-14 md:grid-cols-[1.3fr_0.7fr_1fr]">
        <div>
          <p className="font-semibold text-slate-100">Felix Zuo</p>
          <p className="mono-label mt-2 text-slate-500">{copy.headline}</p>
          <p className="mt-5 max-w-sm text-sm leading-6 text-slate-400">
            {copy.description}
          </p>
        </div>
        <nav aria-label={copy.footerNavigation}>
          <p className="mono-label text-slate-500">{copy.site}</p>
          <ul className="mt-4 space-y-2.5">
            {navigation.map((item) => (
              <li key={item.href}>
                <a className="text-sm text-slate-400 transition-colors hover:text-slate-100" href={`/${item.href}`}>
                  {NAV_LABELS[item.href]?.[locale] ?? item.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div>
          <p className="mono-label text-slate-500">{copy.contact}</p>
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
            {copy.syntheticOnly}
          </p>
        </div>
      </div>
      <div className="border-t hairline">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-5">
          <p className="text-xs text-slate-600">{copy.copyright(new Date().getFullYear())}</p>
          <p className="mono-label text-slate-600">{copy.technology}</p>
        </div>
      </div>
    </footer>
  );
}
