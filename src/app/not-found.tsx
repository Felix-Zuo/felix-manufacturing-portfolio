import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-5 text-white">
      <section className="max-w-xl rounded-lg border border-slate-700 bg-slate-900 p-8">
        <p className="text-sm font-semibold uppercase tracking-wider text-amber-300">404</p>
        <h1 className="mt-3 text-3xl font-semibold">Case study not found</h1>
        <p className="mt-4 leading-7 text-slate-300">
          The requested portfolio page is not part of the current public case-study set.
        </p>
        <Link
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-emerald-500 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400"
          href="/"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to portfolio
        </Link>
      </section>
    </main>
  );
}
