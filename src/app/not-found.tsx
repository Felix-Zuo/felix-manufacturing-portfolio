import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <main className="flex min-h-screen items-center justify-center px-5 pt-16">
      <section className="surface-card max-w-xl rounded-xl p-8">
        <p className="mono-label text-amber-400/90">404</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-100">Page not found</h1>
        <p className="mt-4 leading-7 text-slate-400">
          The requested page is not part of the current public portfolio.
        </p>
        <Link
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-amber-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-amber-300"
          href="/"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to portfolio
        </Link>
      </section>
    </main>
  );
}
