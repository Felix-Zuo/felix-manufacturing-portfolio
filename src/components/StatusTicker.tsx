const readouts = [
  "NOTICE PREP 20-40 MIN → <1 MIN",
  "TRIAL TAKT CYCLE 3 DAYS → 1 DAY",
  "TRIAL SCRAP −90%",
  "EST. SAVING RMB 20,000 / CHANGEOVER",
  "DASHBOARD ADOPTED IN DEPT. REPORTING",
  "SYNTHETIC DATA ONLY — NO FACTORY FILES",
];

export function StatusTicker() {
  const row = readouts.map((item) => (
    <span className="inline-flex items-center gap-6 pr-6" key={item}>
      <span className="whitespace-nowrap">{item}</span>
      <span aria-hidden="true" className="text-amber-400/70">
        ◆
      </span>
    </span>
  ));

  return (
    <div aria-label="Key outcome readouts" className="overflow-hidden border-y hairline bg-[#070c16]">
      <div className="ticker-track mono-label flex w-max items-center py-3 text-slate-400">
        <span aria-hidden="false">{row}</span>
        <span aria-hidden="true">{row}</span>
      </div>
    </div>
  );
}
