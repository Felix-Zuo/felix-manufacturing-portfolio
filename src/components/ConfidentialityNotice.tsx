import { ShieldCheck } from "lucide-react";

import { profile } from "@/data/profile";

export function ConfidentialityNotice({ compact = false }: { compact?: boolean }) {
  return (
    <aside className="rounded-lg border border-emerald-300 bg-emerald-950 p-5 text-emerald-50">
      <div className="flex gap-3">
        <ShieldCheck className="mt-1 h-5 w-5 flex-none text-emerald-300" aria-hidden="true" />
        <div>
          <h3 className="font-semibold">Public confidentiality boundary</h3>
          <p className={`mt-2 leading-7 text-emerald-100 ${compact ? "text-sm" : "text-base"}`}>
            {profile.confidentiality}
          </p>
        </div>
      </div>
    </aside>
  );
}

