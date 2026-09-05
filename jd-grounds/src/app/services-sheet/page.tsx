import type { Metadata } from "next";
import Link from "next/link";
import { areas, business, sectors, services, trustPoints } from "@/lib/site";
import { Logo } from "@/components/Logo";
import { Check } from "@/components/ui";
import { PrintButton } from "./PrintButton";

export const metadata: Metadata = {
  title: "Services sheet (print)",
  description: "One-page printable summary of JD Grounds services, sectors and contact details.",
  alternates: { canonical: "/services-sheet" },
  robots: { index: false, follow: true },
};

export default function ServicesSheetPage() {
  return (
    <div className="bg-white">
      <div className="print-hidden border-b border-green-900/10 bg-cream-100">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3 px-5 py-3 text-sm">
          <p className="text-muted">
            One-page services sheet, formatted for A4. Attach it to quotes or hand it over on site visits.
          </p>
          <div className="flex gap-2">
            <Link href="/services" className="rounded-full border-2 border-green-800 px-4 py-1.5 font-semibold text-green-900 hover:bg-green-100">
              Back to services
            </Link>
            <PrintButton />
          </div>
        </div>
      </div>

      <article className="mx-auto max-w-3xl overflow-x-hidden px-5 py-10 text-[13.5px] leading-snug text-ink sm:px-6 print:max-w-none print:overflow-visible print:px-0 print:py-0">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b-2 border-green-900 pb-4 print:flex-nowrap print:gap-6">
          <div>
            <Logo className="h-11 w-auto" />
            <p className="mt-2 text-base font-extrabold text-green-950">{business.tagline}</p>
          </div>
          <address className="text-[13px] not-italic sm:text-right print:text-right">
            <p className="font-bold">{business.phone}</p>
            <p className="font-bold">{business.email}</p>
            <p className="text-muted">{business.region}, UK</p>
          </address>
        </header>

        <ul className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs font-semibold text-green-900">
          {trustPoints.map((t) => (
            <li key={t} className="inline-flex items-center gap-1">
              <Check className="h-3.5 w-3.5" /> {t}
            </li>
          ))}
        </ul>

        <section className="mt-5">
          <h2 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Services</h2>
          <div className="mt-2 grid gap-x-6 gap-y-3 sm:grid-cols-2 print:grid-cols-2">
            {services.map((s) => (
              <div key={s.slug} className="break-inside-avoid">
                <h3 className="font-extrabold text-green-950">{s.title}</h3>
                <p className="text-muted">{s.summary}</p>
                <p className="mt-0.5 text-[12px] text-ink">{s.includes.slice(0, 4).join(" · ")}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-5">
          <h2 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Who we work with</h2>
          <p className="mt-1.5">{sectors.map((s) => s.title).join(" · ")}</p>
        </section>

        <section className="mt-5 grid gap-6 sm:grid-cols-[1.4fr_1fr] print:grid-cols-[1.4fr_1fr]">
          <div>
            <h2 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">How it works</h2>
            <ol className="mt-1.5 list-decimal space-y-1 pl-5">
              <li>Get in touch: email, call, or use the quote form on the website.</li>
              <li>We visit the site or walk it through with you by phone.</li>
              <li>You receive a written quote with scope and frequency spelled out. No obligation.</li>
            </ol>
          </div>
          <div>
            <h2 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Areas covered</h2>
            <p className="mt-1.5 text-[12.5px]">{areas.join(", ")} and surrounds.</p>
          </div>
        </section>

        <section className="mt-5 rounded-lg border border-green-900/20 bg-cream-50 p-4 print:bg-white">
          <h2 className="font-extrabold text-green-950">Pricing</h2>
          <p className="mt-1">
            Free, no-obligation quotes, priced per site after a look at the grounds. No published rates because every site is different. Fully insured for commercial work; certificate available on request.
          </p>
        </section>

        <footer className="mt-6 flex flex-wrap items-center justify-between gap-1 border-t border-green-900/20 pt-3 text-[11.5px] text-muted">
          <p>{business.name} · {business.region}</p>
          <p>
            {business.phone} · {business.email}
          </p>
        </footer>
      </article>
    </div>
  );
}
