import type { Metadata } from "next";
import { sectors, services } from "@/lib/site";
import { Button, Check, Container, PageHero, SectionHeading } from "@/components/ui";
import { ServiceIcon } from "@/components/Icons";
import { Photo } from "@/components/Photo";
import { CtaBand } from "@/components/CtaBand";

export const metadata: Metadata = {
  title: "Services: grass cutting, grounds maintenance and landscaping",
  description:
    "Regular commercial grass cutting, grounds maintenance, one-off clear-ups, practical landscaping and flexible scheduled visits around St Austell, Cornwall. Free, no-obligation quotes.",
  alternates: { canonical: "/services" },
  openGraph: { url: "/services", title: "Services | JD Grounds" },
};

export default function ServicesPage() {
  return (
    <>
      <PageHero
        eyebrow="Services"
        title="Grass cutting, grounds maintenance and practical landscaping"
        intro="Everything a commercial site needs to look cared for through the year. We agree the scope with you up front and put it in writing, so you know exactly what's covered."
      >
        <div className="mt-8 flex flex-wrap gap-3">
          <Button href="/contact" variant="secondary" size="lg">
            Get a free quote
          </Button>
          <Button href="/services-sheet" variant="light" size="lg">
            Printable services sheet
          </Button>
        </div>
      </PageHero>

      <section className="bg-cream-100 py-14 sm:py-20">
        <Container>
          <nav aria-label="On this page" className="flex flex-wrap gap-2">
            {services.map((s) => (
              <a
                key={s.slug}
                href={`#${s.slug}`}
                className="rounded-full border border-green-900/15 bg-white px-3.5 py-1.5 text-sm font-semibold text-green-900 hover:border-green-700"
              >
                {s.title}
              </a>
            ))}
          </nav>

          <div className="mt-12 space-y-8">
            {services.map((s, i) => (
              <article
                key={s.slug}
                id={s.slug}
                className="scroll-mt-24 grid gap-8 rounded-3xl border border-green-900/10 bg-white p-6 shadow-soft sm:p-8 lg:grid-cols-[1.3fr_1fr]"
              >
                <div>
                  <div className="flex items-center gap-4">
                    <span className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-green-800 text-cream-50">
                      <ServiceIcon name={s.icon} />
                    </span>
                    <h2 className="text-2xl font-extrabold tracking-tight text-green-950 sm:text-3xl">{s.title}</h2>
                  </div>
                  <p className="mt-4 text-lg font-semibold text-green-900">{s.summary}</p>
                  <p className="mt-3 leading-relaxed text-muted">{s.detail}</p>
                </div>
                <div className="rounded-2xl bg-cream-50 p-5 sm:p-6">
                  <h3 className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Typically includes</h3>
                  <ul className="mt-3 space-y-2.5">
                    {s.includes.map((item) => (
                      <li key={item} className="flex items-start gap-2.5 text-[15px] text-ink">
                        <Check className="mt-0.5 h-5 w-5 shrink-0 text-green-700" /> {item}
                      </li>
                    ))}
                  </ul>
                  {i === 0 && (
                    <p className="mt-4 text-sm text-muted">Frequency and scope are agreed per site and can change with the season.</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        </Container>
      </section>

      <section className="bg-white py-14 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-2 lg:items-center">
          <Photo slot="services" className="aspect-[4/3] rounded-3xl shadow-soft" />
          <div>
            <SectionHeading
              eyebrow="Pricing"
              title="Free, no-obligation quotes"
              intro="We don't publish rates because no two sites are the same. A holiday park with twelve acres and a Friday changeover is a different job to a care home lawn with a hedge. We look, we listen, and we quote in writing."
            />
            <ul className="mt-6 space-y-2.5 text-[15px]">
              {["Written scope so nothing is assumed", "Frequency that suits the site and the season", "Clear about what's included and what isn't", "No obligation and no hard sell"].map((t) => (
                <li key={t} className="flex items-start gap-2.5">
                  <Check className="mt-0.5 h-5 w-5 shrink-0 text-green-700" /> {t}
                </li>
              ))}
            </ul>
            <Button href="/contact" className="mt-7" size="lg">
              Request a quote
            </Button>
          </div>
        </Container>
      </section>

      <section className="texture bg-cream-100 py-14 sm:py-20">
        <Container>
          <SectionHeading
            eyebrow="By site type"
            title="What different sites usually need"
            intro="A rough guide. We'll shape the plan to your grounds when we visit."
          />
          <ul className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sectors.map((s) => (
              <li key={s.slug} className="rounded-2xl border border-green-900/10 bg-white p-5">
                <h3 className="font-extrabold text-green-950">{s.title}</h3>
                <ul className="mt-3 flex flex-wrap gap-1.5">
                  {s.needs.map((n) => (
                    <li key={n} className="rounded-full bg-green-100 px-2.5 py-1 text-xs font-semibold text-green-900">
                      {n}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
          <p className="mt-8 max-w-2xl text-sm text-muted">
            For golf clubs and schools we support the areas around the playing surfaces: amenity and overflow grass, hedges, car parks, approaches and winter works. We don&rsquo;t offer greenkeeping or sports-turf agronomy.
          </p>
        </Container>
      </section>

      <CtaBand />
    </>
  );
}
