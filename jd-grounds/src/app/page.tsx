import Link from "next/link";
import type { Metadata } from "next";
import { areas, business, howItWorks, sectors, services, trustPoints } from "@/lib/site";
import { Button, Check, Container, Eyebrow, GroundLine, SectionHeading } from "@/components/ui";
import { SectorIcon, ServiceIcon, MailIcon, PhoneIcon } from "@/components/Icons";
import { Photo } from "@/components/Photo";
import { CtaBand } from "@/components/CtaBand";

export const metadata: Metadata = {
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-green-950 text-cream-50">
        <div aria-hidden className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,rgb(42_107_69_/_0.6),transparent_55%)]" />
        <Container className="relative grid items-center gap-10 py-14 sm:py-20 lg:grid-cols-[1.1fr_1fr] lg:py-24">
          <div>
            <Eyebrow tone="light">St Austell · Cornwall</Eyebrow>
            <h1 className="mt-4 text-4xl font-extrabold tracking-tight text-balance sm:text-5xl lg:text-[3.4rem] lg:leading-[1.05]">
              Commercial grass cutting and grounds care for St Austell and surrounds
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-green-100 sm:text-xl">
              Regular cuts, hedges, seasonal tidy-ups and one-off clear-ups for hotels, holiday parks, business parks,
              schools, care homes and pubs. Shaped to your site, on a schedule you can rely on.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button href="/contact" variant="secondary" size="lg">
                Get a free quote
              </Button>
              <Button href="/services" variant="light" size="lg">
                See what we do
              </Button>
            </div>
            <p className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-green-100">
              <a href={business.phoneHref} className="inline-flex items-center gap-2 font-semibold hover:text-earth-400">
                <PhoneIcon className="h-4 w-4" /> {business.phone}
              </a>
              <a href={`mailto:${business.email}`} className="inline-flex items-center gap-2 font-semibold break-all hover:text-earth-400">
                <MailIcon className="h-4 w-4" /> {business.email}
              </a>
            </p>
          </div>
          <div className="relative">
            <Photo slot="hero" priority className="aspect-[4/3] rounded-3xl shadow-lift ring-1 ring-cream-100/10 lg:aspect-[5/4]" />
            <div className="absolute -bottom-4 -left-2 hidden rounded-2xl bg-cream-100 px-5 py-4 text-green-950 shadow-lift sm:block">
              <p className="text-xs font-bold tracking-[0.18em] text-green-700 uppercase">Free quotes</p>
              <p className="mt-1 text-sm font-semibold">Written scope. No obligation.</p>
            </div>
          </div>
        </Container>
        <GroundLine />
      </section>

      {/* Trust strip */}
      <section aria-label="Why JD Grounds" className="bg-cream-100">
        <Container className="-mt-2 py-6 sm:py-8">
          <ul className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm font-semibold text-green-900 sm:text-[15px]">
            {trustPoints.map((t) => (
              <li key={t} className="inline-flex items-center gap-2">
                <Check className="h-5 w-5 text-green-700" /> {t}
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* Who we help */}
      <section className="texture bg-cream-100 py-16 sm:py-20">
        <Container>
          <SectionHeading
            eyebrow="Who we help"
            title="Grounds care built around commercial sites"
            intro="Every site has its own rhythm: changeover days, term times, opening hours. We plan the work around yours, not the other way round."
          />
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {sectors.map((s) => (
              <li key={s.slug} className="group rounded-2xl border border-green-900/10 bg-white p-6 shadow-soft transition-shadow hover:shadow-lift">
                <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-green-100 text-green-800">
                  <SectorIcon name={s.icon} />
                </div>
                <h3 className="mt-4 text-lg font-extrabold text-green-950">{s.title}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-muted">{s.blurb}</p>
              </li>
            ))}
            <li className="flex flex-col justify-between rounded-2xl bg-green-900 p-6 text-cream-50 shadow-soft">
              <div>
                <p className="text-xs font-bold tracking-[0.18em] text-green-200 uppercase">Something else?</p>
                <h3 className="mt-3 text-lg font-extrabold">If it&rsquo;s a commercial site with grass and hedges, ask.</h3>
                <p className="mt-2 text-[15px] text-green-100">Churches, clubs, community buildings, car parks, land agents. We&rsquo;ll tell you honestly if we can help.</p>
              </div>
              <Button href="/contact" variant="secondary" className="mt-6 self-start">
                Ask about your site
              </Button>
            </li>
          </ul>
        </Container>
      </section>

      {/* Services snapshot */}
      <section className="bg-white py-16 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-[1fr_1.2fr] lg:items-center">
          <div>
            <SectionHeading
              eyebrow="What we do"
              title="Straightforward services, done properly"
              intro="No price lists, no packages. We look at the site, agree what needs doing and how often, and put it in writing."
            />
            <Button href="/services" variant="ghost" className="mt-6">
              All services in detail
            </Button>
          </div>
          <ul className="grid gap-3 sm:grid-cols-2">
            {services.map((s) => (
              <li key={s.slug}>
                <Link
                  href={`/services#${s.slug}`}
                  className="flex h-full gap-4 rounded-2xl border border-green-900/10 bg-cream-50 p-5 transition-colors hover:border-green-700/40 hover:bg-green-50"
                >
                  <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-green-800 text-cream-50">
                    <ServiceIcon name={s.icon} className="h-6 w-6" />
                  </span>
                  <span>
                    <span className="block font-extrabold text-green-950">{s.title}</span>
                    <span className="mt-1 block text-sm leading-relaxed text-muted">{s.summary}</span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* How it works */}
      <section className="bg-green-950 py-16 text-cream-50 sm:py-20">
        <Container>
          <SectionHeading
            tone="light"
            eyebrow="How it works"
            title="Three steps to a tidy site"
            intro="No forms to fill in triplicate. A quick conversation, a look at the grounds, and a clear quote."
          />
          <ol className="mt-10 grid gap-5 md:grid-cols-3">
            {howItWorks.map((step) => (
              <li key={step.step} className="relative rounded-2xl border border-green-100/15 bg-green-900/60 p-6">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-earth-400 text-lg font-extrabold text-green-950">
                  {step.step}
                </span>
                <h3 className="mt-4 text-xl font-extrabold">{step.title}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-green-100">{step.text}</p>
              </li>
            ))}
          </ol>
        </Container>
      </section>

      {/* Areas */}
      <section className="texture bg-cream-100 py-16 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-[1.2fr_1fr] lg:items-center">
          <div>
            <SectionHeading
              eyebrow="Where we work"
              title="St Austell and the surrounding towns and villages"
              intro="We're based in St Austell and cover the coast and countryside around it. Not sure if you're in range? Ask; it's usually yes."
            />
            <ul className="mt-6 flex flex-wrap gap-2">
              {areas.map((a) => (
                <li key={a} className="rounded-full border border-green-900/15 bg-white px-3.5 py-1.5 text-sm font-semibold text-green-900">
                  {a}
                </li>
              ))}
            </ul>
            <Button href="/areas" variant="ghost" className="mt-6">
              More about our service area
            </Button>
          </div>
          <Photo slot="areas" className="aspect-[4/3] rounded-3xl shadow-soft" />
        </Container>
      </section>

      <CtaBand />
    </>
  );
}
