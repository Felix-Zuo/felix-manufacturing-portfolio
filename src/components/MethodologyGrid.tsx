import { methodology } from "@/data/methodology";
import { Reveal } from "./Reveal";

export function MethodologyGrid() {
  return (
    <div className="grid gap-px overflow-hidden rounded-xl border hairline bg-slate-800/40 md:grid-cols-2 xl:grid-cols-4">
      {methodology.map((pillar, index) => (
        <Reveal className="h-full" delay={index * 0.05} key={pillar.title}>
          <article className="flex h-full flex-col bg-[#080d18] p-6 transition-colors hover:bg-[#0a101d]">
            <p className="mono-label text-amber-400/80">{String(index + 1).padStart(2, "0")}</p>
            <h3 className="mt-3 text-lg font-semibold tracking-tight text-slate-100">{pillar.title}</h3>
            <p className="mt-2.5 text-sm leading-6 text-slate-500">{pillar.summary}</p>
            <ul className="mt-5 space-y-2 text-sm text-slate-400">
              {pillar.practices.map((practice) => (
                <li className="flex gap-2.5" key={practice}>
                  <span className="mt-[9px] h-px w-3 flex-none bg-emerald-400/60" aria-hidden="true" />
                  <span>{practice}</span>
                </li>
              ))}
            </ul>
          </article>
        </Reveal>
      ))}
    </div>
  );
}
