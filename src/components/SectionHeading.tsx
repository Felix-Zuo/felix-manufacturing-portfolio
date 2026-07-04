type SectionHeadingProps = {
  index: string;
  eyebrow: string;
  title: string;
  summary?: string;
};

export function SectionHeading({ index, eyebrow, title, summary }: SectionHeadingProps) {
  return (
    <div className="mb-12 max-w-3xl">
      <p className="mono-label flex items-center gap-3 text-amber-400/90">
        <span className="text-slate-600">{index}</span>
        <span className="h-px w-8 bg-amber-400/50" aria-hidden="true" />
        {eyebrow}
      </p>
      <h2 className="mt-4 text-3xl font-semibold tracking-tight text-slate-100 sm:text-4xl">{title}</h2>
      {summary && <p className="mt-4 text-base leading-7 text-slate-400">{summary}</p>}
    </div>
  );
}
