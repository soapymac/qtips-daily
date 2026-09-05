import type { Metadata } from "next";
import { areas } from "@/lib/site";
import { Button, Container, PageHero, SectionHeading } from "@/components/ui";
import { PinIcon } from "@/components/Icons";
import { Photo } from "@/components/Photo";
import { CtaBand } from "@/components/CtaBand";

export const metadata: Metadata = {
  title: "Areas covered: St Austell and surrounding towns and villages",
  description:
    "JD Grounds covers St Austell, Charlestown, Carlyon Bay, Pentewan, Mevagissey, Fowey, Bugle, Holmbush, London Apprentice, Gorran, Carthew and the surrounding area of mid and south Cornwall.",
  alternates: { canonical: "/areas" },
  openGraph: { url: "/areas", title: "Areas covered | JD Grounds" },
};

const clusters = [
  { name: "St Austell and town edges", places: ["St Austell", "Holmbush", "Carthew", "Trewoon", "Polgooth", "Sticker", "Bugle", "Roche"] },
  { name: "The coast", places: ["Charlestown", "Carlyon Bay", "Par", "Pentewan", "Mevagissey", "Gorran", "Fowey"] },
  { name: "Villages and valleys", places: ["London Apprentice", "St Blazey", "Tywardreath", "Lostwithiel", "Grampound"] },
];

export default function AreasPage() {
  return (
    <>
      <PageHero
        eyebrow="Areas covered"
        title="Based in St Austell. Working across the surrounding coast and countryside."
        intro="Holiday parks on the coast, business parks by the A390, estates and schools in the villages. If your site is around St Austell, we can almost certainly get to it on a regular schedule."
      >
        <div className="mt-8">
          <Button href="/contact" variant="secondary" size="lg">
            Check we cover your site
          </Button>
        </div>
      </PageHero>

      <section className="bg-cream-100 py-14 sm:py-20">
        <Container className="grid gap-10 lg:grid-cols-[1fr_1fr] lg:items-start">
          <div>
            <SectionHeading
              eyebrow="Towns and villages"
              title="Where we regularly work"
              intro="Grouped roughly by direction. Somewhere not listed? Ask. Being local means short travel times and reliable visits, so we keep the area sensible rather than sprawling."
            />
            <div className="mt-8 space-y-6">
              {clusters.map((c) => (
                <div key={c.name}>
                  <h3 className="inline-flex items-center gap-2 text-sm font-bold tracking-[0.12em] text-green-800 uppercase">
                    <PinIcon className="h-4 w-4" /> {c.name}
                  </h3>
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {c.places.map((p) => (
                      <li key={p} className="rounded-full border border-green-900/15 bg-white px-3.5 py-1.5 text-sm font-semibold text-green-950">
                        {p}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
          <div className="lg:sticky lg:top-28">
            <Photo slot="areas" className="aspect-[4/3] rounded-3xl shadow-soft" />
            <div className="mt-5 rounded-2xl border border-green-900/10 bg-white p-6">
              <h3 className="font-extrabold text-green-950">Multi-site contracts</h3>
              <p className="mt-2 text-[15px] leading-relaxed text-muted">
                Managing several sites across the area? We can put them on one schedule with one point of contact and one invoice, so you&rsquo;re not juggling contractors.
              </p>
            </div>
          </div>
        </Container>
      </section>

      <section className="bg-white py-12">
        <Container>
          <p className="text-sm text-muted">
            Full list: {areas.join(", ")} and the surrounding area.
          </p>
        </Container>
      </section>

      <CtaBand title="Somewhere near St Austell?" text="Tell us where the site is and what it needs. We'll confirm we cover it and come back with a written quote." />
    </>
  );
}
