"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "framer-motion";

type Station = {
  id: string;
  takt: string;
  util: number;
  bottleneck?: boolean;
};

const stations: Station[] = [
  { id: "FEED", takt: "3.0s", util: 0.92 },
  { id: "PROC-A", takt: "7.4s", util: 0.74 },
  { id: "PROC-B", takt: "13.6s", util: 0.97, bottleneck: true },
  { id: "QA", takt: "4.0s", util: 0.63 },
  { id: "PACK", takt: "5.2s", util: 0.58 },
];

function format(seconds: number) {
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

export function HeroConsole() {
  const reduceMotion = useReducedMotion();
  const [elapsed, setElapsed] = useState(84);
  const [output, setOutput] = useState(26);

  useEffect(() => {
    if (reduceMotion) return;
    const timer = setInterval(() => {
      setElapsed((t) => t + 1);
      setOutput((n) => (Math.random() > 0.55 ? n + 1 : n));
    }, 1000);
    return () => clearInterval(timer);
  }, [reduceMotion]);

  return (
    <div className="surface-card overflow-hidden rounded-md shadow-[0_24px_80px_-32px_rgba(2,6,17,0.9)]">
      {/* header */}
      <div className="flex items-center justify-between border-b hairline px-4 py-3">
        <span className="mono-label flex items-center gap-2 text-slate-300">
          <span className="status-dot h-1.5 w-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
          Line simulation
        </span>
        <span className="mono-label text-emerald-400/90">Synthetic data</span>
      </div>

      {/* stations + flow */}
      <div className="relative px-4 pb-2 pt-5">
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          {stations.map((station) => (
            <div
              className={`min-w-0 rounded-md border bg-[#0a101d] px-2.5 py-2 ${
                station.bottleneck ? "console-bottleneck border-amber-400/70" : "border-slate-700/60"
              }`}
              key={station.id}
            >
              <p className="break-words font-mono text-[11px] font-semibold text-slate-200">{station.id}</p>
              <p className="mt-0.5 font-mono text-[10px] text-slate-500">Takt {station.takt}</p>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-slate-800">
                <div
                  className={`console-util h-full w-full rounded-full ${
                    station.bottleneck ? "bg-amber-400" : "bg-sky-400/80"
                  }`}
                  style={{ "--util": station.util } as React.CSSProperties}
                />
              </div>
            </div>
          ))}
        </div>
        {stations[2] && (
          <p className="mono-label mt-2 text-right text-amber-400/90">▲ bottleneck {stations[2].id}</p>
        )}

        {/* transfer rail with travelling parts */}
        <div className="relative mt-1 h-8">
          <div className="absolute left-[2%] right-[3%] top-1/2 h-px bg-slate-700/80" aria-hidden="true" />
          {[0, 1.5, 3, 4.5, 6].map((delay) => (
            <span
              aria-hidden="true"
              className="console-part absolute top-1/2 h-2 w-2 -translate-y-1/2 rounded-[2px] bg-sky-300 shadow-[0_0_8px_rgba(125,211,252,0.8)]"
              key={delay}
              style={{ animationDelay: `${delay}s` }}
            />
          ))}
        </div>
      </div>

      {/* readouts */}
      <div className="grid grid-cols-2 border-t hairline sm:grid-cols-4">
        {[
          { label: "Elapsed", value: `t+${format(elapsed)}` },
          { label: "Output", value: `${output} pcs` },
          { label: "Capacity", value: "236 pcs/h" },
          { label: "Balance", value: "27.8%" },
        ].map((readout, index) => (
          <div
            className={`min-w-0 px-3 py-3 ${index % 2 === 1 ? "border-l hairline" : ""} ${
              index >= 2 ? "border-t hairline sm:border-t-0" : ""
            } ${index === 2 ? "sm:border-l" : ""}`}
            key={readout.label}
          >
            <p className="mono-label text-slate-500">{readout.label}</p>
            <p className="mt-1 font-mono text-xs font-semibold tabular-nums text-slate-100 sm:text-sm">{readout.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
