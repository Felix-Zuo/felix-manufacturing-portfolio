import { ShieldCheck } from "lucide-react";

import { profile } from "@/data/profile";

export function ConfidentialityNotice({
  compact = false,
  text = profile.confidentiality,
}: {
  compact?: boolean;
  text?: string;
}) {
  return (
    <aside className="rounded-md border border-emerald-400/25 bg-emerald-950/25 p-5">
      <div className="flex gap-3.5">
        <ShieldCheck className="mt-0.5 h-5 w-5 flex-none text-emerald-400" aria-hidden="true" />
        <div>
          <h3 className="mono-label text-emerald-300">Public confidentiality boundary</h3>
          <p className={`mt-2.5 leading-7 text-slate-400 ${compact ? "text-sm" : "text-[15px]"}`}>{text}</p>
        </div>
      </div>
    </aside>
  );
}
