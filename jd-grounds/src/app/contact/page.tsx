import type { Metadata } from "next";
import { business } from "@/lib/site";
import { Container, PageHero } from "@/components/ui";
import { MailIcon, PhoneIcon, PinIcon } from "@/components/Icons";
import { QuoteForm } from "@/components/QuoteForm";

export const metadata: Metadata = {
  title: "Contact: get a free quote",
  description:
    "Request a free, no-obligation quote for commercial grass cutting or grounds maintenance around St Austell. Email jdouqa@hotmail.co.uk or call 07944 201086.",
  alternates: { canonical: "/contact" },
  openGraph: { url: "/contact", title: "Contact | JD Grounds" },
};

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="Get a free, no-obligation quote"
        intro="Tell us a bit about the site and what you need. We'll come back to you, arrange a look round if it helps, and send a written quote."
      />

      <section className="bg-cream-100 py-14 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-[1fr_1.5fr] lg:items-start">
          <aside className="space-y-5 lg:sticky lg:top-28">
            <div className="rounded-2xl border border-green-900/10 bg-white p-6 shadow-soft">
              <h2 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Direct contact</h2>
              <ul className="mt-4 space-y-4">
                <li>
                  <a href={`mailto:${business.email}`} className="group flex items-start gap-3">
                    <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-800">
                      <MailIcon />
                    </span>
                    <span>
                      <span className="block text-sm text-muted">Email</span>
                      <span className="block font-semibold break-all text-green-950 group-hover:underline">{business.email}</span>
                    </span>
                  </a>
                </li>
                <li>
                  <a href={business.phoneHref} className="group flex items-start gap-3">
                    <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-800">
                      <PhoneIcon />
                    </span>
                    <span>
                      <span className="block text-sm text-muted">Phone</span>
                      <span className="block font-semibold text-green-950 group-hover:underline">{business.phone}</span>
                    </span>
                  </a>
                </li>
                <li className="flex items-start gap-3">
                  <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-green-100 text-green-800">
                    <PinIcon />
                  </span>
                  <span>
                    <span className="block text-sm text-muted">Based in</span>
                    <span className="block font-semibold text-green-950">{business.region}</span>
                  </span>
                </li>
              </ul>
            </div>
            <div className="rounded-2xl bg-green-900 p-6 text-cream-50">
              <h2 className="font-extrabold">What happens next</h2>
              <ol className="mt-3 list-decimal space-y-2 pl-5 text-[15px] text-green-100">
                <li>We reply to confirm we cover the site and ask anything we need to.</li>
                <li>A quick visit or phone walk-through of the grounds.</li>
                <li>A written quote with the scope and frequency spelled out.</li>
              </ol>
            </div>
          </aside>

          <div className="rounded-3xl border border-green-900/10 bg-white p-6 shadow-soft sm:p-8">
            <h2 className="text-2xl font-extrabold tracking-tight text-green-950">Quote request</h2>
            <p className="mt-2 text-muted">Fields marked * are required. We don&rsquo;t share your details with anyone.</p>
            <div className="mt-6">
              <QuoteForm />
            </div>
          </div>
        </Container>
      </section>
    </>
  );
}
