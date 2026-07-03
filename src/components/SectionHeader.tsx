type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  summary: string;
  inverse?: boolean;
};

export function SectionHeader({ eyebrow, title, summary, inverse = false }: SectionHeaderProps) {
  return (
    <div className="mb-8 max-w-3xl">
      <p className={`mb-3 text-sm font-semibold uppercase ${inverse ? "text-amber-300" : "text-blue-700"}`}>
        {eyebrow}
      </p>
      <h2 className={`text-3xl font-semibold ${inverse ? "text-white" : "text-slate-950"}`}>{title}</h2>
      <p className={`mt-4 text-base leading-7 ${inverse ? "text-slate-300" : "text-slate-600"}`}>{summary}</p>
    </div>
  );
}

